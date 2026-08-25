"""
Quant Buffet IN-HOUSE draft — the-analysis-of-investment-into-industries-based-on-portfolio-managers
Title: The analysis of investment into industries based on portfolio managers
Template: vol_target
Fidelity: theme_proxy_vol_managed
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

SLUG = 'the-analysis-of-investment-into-industries-based-on-portfolio-managers'
TITLE = 'The analysis of investment into industries based on portfolio managers'
TEMPLATE = 'vol_target'
FIDELITY = 'theme_proxy_vol_managed'

ASSETS = ['SPY', 'BIL']
TARGET_VOL = 0.1
VOL_LOOKBACK = 63

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change()
    vol = rets.rolling(VOL_LOOKBACK, min_periods=VOL_LOOKBACK).std() * np.sqrt(252)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        weights = {}
        for s in cols:
            v = vol.at[dt, s]
            if pd.isna(v) or v <= 1e-8:
                continue
            weights[s] = min(1.0, TARGET_VOL / float(v))
        total = sum(weights.values())
        if total > 1.0:
            weights = {k: v / total for k, v in weights.items()}
        engine.set_target_weights(dt, weights)

    ready = vol.dropna(how="all").index.min() if vol.notna().any().any() else None
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
