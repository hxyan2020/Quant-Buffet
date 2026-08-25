"""
Quant Buffet IN-HOUSE backtest — 期货市场中的横截面动量策略 [zh]
file_key: zh__id-cmpe7ie1f00yzxlb0g4yd0o4z
Title: 期货市场中的跨行业动量策略
Template: momentum_rotation
Fidelity: qc_present_theme_assets
Has QC source in DB: True

DATA SOURCE
-----------
Provider : Yahoo Finance via yfinance (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SHY', 'IEF', 'TLT', 'LQD', 'HYG', 'TIP', 'BND']
Start    : 2000-01-01 (actual start = IPO + signal warmup)
Costs    : 5 bps commission + 2 bps slippage (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/zh__id-cmpe7ie1f00yzxlb0g4yd0o4z.qc.py

Run from repo root:
  python backtest/strategies/generated/zh__id-cmpe7ie1f00yzxlb0g4yd0o4z.py
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

SLUG = '期货市场中的横截面动量策略'
LOCALE = 'zh'
FILE_KEY = 'zh__id-cmpe7ie1f00yzxlb0g4yd0o4z'
TITLE = '期货市场中的跨行业动量策略'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'qc_present_theme_assets'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SHY', 'IEF', 'TLT', 'LQD', 'HYG', 'TIP', 'BND'],
    "history_start": "2000-01-01",
}


ASSETS = ['SHY', 'IEF', 'TLT', 'LQD', 'HYG', 'TIP', 'BND']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

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
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
    return on_day, ready


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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{FILE_KEY}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{FILE_KEY}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
