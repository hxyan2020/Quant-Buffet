"""
Quant Buffet IN-HOUSE draft — on-the-efficacy-of-shorting-corporate-bonds-as-a-tail-risk-hedging-solution
Title: On the Efficacy of Shorting Corporate Bonds as a Tail Risk Hedging Solution
Template: mean_reversion
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

SLUG = 'on-the-efficacy-of-shorting-corporate-bonds-as-a-tail-risk-hedging-solution'
TITLE = 'On the Efficacy of Shorting Corporate Bonds as a Tail Risk Hedging Solution'
TEMPLATE = 'mean_reversion'
FIDELITY = 'no_qc_theme_proxy'

ASSETS = ['LQD', 'HYG', 'AGG', 'BIL']
LOOKBACK = 20
ENTRY_Z = -1.0
EXIT_Z = 0.0

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    mu = prices[cols].rolling(LOOKBACK, min_periods=LOOKBACK).mean()
    sd = prices[cols].rolling(LOOKBACK, min_periods=LOOKBACK).std(ddof=0)
    z = (prices[cols] - mu) / sd.replace(0, np.nan)
    held = {s: False for s in cols}

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
        w = {} if not long else {s: 1.0 / len(long) for s in long}
        engine.set_target_weights(dt, w)

    ready = z.dropna(how="all").index.min() if z.notna().any().any() else None
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
