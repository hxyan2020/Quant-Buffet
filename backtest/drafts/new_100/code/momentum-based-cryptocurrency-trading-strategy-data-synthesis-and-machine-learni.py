"""
Quant Buffet IN-HOUSE draft — momentum-based-cryptocurrency-trading-strategy-data-synthesis-and-machine-learni
Title: Momentum-Based Cryptocurrency Trading Strategy
Template: abs_momentum
Fidelity: signal_unavailable_etf_proxy
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

SLUG = 'momentum-based-cryptocurrency-trading-strategy-data-synthesis-and-machine-learni'
TITLE = 'Momentum-Based Cryptocurrency Trading Strategy'
TEMPLATE = 'abs_momentum'
FIDELITY = 'signal_unavailable_etf_proxy'

ASSETS = ['BTC-USD', 'ETH-USD']
LOOKBACK = 252

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if rets.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        long = [s for s in cols if pd.notna(rets.at[dt, s]) and rets.at[dt, s] > 0]
        w = {} if not long else {s: 1.0 / len(long) for s in long}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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
