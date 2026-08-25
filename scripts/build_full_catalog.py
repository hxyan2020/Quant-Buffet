"""
Build full-library catalog: every published EN + ZH strategy gets an in-house spec.

- Preserves QC mapping via slug/locale
- Strategies without QC still get a theme-based ETF rule (fidelity labeled)
- Never drops a strategy (always assigns template + assets)
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import Counter
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backtest.universes import BOOKS, WHITELIST  # noqa: E402

DB = ROOT / "prisma" / "dev.db"
OUT = ROOT / "backtest" / "catalog" / "strategies_full.json"


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<[^>]+>", "\n", t)
    return t


def safe_file_key(locale: str, slug: str, sid: str) -> str:
    """Filesystem-safe unique key."""
    raw = slug or ""
    cleaned = re.sub(r"[^a-zA-Z0-9\-]+", "-", raw).strip("-").lower()
    cleaned = re.sub(r"-{2,}", "-", cleaned)
    if not cleaned or not re.fullmatch(r"[a-z0-9\-]+", cleaned):
        cleaned = f"id-{sid}"
    # Avoid collisions across locales / sanitized names
    return f"{locale}__{cleaned}"[:180]


def extract_tickers(text: str) -> list[str]:
    out: list[str] = []
    for pat in [
        r"add_equity\(\s*[\"']([A-Za-z][A-Za-z0-9.\-]{1,10})[\"']",
        r"AddEquity\(\s*[\"']([A-Za-z][A-Za-z0-9.\-]{1,10})[\"']",
        r"[\"'](BTC-USD|ETH-USD)[\"']",
        r"[\"']([A-Z]{2,5})[\"']",
        r"\b(BTC-USD|ETH-USD)\b",
        r"\b([A-Z]{2,5})\b",
    ]:
        for m in re.findall(pat, text):
            u = m.upper() if not m.startswith("BTC") and not m.startswith("ETH") else m
            if u == "BTC-USD" or u == "ETH-USD":
                pass
            elif u not in WHITELIST:
                continue
            if u not in out:
                out.append(u)
    return out[:15]


def sma_period(code: str) -> int:
    m = re.search(r"(\d+)\s*\*\s*21", code)
    if m:
        return int(m.group(1)) * 21
    m = re.search(r"(?:moving_avg_period|sma_period)\s*=\s*(\d+)", code, re.I)
    if m:
        v = int(m.group(1))
        return v if v > 20 else v * 21
    m = re.search(r"SimpleMovingAverage\([^,]+,\s*(\d+)", code, re.I)
    if m:
        return int(m.group(1))
    return 200


def pick_book(low: str, asset_class: str, region: str) -> tuple[list[str], str]:
    """Return (assets, book_name) from theme keywords."""
    ac = (asset_class or "").lower()
    rg = (region or "").lower()

    if any(k in low for k in ("bitcoin", "crypto", "ethereum", "cryptocurrenc")):
        return BOOKS["crypto"][:], "crypto"
    if any(k in low for k in ("vix", "volatility risk premia", "variance risk")):
        return BOOKS["vol"][:], "vol"
    if any(k in low for k in ("sector", "industry rotation", "industry momentum")):
        return BOOKS["us_sectors"][:], "us_sectors"
    if any(k in low for k in ("country", "international equity", "emerging market", "global equity")):
        if "emerging" in low or "china" in low or "em " in low:
            return BOOKS["country_em"][:], "country_em"
        return BOOKS["country_dm"][:], "country_dm"
    if "china" in low or "ashr" in low or "fxi" in low:
        return ["FXI", "ASHR", "EWH", "SPY", "BIL"], "china"
    if any(k in low for k in ("reit", "real estate", "property")):
        return BOOKS["real_estate"][:] + ["SPY", "BIL"], "real_estate"
    if any(k in low for k in ("commodity", "crude", "oil", "gold", "metal", "grain")):
        return BOOKS["commodities"][:], "commodities"
    if any(k in low for k in ("bond", "fixed income", "treasury", "duration", "credit", "corporate bond")):
        if "credit" in low or "corporate" in low or "high yield" in low or "hyg" in low:
            return BOOKS["credit"][:], "credit"
        return BOOKS["bonds"][:], "bonds"
    if any(k in low for k in ("fx ", "forex", "currency", "dollar", "carry trade")):
        return BOOKS["fx"][:], "fx"
    if any(k in low for k in ("multi-asset", "multi asset", "asset allocation", "risk parity", "all weather")):
        return BOOKS["multi_asset"][:], "multi_asset"
    if "option" in low or "collar" in low:
        return BOOKS["qqq_bil"][:], "options_underlying"
    if "etf" in ac and "bond" in ac:
        return BOOKS["bonds"][:], "bonds"
    if "bond" in ac:
        return BOOKS["bonds"][:], "bonds"
    if "crypto" in ac:
        return BOOKS["crypto"][:], "crypto"
    if "future" in ac or "cfd" in ac:
        return BOOKS["multi_asset"][:], "futures_etf_proxy"
    if "option" in ac:
        return BOOKS["spy_bil"][:], "options_underlying"
    if "china" in rg or "asia" in rg:
        return BOOKS["country_em"][:], "country_em"
    if "europe" in rg:
        return ["VGK", "EWU", "EWG", "EWQ", "EWI", "SPY"], "europe"
    if "global" in rg or "world" in rg:
        return BOOKS["global_equity"][:], "global_equity"

    # Default equity book
    return BOOKS["spy_bil"][:], "us_equity_default"


def classify_always(
    *,
    title: str,
    low: str,
    code: str,
    has_qc: bool,
    asset_class: str,
    region: str,
) -> tuple[str, dict, str, list[str]]:
    """
    Always returns (template, params, fidelity, assets).
    """
    tickers = extract_tickers(code + "\n" + low[:8000])
    # Drop junk short tokens that slipped through
    tickers = [t for t in tickers if t in WHITELIST or t in ("BTC-USD", "ETH-USD")]

    book, book_name = pick_book(low, asset_class, region)
    if len(tickers) >= 2:
        assets = tickers[:12]
        asset_origin = "extracted"
    elif len(tickers) == 1:
        # Pair with cash for timing strategies
        assets = tickers + (["BIL"] if tickers[0] != "BIL" else ["SHY"])
        asset_origin = "extracted+cash"
    else:
        assets = book[:12]
        asset_origin = f"theme_book:{book_name}"

    # Fidelity
    if has_qc and asset_origin.startswith("extracted"):
        fidelity = "reconstructed_etf_rules"
    elif has_qc:
        fidelity = "qc_present_theme_assets"
    elif asset_origin.startswith("theme_book"):
        fidelity = "no_qc_theme_proxy"
    else:
        fidelity = "no_qc_extracted_assets"

    # Soft proxies for fundamentals / alt-data / ML
    hard_proxy_kw = (
        "machine learning",
        "neural",
        "random forest",
        "gradient boost",
        "deep learning",
        "nlp",
        "sentiment",
        "earnings call",
        "satellite",
        "alternative data",
        "order imbalance",
        "options implied",
        "butterfly",
        "cointegration",
        "pairs trading",
        "merger arb",
        "ipo",
        "spin-off",
        "insider",
        "esg",
        "carbon risk",
        "demographic",
    )
    if any(k in low for k in hard_proxy_kw):
        fidelity = "signal_unavailable_etf_proxy"

    # Template selection
    if re.search(r"dual.?momentum|absolute.?momentum", low):
        cash = "BIL" if "BIL" in assets else ("SHY" if "SHY" in assets else "BIL")
        if cash not in assets:
            assets = list(assets) + [cash]
        return (
            "dual_momentum",
            {"lookback": 252, "cash_symbol": cash, "rebalance": "monthly"},
            fidelity,
            assets,
        )

    if re.search(r"risk parity|equal risk contribution", low) and len(assets) >= 3:
        return "risk_parity", {"vol_lookback": 63, "rebalance": "monthly"}, fidelity, assets

    if re.search(r"volatility.?target|managed volatility|vol target", low):
        return (
            "vol_target",
            {"target_vol": 0.10, "vol_lookback": 63, "rebalance": "monthly"},
            fidelity,
            assets,
        )

    if re.search(r"mean.?revert|bollinger|z-?score|reversal", low):
        if len(assets) >= 4 and "reversal" in low and "momentum" not in low[:80]:
            return (
                "momentum_rotation",
                {
                    "lookback": 21,
                    "top_n": max(1, len(assets) // 4),
                    "rebalance": "monthly",
                    "invert": True,
                },
                fidelity,
                assets,
            )
        return (
            "mean_reversion",
            {"lookback": 20, "entry_z": -1.0, "exit_z": 0.0, "rebalance": "daily"},
            fidelity,
            assets,
        )

    if re.search(r"golden.?cross|dual.?ma|50.?200", low):
        return "dual_ma", {"fast": 50, "slow": 200, "rebalance": "daily"}, fidelity, assets

    if re.search(
        r"trend.?follow|moving average|sma|price above|market timing|bear market",
        low,
    ):
        sma = sma_period(code) if code else 200
        return "sma_trend", {"sma_days": sma, "rebalance": "monthly"}, fidelity, assets

    if re.search(
        r"rotat|asset.?alloc|momentum|relative strength|cross.?section|factor",
        low,
    ):
        if len(assets) >= 3:
            top_n = 1 if any(k in low for k in ("vigilant", "defensive", "protective")) else max(
                1, min(3, len(assets) // 3)
            )
            lb = 21 if "1-month" in low or "short-term" in low or "short term" in low else 126
            return (
                "momentum_rotation",
                {"lookback": lb, "top_n": top_n, "rebalance": "monthly"},
                fidelity,
                assets,
            )
        return "abs_momentum", {"lookback": 252, "rebalance": "monthly"}, fidelity, assets

    if re.search(r"buy.?and.?hold|passive", low):
        return "equal_weight", {"rebalance": "once"}, fidelity, assets

    if len(assets) >= 4:
        return "equal_weight", {"rebalance": "monthly"}, fidelity, assets

    if len(assets) <= 2:
        # Timing vs cash
        if "BIL" not in assets and "SHY" not in assets:
            assets = list(assets) + ["BIL"]
        return (
            "dual_momentum",
            {"lookback": 252, "cash_symbol": "BIL", "rebalance": "monthly"},
            fidelity,
            assets,
        )

    return "equal_weight", {"rebalance": "monthly"}, fidelity, assets


def main() -> None:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """
        SELECT id, slug, locale, title, teaser, summary, annualisedReturn, sharpeRatio,
               maxDrawdown, pythonCodeHtml, contentHtml, hasPythonCode, isPaywalled,
               assetClass, region, market, frequency
        FROM Strategy
        WHERE published = 1
        ORDER BY locale, slug
        """
    ).fetchall()

    specs = []
    seen_keys = set()
    for r in rows:
        code = strip_html(r["pythonCodeHtml"] or "") if r["hasPythonCode"] else ""
        has_qc = bool(code and len(code) > 50)
        title = r["title"] or r["slug"] or ""
        teaser = r["teaser"] or ""
        summary = r["summary"] or ""
        content = strip_html(r["contentHtml"] or "")[:12000]
        low = f"{title}\n{teaser}\n{summary}\n{content}\n{code[:4000]}".lower()

        template, params, fidelity, assets = classify_always(
            title=title,
            low=low,
            code=code,
            has_qc=has_qc,
            asset_class=r["assetClass"] or "",
            region=r["region"] or "",
        )

        # Ensure cash symbol exists for dual momentum
        if template == "dual_momentum":
            cash = params.get("cash_symbol") or "BIL"
            if cash not in assets:
                assets = list(assets) + [cash]

        file_key = safe_file_key(r["locale"], r["slug"], r["id"])
        if file_key in seen_keys:
            file_key = f"{file_key}-{r['id'][-6:]}"
        seen_keys.add(file_key)

        specs.append(
            {
                "id": r["id"],
                "file_key": file_key,
                "slug": r["slug"],
                "locale": r["locale"],
                "title": title,
                "isPaywalled": bool(r["isPaywalled"]),
                "has_qc_source": has_qc,
                "assetClass": r["assetClass"],
                "region": r["region"],
                "site_annualisedReturn": r["annualisedReturn"],
                "site_sharpeRatio": r["sharpeRatio"],
                "site_maxDrawdown": r["maxDrawdown"],
                "template": template,
                "assets": assets,
                "params": params,
                "fidelity": fidelity,
            }
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(specs),
        "note": (
            "Full Quant Buffet library catalog. Every published EN+ZH strategy has an "
            "in-house ETF/rule reconstruction. QC Python is preserved separately when present; "
            "missing QC still gets a theme-based proxy (see fidelity)."
        ),
        "stats": {
            "by_locale": dict(Counter(s["locale"] for s in specs)),
            "with_qc": sum(1 for s in specs if s["has_qc_source"]),
            "without_qc": sum(1 for s in specs if not s["has_qc_source"]),
            "by_template": dict(Counter(s["template"] for s in specs)),
            "by_fidelity": dict(Counter(s["fidelity"] for s in specs)),
        },
        "strategies": specs,
    }
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(payload["stats"], indent=2, ensure_ascii=False))
    print("wrote", OUT, "count", len(specs))


if __name__ == "__main__":
    main()
