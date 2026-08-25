"""
Generate Quant Buffet draft posts + in-house backtests for 100 scraped papers.

Writes ONLY under backtest/drafts/new_100/ — never touches Prisma / published.
"""
from __future__ import annotations

import html
import json
import re
import sys
import time
import traceback
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import importlib.util  # noqa: E402

from backtest.codegen import render_strategy_body  # noqa: E402
from backtest.data import load_price_panel  # noqa: E402
from backtest.engine import EngineConfig, PortfolioEngine  # noqa: E402
from backtest.metrics import compute_metrics  # noqa: E402
from backtest.templates import build_strategy  # noqa: E402
from backtest.universes import WHITELIST  # noqa: E402

_bfc_spec = importlib.util.spec_from_file_location(
    "build_full_catalog", ROOT / "scripts" / "build_full_catalog.py"
)
_bfc = importlib.util.module_from_spec(_bfc_spec)
assert _bfc_spec.loader is not None
_bfc_spec.loader.exec_module(_bfc)
classify_always = _bfc.classify_always
extract_tickers = _bfc.extract_tickers

PAPERS = ROOT / "backtest" / "drafts" / "new_100" / "papers_raw.json"
OUT = ROOT / "backtest" / "drafts" / "new_100"
POSTS = OUT / "posts"
CODE = OUT / "code"
CURVES = OUT / "equity_curves"
CATALOG = OUT / "catalog.json"
SUMMARY = OUT / "backtest_summary.json"
LEADERBOARD = OUT / "leaderboard.json"
MANIFEST = OUT / "MANIFEST.md"


TEMPLATE_BLURB = {
    "sma_trend": "Hold each liquid ETF only when its price is above a long SMA; equal-weight the longs, cash otherwise.",
    "dual_ma": "Long when the fast SMA is above the slow SMA; equal-weight the longs.",
    "abs_momentum": "Hold assets with positive trailing return; equal-weight the winners.",
    "dual_momentum": "Pick the best absolute/relative momentum asset; fall back to T-bills when momentum is negative.",
    "momentum_rotation": "Rank the book by trailing return and hold the top-N names equal-weight.",
    "equal_weight": "Buy and hold an equal-weight basket of the theme ETFs, rebalanced monthly.",
    "mean_reversion": "Enter when short-horizon z-score is deeply negative; exit near zero.",
    "vol_target": "Scale exposure inversely to realized volatility toward a target annual vol.",
    "risk_parity": "Allocate inversely to asset volatility so risk contributions are roughly equal.",
}


def slugify(title: str, idx: int) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    s = re.sub(r"-{2,}", "-", s)[:72]
    return s or f"draft-strategy-{idx:03d}"


def short_title(paper_title: str) -> str:
    t = re.sub(r"\s+", " ", paper_title).strip()
    # Drop trailing subtitle after colon if very long
    if ":" in t and len(t) > 90:
        t = t.split(":", 1)[0].strip()
    if len(t) > 100:
        t = t[:97].rstrip() + "…"
    return t


def infer_meta(title: str, abstract: str = "") -> dict:
    # Weight title heavily — abstracts often mention other asset classes as benchmarks.
    t = (title or "").lower()
    a = (abstract or "")[:280].lower()
    low = f"{t} {t} {a}"
    asset_class = "ETFs"
    market = "equities"
    region = "United States"
    frequency = "Monthly"
    if any(k in t for k in ("crypto", "bitcoin", "ethereum")):
        asset_class, market, region = "crypto", "cryptocurrency", "Global"
    elif any(k in t for k in ("bond", "treasury", "fixed income", "credit", "corporate bond")):
        asset_class, market = "bonds", "fixed income"
    elif any(k in t for k in ("commodity", "cta", "futures")):
        asset_class, market, region = "commodities", "commodities", "Global"
    elif any(k in t for k in ("fx", "currency", "forex", "carry")):
        asset_class, market, region = "FX", "currencies", "Global"
    elif any(k in t for k in ("multi-asset", "asset allocation", "risk parity", "portfolio")):
        asset_class, market, region = "multi-asset", "multi-asset", "Global"
    elif "sector" in t or "industry" in t:
        market = "US sectors"
    if any(k in low for k in ("global", "international", "world", "emerging")):
        region = "Global"
    if any(k in t for k in ("china", "a-share", "csi")):
        region = "China"
    if any(k in t for k in ("daily", "intraday")):
        frequency = "Daily"
    elif "weekly" in t:
        frequency = "Weekly"
    return {
        "assetClass": asset_class,
        "region": region,
        "market": market,
        "frequency": frequency,
    }


