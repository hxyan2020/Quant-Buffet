"""
Quant Buffet IN-HOUSE backtest — investor-meetings-in-china-predicts-stock-returns [en]
file_key: en__investor-meetings-in-china-predicts-stock-returns
Title: Investor Meetings in China Predicts Stock Returns
Template: equal_weight
Fidelity: no_qc_theme_proxy
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
  python backtest/strategies/generated/en__investor-meetings-in-china-predicts-stock-returns.py
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

SLUG = 'investor-meetings-in-china-predicts-stock-returns'
LOCALE = 'en'
FILE_KEY = 'en__investor-meetings-in-china-predicts-stock-returns'
TITLE = 'Investor Meetings in China Predicts Stock Returns'
TEMPLATE = 'equal_weight'
FIDELITY = 'no_qc_theme_proxy'
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
REBALANCE_ONCE = False

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    state = {"last": None, "done": False}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        available = [s for s in cols if pd.notna(prices.at[dt, s])]
        if not available:
            return
        if REBALANCE_ONCE:
            if state["done"]:
                return
            state["done"] = True
            engine.set_target_weights(dt, {s: 1.0 / len(available) for s in available})
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        engine.set_target_weights(dt, {s: 1.0 / len(available) for s in available})

    counts = prices[cols].notna().sum(axis=1)
    need = max(1, len(cols) // 2)
    eligible = counts[counts >= need]
    ready = eligible.index.min() if not eligible.empty else None
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
