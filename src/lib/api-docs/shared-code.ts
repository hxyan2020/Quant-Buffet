/** Python snippets shared across EN/ZH doc pages (code is language-neutral). */

export const IMPORTS = `from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics`;

export const MINIMAL_STRATEGY = `${IMPORTS}

ASSETS = ["SPY", "QQQ", "TLT", "GLD", "BIL"]


def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    sma = prices[cols].rolling(200, min_periods=200).mean()
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if sma.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        long = [s for s in cols if prices.at[dt, s] > sma.at[dt, s]]
        w = 1.0 / len(long) if long else 0.0
        engine.set_target_weights(dt, {s: w for s in long})

    ready = sma.dropna(how="all").index.min()
    return on_day, ready`;

export const LOAD_PRICES = `prices = load_daily_prices(
    ["SPY", "TLT", "GLD"],
    start="2010-01-01",
    end=None,          # optional end date "YYYY-MM-DD"
    use_cache=True,    # default: read/write backtest/data_cache/
    strict=False,      # if True, raise on first symbol failure
)
# prices: pd.DataFrame — DatetimeIndex rows, one column per ticker (adjusted close)`;

export const ENGINE_USAGE = `config = EngineConfig(
    initial_cash=100_000.0,
    commission_bps=5.0,   # 5 bps per fill notional
    slippage_bps=2.0,     # 2 bps price impact per side
)
engine = PortfolioEngine(prices, config)

def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
    engine.set_target_weights(dt, {"SPY": 0.6, "TLT": 0.4})

result = engine.run(on_day, start=pd.Timestamp("2015-01-01"))
# result.equity, result.holdings, result.trades, result.cash`;

export const METRICS_USAGE = `metrics = compute_metrics(
    result.equity,
    benchmark=spy_buy_and_hold,  # optional pd.Series, same index as equity
    risk_free=0.0,
    trades_count=len(result.trades),
)
# keys: start, end, years, cagr, volatility, sharpe, sortino,
#       max_drawdown, calmar, daily_win_rate, trades, alpha, beta, ...`;

export const TEMPLATE_SMA = `from backtest.templates import make_sma_trend

ASSETS = ["SPY", "QQQ", "IWM"]

def make_on_day(prices: pd.DataFrame):
    return make_sma_trend(prices, ASSETS, {"sma_days": 200})`;

export const MEAN_REVERSION = `${IMPORTS}

ASSETS = ["SPY", "QQQ", "IWM", "TLT"]
LOOKBACK = 20
ENTRY_Z = 1.0


def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change()
    mu = rets.rolling(LOOKBACK, min_periods=LOOKBACK).mean()
    sigma = rets.rolling(LOOKBACK, min_periods=LOOKBACK).std()
    z = (rets - mu) / sigma.replace(0, np.nan)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if z.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        # Buy recent losers (negative z), equal weight
        picks = [s for s in cols if z.at[dt, s] < -ENTRY_Z]
        w = 1.0 / len(picks) if picks else 0.0
        engine.set_target_weights(dt, {s: w for s in picks})

    ready = z.dropna(how="all").index.min()
    return on_day, ready`;