def keywords_from(title: str, query: str) -> str:
    stop = {
        "the", "a", "an", "and", "or", "of", "in", "on", "for", "to", "with",
        "from", "by", "using", "based", "new", "evidence", "study", "paper",
    }
    words = re.findall(r"[A-Za-z]{4,}", f"{title} {query}")
    seen = []
    for w in words:
        lw = w.lower()
        if lw in stop or w in seen:
            continue
        seen.append(w.title() if w.islower() else w)
        if len(seen) >= 5:
            break
    return ", ".join(seen) if seen else "Trading, Strategy"


def authors_str(authors: list) -> str:
    names = [a.get("name") for a in (authors or []) if a.get("name")]
    return "; ".join(names[:8]) if names else "N/A"


def institute_str(insts: list) -> str:
    clean = [i for i in (insts or []) if i and "Museum" not in i and "Conference Board" not in i]
    # Prefer universities / research orgs
    uni = [i for i in clean if re.search(r"university|college|school|nber|institute", i, re.I)]
    pick = uni[:4] or clean[:4]
    return "; ".join(pick) if pick else "N/A"


def nutshell(template: str, assets: list[str], params: dict, abstract: str, fidelity: str) -> str:
    rule = TEMPLATE_BLURB.get(template, "Rule-based ETF allocation.")
    assets_s = ", ".join(assets)
    param_bits = []
    for k, v in (params or {}).items():
        if k == "cash_symbol":
            continue
        param_bits.append(f"{k}={v}")
    params_s = "; ".join(param_bits) if param_bits else "defaults"
    abs_snip = re.sub(r"\s+", " ", (abstract or "")).strip()
    if abs_snip.lower().startswith("abstract"):
        abs_snip = abs_snip[8:].strip()
    abs_snip = abs_snip[:420]
    proxy_note = ""
    if fidelity == "signal_unavailable_etf_proxy":
        proxy_note = (
            " Because the paper's primary signal (ML, sentiment, or proprietary data) is not "
            "available in our public ETF engine, this draft uses a liquid ETF rule that preserves "
            "the paper's economic theme rather than a bit-exact replication."
        )
    return (
        f"{rule} Universe: {assets_s}. Parameters: {params_s}. "
        f"Rebalanced on the engine's template schedule with 5 bps commission and 2 bps slippage."
        f"{proxy_note} Paper focus: {abs_snip}"
    )


