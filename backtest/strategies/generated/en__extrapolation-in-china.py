"""
Quant Buffet IN-HOUSE backtest — extrapolation-in-china [en]
file_key: en__extrapolation-in-china
Title: Extrapolation in China
Template: sma_trend
Fidelity: signal_unavailable_etf_proxy
Has QC source in DB: False

DATA SOURCE
-----------
Provider : Yahoo Finance via yfinance (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['FXI', 'ASHR', 'EWH', 'SPY', 'BIL']
Start    : 2000-01-01 (actual start = IPO + signal warmup)
Costs    : 5 bps commission + 2 bps slippage (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
No QuantConnect / AlgoLib source was stored for this strategy in the DB.
This in-house file is a theme-based reconstruction (see Fidelity).

Run from repo root:
  python backtest/strategies/generated/en__extrapolation-in-china.py
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

SLUG = 'extrapolation-in-china'
LOCALE = 'en'
FILE_KEY = 'en__extrapolation-in-china'
TITLE = 'Extrapolation in China'
TEMPLATE = 'sma_trend'
FIDELITY = 'signal_unavailable_etf_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['FXI', 'ASHR', 'EWH', 'SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['FXI', 'ASHR', 'EWH', 'SPY', 'BIL']
SMA_DAYS = 200

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    sma = prices[cols].rolling(SMA_DAYS, min_periods=SMA_DAYS).mean()
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if sma.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        long = [
            s for s in cols
            if pd.notna(prices.at[dt, s]) and pd.notna(sma.at[dt, s])
            and prices.at[dt, s] > sma.at[dt, s]
        ]
        w = {} if not long else {s: 1.0 / len(long) for s in long}
        engine.set_target_weights(dt, w)

    ready = sma.dropna(how="all").index.min() if sma.notna().any().any() else None
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
