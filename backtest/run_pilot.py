"""Run the Quant Buffet in-house pilot backtest and emit JSON for the canvas."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics
from backtest.strategies.asset_class_trend_following import ASSETS, SMA_DAYS, make_strategy

OUT_DIR = Path(__file__).resolve().parent / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def downsample_equity(equity: pd.Series, max_points: int = 400) -> list[dict]:
    if len(equity) <= max_points:
        step = 1
    else:
        step = max(1, len(equity) // max_points)
    points = []
    for dt, val in equity.iloc[::step].items():
        points.append({"date": dt.strftime("%Y-%m-%d"), "equity": round(float(val), 2)})
    # Always include last
    last_dt, last_val = equity.index[-1], equity.iloc[-1]
    if not points or points[-1]["date"] != last_dt.strftime("%Y-%m-%d"):
        points.append({"date": last_dt.strftime("%Y-%m-%d"), "equity": round(float(last_val), 2)})
    return points


def main() -> None:
    print("Downloading / loading prices…")
    prices = load_daily_prices(ASSETS, start="2000-01-01")
    # Drop rows where all NaN
    prices = prices.dropna(how="all")

    # Benchmark: buy & hold SPY, normalized to same initial cash later
    spy = prices["SPY"].dropna()

    on_day, sma = make_strategy(prices)
    engine = PortfolioEngine(
        prices,
        EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0),
    )

    # Start once SMA window can fill for majority of assets (post-GSG listing + warmup)
    first_valid = sma.dropna(how="any").index.min()
    if pd.isna(first_valid):
        # GSG may lag — start when at least 3 assets have SMA
        counts = sma.notna().sum(axis=1)
        eligible = counts[counts >= 3]
        if eligible.empty:
            raise SystemExit("SMA never ready")
        first_valid = eligible.index.min()

    print(f"Backtest window starts {first_valid.date()} (SMA={SMA_DAYS}d)")
    result = engine.run(on_day, start=first_valid)

    # Buy-hold SPY benchmark on same dates / cash
    bh = spy.reindex(result.equity.index).ffill()
    bh_equity = 100_000 * (bh / bh.iloc[0])

    metrics = compute_metrics(
        result.equity,
        benchmark=bh_equity,
        trades_count=len(result.trades),
    )

    # Monthly exposure summary
    holdings = result.holdings.copy()
    invested = holdings[ASSETS].abs().sum(axis=1) > 1e-6
    months = holdings.index.to_period("M")
    exposure_by_month = (
        holdings.assign(_m=months, _on=invested)
        .groupby("_m")["_on"]
        .mean()
        .tail(24)
    )

    # Trade blotter (last 40 + first 10 if long)
    trades = [
        {
            "date": t.date,
            "symbol": t.symbol,
            "side": t.side,
            "shares": t.shares,
            "price": t.price,
            "value": t.value,
            "commission": t.commission,
        }
        for t in result.trades
    ]

    # Drawdown series (downsampled)
    peak = result.equity.cummax()
    dd = (result.equity / peak - 1).fillna(0)
    eq_pts = downsample_equity(result.equity)
    dd_points = []
    for p in eq_pts:
        ts = pd.Timestamp(p["date"])
        if ts in dd.index:
            dd_points.append({"date": p["date"], "drawdown": round(float(dd.loc[ts]), 6)})

    # Allocation on last day
    last = result.holdings.iloc[-1]
    last_px = prices.loc[result.equity.index[-1]]
    last_alloc = []
    eq = float(result.equity.iloc[-1])
    for s in ASSETS:
        shares = float(last[s])
        px = float(last_px[s]) if not pd.isna(last_px[s]) else 0.0
        mv = shares * px
        last_alloc.append(
            {
                "symbol": s,
                "shares": round(shares, 4),
                "price": round(px, 4),
                "market_value": round(mv, 2),
                "weight": round(mv / eq, 4) if eq else 0.0,
            }
        )
    cash_w = float(result.cash.iloc[-1]) / eq if eq else 0
    last_alloc.append(
        {
            "symbol": "CASH",
            "shares": 0,
            "price": 1,
            "market_value": round(float(result.cash.iloc[-1]), 2),
            "weight": round(cash_w, 4),
        }
    )

    payload = {
        "strategy": {
            "slug": "asset-class-trend-following",
            "title": "Global 5-Asset Trend-Following Strategy Using 10-Month SMA Filter",
            "engine": "Quant Buffet in-house daily backtester (yfinance adjusted closes)",
            "assets": ASSETS,
            "sma_days": SMA_DAYS,
            "rebalance": "First trading day of each new calendar month",
            "rule": "Equal-weight assets with Close > SMA(210); else cash",
            "costs": {"commission_bps": 5, "slippage_bps": 2},
            "site_listed": {"annualised_return": "11.50%", "sharpe": "1.40"},
            "notes": [
                "Port of QCAlgorithm AssetClassTrendFollowing — no AlgoLib / QuantConnect runtime.",
                "Daily bars approximate the QC monthly check (QC used minute data but only acted monthly at 09:31).",
                "GSG history starts mid-2006; early years may hold fewer than 5 names when SMA is unavailable.",
                "Site metrics may use different dates, corporate-action handling, or no friction — expect divergence.",
            ],
        },
        "metrics": metrics,
        "equity_curve": downsample_equity(result.equity),
        "benchmark_curve": downsample_equity(bh_equity),
        "drawdown_curve": dd_points,
        "trades_total": len(trades),
        "trades_sample": trades[:15] + ([{"_separator": "…"}] if len(trades) > 55 else []) + trades[-40:],
        "last_allocation": last_alloc,
        "recent_month_invested_fraction": {
            str(k): round(float(v), 3) for k, v in exposure_by_month.items()
        },
    }

    out = OUT_DIR / "asset-class-trend-following.json"
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"Wrote {out} ({len(trades)} trades)")


if __name__ == "__main__":
    main()