def rationale(template: str, title: str, abstract: str) -> str:
    abs_snip = re.sub(r"\s+", " ", (abstract or "")).strip()[:500]
    base = {
        "sma_trend": (
            "Trend filters exploit persistent serial correlation in asset returns and "
            "reduce exposure when prices fall below a long-horizon average, cutting left-tail risk."
        ),
        "dual_momentum": (
            "Relative momentum captures cross-sectional continuation; absolute momentum "
            "gates risk when the trend is negative, shifting to cash."
        ),
        "momentum_rotation": (
            "Assets with stronger recent relative performance tend to continue outperforming "
            "over intermediate horizons; rotating into leaders harvests that premium."
        ),
        "vol_target": (
            "Volatility is more forecastable than expected returns; scaling down when vol is "
            "high improves risk-adjusted outcomes (volatility-managed portfolios)."
        ),
        "risk_parity": (
            "Equalizing risk contributions avoids concentration in the noisiest assets and "
            "stabilizes multi-asset drawdowns."
        ),
        "mean_reversion": (
            "Short-horizon overreaction produces temporary dislocations that reverse toward "
            "a local mean."
        ),
        "abs_momentum": (
            "Positive time-series momentum indicates a favorable trend state; holding only "
            "assets with positive trailing returns tilts toward that premium."
        ),
        "equal_weight": (
            "Diversified equal-weight exposure to the paper's theme captures the average "
            "premium without timing complexity."
        ),
        "dual_ma": (
            "Fast/slow moving-average crosses approximate a trend regime filter used widely "
            "in CTA-style timing."
        ),
    }.get(template, "The paper documents a systematic return pattern that can be harvested with liquid ETFs.")
    return f"{base} Related evidence from “{title}”: {abs_snip}"


def fmt_pct(x, digits=2) -> str:
    if x is None:
        return "N/A"
    try:
        return f"{float(x) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "N/A"


def fmt_num(x, digits=2) -> str:
    if x is None:
        return "N/A"
    try:
        return f"{float(x):.{digits}f}"
    except (TypeError, ValueError):
        return "N/A"


def metrics_block(m: dict | None) -> str:
    if not m:
        return "<p>Backtest pending or failed.</p>"
    rows = [
        ("Annualised Return", fmt_pct(m.get("cagr"))),
        ("Volatility", fmt_pct(m.get("volatility"))),
        ("Sharpe Ratio", fmt_num(m.get("sharpe"))),
        ("Sortino Ratio", fmt_num(m.get("sortino"))),
        ("Max Drawdown", fmt_pct(m.get("max_drawdown"))),
        ("Alpha (vs SPY)", fmt_pct(m.get("alpha"))),
        ("Beta (vs SPY)", fmt_num(m.get("beta"))),
        ("Win Rate", fmt_pct(m.get("win_rate")) if m.get("win_rate") is not None else "N/A"),
    ]
    lis = "".join(f"<li><strong>{k}:</strong> {v}</li>" for k, v in rows)
    return (
        "<p>In-house Quant Buffet engine (Yahoo Finance adjusted closes, daily bars, "
        "5 bps commission + 2 bps slip). DRAFT — not published.</p>"
        f"<ul>{lis}</ul>"
    )


def python_html(code: str) -> str:
    esc = html.escape(code)
    return f'<pre class="qb-python-pretty"><code class="language-python">{esc}</code></pre>'


def build_content_html(
    *,
    teaser: str,
    meta: dict,
    keywords: str,
    nutshell_text: str,
    rationale_text: str,
    paper_title: str,
    authors: str,
    institute: str,
    link: str,
    metrics_html: str,
    code_html: str,
) -> str:
    meta_line = (
        f"ASSET CLASS: {meta['assetClass']} | REGION: {meta['region']} | FREQUENCY: "
        f"{meta['frequency']} | MARKET: {meta['market']} | KEYWORD: {keywords}"
    )
    return f"""<p>{html.escape(teaser)}</p>
<p>{html.escape(meta_line)}</p>
<p><strong>I. STRATEGY IN A NUTSHELL</strong></p>
<p>{html.escape(nutshell_text)}</p>
<p><strong>II. ECONOMIC RATIONALE</strong></p>
<p>{html.escape(rationale_text)}</p>
<p><strong>III. SOURCE PAPER</strong></p>
<p><strong>Title:</strong> {html.escape(paper_title)}<br/>
<strong>Authors:</strong> {html.escape(authors)}<br/>
<strong>Institute:</strong> {html.escape(institute)}<br/>
<strong>Link:</strong> <a href="{html.escape(link or '#')}">{html.escape(link or 'N/A')}</a></p>
<p><strong>IV. BACKTEST PERFORMANCE</strong></p>
{metrics_html}
<p><strong>V. PYTHON CODE</strong></p>
{code_html}
<p><em>Status: DRAFT — not published to Quant Buffet.</em></p>
"""


