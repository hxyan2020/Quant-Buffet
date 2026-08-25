"""Parameterized strategy templates for Quant Buffet in-house backtests."""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from backtest.engine import PortfolioEngine


OnDay = Callable[[PortfolioEngine, pd.Timestamp], None]


def _month_key(dt: pd.Timestamp) -> tuple[int, int]:
    return (dt.year, dt.month)


def _equal_weights(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        return {}
    w = 1.0 / len(symbols)
    return {s: w for s in symbols}


def make_sma_trend(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    sma_days = int(params.get("sma_days", 200))
    cols = [c for c in assets if c in prices.columns]
    sma = prices[cols].rolling(sma_days, min_periods=sma_days).mean()
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if sma.loc[dt].isna().all():
            return
        key = _month_key(dt)
        if state["last"] == key:
            return
        state["last"] = key
        long = []
        for s in cols:
            px = prices.at[dt, s]
            m = sma.at[dt, s]
            if pd.notna(px) and pd.notna(m) and px > m:
                long.append(s)
        engine.set_target_weights(dt, _equal_weights(long))

    ready = sma.dropna(how="all").index.min() if sma.notna().any().any() else None
    return on_day, ready


def make_dual_ma(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    fast_n = int(params.get("fast", 50))
    slow_n = int(params.get("slow", 200))
    cols = [c for c in assets if c in prices.columns]
    fast = prices[cols].rolling(fast_n, min_periods=fast_n).mean()
    slow = prices[cols].rolling(slow_n, min_periods=slow_n).mean()
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if slow.loc[dt].isna().all():
            return
        # Daily signal, rebalance only when month changes to limit churn — or daily for true cross
        key = dt.date()
        if state["last"] == key:
            return
        state["last"] = key
        long = []
        for s in cols:
            f = fast.at[dt, s]
            s_ = slow.at[dt, s]
            if pd.notna(f) and pd.notna(s_) and f > s_:
                long.append(s)
        engine.set_target_weights(dt, _equal_weights(long))

    ready = slow.dropna(how="all").index.min() if slow.notna().any().any() else None
    return on_day, ready


def make_abs_momentum(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    lookback = int(params.get("lookback", 252))
    cols = [c for c in assets if c in prices.columns]
    rets = prices[cols].pct_change(lookback)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if rets.loc[dt].isna().all():
            return
        key = _month_key(dt)
        if state["last"] == key:
            return
        state["last"] = key
        long = [s for s in cols if pd.notna(rets.at[dt, s]) and rets.at[dt, s] > 0]
        engine.set_target_weights(dt, _equal_weights(long))

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
    return on_day, ready


def make_dual_momentum(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    lookback = int(params.get("lookback", 252))
    cash = params.get("cash_symbol") or "BIL"
    cols = [c for c in assets if c in prices.columns]
    risky = [c for c in cols if c != cash]
    if cash not in cols and cash in prices.columns:
        cols = cols + [cash]
    rets = prices[cols].pct_change(lookback)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = _month_key(dt)
        if state["last"] == key:
            return
        state["last"] = key
        # Relative: pick best risky; absolute: require positive return else cash
        scores = {}
        for s in risky:
            r = rets.at[dt, s] if s in rets.columns else np.nan
            if pd.notna(r):
                scores[s] = float(r)
        if not scores:
            engine.set_target_weights(dt, {cash: 1.0} if cash in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif cash in cols:
            engine.set_target_weights(dt, {cash: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
    return on_day, ready


def make_momentum_rotation(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    lookback = int(params.get("lookback", 126))
    top_n = int(params.get("top_n", 1))
    cols = [c for c in assets if c in prices.columns]
    rets = prices[cols].pct_change(lookback)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = _month_key(dt)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=False)
        if params.get("invert"):
            ranked = ranked.sort_values(ascending=True)
        picks = list(ranked.head(top_n).index)
        # Absolute filter: skip negative momentum names when alternatives exist
        if not params.get("invert"):
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        engine.set_target_weights(dt, _equal_weights(picks))

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
    return on_day, ready


def make_equal_weight(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    cols = [c for c in assets if c in prices.columns]
    state = {"last": None, "done_once": False}
    once = params.get("rebalance") == "once"

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        available = [s for s in cols if pd.notna(prices.at[dt, s])]
        if not available:
            return
        if once:
            if state["done_once"]:
                return
            state["done_once"] = True
            engine.set_target_weights(dt, _equal_weights(available))
            return
        key = _month_key(dt)
        if state["last"] == key:
            return
        state["last"] = key
        engine.set_target_weights(dt, _equal_weights(available))

    # start when at least half the book has prices
    counts = prices[cols].notna().sum(axis=1)
    need = max(1, len(cols) // 2)
    eligible = counts[counts >= need]
    ready = eligible.index.min() if not eligible.empty else None
    return on_day, ready


def make_mean_reversion(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    lookback = int(params.get("lookback", 20))
    entry_z = float(params.get("entry_z", -1.0))
    exit_z = float(params.get("exit_z", 0.0))
    cols = [c for c in assets if c in prices.columns]
    mu = prices[cols].rolling(lookback, min_periods=lookback).mean()
    sd = prices[cols].rolling(lookback, min_periods=lookback).std(ddof=0)
    z = (prices[cols] - mu) / sd.replace(0, np.nan)
    held: dict[str, bool] = {s: False for s in cols}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        long = []
        for s in cols:
            zv = z.at[dt, s]
            if pd.isna(zv):
                continue
            if not held[s] and zv <= entry_z:
                held[s] = True
            elif held[s] and zv >= exit_z:
                held[s] = False
            if held[s]:
                long.append(s)
        engine.set_target_weights(dt, _equal_weights(long))

    ready = z.dropna(how="all").index.min() if z.notna().any().any() else None
    return on_day, ready


def make_vol_target(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    target = float(params.get("target_vol", 0.10))
    lookback = int(params.get("vol_lookback", 63))
    cols = [c for c in assets if c in prices.columns]
    rets = prices[cols].pct_change()
    vol = rets.rolling(lookback, min_periods=lookback).std() * np.sqrt(252)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = _month_key(dt)
        if state["last"] == key:
            return
        state["last"] = key
        weights = {}
        for s in cols:
            v = vol.at[dt, s]
            if pd.isna(v) or v <= 1e-8:
                continue
            weights[s] = min(1.0, target / float(v))
        # If multi-asset, scale so sum <= 1 equally among available
        if len(weights) > 1:
            # equal risk-ish: each gets target/vol then normalize to sum<=1
            total = sum(weights.values())
            if total > 1:
                weights = {k: v / total for k, v in weights.items()}
            else:
                # leave cash remainder
                pass
        engine.set_target_weights(dt, weights)

    ready = vol.dropna(how="all").index.min() if vol.notna().any().any() else None
    return on_day, ready


def make_risk_parity(prices: pd.DataFrame, assets: list[str], params: dict) -> tuple[OnDay, pd.Timestamp | None]:
    lookback = int(params.get("vol_lookback", 63))
    cols = [c for c in assets if c in prices.columns]
    rets = prices[cols].pct_change()
    vol = rets.rolling(lookback, min_periods=lookback).std() * np.sqrt(252)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = _month_key(dt)
        if state["last"] == key:
            return
        state["last"] = key
        inv = {}
        for s in cols:
            v = vol.at[dt, s]
            if pd.notna(v) and v > 1e-8:
                inv[s] = 1.0 / float(v)
        total = sum(inv.values())
        weights = {k: v / total for k, v in inv.items()} if total > 0 else {}
        engine.set_target_weights(dt, weights)

    ready = vol.dropna(how="all").index.min() if vol.notna().any().any() else None
    return on_day, ready


TEMPLATES = {
    "sma_trend": make_sma_trend,
    "dual_ma": make_dual_ma,
    "abs_momentum": make_abs_momentum,
    "dual_momentum": make_dual_momentum,
    "momentum_rotation": make_momentum_rotation,
    "equal_weight": make_equal_weight,
    "mean_reversion": make_mean_reversion,
    "vol_target": make_vol_target,
    "risk_parity": make_risk_parity,
}


def build_strategy(template: str, prices: pd.DataFrame, assets: list[str], params: dict):
    if template not in TEMPLATES:
        raise ValueError(f"Unknown template: {template}")
    return TEMPLATES[template](prices, assets, params or {})
