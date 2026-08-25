"""
Quant Buffet IN-HOUSE backtest — generalised-risk-adjusted-momentum-in-equity-indexes [en]
file_key: en__generalised-risk-adjusted-momentum-in-equity-indexes
Title: Generalised Risk-Adjusted Momentum in Equity Indexes
Template: vol_target
Fidelity: reconstructed_etf_rules
Has QC source in DB: True

DATA SOURCE
-----------
Provider : Yahoo Finance via yfinance (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['ACWI', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN']
Start    : 2000-01-01 (actual start = IPO + signal warmup)
Costs    : 5 bps commission + 2 bps slippage (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/en__generalised-risk-adjusted-momentum-in-equity-indexes.qc.py

Run from repo root:
  python backtest/strategies/generated/en__generalised-risk-adjusted-momentum-in-equity-indexes.py
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

SLUG = 'generalised-risk-adjusted-momentum-in-equity-indexes'
LOCALE = 'en'
FILE_KEY = 'en__generalised-risk-adjusted-momentum-in-equity-indexes'
TITLE = 'Generalised Risk-Adjusted Momentum in Equity Indexes'
TEMPLATE = 'vol_target'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['ACWI', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN'],
    "history_start": "2000-01-01",
}


ASSETS = ['ACWI', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN']
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