def render_runner(slug: str, title: str, template: str, fidelity: str, assets: list[str], params: dict) -> str:
    body = render_strategy_body(template, assets, params or {})
    return f'''"""
Quant Buffet IN-HOUSE draft — {slug}
Title: {title}
Template: {template}
Fidelity: {fidelity}
Status: DRAFT (not published)

DATA SOURCE: Yahoo Finance via yfinance adjusted close · backtest.data.load_daily_prices
Costs: 5 bps commission + 2 bps slippage
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics

SLUG = {slug!r}
TITLE = {title!r}
TEMPLATE = {template!r}
FIDELITY = {fidelity!r}

{body}

def main() -> None:
    prices = load_daily_prices(ASSETS, start="2000-01-01").dropna(how="all")
    on_day, ready = make_on_day(prices)
    if ready is None or pd.isna(ready):
        raise SystemExit("signal never ready")
    engine = PortfolioEngine(prices, EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0))
    result = engine.run(on_day, start=ready)
    bench_sym = "SPY" if "SPY" in prices.columns else ASSETS[0]
    spy = prices[bench_sym].reindex(result.equity.index).ffill()
    bh = float(result.equity.iloc[0]) * (spy / spy.iloc[0])
    print(json.dumps(compute_metrics(result.equity, benchmark=bh, trades_count=len(result.trades)), indent=2))

if __name__ == "__main__":
    main()
'''


def downsample(equity: pd.Series, max_points: int = 80) -> list[dict]:
    if equity.empty:
        return []
    step = max(1, len(equity) // max_points)
    pts = [
        {"date": dt.strftime("%Y-%m-%d"), "equity": round(float(v), 2)}
        for dt, v in equity.iloc[::step].items()
    ]
    last_dt, last_v = equity.index[-1], float(equity.iloc[-1])
    if not pts or pts[-1]["date"] != last_dt.strftime("%Y-%m-%d"):
        pts.append({"date": last_dt.strftime("%Y-%m-%d"), "equity": round(last_v, 2)})
    return pts


def run_backtest(spec: dict, price_cache: dict[str, pd.Series]) -> dict:
    assets = list(spec["assets"])
    missing = [a for a in assets if a not in price_cache]
    if missing:
        return {"slug": spec["slug"], "status": "error", "error": f"missing prices: {missing}"}
    prices = pd.concat({a: price_cache[a] for a in assets}, axis=1).sort_index()
    prices = prices.apply(lambda c: c.ffill()).dropna(how="all")
    on_day, ready = build_strategy(spec["template"], prices, assets, spec.get("params") or {})
    if ready is None or pd.isna(ready):
        return {"slug": spec["slug"], "status": "error", "error": "signal never ready"}
    engine = PortfolioEngine(
        prices,
        EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0),
    )
    result = engine.run(on_day, start=ready)
    if result.equity.empty or len(result.equity) < 20:
        return {"slug": spec["slug"], "status": "error", "error": "equity too short"}
    bench_sym = "SPY" if "SPY" in price_cache else assets[0]
    spy = price_cache[bench_sym].reindex(result.equity.index).ffill()
    bh = float(result.equity.iloc[0]) * (spy / spy.iloc[0])
    metrics = compute_metrics(result.equity, benchmark=bh, trades_count=len(result.trades))
    curve_path = CURVES / f"{spec['slug']}.json"
    curve_path.write_text(
        json.dumps({"equity": downsample(result.equity), "benchmark": downsample(bh)}),
        encoding="utf-8",
    )
    return {
        "slug": spec["slug"],
        "title": spec["title"],
        "template": spec["template"],
        "assets": assets,
        "params": spec.get("params"),
        "fidelity": spec.get("fidelity"),
        "status": "ok",
        "metrics": metrics,
        "trades": len(result.trades),
        "curve_file": curve_path.name,
        "start": str(result.equity.index[0].date()),
        "end": str(result.equity.index[-1].date()),
    }


