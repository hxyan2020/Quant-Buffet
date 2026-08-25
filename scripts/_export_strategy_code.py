"""
Export full in-house Python + preserved QuantConnect originals for catalog strategies.

Writes:
  backtest/strategies/generated/{slug}.py      — runnable Quant Buffet in-house code
  backtest/strategies/qc_original/{slug}.qc.py — original QC / AlgoLib code (unchanged)
  backtest/strategies/INDEX.json               — catalog + data sources + paths
  backtest/strategies/CODEBOOK.md              — all in-house codes in one browseable file
"""
from __future__ import annotations

import json
import re
import sqlite3
import textwrap
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "backtest" / "catalog" / "strategies_100.json"
DB = ROOT / "prisma" / "dev.db"
OUT_IH = ROOT / "backtest" / "strategies" / "generated"
OUT_QC = ROOT / "backtest" / "strategies" / "qc_original"
INDEX = ROOT / "backtest" / "strategies" / "INDEX.json"
CODEBOOK = ROOT / "backtest" / "strategies" / "CODEBOOK.md"


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</p>", "\n\n", t, flags=re.I)
    t = re.sub(r"</div>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("\xa0", " ")
    return t.strip() + ("\n" if t.strip() else "")


def load_qc_map() -> dict[str, str]:
    con = sqlite3.connect(DB)
    rows = con.execute(
        "SELECT slug, pythonCodeHtml FROM Strategy WHERE locale='en' AND published=1"
    ).fetchall()
    return {slug: strip_html(html) for slug, html in rows}


def render_strategy_body(template: str, assets: list[str], params: dict) -> str:
    assets_lit = repr(assets)
    p = params or {}

    if template == "sma_trend":
        sma = int(p.get("sma_days", 200))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            SMA_DAYS = {sma}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                sma = prices[cols].rolling(SMA_DAYS, min_periods=SMA_DAYS).mean()
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    if sma.loc[dt].isna().all():
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    long = [
                        s for s in cols
                        if pd.notna(prices.at[dt, s]) and pd.notna(sma.at[dt, s])
                        and prices.at[dt, s] > sma.at[dt, s]
                    ]
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = sma.dropna(how="all").index.min() if sma.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "dual_ma":
        fast, slow = int(p.get("fast", 50)), int(p.get("slow", 200))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            FAST = {fast}
            SLOW = {slow}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                fast = prices[cols].rolling(FAST, min_periods=FAST).mean()
                slow = prices[cols].rolling(SLOW, min_periods=SLOW).mean()
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    if slow.loc[dt].isna().all():
                        return
                    if state["last"] == dt.date():
                        return
                    state["last"] = dt.date()
                    long = [
                        s for s in cols
                        if pd.notna(fast.at[dt, s]) and pd.notna(slow.at[dt, s])
                        and fast.at[dt, s] > slow.at[dt, s]
                    ]
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = slow.dropna(how="all").index.min() if slow.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "abs_momentum":
        lb = int(p.get("lookback", 252))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change(LOOKBACK)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    if rets.loc[dt].isna().all():
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    long = [s for s in cols if pd.notna(rets.at[dt, s]) and rets.at[dt, s] > 0]
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "dual_momentum":
        lb = int(p.get("lookback", 252))
        cash = p.get("cash_symbol") or "BIL"
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}
            CASH = {cash!r}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                if CASH not in cols and CASH in prices.columns:
                    cols = cols + [CASH]
                risky = [c for c in cols if c != CASH]
                rets = prices[cols].pct_change(LOOKBACK)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    scores = {{
                        s: float(rets.at[dt, s])
                        for s in risky
                        if s in rets.columns and pd.notna(rets.at[dt, s])
                    }}
                    if not scores:
                        engine.set_target_weights(dt, {{CASH: 1.0}} if CASH in cols else {{}})
                        return
                    best = max(scores, key=scores.get)
                    if scores[best] > 0:
                        engine.set_target_weights(dt, {{best: 1.0}})
                    elif CASH in cols:
                        engine.set_target_weights(dt, {{CASH: 1.0}})
                    else:
                        engine.set_target_weights(dt, {{}})

                ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "momentum_rotation":
        lb = int(p.get("lookback", 126))
        top_n = int(p.get("top_n", 1))
        invert = bool(p.get("invert", False))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}
            TOP_N = {top_n}
            INVERT = {invert!r}  # True = short-term reversal (rank ascending)

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change(LOOKBACK)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    row = rets.loc[dt]
                    if row.isna().all():
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    ranked = row.dropna().sort_values(ascending=INVERT)
                    picks = list(ranked.head(TOP_N).index)
                    if not INVERT:
                        picks = [s for s in picks if ranked[s] > 0] or picks[:1]
                    w = {{}} if not picks else {{s: 1.0 / len(picks) for s in picks}}
                    engine.set_target_weights(dt, w)

                ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "equal_weight":
        once = p.get("rebalance") == "once"
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            REBALANCE_ONCE = {once!r}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                state = {{"last": None, "done": False}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    available = [s for s in cols if pd.notna(prices.at[dt, s])]
                    if not available:
                        return
                    if REBALANCE_ONCE:
                        if state["done"]:
                            return
                        state["done"] = True
                        engine.set_target_weights(dt, {{s: 1.0 / len(available) for s in available}})
                        return
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    engine.set_target_weights(dt, {{s: 1.0 / len(available) for s in available}})

                counts = prices[cols].notna().sum(axis=1)
                need = max(1, len(cols) // 2)
                eligible = counts[counts >= need]
                ready = eligible.index.min() if not eligible.empty else None
                return on_day, ready
            """
        )

    if template == "mean_reversion":
        lb = int(p.get("lookback", 20))
        entry_z = float(p.get("entry_z", -1.0))
        exit_z = float(p.get("exit_z", 0.0))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            LOOKBACK = {lb}
            ENTRY_Z = {entry_z}
            EXIT_Z = {exit_z}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                mu = prices[cols].rolling(LOOKBACK, min_periods=LOOKBACK).mean()
                sd = prices[cols].rolling(LOOKBACK, min_periods=LOOKBACK).std(ddof=0)
                z = (prices[cols] - mu) / sd.replace(0, np.nan)
                held = {{s: False for s in cols}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    long = []
                    for s in cols:
                        zv = z.at[dt, s]
                        if pd.isna(zv):
                            continue
                        if not held[s] and zv <= ENTRY_Z:
                            held[s] = True
                        elif held[s] and zv >= EXIT_Z:
                            held[s] = False
                        if held[s]:
                            long.append(s)
                    w = {{}} if not long else {{s: 1.0 / len(long) for s in long}}
                    engine.set_target_weights(dt, w)

                ready = z.dropna(how="all").index.min() if z.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "vol_target":
        target = float(p.get("target_vol", 0.10))
        lb = int(p.get("vol_lookback", 63))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            TARGET_VOL = {target}
            VOL_LOOKBACK = {lb}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change()
                vol = rets.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).std() * np.sqrt(252)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    weights = {{}}
                    for s in cols:
                        v = vol.at[dt, s]
                        if pd.isna(v) or v <= 1e-8:
                            continue
                        weights[s] = min(1.0, TARGET_VOL / float(v))
                    total = sum(weights.values())
                    if total > 1.0:
                        weights = {{k: v / total for k, v in weights.items()}}
                    engine.set_target_weights(dt, weights)

                ready = vol.dropna(how="all").index.min() if vol.notna().any().any() else None
                return on_day, ready
            """
        )

    if template == "risk_parity":
        lb = int(p.get("vol_lookback", 63))
        return textwrap.dedent(
            f"""\
            ASSETS = {assets_lit}
            VOL_LOOKBACK = {lb}

            def make_on_day(prices: pd.DataFrame):
                cols = [c for c in ASSETS if c in prices.columns]
                rets = prices[cols].pct_change()
                vol = rets.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).std() * np.sqrt(252)
                state = {{"last": None}}

                def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
                    key = (dt.year, dt.month)
                    if state["last"] == key:
                        return
                    state["last"] = key
                    inv = {{
                        s: 1.0 / float(vol.at[dt, s])
                        for s in cols
                        if pd.notna(vol.at[dt, s]) and vol.at[dt, s] > 1e-8
                    }}
                    total = sum(inv.values())
                    weights = {{k: v / total for k, v in inv.items()}} if total > 0 else {{}}
                    engine.set_target_weights(dt, weights)

                ready = vol.dropna(how="all").index.min() if vol.notna().any().any() else None
                return on_day, ready
            """
        )

    raise ValueError(f"unknown template {template}")


FOOTER = r'''

def main() -> None:
    print(f"[{SLUG}] loading {ASSETS} from Yahoo Finance / cache…")
    prices = load_daily_prices(ASSETS, start="2000-01-01").dropna(how="all")
    on_day, ready = make_on_day(prices)
    if ready is None or pd.isna(ready):
        raise SystemExit("signal never ready — check symbol history")

    engine = PortfolioEngine(
        prices,
        EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0),
    )
    result = engine.run(on_day, start=ready)

    bench_sym = "SPY" if "SPY" in prices.columns else ASSETS[0]
    spy = prices[bench_sym].reindex(result.equity.index).ffill()
    bh = float(result.equity.iloc[0]) * (spy / spy.iloc[0])
    metrics = compute_metrics(result.equity, benchmark=bh, trades_count=len(result.trades))

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
'''


def build_header(slug: str, title: str, template: str, fidelity: str, assets: list[str]) -> str:
    assets_repr = repr(assets)
    return f'''\
"""
Quant Buffet IN-HOUSE backtest — {slug}
Title: {title}
Template: {template}
Fidelity: {fidelity}

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{{SYMBOL}}_2000-01-01_latest.csv
Symbols  : {assets}
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/{slug}.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/{slug}.py
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
DATA_SOURCE = {{
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": {assets_repr},
    "history_start": "2000-01-01",
}}

'''


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    qc_map = load_qc_map()
    OUT_IH.mkdir(parents=True, exist_ok=True)
    OUT_QC.mkdir(parents=True, exist_ok=True)

    (OUT_IH / "__init__.py").write_text('"""Generated in-house strategy runners."""\n', encoding="utf-8")

    index_rows = []
    codebook_parts = [
        "# Quant Buffet in-house strategy codebook\n",
        f"Generated from `{CATALOG.as_posix()}`.\n",
        "QC originals preserved under `backtest/strategies/qc_original/`.\n",
        "Data for every strategy: **Yahoo Finance adjusted closes via yfinance** "
        "(cached in `backtest/data_cache/`).\n\n",
    ]

    for spec in catalog["strategies"]:
        slug = spec["slug"]
        title = spec["title"]
        template = spec["template"]
        assets = spec["assets"]
        fidelity = spec.get("fidelity", "reconstructed_etf_rules")
        params = spec.get("params") or {}

        qc = qc_map.get(slug, "")
        qc_path = OUT_QC / f"{slug}.qc.py"
        if qc.strip():
            qc_path.write_text(
                f'# Original QuantConnect / library Python for slug="{slug}"\n'
                f"# Extracted from Strategy.pythonCodeHtml — NOT modified by Quant Buffet export.\n\n"
                + qc,
                encoding="utf-8",
            )
        else:
            qc_path.write_text(
                f'# No pythonCodeHtml found in DB for slug="{slug}"\n',
                encoding="utf-8",
            )

        body = render_strategy_body(template, assets, params)
        header = build_header(slug, title.replace('"', "'"), template, fidelity, assets)
        ih_code = header + "\n" + body + FOOTER
        ih_path = OUT_IH / f"{slug}.py"
        ih_path.write_text(ih_code, encoding="utf-8")

        data_source = {
            "provider": "Yahoo Finance",
            "library": "yfinance",
            "field": "adjusted close (auto_adjust=True)",
            "loader": "backtest.data.load_daily_prices",
            "cache_dir": "backtest/data_cache",
            "symbols": assets,
            "history_start": "2000-01-01",
            "cache_files": [f"backtest/data_cache/{s}_2000-01-01_latest.csv" for s in assets],
        }
        index_rows.append(
            {
                "slug": slug,
                "title": title,
                "template": template,
                "fidelity": fidelity,
                "assets": assets,
                "params": params,
                "data_source": data_source,
                "in_house_python": str(ih_path.relative_to(ROOT)).replace("\\", "/"),
                "quantconnect_python": str(qc_path.relative_to(ROOT)).replace("\\", "/"),
                "qc_bytes": len(qc.encode("utf-8")),
            }
        )

        codebook_parts.append(f"\n---\n\n## `{slug}`\n\n")
        codebook_parts.append(f"**Title:** {title}  \n")
        codebook_parts.append(f"**Template:** `{template}` · **Fidelity:** `{fidelity}`  \n")
        codebook_parts.append(
            f"**Data:** Yahoo Finance / yfinance adjusted close · symbols: `{', '.join(assets)}`  \n"
        )
        codebook_parts.append(
            f"**QC original (preserved):** `{qc_path.relative_to(ROOT).as_posix()}`  \n\n"
        )
        codebook_parts.append("### In-house Python\n\n```python\n")
        codebook_parts.append(ih_code)
        codebook_parts.append("\n```\n")

    INDEX.write_text(
        json.dumps(
            {
                "count": len(index_rows),
                "in_house_libraries": [
                    "backtest/data.py — load_daily_prices / load_price_panel",
                    "backtest/engine.py — Trade, BacktestResult, EngineConfig, PortfolioEngine",
                    "backtest/metrics.py — compute_metrics",
                    "backtest/templates.py — parameterized rule builders (batch path)",
                ],
                "data_source_default": {
                    "provider": "Yahoo Finance",
                    "library": "yfinance",
                    "field": "adjusted close",
                    "cache": "backtest/data_cache/",
                },
                "strategies": index_rows,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    CODEBOOK.write_text("".join(codebook_parts), encoding="utf-8")
    print(f"exported {len(index_rows)} strategies")
    print(f"  in-house → {OUT_IH}")
    print(f"  QC kept  → {OUT_QC}")
    print(f"  index    → {INDEX}")
    print(f"  codebook → {CODEBOOK}")


if __name__ == "__main__":
    main()
