"""
Quant Buffet IN-HOUSE draft — fast-times-slow-times-timescale-separation-in-financial-timeseries-data
Title: Fast Times, Slow Times: Timescale Separation in Financial Timeseries Data
Template: equal_weight
Fidelity: no_qc_theme_proxy
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

SLUG = 'fast-times-slow-times-timescale-separation-in-financial-timeseries-data'
TITLE = 'Fast Times, Slow Times: Timescale Separation in Financial Timeseries Data'
TEMPLATE = 'equal_weight'
FIDELITY = 'no_qc_theme_proxy'

ASSETS = ['SHY', 'IEF', 'TLT', 'LQD', 'HYG', 'TIP', 'BND']
REBALANCE_ONCE = False

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    state = {"last": None, "done": False}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        available = [s for s in cols if pd.notna(prices.at[dt, s])]
        if not available:
            return
        if REBALANCE_ONCE:
            if state["done"]:
                return
            state["done"] = True
            engine.set_target_weights(dt, {s: 1.0 / len(available) for s in available})
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        engine.set_target_weights(dt, {s: 1.0 / len(available) for s in available})

    counts = prices[cols].notna().sum(axis=1)
    need = max(1, len(cols) // 2)
    eligible = counts[counts >= need]
    ready = eligible.index.min() if not eligible.empty else None
    return on_day, ready


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