def classify_paper(paper: dict) -> tuple[str, dict, str, list[str]]:
    title = paper.get("title") or ""
    abstract = paper.get("abstract") or ""
    query = paper.get("_query") or ""
    low = f"{title}\n{abstract}\n{query}".lower()
    tickers = extract_tickers(f"{title}\n{abstract}")
    meta = infer_meta(title, abstract)

    # Title-level overrides before generic keyword cascade
    if re.search(r"volatility[\s\-‐‑–—]*managed|vol[\s\-]*managed|managed volatilit", low):
        assets = BOOKS_SPY_BIL()
        return (
            "vol_target",
            {"target_vol": 0.10, "vol_lookback": 63, "rebalance": "monthly"},
            "theme_proxy_vol_managed",
            assets,
        )

    template, params, fidelity, assets = classify_always(
        title=title,
        low=low,
        code="",
        has_qc=False,
        asset_class=meta["assetClass"],
        region=meta["region"],
    )
    if len(tickers) >= 2:
        assets = [t for t in tickers if t in WHITELIST or t in ("BTC-USD", "ETH-USD")][:12]
        if template == "dual_momentum" and "BIL" not in assets:
            assets = list(assets) + ["BIL"]
        fidelity = "paper_tickers_extracted"
    elif len(tickers) == 1:
        assets = tickers + (["BIL"] if tickers[0] != "BIL" else ["SHY"])
        fidelity = "paper_tickers_extracted"
    return template, params, fidelity, assets


