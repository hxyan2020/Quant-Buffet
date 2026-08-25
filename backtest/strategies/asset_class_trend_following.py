"""
In-house port of Quant Buffet strategy:
  slug: asset-class-trend-following
  title: Global 5-Asset Trend-Following Strategy Using 10-Month SMA Filter

Original QC logic (simplified for daily bars):
  - Universe: SPY, EFA, IEF, VNQ, GSG
  - SMA length: 10 * 21 = 210 trading days
  - Rebalance once per calendar month when price > SMA
  - Equal-weight the long book; liquidate the rest (cash if none qualify)
"""

from __future__ import annotations

import pandas as pd

from backtest.engine import PortfolioEngine


ASSETS = ["SPY", "EFA", "IEF", "VNQ", "GSG"]
SMA_DAYS = 10 * 21  # matches QC moving_avg_period


def make_strategy(prices: pd.DataFrame):
    sma = prices.rolling(SMA_DAYS, min_periods=SMA_DAYS).mean()
    state = {"last_month": -1, "warm": True}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        # Warmup until SMA ready for at least one asset
        ready = sma.loc[dt].notna().any()
        if not ready:
            return

        if dt.month == state["last_month"]:
            return
        state["last_month"] = dt.month

        long_assets: list[str] = []
        for symbol in ASSETS:
            px = prices.at[dt, symbol]
            ma = sma.at[dt, symbol]
            if pd.isna(px) or pd.isna(ma):
                continue
            if float(px) > float(ma):
                long_assets.append(symbol)

        if not long_assets:
            engine.set_target_weights(dt, {s: 0.0 for s in ASSETS})
            return

        w = 1.0 / len(long_assets)
        engine.set_target_weights(dt, {s: (w if s in long_assets else 0.0) for s in ASSETS})

    return on_day, sma
