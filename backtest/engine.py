"""Quant Buffet in-house backtest engine (daily, long-only / cash)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


@dataclass
class Trade:
    date: str
    symbol: str
    side: str  # buy | sell
    shares: float
    price: float
    value: float
    commission: float


@dataclass
class BacktestResult:
    equity: pd.Series
    holdings: pd.DataFrame
    trades: list[Trade]
    cash: pd.Series
    benchmark: pd.Series | None = None
    meta: dict = field(default_factory=dict)


@dataclass
class EngineConfig:
    initial_cash: float = 100_000.0
    commission_bps: float = 5.0  # 5 bps per fill notional
    slippage_bps: float = 2.0


class PortfolioEngine:
    def __init__(self, prices: pd.DataFrame, config: EngineConfig | None = None):
        self.prices = prices.sort_index()
        self.config = config or EngineConfig()
        self.symbols = list(prices.columns)
        self.cash = self.config.initial_cash
        self.positions: dict[str, float] = {s: 0.0 for s in self.symbols}
        self.trades: list[Trade] = []
        self.equity_curve: list[tuple[pd.Timestamp, float]] = []
        self.cash_curve: list[tuple[pd.Timestamp, float]] = []
        self.holding_rows: list[dict] = []
        self._last_target_weights: dict[str, float] | None = None

    def _mark(self, dt: pd.Timestamp) -> float:
        equity = self.cash
        row = {"date": dt}
        for s in self.symbols:
            px = self.prices.at[dt, s]
            shares = self.positions[s]
            mv = 0.0 if pd.isna(px) else shares * float(px)
            equity += mv
            row[s] = shares
        self.equity_curve.append((dt, equity))
        self.cash_curve.append((dt, self.cash))
        self.holding_rows.append(row)
        return equity

    def _fill_price(self, raw: float, side: str) -> float:
        slip = self.config.slippage_bps / 10_000.0
        return raw * (1 + slip) if side == "buy" else raw * (1 - slip)

    def set_target_weights(self, dt: pd.Timestamp, weights: dict[str, float]) -> None:
        """Rebalance to target weights (must sum <= 1). Missing symbols → 0."""
        px = self.prices.loc[dt]
        clean = {s: max(0.0, float(w)) for s, w in weights.items() if s in self.symbols}
        total_w = sum(clean.values())
        if total_w > 1.0 + 1e-9:
            clean = {s: w / total_w for s, w in clean.items()}
        # Skip no-op rebalances when targets are unchanged (avoids dust churn).
        if self._last_target_weights is not None:
            keys = set(clean) | set(self._last_target_weights)
            if all(abs(clean.get(k, 0.0) - self._last_target_weights.get(k, 0.0)) < 1e-6 for k in keys):
                return
        self._last_target_weights = dict(clean)

        equity = self.cash + sum(
            self.positions[s] * float(px[s])
            for s in self.symbols
            if not pd.isna(px[s])
        )

        targets_shares: dict[str, float] = {}
        for s in self.symbols:
            w = clean.get(s, 0.0)
            price = px[s]
            if pd.isna(price) or price <= 0:
                targets_shares[s] = 0.0
            else:
                targets_shares[s] = (equity * w) / float(price)

        # Sell first to free cash
        for s in self.symbols:
            delta = targets_shares[s] - self.positions[s]
            if delta < -1e-8:
                self._trade(dt, s, delta, float(px[s]))

        for s in self.symbols:
            delta = targets_shares[s] - self.positions[s]
            if delta > 1e-8:
                self._trade(dt, s, delta, float(px[s]))

    def _trade(self, dt: pd.Timestamp, symbol: str, delta_shares: float, raw_price: float) -> None:
        side = "buy" if delta_shares > 0 else "sell"
        price = self._fill_price(raw_price, side)
        shares = abs(delta_shares)
        notional = shares * price
        commission = notional * (self.config.commission_bps / 10_000.0)

        if side == "buy":
            cost = notional + commission
            if cost > self.cash + 1e-6:
                # Scale down to available cash
                afford = max(0.0, self.cash - commission)
                if afford <= 0 or price <= 0:
                    return
                shares = afford / price
                notional = shares * price
                commission = notional * (self.config.commission_bps / 10_000.0)
                cost = notional + commission
                if shares <= 1e-8:
                    return
            self.cash -= cost
            self.positions[symbol] += shares
        else:
            self.cash += notional - commission
            self.positions[symbol] -= shares
            if abs(self.positions[symbol]) < 1e-8:
                self.positions[symbol] = 0.0

        self.trades.append(
            Trade(
                date=dt.strftime("%Y-%m-%d"),
                symbol=symbol,
                side=side,
                shares=round(shares, 6),
                price=round(price, 6),
                value=round(notional, 2),
                commission=round(commission, 4),
            )
        )

    def run(
        self,
        on_day: Callable[["PortfolioEngine", pd.Timestamp], None],
        *,
        start: pd.Timestamp | None = None,
        end: pd.Timestamp | None = None,
    ) -> BacktestResult:
        idx = self.prices.index
        if start is not None:
            idx = idx[idx >= start]
        if end is not None:
            idx = idx[idx <= end]

        for dt in idx:
            on_day(self, dt)
            self._mark(dt)

        equity = pd.Series(
            {d: v for d, v in self.equity_curve},
            name="equity",
        ).sort_index()
        cash = pd.Series({d: v for d, v in self.cash_curve}, name="cash").sort_index()
        holdings = pd.DataFrame(self.holding_rows).set_index("date").sort_index()
        return BacktestResult(equity=equity, holdings=holdings, trades=self.trades, cash=cash)