def BOOKS_SPY_BIL() -> list[str]:
    return ["SPY", "BIL"]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    POSTS.mkdir(parents=True, exist_ok=True)
    CODE.mkdir(parents=True, exist_ok=True)
    CURVES.mkdir(parents=True, exist_ok=True)

    raw = json.loads(PAPERS.read_text(encoding="utf-8"))
    papers = raw["papers"]
    print(f"Building drafts for {len(papers)} papers…")

    specs = []
    used_slugs: set[str] = set()
    for i, p in enumerate(papers, 1):
        base = p.get("_slug") or slugify(p.get("title") or f"draft-{i}", i)
        slug = base
        n = 2
        while slug in used_slugs:
            slug = f"{base}-{n}"
            n += 1
        used_slugs.add(slug)

        title = short_title(p.get("title") or slug)
        abstract = p.get("abstract") or ""
        template, params, fidelity, assets = classify_paper(p)
        meta = infer_meta(title, abstract)
        specs.append(
            {
                "slug": slug,
                "title": title,
                "paperTitle": p.get("title"),
                "paperAuthors": authors_str(p.get("authors") or []),
                "paperInstitute": institute_str(p.get("institutions") or []),
                "academicLink": p.get("url") or "",
                "year": p.get("year"),
                "venue": p.get("venue"),
                "source": p.get("source"),
                "citationCount": p.get("citationCount"),
                "query": p.get("_query"),
                "score": p.get("_score"),
                "abstract": abstract,
                "template": template,
                "params": params,
                "fidelity": fidelity,
                "assets": assets,
                "assetClass": meta["assetClass"],
                "region": meta["region"],
                "market": meta["market"],
                "frequency": meta["frequency"],
                "keywords": keywords_from(title, p.get("_query") or ""),
                "published": False,
                "draft": True,
            }
        )

    CATALOG.write_text(
        json.dumps(
            {
                "count": len(specs),
                "published": False,
                "note": "DRAFT ONLY — not inserted into Prisma",
                "by_template": dict(Counter(s["template"] for s in specs)),
                "by_fidelity": dict(Counter(s["fidelity"] for s in specs)),
                "strategies": specs,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("Catalog:", dict(Counter(s["template"] for s in specs)))

    all_assets = sorted({a for s in specs for a in s["assets"]} | {"SPY"})
    print(f"Loading {len(all_assets)} symbols…")
    t0 = time.time()
    panel, missing = load_price_panel(all_assets, start="2000-01-01")
    print(f"Loaded in {time.time()-t0:.1f}s; missing={missing}")
    price_cache = {c: panel[c] for c in panel.columns}

    results = []
    for i, spec in enumerate(specs, 1):
        try:
            # Drop assets missing from panel
            avail = [a for a in spec["assets"] if a in price_cache]
            if len(avail) < 1:
                results.append({"slug": spec["slug"], "status": "error", "error": "no assets loaded"})
                continue
            if len(avail) < len(spec["assets"]):
                spec = {**spec, "assets": avail}
            r = run_backtest(spec, price_cache)
            results.append(r)
            if i % 10 == 0 or i == len(specs):
                ok = sum(1 for x in results if x.get("status") == "ok")
                print(f"  [{i}/{len(specs)}] ok={ok}")
        except Exception as e:
            results.append(
                {
                    "slug": spec["slug"],
                    "status": "error",
                    "error": f"{type(e).__name__}: {e}",
                    "trace": traceback.format_exc()[-500:],
                }
            )

    # Attach metrics into posts
    by_slug = {r["slug"]: r for r in results}
    posts_index = []
    for spec in specs:
        r = by_slug.get(spec["slug"]) or {}
        m = r.get("metrics") if r.get("status") == "ok" else None
        code = render_runner(
            spec["slug"],
            spec["title"],
            spec["template"],
            spec["fidelity"],
            spec["assets"],
            spec.get("params") or {},
        )
        (CODE / f"{spec['slug']}.py").write_text(code, encoding="utf-8")

        teaser = nutshell(spec["template"], spec["assets"], spec.get("params") or {}, "", spec["fidelity"])
        teaser = teaser.split(" Paper focus:")[0].strip()
        nut = nutshell(
            spec["template"],
            spec["assets"],
            spec.get("params") or {},
            spec.get("abstract") or "",
            spec["fidelity"],
        )
        rat = rationale(spec["template"], spec["paperTitle"], spec.get("abstract") or "")
        content = build_content_html(
            teaser=teaser,
            meta={
                "assetClass": spec["assetClass"],
                "region": spec["region"],
                "market": spec["market"],
                "frequency": spec["frequency"],
            },
            keywords=spec["keywords"],
            nutshell_text=nut,
            rationale_text=rat,
            paper_title=spec["paperTitle"],
            authors=spec["paperAuthors"],
            institute=spec["paperInstitute"],
            link=spec["academicLink"],
            metrics_html=metrics_block(m),
            code_html=python_html(code),
        )

        post = {
            "slug": spec["slug"],
            "locale": "en",
            "published": False,
            "draft": True,
            "title": spec["title"],
            "teaser": teaser[:500],
            "summary": (spec.get("abstract") or "")[:800],
            "economicRationale": rat[:1200],
            "paperTitle": spec["paperTitle"],
            "paperAuthors": spec["paperAuthors"],
            "paperInstitute": spec["paperInstitute"],
            "academicLink": spec["academicLink"],
            "assetClass": spec["assetClass"],
            "region": spec["region"],
            "market": spec["market"],
            "frequency": spec["frequency"],
            "isPaywalled": True,
            "hasPythonCode": True,
            "annualisedReturn": fmt_pct(m.get("cagr")) if m else None,
            "sharpeRatio": fmt_num(m.get("sharpe")) if m else None,
            "maxDrawdown": fmt_pct(m.get("max_drawdown")) if m else None,
            "volatility": fmt_pct(m.get("volatility")) if m else None,
            "beta": fmt_num(m.get("beta")) if m else None,
            "sortinoRatio": fmt_num(m.get("sortino")) if m else None,
            "winRate": fmt_pct(m.get("win_rate")) if m and m.get("win_rate") is not None else None,
            "pythonCodeHtml": python_html(code),
            "contentHtml": content,
            "template": spec["template"],
            "assets": spec["assets"],
            "params": spec.get("params"),
            "fidelity": spec["fidelity"],
            "backtest": {
                "status": r.get("status"),
                "metrics": m,
                "trades": r.get("trades"),
                "start": r.get("start"),
                "end": r.get("end"),
                "curve_file": r.get("curve_file"),
                "error": r.get("error"),
            },
            "source_paper": {
                "year": spec.get("year"),
                "venue": spec.get("venue"),
                "source": spec.get("source"),
                "citationCount": spec.get("citationCount"),
                "query": spec.get("query"),
                "score": spec.get("score"),
            },
        }
        (POSTS / f"{spec['slug']}.json").write_text(json.dumps(post, indent=2), encoding="utf-8")
        posts_index.append(
            {
                "slug": spec["slug"],
                "title": spec["title"],
                "template": spec["template"],
                "cagr": m.get("cagr") if m else None,
                "sharpe": m.get("sharpe") if m else None,
                "max_drawdown": m.get("max_drawdown") if m else None,
                "status": r.get("status"),
                "paperTitle": spec["paperTitle"],
                "academicLink": spec["academicLink"],
                "post_file": f"posts/{spec['slug']}.json",
            }
        )

    ok_results = [r for r in results if r.get("status") == "ok" and r.get("metrics")]
    ok_results.sort(key=lambda r: (r["metrics"].get("sharpe") or -99), reverse=True)

    SUMMARY.write_text(
        json.dumps(
            {
                "published": False,
                "count": len(results),
                "ok": len(ok_results),
                "errors": len(results) - len(ok_results),
                "by_template": dict(Counter(s["template"] for s in specs)),
                "median_cagr": (
                    float(pd.Series([r["metrics"]["cagr"] for r in ok_results]).median())
                    if ok_results
                    else None
                ),
                "median_sharpe": (
                    float(pd.Series([r["metrics"]["sharpe"] for r in ok_results]).median())
                    if ok_results
                    else None
                ),
                "results": results,
                "posts_index": posts_index,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    lb = [
        {
            "rank": i,
            "slug": r["slug"],
            "title": r["title"],
            "template": r["template"],
            "cagr": r["metrics"].get("cagr"),
            "sharpe": r["metrics"].get("sharpe"),
            "max_drawdown": r["metrics"].get("max_drawdown"),
            "volatility": r["metrics"].get("volatility"),
            "fidelity": r.get("fidelity"),
            "assets": r.get("assets"),
        }
        for i, r in enumerate(ok_results, 1)
    ]
    LEADERBOARD.write_text(json.dumps(lb, indent=2), encoding="utf-8")

    lines = [
        "# New 100 strategy drafts — NOT PUBLISHED",
        "",
        f"- Papers: {len(papers)}",
        f"- Posts written: {len(posts_index)} under `posts/`",
        f"- Backtests OK: {len(ok_results)} / {len(results)}",
        f"- Templates: {dict(Counter(s['template'] for s in specs))}",
        "",
        "## Top 10 by Sharpe",
        "",
    ]
    for row in lb[:10]:
        lines.append(
            f"{row['rank']}. `{row['slug']}` — CAGR {fmt_pct(row['cagr'])}, "
            f"Sharpe {fmt_num(row['sharpe'])}, MaxDD {fmt_pct(row['max_drawdown'])} "
            f"[{row['template']}]"
        )
    lines += [
        "",
        "## Review path",
        "",
        "1. Open `backtest/drafts/new_100/leaderboard.json`",
        "2. Inspect a post JSON under `posts/`",
        "3. Approve → then a separate publish script can insert into Prisma with `published=false` or true",
        "",
    ]
    MANIFEST.write_text("\n".join(lines), encoding="utf-8")
    print(f"Done. OK={len(ok_results)} errors={len(results)-len(ok_results)}")
    print(f"Wrote {SUMMARY}")


if __name__ == "__main__":
    main()
