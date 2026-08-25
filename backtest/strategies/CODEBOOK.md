# Quant Buffet in-house strategy codebook
Generated from `C:/Users/Hansel Yan/Projects/quant-buffet/backtest/catalog/strategies_100.json`.
QC originals preserved under `backtest/strategies/qc_original/`.
Data for every strategy: **Yahoo Finance adjusted closes via yfinance** (cached in `backtest/data_cache/`).


---

## `1-month-momentum-in-international-equities`

**Title:** 1 Month Momentum in International Equities  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWJ, EWQ, EWH, EIDO, EWI, EWY, EWP, EWD, EWL, EWC, EWZ, ARGT`  
**QC original (preserved):** `backtest/strategies/qc_original/1-month-momentum-in-international-equities.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — 1-month-momentum-in-international-equities
Title: 1 Month Momentum in International Equities
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/1-month-momentum-in-international-equities.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/1-month-momentum-in-international-equities.py
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

SLUG = '1-month-momentum-in-international-equities'
TITLE = '1 Month Momentum in International Equities'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `adaptive-asset-allocation-v-2`

**Title:** Adaptive Asset Allocation v.2  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, QQQ, IWM, VGK, EWJ, EEM, VNQ, DBC, DBA, GLD, LQD, HYG`  
**QC original (preserved):** `backtest/strategies/qc_original/adaptive-asset-allocation-v-2.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — adaptive-asset-allocation-v-2
Title: Adaptive Asset Allocation v.2
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'VNQ', 'DBC', 'DBA', 'GLD', 'LQD', 'HYG']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/adaptive-asset-allocation-v-2.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/adaptive-asset-allocation-v-2.py
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

SLUG = 'adaptive-asset-allocation-v-2'
TITLE = 'Adaptive Asset Allocation v.2'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'VNQ', 'DBC', 'DBA', 'GLD', 'LQD', 'HYG'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'VNQ', 'DBC', 'DBA', 'GLD', 'LQD', 'HYG']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `alpha-momentum-in-country-and-industry-equity-indexes`

**Title:** Alpha Momentum in Country and Industry Equity Indexes  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWJ, EWQ, EWH, EIDO, EWI, EWY, EWP, EWD, EWL, EWC, EWZ, ARGT`  
**QC original (preserved):** `backtest/strategies/qc_original/alpha-momentum-in-country-and-industry-equity-indexes.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — alpha-momentum-in-country-and-industry-equity-indexes
Title: Alpha Momentum in Country and Industry Equity Indexes
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/alpha-momentum-in-country-and-industry-equity-indexes.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/alpha-momentum-in-country-and-industry-equity-indexes.py
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

SLUG = 'alpha-momentum-in-country-and-industry-equity-indexes'
TITLE = 'Alpha Momentum in Country and Industry Equity Indexes'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `betting-against-beta-factor-in-international-equities`

**Title:** Global Country ETF Betting-Against-Beta Strategy  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN, EWS`  
**QC original (preserved):** `backtest/strategies/qc_original/betting-against-beta-factor-in-international-equities.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — betting-against-beta-factor-in-international-equities
Title: Global Country ETF Betting-Against-Beta Strategy
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/betting-against-beta-factor-in-international-equities.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/betting-against-beta-factor-in-international-equities.py
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

SLUG = 'betting-against-beta-factor-in-international-equities'
TITLE = 'Global Country ETF Betting-Against-Beta Strategy'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `bold-asset-allocation`

**Title:** Bold Asset Allocation  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, QQQ, IWM, VGK, EWJ, VWO, VNQ, DBC, GLD, TLT, HYG, LQD`  
**QC original (preserved):** `backtest/strategies/qc_original/bold-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — bold-asset-allocation
Title: Bold Asset Allocation
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'VWO', 'VNQ', 'DBC', 'GLD', 'TLT', 'HYG', 'LQD']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/bold-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/bold-asset-allocation.py
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

SLUG = 'bold-asset-allocation'
TITLE = 'Bold Asset Allocation'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'VWO', 'VNQ', 'DBC', 'GLD', 'TLT', 'HYG', 'LQD'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'VWO', 'VNQ', 'DBC', 'GLD', 'TLT', 'HYG', 'LQD']
LOOKBACK = 126
TOP_N = 1
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `bond-yield-changes-and-the-cross-section-of-equity-indices`

**Title:** Bond Yield Changes and the Cross Section of Equity Indices  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN`  
**QC original (preserved):** `backtest/strategies/qc_original/bond-yield-changes-and-the-cross-section-of-equity-indices.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — bond-yield-changes-and-the-cross-section-of-equity-indices
Title: Bond Yield Changes and the Cross Section of Equity Indices
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/bond-yield-changes-and-the-cross-section-of-equity-indices.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/bond-yield-changes-and-the-cross-section-of-equity-indices.py
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

SLUG = 'bond-yield-changes-and-the-cross-section-of-equity-indices'
TITLE = 'Bond Yield Changes and the Cross Section of Equity Indices'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `double-bottom-country-trading-strategy`

**Title:** Double Bottom Country Trading Strategy  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN, EWS`  
**QC original (preserved):** `backtest/strategies/qc_original/double-bottom-country-trading-strategy.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — double-bottom-country-trading-strategy
Title: Double Bottom Country Trading Strategy
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/double-bottom-country-trading-strategy.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/double-bottom-country-trading-strategy.py
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

SLUG = 'double-bottom-country-trading-strategy'
TITLE = 'Double Bottom Country Trading Strategy'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `generalised-risk-adjusted-momentum-in-equity-indexes`

**Title:** Generalised Risk-Adjusted Momentum in Equity Indexes  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `ACWI, EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN`  
**QC original (preserved):** `backtest/strategies/qc_original/generalised-risk-adjusted-momentum-in-equity-indexes.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — generalised-risk-adjusted-momentum-in-equity-indexes
Title: Generalised Risk-Adjusted Momentum in Equity Indexes
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['ACWI', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/generalised-risk-adjusted-momentum-in-equity-indexes.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/generalised-risk-adjusted-momentum-in-equity-indexes.py
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
TITLE = 'Generalised Risk-Adjusted Momentum in Equity Indexes'
TEMPLATE = 'momentum_rotation'
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
LOOKBACK = 126
TOP_N = 5
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `geographical-country-momentum`

**Title:** Geographical Country Momentum  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN, EWS`  
**QC original (preserved):** `backtest/strategies/qc_original/geographical-country-momentum.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — geographical-country-momentum
Title: Geographical Country Momentum
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/geographical-country-momentum.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/geographical-country-momentum.py
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

SLUG = 'geographical-country-momentum'
TITLE = 'Geographical Country Momentum'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `international-volatility-arbitrage`

**Title:** International Volatility Arbitrage  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN, EWS`  
**QC original (preserved):** `backtest/strategies/qc_original/international-volatility-arbitrage.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — international-volatility-arbitrage
Title: International Volatility Arbitrage
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/international-volatility-arbitrage.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/international-volatility-arbitrage.py
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

SLUG = 'international-volatility-arbitrage'
TITLE = 'International Volatility Arbitrage'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `kellers-keunigs-defensive-asset-allocation`

**Title:** Keller’s & Keunig’s Defensive Asset Allocation  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, IWM, QQQ, VGK, EWJ, VWO, VNQ, GSG, GLD, TLT, HYG, LQD`  
**QC original (preserved):** `backtest/strategies/qc_original/kellers-keunigs-defensive-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — kellers-keunigs-defensive-asset-allocation
Title: Keller’s & Keunig’s Defensive Asset Allocation
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'VWO', 'VNQ', 'GSG', 'GLD', 'TLT', 'HYG', 'LQD']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/kellers-keunigs-defensive-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/kellers-keunigs-defensive-asset-allocation.py
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

SLUG = 'kellers-keunigs-defensive-asset-allocation'
TITLE = 'Keller’s & Keunig’s Defensive Asset Allocation'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'VWO', 'VNQ', 'GSG', 'GLD', 'TLT', 'HYG', 'LQD'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'VWO', 'VNQ', 'GSG', 'GLD', 'TLT', 'HYG', 'LQD']
LOOKBACK = 126
TOP_N = 1
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `kellers-keunigs-vigilant-asset-allocation`

**Title:** Keller’s & Keunig’s Vigilant Asset Allocation  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, IWM, QQQ, VGK, EWJ, EEM, EFA, ACWX, IYR, GSG, GLD, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/kellers-keunigs-vigilant-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — kellers-keunigs-vigilant-asset-allocation
Title: Keller’s & Keunig’s Vigilant Asset Allocation
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'EEM', 'EFA', 'ACWX', 'IYR', 'GSG', 'GLD', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/kellers-keunigs-vigilant-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/kellers-keunigs-vigilant-asset-allocation.py
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

SLUG = 'kellers-keunigs-vigilant-asset-allocation'
TITLE = 'Keller’s & Keunig’s Vigilant Asset Allocation'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'EEM', 'EFA', 'ACWX', 'IYR', 'GSG', 'GLD', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'IWM', 'QQQ', 'VGK', 'EWJ', 'EEM', 'EFA', 'ACWX', 'IYR', 'GSG', 'GLD', 'SHY']
LOOKBACK = 126
TOP_N = 1
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `long-term-reversal-combined-with-a-momentum-effect`

**Title:** Long-Term Reversal Combined with a Momentum Effect  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWJ, EWA, EWG, EWU, EWS, EWQ, EWH, EIDO, EWI, EWY, EWP, EWD`  
**QC original (preserved):** `backtest/strategies/qc_original/long-term-reversal-combined-with-a-momentum-effect.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — long-term-reversal-combined-with-a-momentum-effect
Title: Long-Term Reversal Combined with a Momentum Effect
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWJ', 'EWA', 'EWG', 'EWU', 'EWS', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/long-term-reversal-combined-with-a-momentum-effect.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/long-term-reversal-combined-with-a-momentum-effect.py
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

SLUG = 'long-term-reversal-combined-with-a-momentum-effect'
TITLE = 'Long-Term Reversal Combined with a Momentum Effect'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWJ', 'EWA', 'EWG', 'EWU', 'EWS', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWJ', 'EWA', 'EWG', 'EWU', 'EWS', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD']
LOOKBACK = 21
TOP_N = 4
INVERT = True  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `market-breadth-in-global-equities`

**Title:** Market Breadth in Global Equities  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, EWA, EWZ, EWC, FXI, EWQ, EWG, EWH, EWJ, EWN, EWS, EWY`  
**QC original (preserved):** `backtest/strategies/qc_original/market-breadth-in-global-equities.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — market-breadth-in-global-equities
Title: Market Breadth in Global Equities
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'EWA', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWJ', 'EWN', 'EWS', 'EWY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/market-breadth-in-global-equities.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/market-breadth-in-global-equities.py
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

SLUG = 'market-breadth-in-global-equities'
TITLE = 'Market Breadth in Global Equities'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'EWA', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWJ', 'EWN', 'EWS', 'EWY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'EWA', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWJ', 'EWN', 'EWS', 'EWY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `momentum-and-trend-following-in-global-asset-allocation`

**Title:** Momentum and Trend Following in Global Asset Allocation  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `BIL, EWJ, EWQ, EWU, EWI, EWY, EWP, EWD, EWG, EWL, EWC, EWK`  
**QC original (preserved):** `backtest/strategies/qc_original/momentum-and-trend-following-in-global-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — momentum-and-trend-following-in-global-asset-allocation
Title: Momentum and Trend Following in Global Asset Allocation
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['BIL', 'EWJ', 'EWQ', 'EWU', 'EWI', 'EWY', 'EWP', 'EWD', 'EWG', 'EWL', 'EWC', 'EWK']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/momentum-and-trend-following-in-global-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/momentum-and-trend-following-in-global-asset-allocation.py
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

SLUG = 'momentum-and-trend-following-in-global-asset-allocation'
TITLE = 'Momentum and Trend Following in Global Asset Allocation'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['BIL', 'EWJ', 'EWQ', 'EWU', 'EWI', 'EWY', 'EWP', 'EWD', 'EWG', 'EWL', 'EWC', 'EWK'],
    "history_start": "2000-01-01",
}


ASSETS = ['BIL', 'EWJ', 'EWQ', 'EWU', 'EWI', 'EWY', 'EWP', 'EWD', 'EWG', 'EWL', 'EWC', 'EWK']
LOOKBACK = 21
TOP_N = 7
INVERT = True  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `momentum-combined-with-value-effect-within-countries`

**Title:** Momentum Combined with Value Effect within Countries  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `ARGT, EWA, EWK, EWZ, EWC, ECH, FXI, EWQ, EWG, EWH, EIDO, EWI`  
**QC original (preserved):** `backtest/strategies/qc_original/momentum-combined-with-value-effect-within-countries.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — momentum-combined-with-value-effect-within-countries
Title: Momentum Combined with Value Effect within Countries
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['ARGT', 'EWA', 'EWK', 'EWZ', 'EWC', 'ECH', 'FXI', 'EWQ', 'EWG', 'EWH', 'EIDO', 'EWI']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/momentum-combined-with-value-effect-within-countries.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/momentum-combined-with-value-effect-within-countries.py
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

SLUG = 'momentum-combined-with-value-effect-within-countries'
TITLE = 'Momentum Combined with Value Effect within Countries'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['ARGT', 'EWA', 'EWK', 'EWZ', 'EWC', 'ECH', 'FXI', 'EWQ', 'EWG', 'EWH', 'EIDO', 'EWI'],
    "history_start": "2000-01-01",
}


ASSETS = ['ARGT', 'EWA', 'EWK', 'EWZ', 'EWC', 'ECH', 'FXI', 'EWQ', 'EWG', 'EWH', 'EIDO', 'EWI']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `momentum-factor-effect-in-country-equity-indexes`

**Title:** Country ETF Momentum Strategy Selecting Top 5 with 10-12 Month Momentum  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN, EWS`  
**QC original (preserved):** `backtest/strategies/qc_original/momentum-factor-effect-in-country-equity-indexes.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — momentum-factor-effect-in-country-equity-indexes
Title: Country ETF Momentum Strategy Selecting Top 5 with 10-12 Month Momentum
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/momentum-factor-effect-in-country-equity-indexes.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/momentum-factor-effect-in-country-equity-indexes.py
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

SLUG = 'momentum-factor-effect-in-country-equity-indexes'
TITLE = 'Country ETF Momentum Strategy Selecting Top 5 with 10-12 Month Momentum'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
LOOKBACK = 126
TOP_N = 5
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `multi-asset-market-breadth-momentum`

**Title:** Multi-Asset Market Breadth Momentum  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, QQQ, IWM, VGK, EWJ, EEM, GSG, GLD, IYR, HYG, LQD, TLT`  
**QC original (preserved):** `backtest/strategies/qc_original/multi-asset-market-breadth-momentum.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — multi-asset-market-breadth-momentum
Title: Multi-Asset Market Breadth Momentum
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'GSG', 'GLD', 'IYR', 'HYG', 'LQD', 'TLT']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/multi-asset-market-breadth-momentum.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/multi-asset-market-breadth-momentum.py
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

SLUG = 'multi-asset-market-breadth-momentum'
TITLE = 'Multi-Asset Market Breadth Momentum'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'GSG', 'GLD', 'IYR', 'HYG', 'LQD', 'TLT'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'GSG', 'GLD', 'IYR', 'HYG', 'LQD', 'TLT']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `oil-beta-uncertainty-and-global-stock-returns`

**Title:** Oil Beta Uncertainty and Global Stock Returns  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `URTH, EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN`  
**QC original (preserved):** `backtest/strategies/qc_original/oil-beta-uncertainty-and-global-stock-returns.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — oil-beta-uncertainty-and-global-stock-returns
Title: Oil Beta Uncertainty and Global Stock Returns
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['URTH', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/oil-beta-uncertainty-and-global-stock-returns.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/oil-beta-uncertainty-and-global-stock-returns.py
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

SLUG = 'oil-beta-uncertainty-and-global-stock-returns'
TITLE = 'Oil Beta Uncertainty and Global Stock Returns'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['URTH', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN'],
    "history_start": "2000-01-01",
}


ASSETS = ['URTH', 'EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `price-based-quantitative-strategy-for-country-valuation`

**Title:** Price-Based Quantitative Strategy for Country Valuation  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWU, EWG, EWQ, EWI, EWD, EWN, EWP, EWK, EWL, EWC, EWJ, EWA`  
**QC original (preserved):** `backtest/strategies/qc_original/price-based-quantitative-strategy-for-country-valuation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — price-based-quantitative-strategy-for-country-valuation
Title: Price-Based Quantitative Strategy for Country Valuation
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWU', 'EWG', 'EWQ', 'EWI', 'EWD', 'EWN', 'EWP', 'EWK', 'EWL', 'EWC', 'EWJ', 'EWA']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/price-based-quantitative-strategy-for-country-valuation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/price-based-quantitative-strategy-for-country-valuation.py
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

SLUG = 'price-based-quantitative-strategy-for-country-valuation'
TITLE = 'Price-Based Quantitative Strategy for Country Valuation'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWU', 'EWG', 'EWQ', 'EWI', 'EWD', 'EWN', 'EWP', 'EWK', 'EWL', 'EWC', 'EWJ', 'EWA'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWU', 'EWG', 'EWQ', 'EWI', 'EWD', 'EWN', 'EWP', 'EWK', 'EWL', 'EWC', 'EWJ', 'EWA']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `reversal-effect-in-international-equity-etfs`

**Title:** Country ETF Long-Short Reversal Strategy Based on 36-Month Returns with Triennial Rebalance  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWK, EWZ, EWC, FXI, EWQ, EWG, EWH, EWI, EWJ, EWN, EWS`  
**QC original (preserved):** `backtest/strategies/qc_original/reversal-effect-in-international-equity-etfs.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — reversal-effect-in-international-equity-etfs
Title: Country ETF Long-Short Reversal Strategy Based on 36-Month Returns with Triennial Rebalance
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/reversal-effect-in-international-equity-etfs.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/reversal-effect-in-international-equity-etfs.py
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

SLUG = 'reversal-effect-in-international-equity-etfs'
TITLE = 'Country ETF Long-Short Reversal Strategy Based on 36-Month Returns with Triennial Rebalance'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWK', 'EWZ', 'EWC', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWN', 'EWS']
LOOKBACK = 21
TOP_N = 5
INVERT = True  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `skewness-effect-in-country-equity-indexes`

**Title:** Skewness Effect in Country Equity Indexes  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWJ, EWQ, EWH, EIDO, EWI, EWY, EWP, EWD, EWL, EWC, EWZ, ARGT`  
**QC original (preserved):** `backtest/strategies/qc_original/skewness-effect-in-country-equity-indexes.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — skewness-effect-in-country-equity-indexes
Title: Skewness Effect in Country Equity Indexes
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/skewness-effect-in-country-equity-indexes.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/skewness-effect-in-country-equity-indexes.py
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

SLUG = 'skewness-effect-in-country-equity-indexes'
TITLE = 'Skewness Effect in Country Equity Indexes'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWJ', 'EWQ', 'EWH', 'EIDO', 'EWI', 'EWY', 'EWP', 'EWD', 'EWL', 'EWC', 'EWZ', 'ARGT']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `spin-off-anomaly`

**Title:** Spin-off Anomaly  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, VNQ, XLK, XLE, XLV, XLF, XLI, XLB, XLY, XLP, XLU, XLC`  
**QC original (preserved):** `backtest/strategies/qc_original/spin-off-anomaly.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — spin-off-anomaly
Title: Spin-off Anomaly
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU', 'XLC']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/spin-off-anomaly.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/spin-off-anomaly.py
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

SLUG = 'spin-off-anomaly'
TITLE = 'Spin-off Anomaly'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU', 'XLC'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU', 'XLC']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `value-effect-within-countries-v2`

**Title:** Value Effect within Countries v2  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `ARGT, EWA, EWK, EWZ, EWC, ECH, FXI, EWQ, EWG, EWH, EIDO, EWI`  
**QC original (preserved):** `backtest/strategies/qc_original/value-effect-within-countries-v2.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — value-effect-within-countries-v2
Title: Value Effect within Countries v2
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['ARGT', 'EWA', 'EWK', 'EWZ', 'EWC', 'ECH', 'FXI', 'EWQ', 'EWG', 'EWH', 'EIDO', 'EWI']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/value-effect-within-countries-v2.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/value-effect-within-countries-v2.py
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

SLUG = 'value-effect-within-countries-v2'
TITLE = 'Value Effect within Countries v2'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['ARGT', 'EWA', 'EWK', 'EWZ', 'EWC', 'ECH', 'FXI', 'EWQ', 'EWG', 'EWH', 'EIDO', 'EWI'],
    "history_start": "2000-01-01",
}


ASSETS = ['ARGT', 'EWA', 'EWK', 'EWZ', 'EWC', 'ECH', 'FXI', 'EWQ', 'EWG', 'EWH', 'EIDO', 'EWI']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `value-factor-cape-effect-within-countries`

**Title:** Global Low-CAPE Value Strategy with Annual Rebalance  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWZ, EWC, EWL, FXI, EWQ, EWG, EWH, EWI, EWJ, EWY, EWN`  
**QC original (preserved):** `backtest/strategies/qc_original/value-factor-cape-effect-within-countries.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — value-factor-cape-effect-within-countries
Title: Global Low-CAPE Value Strategy with Annual Rebalance
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWZ', 'EWC', 'EWL', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWY', 'EWN']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/value-factor-cape-effect-within-countries.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/value-factor-cape-effect-within-countries.py
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

SLUG = 'value-factor-cape-effect-within-countries'
TITLE = 'Global Low-CAPE Value Strategy with Annual Rebalance'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWZ', 'EWC', 'EWL', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWY', 'EWN'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWZ', 'EWC', 'EWL', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWY', 'EWN']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `value-factor-cape-effect-within-countries-2`

**Title:** Global Low-CAPE Value Strategy with Annual Rebalance  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWZ, EWC, EWL, FXI, EWQ, EWG, EWH, EWI, EWJ, EWY, EWN`  
**QC original (preserved):** `backtest/strategies/qc_original/value-factor-cape-effect-within-countries-2.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — value-factor-cape-effect-within-countries-2
Title: Global Low-CAPE Value Strategy with Annual Rebalance
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWZ', 'EWC', 'EWL', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWY', 'EWN']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/value-factor-cape-effect-within-countries-2.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/value-factor-cape-effect-within-countries-2.py
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

SLUG = 'value-factor-cape-effect-within-countries-2'
TITLE = 'Global Low-CAPE Value Strategy with Annual Rebalance'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWZ', 'EWC', 'EWL', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWY', 'EWN'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWZ', 'EWC', 'EWL', 'FXI', 'EWQ', 'EWG', 'EWH', 'EWI', 'EWJ', 'EWY', 'EWN']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `volatility-weighted-short-term-reversal-strategy-in-emerging-market-equities`

**Title:** Volatility-Weighted Short-Term Reversal Strategy in Emerging Market Equities  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `FXI, EWH, EWT, EIDO, EPHE, THD, EWS, TUR, EWZ, ARGT, ECH, EPOL`  
**QC original (preserved):** `backtest/strategies/qc_original/volatility-weighted-short-term-reversal-strategy-in-emerging-market-equities.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — volatility-weighted-short-term-reversal-strategy-in-emerging-market-equities
Title: Volatility-Weighted Short-Term Reversal Strategy in Emerging Market Equities
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['FXI', 'EWH', 'EWT', 'EIDO', 'EPHE', 'THD', 'EWS', 'TUR', 'EWZ', 'ARGT', 'ECH', 'EPOL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/volatility-weighted-short-term-reversal-strategy-in-emerging-market-equities.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/volatility-weighted-short-term-reversal-strategy-in-emerging-market-equities.py
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

SLUG = 'volatility-weighted-short-term-reversal-strategy-in-emerging-market-equities'
TITLE = 'Volatility-Weighted Short-Term Reversal Strategy in Emerging Market Equities'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['FXI', 'EWH', 'EWT', 'EIDO', 'EPHE', 'THD', 'EWS', 'TUR', 'EWZ', 'ARGT', 'ECH', 'EPOL'],
    "history_start": "2000-01-01",
}


ASSETS = ['FXI', 'EWH', 'EWT', 'EIDO', 'EPHE', 'THD', 'EWS', 'TUR', 'EWZ', 'ARGT', 'ECH', 'EPOL']
LOOKBACK = 21
TOP_N = 3
INVERT = True  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `cape-sector-picking-strategy`

**Title:** CAPE Sector Picking Strategy  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `XLC, XLRE, XLV, XLI, XLY, XLP, XLB, XLK, XLU, XLE, XLF`  
**QC original (preserved):** `backtest/strategies/qc_original/cape-sector-picking-strategy.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — cape-sector-picking-strategy
Title: CAPE Sector Picking Strategy
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['XLC', 'XLRE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLK', 'XLU', 'XLE', 'XLF']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/cape-sector-picking-strategy.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/cape-sector-picking-strategy.py
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

SLUG = 'cape-sector-picking-strategy'
TITLE = 'CAPE Sector Picking Strategy'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['XLC', 'XLRE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLK', 'XLU', 'XLE', 'XLF'],
    "history_start": "2000-01-01",
}


ASSETS = ['XLC', 'XLRE', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLK', 'XLU', 'XLE', 'XLF']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `cold-ipos-effect`

**Title:** Cold IPOs Effect  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, VNQ, XLK, XLE, XLV, XLF, XLI, XLB, XLY, XLP, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/cold-ipos-effect.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — cold-ipos-effect
Title: Cold IPOs Effect
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/cold-ipos-effect.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/cold-ipos-effect.py
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

SLUG = 'cold-ipos-effect'
TITLE = 'Cold IPOs Effect'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `multi-asset-pairs-momentum`

**Title:** Multi Asset Pairs Momentum  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SHY, AGG, TLT, LQD, HYG, DBC, VNQ, IWM, SPY, EFA, EEM`  
**QC original (preserved):** `backtest/strategies/qc_original/multi-asset-pairs-momentum.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — multi-asset-pairs-momentum
Title: Multi Asset Pairs Momentum
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SHY', 'AGG', 'TLT', 'LQD', 'HYG', 'DBC', 'VNQ', 'IWM', 'SPY', 'EFA', 'EEM']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/multi-asset-pairs-momentum.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/multi-asset-pairs-momentum.py
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

SLUG = 'multi-asset-pairs-momentum'
TITLE = 'Multi Asset Pairs Momentum'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SHY', 'AGG', 'TLT', 'LQD', 'HYG', 'DBC', 'VNQ', 'IWM', 'SPY', 'EFA', 'EEM'],
    "history_start": "2000-01-01",
}


ASSETS = ['SHY', 'AGG', 'TLT', 'LQD', 'HYG', 'DBC', 'VNQ', 'IWM', 'SPY', 'EFA', 'EEM']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `optimalized-subportfolio-momentum`

**Title:** Optimalized Subportfolio Momentum  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `BIL, XLB, XLY, XLF, XLP, XLV, XLU, XLC, XLE, XLI, XLK`  
**QC original (preserved):** `backtest/strategies/qc_original/optimalized-subportfolio-momentum.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — optimalized-subportfolio-momentum
Title: Optimalized Subportfolio Momentum
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['BIL', 'XLB', 'XLY', 'XLF', 'XLP', 'XLV', 'XLU', 'XLC', 'XLE', 'XLI', 'XLK']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/optimalized-subportfolio-momentum.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/optimalized-subportfolio-momentum.py
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

SLUG = 'optimalized-subportfolio-momentum'
TITLE = 'Optimalized Subportfolio Momentum'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['BIL', 'XLB', 'XLY', 'XLF', 'XLP', 'XLV', 'XLU', 'XLC', 'XLE', 'XLI', 'XLK'],
    "history_start": "2000-01-01",
}


ASSETS = ['BIL', 'XLB', 'XLY', 'XLF', 'XLP', 'XLV', 'XLU', 'XLC', 'XLE', 'XLI', 'XLK']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `relative-value-factor-in-us`

**Title:** Relative Value Factor in US  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, VNQ, XLK, XLE, XLV, XLF, XLI, XLB, XLY, XLP, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/relative-value-factor-in-us.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — relative-value-factor-in-us
Title: Relative Value Factor in US
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/relative-value-factor-in-us.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/relative-value-factor-in-us.py
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

SLUG = 'relative-value-factor-in-us'
TITLE = 'Relative Value Factor in US'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `sector-rotation-strategy-based-on-multivariate-regression-analysis`

**Title:** Sector Rotation Strategy Based on Multivariate Regression Analysis  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, SHY, XLV, XLI, XLY, XLP, XLB, XLK, XLU, XLE, XLF`  
**QC original (preserved):** `backtest/strategies/qc_original/sector-rotation-strategy-based-on-multivariate-regression-analysis.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — sector-rotation-strategy-based-on-multivariate-regression-analysis
Title: Sector Rotation Strategy Based on Multivariate Regression Analysis
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'SHY', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLK', 'XLU', 'XLE', 'XLF']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/sector-rotation-strategy-based-on-multivariate-regression-analysis.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/sector-rotation-strategy-based-on-multivariate-regression-analysis.py
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

SLUG = 'sector-rotation-strategy-based-on-multivariate-regression-analysis'
TITLE = 'Sector Rotation Strategy Based on Multivariate Regression Analysis'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'SHY', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLK', 'XLU', 'XLE', 'XLF'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'SHY', 'XLV', 'XLI', 'XLY', 'XLP', 'XLB', 'XLK', 'XLU', 'XLE', 'XLF']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `sector-rotation-via-credit-relative-value`

**Title:** Sector Rotation via Credit Relative Value  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `BIL, SPY, XLK, XLE, XLV, XLF, XLI, XLB, XLY, XLP, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/sector-rotation-via-credit-relative-value.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — sector-rotation-via-credit-relative-value
Title: Sector Rotation via Credit Relative Value
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['BIL', 'SPY', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/sector-rotation-via-credit-relative-value.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/sector-rotation-via-credit-relative-value.py
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

SLUG = 'sector-rotation-via-credit-relative-value'
TITLE = 'Sector Rotation via Credit Relative Value'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['BIL', 'SPY', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['BIL', 'SPY', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `adaptive-asset-allocation`

**Title:** Adaptive Asset Allocation  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, VGK, EWJ, EEM, VNQ, RWX, IEI, IEF, DBC, GLD`  
**QC original (preserved):** `backtest/strategies/qc_original/adaptive-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — adaptive-asset-allocation
Title: Adaptive Asset Allocation
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'VGK', 'EWJ', 'EEM', 'VNQ', 'RWX', 'IEI', 'IEF', 'DBC', 'GLD']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/adaptive-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/adaptive-asset-allocation.py
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

SLUG = 'adaptive-asset-allocation'
TITLE = 'Adaptive Asset Allocation'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'VGK', 'EWJ', 'EEM', 'VNQ', 'RWX', 'IEI', 'IEF', 'DBC', 'GLD'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'VGK', 'EWJ', 'EEM', 'VNQ', 'RWX', 'IEI', 'IEF', 'DBC', 'GLD']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `industry-momentum-riding-industry-bubbles`

**Title:** Industry Alpha Bubble Strategy: Monthly Long Allocation to Statistically Significant Outperforming Sectors  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, XLF, XLV, XLP, XLY, XLI, XLE, XLB, XLK, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/industry-momentum-riding-industry-bubbles.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — industry-momentum-riding-industry-bubbles
Title: Industry Alpha Bubble Strategy: Monthly Long Allocation to Statistically Significant Outperforming Sectors
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'XLF', 'XLV', 'XLP', 'XLY', 'XLI', 'XLE', 'XLB', 'XLK', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/industry-momentum-riding-industry-bubbles.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/industry-momentum-riding-industry-bubbles.py
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

SLUG = 'industry-momentum-riding-industry-bubbles'
TITLE = 'Industry Alpha Bubble Strategy: Monthly Long Allocation to Statistically Significant Outperforming Sectors'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'XLF', 'XLV', 'XLP', 'XLY', 'XLI', 'XLE', 'XLB', 'XLK', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'XLF', 'XLV', 'XLP', 'XLY', 'XLI', 'XLE', 'XLB', 'XLK', 'XLU']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `kellers-keunigs-protective-asset-allocation`

**Title:** Keller’s & Keunig’s Protective Asset Allocation  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SHY, SPY, QQQ, IWM, VGK, EWJ, EEM, IYR, GSG, GLD`  
**QC original (preserved):** `backtest/strategies/qc_original/kellers-keunigs-protective-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — kellers-keunigs-protective-asset-allocation
Title: Keller’s & Keunig’s Protective Asset Allocation
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SHY', 'SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'IYR', 'GSG', 'GLD']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/kellers-keunigs-protective-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/kellers-keunigs-protective-asset-allocation.py
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

SLUG = 'kellers-keunigs-protective-asset-allocation'
TITLE = 'Keller’s & Keunig’s Protective Asset Allocation'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SHY', 'SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'IYR', 'GSG', 'GLD'],
    "history_start": "2000-01-01",
}


ASSETS = ['SHY', 'SPY', 'QQQ', 'IWM', 'VGK', 'EWJ', 'EEM', 'IYR', 'GSG', 'GLD']
SMA_DAYS = 252

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `long-term-reversal-combined-with-a-momentum-effect-in-industry-portfolios`

**Title:** Long-Term Reversal Combined with a Momentum Effect in Industry Portfolios  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, XLY, XLP, XLE, XLF, XLV, XLI, XLB, XLK, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/long-term-reversal-combined-with-a-momentum-effect-in-industry-portfolios.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — long-term-reversal-combined-with-a-momentum-effect-in-industry-portfolios
Title: Long-Term Reversal Combined with a Momentum Effect in Industry Portfolios
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/long-term-reversal-combined-with-a-momentum-effect-in-industry-portfolios.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/long-term-reversal-combined-with-a-momentum-effect-in-industry-portfolios.py
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

SLUG = 'long-term-reversal-combined-with-a-momentum-effect-in-industry-portfolios'
TITLE = 'Long-Term Reversal Combined with a Momentum Effect in Industry Portfolios'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU']
LOOKBACK = 21
TOP_N = 2
INVERT = True  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `stock-and-bond-returns-predict-currency-returns`

**Title:** Stock and Bond Returns Predict Currency Returns  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `VTI, EWA, EWC, EWG, EWJ, EWL, EWU, EPOL, EWS, TUR`  
**QC original (preserved):** `backtest/strategies/qc_original/stock-and-bond-returns-predict-currency-returns.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — stock-and-bond-returns-predict-currency-returns
Title: Stock and Bond Returns Predict Currency Returns
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['VTI', 'EWA', 'EWC', 'EWG', 'EWJ', 'EWL', 'EWU', 'EPOL', 'EWS', 'TUR']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/stock-and-bond-returns-predict-currency-returns.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/stock-and-bond-returns-predict-currency-returns.py
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

SLUG = 'stock-and-bond-returns-predict-currency-returns'
TITLE = 'Stock and Bond Returns Predict Currency Returns'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['VTI', 'EWA', 'EWC', 'EWG', 'EWJ', 'EWL', 'EWU', 'EPOL', 'EWS', 'TUR'],
    "history_start": "2000-01-01",
}


ASSETS = ['VTI', 'EWA', 'EWC', 'EWG', 'EWJ', 'EWL', 'EWU', 'EPOL', 'EWS', 'TUR']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `the-u-s-dollar-and-variance-risk-premia-imbalances`

**Title:** The U.S. Dollar and Variance Risk Premia Imbalances  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, EWQ, EWG, EWI, EWN, EWA, EWC, EWJ, EWL, EWU`  
**QC original (preserved):** `backtest/strategies/qc_original/the-u-s-dollar-and-variance-risk-premia-imbalances.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — the-u-s-dollar-and-variance-risk-premia-imbalances
Title: The U.S. Dollar and Variance Risk Premia Imbalances
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'EWQ', 'EWG', 'EWI', 'EWN', 'EWA', 'EWC', 'EWJ', 'EWL', 'EWU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/the-u-s-dollar-and-variance-risk-premia-imbalances.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/the-u-s-dollar-and-variance-risk-premia-imbalances.py
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

SLUG = 'the-u-s-dollar-and-variance-risk-premia-imbalances'
TITLE = 'The U.S. Dollar and Variance Risk Premia Imbalances'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'EWQ', 'EWG', 'EWI', 'EWN', 'EWA', 'EWC', 'EWJ', 'EWL', 'EWU'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'EWQ', 'EWG', 'EWI', 'EWN', 'EWA', 'EWC', 'EWJ', 'EWL', 'EWU']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `us-sector-rotation-with-five-factor-fama-french-alphas`

**Title:** US Sector Rotation with Five-Factor Fama-French Alphas  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `VNQ, XLK, XLE, XLV, XLF, XLI, XLB, XLY, XLP, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/us-sector-rotation-with-five-factor-fama-french-alphas.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — us-sector-rotation-with-five-factor-fama-french-alphas
Title: US Sector Rotation with Five-Factor Fama-French Alphas
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/us-sector-rotation-with-five-factor-fama-french-alphas.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/us-sector-rotation-with-five-factor-fama-french-alphas.py
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

SLUG = 'us-sector-rotation-with-five-factor-fama-french-alphas'
TITLE = 'US Sector Rotation with Five-Factor Fama-French Alphas'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['VNQ', 'XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `antonaccis-dual-momentum`

**Title:** Antonacci’s Dual Momentum  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `BIL, SPY, EFA, HYG, LQD, MBB, VNQ, TLT, GLD`  
**QC original (preserved):** `backtest/strategies/qc_original/antonaccis-dual-momentum.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — antonaccis-dual-momentum
Title: Antonacci’s Dual Momentum
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['BIL', 'SPY', 'EFA', 'HYG', 'LQD', 'MBB', 'VNQ', 'TLT', 'GLD']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/antonaccis-dual-momentum.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/antonaccis-dual-momentum.py
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

SLUG = 'antonaccis-dual-momentum'
TITLE = 'Antonacci’s Dual Momentum'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['BIL', 'SPY', 'EFA', 'HYG', 'LQD', 'MBB', 'VNQ', 'TLT', 'GLD'],
    "history_start": "2000-01-01",
}


ASSETS = ['BIL', 'SPY', 'EFA', 'HYG', 'LQD', 'MBB', 'VNQ', 'TLT', 'GLD']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `combining-seasonality-and-momentum-in-us-equity-sectors`

**Title:** Combining Seasonality and Momentum in US Equity Sectors  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `XLI, XLY, XLP, XLV, XLU, XLK, XLF, XLE, VNQ`  
**QC original (preserved):** `backtest/strategies/qc_original/combining-seasonality-and-momentum-in-us-equity-sectors.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — combining-seasonality-and-momentum-in-us-equity-sectors
Title: Combining Seasonality and Momentum in US Equity Sectors
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['XLI', 'XLY', 'XLP', 'XLV', 'XLU', 'XLK', 'XLF', 'XLE', 'VNQ']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/combining-seasonality-and-momentum-in-us-equity-sectors.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/combining-seasonality-and-momentum-in-us-equity-sectors.py
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

SLUG = 'combining-seasonality-and-momentum-in-us-equity-sectors'
TITLE = 'Combining Seasonality and Momentum in US Equity Sectors'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['XLI', 'XLY', 'XLP', 'XLV', 'XLU', 'XLK', 'XLF', 'XLE', 'VNQ'],
    "history_start": "2000-01-01",
}


ASSETS = ['XLI', 'XLY', 'XLP', 'XLV', 'XLU', 'XLK', 'XLF', 'XLE', 'VNQ']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `fx-carry-trade`

**Title:** Carry Trade Strategy: Long Highest-Rate Currencies, Short Lowest-Rate  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `XLK, XLE, XLV, XLF, XLI, XLB, XLY, XLP, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/fx-carry-trade.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — fx-carry-trade
Title: Carry Trade Strategy: Long Highest-Rate Currencies, Short Lowest-Rate
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/fx-carry-trade.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/fx-carry-trade.py
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

SLUG = 'fx-carry-trade'
TITLE = 'Carry Trade Strategy: Long Highest-Rate Currencies, Short Lowest-Rate'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `risk-managed-industry-momentum`

**Title:** Risk-Managed Industry Momentum  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `XLY, XLP, XLE, XLF, XLV, XLI, XLB, XLK, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/risk-managed-industry-momentum.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — risk-managed-industry-momentum
Title: Risk-Managed Industry Momentum
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/risk-managed-industry-momentum.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/risk-managed-industry-momentum.py
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

SLUG = 'risk-managed-industry-momentum'
TITLE = 'Risk-Managed Industry Momentum'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLK', 'XLU']
LOOKBACK = 126
TOP_N = 3
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `sector-momentum-rotational-system`

**Title:** Top 3 Sector Momentum Rotation Strategy with Monthly Rebalancing  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `XLK, XLE, XLV, XLF, XLI, XLB, XLY, XLP, XLU`  
**QC original (preserved):** `backtest/strategies/qc_original/sector-momentum-rotational-system.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — sector-momentum-rotational-system
Title: Top 3 Sector Momentum Rotation Strategy with Monthly Rebalancing
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/sector-momentum-rotational-system.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/sector-momentum-rotational-system.py
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

SLUG = 'sector-momentum-rotational-system'
TITLE = 'Top 3 Sector Momentum Rotation Strategy with Monthly Rebalancing'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU'],
    "history_start": "2000-01-01",
}


ASSETS = ['XLK', 'XLE', 'XLV', 'XLF', 'XLI', 'XLB', 'XLY', 'XLP', 'XLU']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `value-and-momentum-factors-across-asset-classes`

**Title:** Multi-Asset Momentum and Valuation Strategy Using Adjusted Yield Rankings  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, MDY, IYR, EWU, EWJ, EEM, LQD, HYG, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/value-and-momentum-factors-across-asset-classes.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — value-and-momentum-factors-across-asset-classes
Title: Multi-Asset Momentum and Valuation Strategy Using Adjusted Yield Rankings
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'MDY', 'IYR', 'EWU', 'EWJ', 'EEM', 'LQD', 'HYG', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/value-and-momentum-factors-across-asset-classes.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/value-and-momentum-factors-across-asset-classes.py
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

SLUG = 'value-and-momentum-factors-across-asset-classes'
TITLE = 'Multi-Asset Momentum and Valuation Strategy Using Adjusted Yield Rankings'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'MDY', 'IYR', 'EWU', 'EWJ', 'EEM', 'LQD', 'HYG', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'MDY', 'IYR', 'EWU', 'EWJ', 'EEM', 'LQD', 'HYG', 'BIL']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `kellers-van-puttens-generalized-momentum-and-flexible-asset-allocation`

**Title:** Keller’s & van Putten’s Generalized Momentum and Flexible Asset Allocation  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `BIL, VTI, VEA, VWO, SHY, BND, GSG, VNQ`  
**QC original (preserved):** `backtest/strategies/qc_original/kellers-van-puttens-generalized-momentum-and-flexible-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — kellers-van-puttens-generalized-momentum-and-flexible-asset-allocation
Title: Keller’s & van Putten’s Generalized Momentum and Flexible Asset Allocation
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['BIL', 'VTI', 'VEA', 'VWO', 'SHY', 'BND', 'GSG', 'VNQ']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/kellers-van-puttens-generalized-momentum-and-flexible-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/kellers-van-puttens-generalized-momentum-and-flexible-asset-allocation.py
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

SLUG = 'kellers-van-puttens-generalized-momentum-and-flexible-asset-allocation'
TITLE = 'Keller’s & van Putten’s Generalized Momentum and Flexible Asset Allocation'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['BIL', 'VTI', 'VEA', 'VWO', 'SHY', 'BND', 'GSG', 'VNQ'],
    "history_start": "2000-01-01",
}


ASSETS = ['BIL', 'VTI', 'VEA', 'VWO', 'SHY', 'BND', 'GSG', 'VNQ']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `volatility-investing-across-asset-classes`

**Title:** Volatility Investing Across Asset Classes  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, IWM, EEM, EWZ, USO, GLD, SLV, IEF`  
**QC original (preserved):** `backtest/strategies/qc_original/volatility-investing-across-asset-classes.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — volatility-investing-across-asset-classes
Title: Volatility Investing Across Asset Classes
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'IWM', 'EEM', 'EWZ', 'USO', 'GLD', 'SLV', 'IEF']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/volatility-investing-across-asset-classes.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/volatility-investing-across-asset-classes.py
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

SLUG = 'volatility-investing-across-asset-classes'
TITLE = 'Volatility Investing Across Asset Classes'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'IWM', 'EEM', 'EWZ', 'USO', 'GLD', 'SLV', 'IEF'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'IWM', 'EEM', 'EWZ', 'USO', 'GLD', 'SLV', 'IEF']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `flight-to-quality-factor-in-fixed-income`

**Title:** Flight to Quality Factor in Fixed Income  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWC, EWG, EWJ, EWU, SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/flight-to-quality-factor-in-fixed-income.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — flight-to-quality-factor-in-fixed-income
Title: Flight to Quality Factor in Fixed Income
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWC', 'EWG', 'EWJ', 'EWU', 'SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/flight-to-quality-factor-in-fixed-income.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/flight-to-quality-factor-in-fixed-income.py
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

SLUG = 'flight-to-quality-factor-in-fixed-income'
TITLE = 'Flight to Quality Factor in Fixed Income'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWC', 'EWG', 'EWJ', 'EWU', 'SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWC', 'EWG', 'EWJ', 'EWU', 'SPY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `predicting-bond-returns-with-equity-return`

**Title:** Predicting Bond Returns with Equity Return  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWA, EWC, EWG, EWU, EWJ, SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/predicting-bond-returns-with-equity-return.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — predicting-bond-returns-with-equity-return
Title: Predicting Bond Returns with Equity Return
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWA', 'EWC', 'EWG', 'EWU', 'EWJ', 'SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/predicting-bond-returns-with-equity-return.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/predicting-bond-returns-with-equity-return.py
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

SLUG = 'predicting-bond-returns-with-equity-return'
TITLE = 'Predicting Bond Returns with Equity Return'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWA', 'EWC', 'EWG', 'EWU', 'EWJ', 'SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWA', 'EWC', 'EWG', 'EWU', 'EWJ', 'SPY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `resilient-asset-allocation`

**Title:** Resilient Asset Allocation  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `QQQ, IEF, TLT, GLD, VWO, BND`  
**QC original (preserved):** `backtest/strategies/qc_original/resilient-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — resilient-asset-allocation
Title: Resilient Asset Allocation
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['QQQ', 'IEF', 'TLT', 'GLD', 'VWO', 'BND']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/resilient-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/resilient-asset-allocation.py
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

SLUG = 'resilient-asset-allocation'
TITLE = 'Resilient Asset Allocation'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['QQQ', 'IEF', 'TLT', 'GLD', 'VWO', 'BND'],
    "history_start": "2000-01-01",
}


ASSETS = ['QQQ', 'IEF', 'TLT', 'GLD', 'VWO', 'BND']
LOOKBACK = 126
TOP_N = 2
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `short-term-reversal-in-equity-index-futures`

**Title:** Short-Term Reversal in Equity Index Futures  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `EWG, EWQ, EWI, EWP, EWN, EWK`  
**QC original (preserved):** `backtest/strategies/qc_original/short-term-reversal-in-equity-index-futures.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — short-term-reversal-in-equity-index-futures
Title: Short-Term Reversal in Equity Index Futures
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['EWG', 'EWQ', 'EWI', 'EWP', 'EWN', 'EWK']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/short-term-reversal-in-equity-index-futures.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/short-term-reversal-in-equity-index-futures.py
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

SLUG = 'short-term-reversal-in-equity-index-futures'
TITLE = 'Short-Term Reversal in Equity Index Futures'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['EWG', 'EWQ', 'EWI', 'EWP', 'EWN', 'EWK'],
    "history_start": "2000-01-01",
}


ASSETS = ['EWG', 'EWQ', 'EWI', 'EWP', 'EWN', 'EWK']
LOOKBACK = 21
TOP_N = 1
INVERT = True  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `asset-class-trend-following`

**Title:** Global 5-Asset Trend-Following Strategy Using 10-Month SMA Filter  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, EFA, IEF, VNQ, GSG`  
**QC original (preserved):** `backtest/strategies/qc_original/asset-class-trend-following.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — asset-class-trend-following
Title: Global 5-Asset Trend-Following Strategy Using 10-Month SMA Filter
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'EFA', 'IEF', 'VNQ', 'GSG']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/asset-class-trend-following.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/asset-class-trend-following.py
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

SLUG = 'asset-class-trend-following'
TITLE = 'Global 5-Asset Trend-Following Strategy Using 10-Month SMA Filter'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'EFA', 'IEF', 'VNQ', 'GSG'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'EFA', 'IEF', 'VNQ', 'GSG']
SMA_DAYS = 210

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `commodities-timing-based-on-a-monetary-conditions`

**Title:** Commodities Timing based on a Monetary Conditions  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, EFA, IEF, LQD, DBC`  
**QC original (preserved):** `backtest/strategies/qc_original/commodities-timing-based-on-a-monetary-conditions.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — commodities-timing-based-on-a-monetary-conditions
Title: Commodities Timing based on a Monetary Conditions
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'EFA', 'IEF', 'LQD', 'DBC']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/commodities-timing-based-on-a-monetary-conditions.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/commodities-timing-based-on-a-monetary-conditions.py
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

SLUG = 'commodities-timing-based-on-a-monetary-conditions'
TITLE = 'Commodities Timing based on a Monetary Conditions'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'EFA', 'IEF', 'LQD', 'DBC'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'EFA', 'IEF', 'LQD', 'DBC']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `commodity-option-implied-volatility-strategy`

**Title:** Commodity Option Implied Volatility Strategy  
**Template:** `equal_weight` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `GLD, USO, UNG, SLV, DBA`  
**QC original (preserved):** `backtest/strategies/qc_original/commodity-option-implied-volatility-strategy.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — commodity-option-implied-volatility-strategy
Title: Commodity Option Implied Volatility Strategy
Template: equal_weight
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['GLD', 'USO', 'UNG', 'SLV', 'DBA']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/commodity-option-implied-volatility-strategy.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/commodity-option-implied-volatility-strategy.py
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

SLUG = 'commodity-option-implied-volatility-strategy'
TITLE = 'Commodity Option Implied Volatility Strategy'
TEMPLATE = 'equal_weight'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['GLD', 'USO', 'UNG', 'SLV', 'DBA'],
    "history_start": "2000-01-01",
}


ASSETS = ['GLD', 'USO', 'UNG', 'SLV', 'DBA']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `lethargic-asset-allocation`

**Title:** Lethargic Asset Allocation  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, GLD, IEF, QQQ, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/lethargic-asset-allocation.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — lethargic-asset-allocation
Title: Lethargic Asset Allocation
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'GLD', 'IEF', 'QQQ', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/lethargic-asset-allocation.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/lethargic-asset-allocation.py
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

SLUG = 'lethargic-asset-allocation'
TITLE = 'Lethargic Asset Allocation'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'GLD', 'IEF', 'QQQ', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'GLD', 'IEF', 'QQQ', 'SHY']
SMA_DAYS = 210

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `momentum-asset-allocation-strategy-2`

**Title:** Top 3 ETF Momentum Strategy Selecting from SPY, EFA, BND, VNQ, GSG  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, EFA, IEF, VNQ, GSG`  
**QC original (preserved):** `backtest/strategies/qc_original/momentum-asset-allocation-strategy-2.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — momentum-asset-allocation-strategy-2
Title: Top 3 ETF Momentum Strategy Selecting from SPY, EFA, BND, VNQ, GSG
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'EFA', 'IEF', 'VNQ', 'GSG']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/momentum-asset-allocation-strategy-2.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/momentum-asset-allocation-strategy-2.py
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

SLUG = 'momentum-asset-allocation-strategy-2'
TITLE = 'Top 3 ETF Momentum Strategy Selecting from SPY, EFA, BND, VNQ, GSG'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'EFA', 'IEF', 'VNQ', 'GSG'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'EFA', 'IEF', 'VNQ', 'GSG']
LOOKBACK = 126
TOP_N = 1
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `the-crisis-alpha-portfolio`

**Title:** The Crisis Alpha Portfolio  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `TLT, IEF, IEI, SHY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/the-crisis-alpha-portfolio.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — the-crisis-alpha-portfolio
Title: The Crisis Alpha Portfolio
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['TLT', 'IEF', 'IEI', 'SHY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/the-crisis-alpha-portfolio.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/the-crisis-alpha-portfolio.py
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

SLUG = 'the-crisis-alpha-portfolio'
TITLE = 'The Crisis Alpha Portfolio'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['TLT', 'IEF', 'IEI', 'SHY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['TLT', 'IEF', 'IEI', 'SHY', 'BIL']
LOOKBACK = 126
TOP_N = 1
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `harvesting-volatility-risk-premia-and-crisis-alpha-via-etfs`

**Title:** Harvesting Volatility Risk Premia and Crisis Alpha via ETFs  
**Template:** `momentum_rotation` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `VIXY, SVXY, USO, UNG`  
**QC original (preserved):** `backtest/strategies/qc_original/harvesting-volatility-risk-premia-and-crisis-alpha-via-etfs.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — harvesting-volatility-risk-premia-and-crisis-alpha-via-etfs
Title: Harvesting Volatility Risk Premia and Crisis Alpha via ETFs
Template: momentum_rotation
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['VIXY', 'SVXY', 'USO', 'UNG']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/harvesting-volatility-risk-premia-and-crisis-alpha-via-etfs.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/harvesting-volatility-risk-premia-and-crisis-alpha-via-etfs.py
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

SLUG = 'harvesting-volatility-risk-premia-and-crisis-alpha-via-etfs'
TITLE = 'Harvesting Volatility Risk Premia and Crisis Alpha via ETFs'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['VIXY', 'SVXY', 'USO', 'UNG'],
    "history_start": "2000-01-01",
}


ASSETS = ['VIXY', 'SVXY', 'USO', 'UNG']
LOOKBACK = 126
TOP_N = 1
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `implied-skewness-strategy-in-commodities`

**Title:** Implied Skewness Strategy in Commodities  
**Template:** `momentum_rotation` · **Fidelity:** `etf_universe_proxy`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `GLD, USO, UNG, SLV`  
**QC original (preserved):** `backtest/strategies/qc_original/implied-skewness-strategy-in-commodities.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — implied-skewness-strategy-in-commodities
Title: Implied Skewness Strategy in Commodities
Template: momentum_rotation
Fidelity: etf_universe_proxy

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['GLD', 'USO', 'UNG', 'SLV']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/implied-skewness-strategy-in-commodities.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/implied-skewness-strategy-in-commodities.py
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

SLUG = 'implied-skewness-strategy-in-commodities'
TITLE = 'Implied Skewness Strategy in Commodities'
TEMPLATE = 'momentum_rotation'
FIDELITY = 'etf_universe_proxy'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['GLD', 'USO', 'UNG', 'SLV'],
    "history_start": "2000-01-01",
}


ASSETS = ['GLD', 'USO', 'UNG', 'SLV']
LOOKBACK = 126
TOP_N = 1
INVERT = False  # True = short-term reversal (rank ascending)

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        row = rets.loc[dt]
        if row.isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        ranked = row.dropna().sort_values(ascending=INVERT)
        picks = list(ranked.head(TOP_N).index)
        if not INVERT:
            picks = [s for s in picks if ranked[s] > 0] or picks[:1]
        w = {} if not picks else {s: 1.0 / len(picks) for s in picks}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `timing-sp500-using-a-large-set-of-forecasting-variables`

**Title:** Timing S&P500 Using a Large Set of Forecasting Variables  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL, GSG`  
**QC original (preserved):** `backtest/strategies/qc_original/timing-sp500-using-a-large-set-of-forecasting-variables.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — timing-sp500-using-a-large-set-of-forecasting-variables
Title: Timing S&P500 Using a Large Set of Forecasting Variables
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL', 'GSG']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/timing-sp500-using-a-large-set-of-forecasting-variables.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/timing-sp500-using-a-large-set-of-forecasting-variables.py
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

SLUG = 'timing-sp500-using-a-large-set-of-forecasting-variables'
TITLE = 'Timing S&P500 Using a Large Set of Forecasting Variables'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL', 'GSG'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL', 'GSG']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `absolute-momentum-effect-in-stocks`

**Title:** Absolute Momentum Effect in Stocks  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/absolute-momentum-effect-in-stocks.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — absolute-momentum-effect-in-stocks
Title: Absolute Momentum Effect in Stocks
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/absolute-momentum-effect-in-stocks.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/absolute-momentum-effect-in-stocks.py
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

SLUG = 'absolute-momentum-effect-in-stocks'
TITLE = 'Absolute Momentum Effect in Stocks'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `avoid-equity-bear-markets-with-a-market-timing-strategy`

**Title:** Avoid Equity Bear Markets with a Market Timing Strategy  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/avoid-equity-bear-markets-with-a-market-timing-strategy.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — avoid-equity-bear-markets-with-a-market-timing-strategy
Title: Avoid Equity Bear Markets with a Market Timing Strategy
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/avoid-equity-bear-markets-with-a-market-timing-strategy.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/avoid-equity-bear-markets-with-a-market-timing-strategy.py
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

SLUG = 'avoid-equity-bear-markets-with-a-market-timing-strategy'
TITLE = 'Avoid Equity Bear Markets with a Market Timing Strategy'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'SHY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `combined-momentum-and-counter-trend-strategy-on-us-equity-indexes`

**Title:** Combined Momentum and Counter Trend Strategy on US Equity Indexes  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, QQQ`  
**QC original (preserved):** `backtest/strategies/qc_original/combined-momentum-and-counter-trend-strategy-on-us-equity-indexes.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — combined-momentum-and-counter-trend-strategy-on-us-equity-indexes
Title: Combined Momentum and Counter Trend Strategy on US Equity Indexes
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'QQQ']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/combined-momentum-and-counter-trend-strategy-on-us-equity-indexes.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/combined-momentum-and-counter-trend-strategy-on-us-equity-indexes.py
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

SLUG = 'combined-momentum-and-counter-trend-strategy-on-us-equity-indexes'
TITLE = 'Combined Momentum and Counter Trend Strategy on US Equity Indexes'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'QQQ'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'QQQ']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `cross-asset-time-series-momentum-equities-and-crude-oil`

**Title:** Cross-asset Time-series Momentum (Equities and Crude Oil)  
**Template:** `abs_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `USO, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/cross-asset-time-series-momentum-equities-and-crude-oil.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — cross-asset-time-series-momentum-equities-and-crude-oil
Title: Cross-asset Time-series Momentum (Equities and Crude Oil)
Template: abs_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['USO', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/cross-asset-time-series-momentum-equities-and-crude-oil.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/cross-asset-time-series-momentum-equities-and-crude-oil.py
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

SLUG = 'cross-asset-time-series-momentum-equities-and-crude-oil'
TITLE = 'Cross-asset Time-series Momentum (Equities and Crude Oil)'
TEMPLATE = 'abs_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['USO', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['USO', 'SHY']
LOOKBACK = 252

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if rets.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        long = [s for s in cols if pd.notna(rets.at[dt, s]) and rets.at[dt, s] > 0]
        w = {} if not long else {s: 1.0 / len(long) for s in long}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `estimating-hedge-funds-returns-out-of-sample`

**Title:** Estimating Hedge Funds’ Returns Out of Sample  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, SVXY`  
**QC original (preserved):** `backtest/strategies/qc_original/estimating-hedge-funds-returns-out-of-sample.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — estimating-hedge-funds-returns-out-of-sample
Title: Estimating Hedge Funds’ Returns Out of Sample
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'SVXY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/estimating-hedge-funds-returns-out-of-sample.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/estimating-hedge-funds-returns-out-of-sample.py
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

SLUG = 'estimating-hedge-funds-returns-out-of-sample'
TITLE = 'Estimating Hedge Funds’ Returns Out of Sample'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'SVXY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'SVXY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `implied-volatility-spreads-and-expected-market-returns-in-sp500`

**Title:** Implied Volatility Spreads and Expected Market Returns in S&P500  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `BIL, SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/implied-volatility-spreads-and-expected-market-returns-in-sp500.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — implied-volatility-spreads-and-expected-market-returns-in-sp500
Title: Implied Volatility Spreads and Expected Market Returns in S&P500
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['BIL', 'SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/implied-volatility-spreads-and-expected-market-returns-in-sp500.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/implied-volatility-spreads-and-expected-market-returns-in-sp500.py
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

SLUG = 'implied-volatility-spreads-and-expected-market-returns-in-sp500'
TITLE = 'Implied Volatility Spreads and Expected Market Returns in S&P500'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['BIL', 'SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['BIL', 'SPY']
SMA_DAYS = 252

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `improved-cross-asset-time-series-momentum-i-xtsm`

**Title:** Improved Cross-Asset Time-Series Momentum I-XTSM  
**Template:** `abs_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/improved-cross-asset-time-series-momentum-i-xtsm.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — improved-cross-asset-time-series-momentum-i-xtsm
Title: Improved Cross-Asset Time-Series Momentum I-XTSM
Template: abs_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/improved-cross-asset-time-series-momentum-i-xtsm.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/improved-cross-asset-time-series-momentum-i-xtsm.py
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

SLUG = 'improved-cross-asset-time-series-momentum-i-xtsm'
TITLE = 'Improved Cross-Asset Time-Series Momentum I-XTSM'
TEMPLATE = 'abs_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if rets.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        long = [s for s in cols if pd.notna(rets.at[dt, s]) and rets.at[dt, s] > 0]
        w = {} if not long else {s: 1.0 / len(long) for s in long}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `inflation-hedging-using-online-prices`

**Title:** Inflation Hedging Using Online Prices  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `TIP, IEF`  
**QC original (preserved):** `backtest/strategies/qc_original/inflation-hedging-using-online-prices.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — inflation-hedging-using-online-prices
Title: Inflation Hedging Using Online Prices
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['TIP', 'IEF']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/inflation-hedging-using-online-prices.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/inflation-hedging-using-online-prices.py
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

SLUG = 'inflation-hedging-using-online-prices'
TITLE = 'Inflation Hedging Using Online Prices'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['TIP', 'IEF'],
    "history_start": "2000-01-01",
}


ASSETS = ['TIP', 'IEF']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `january-barometer`

**Title:** January Return-Based Equity Timing Strategy  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/january-barometer.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — january-barometer
Title: January Return-Based Equity Timing Strategy
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/january-barometer.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/january-barometer.py
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

SLUG = 'january-barometer'
TITLE = 'January Return-Based Equity Timing Strategy'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'SHY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `january-effect-in-stocks`

**Title:** January Small-Cap Entry, Large-Cap Hold Strategy  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, IWM`  
**QC original (preserved):** `backtest/strategies/qc_original/january-effect-in-stocks.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — january-effect-in-stocks
Title: January Small-Cap Entry, Large-Cap Hold Strategy
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'IWM']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/january-effect-in-stocks.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/january-effect-in-stocks.py
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

SLUG = 'january-effect-in-stocks'
TITLE = 'January Small-Cap Entry, Large-Cap Hold Strategy'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'IWM'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'IWM']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `market-seasonality-effect`

**Title:** Global Equity Rotation Strategy Based on Seasonal Market Timing  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/market-seasonality-effect.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — market-seasonality-effect
Title: Global Equity Rotation Strategy Based on Seasonal Market Timing
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/market-seasonality-effect.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/market-seasonality-effect.py
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

SLUG = 'market-seasonality-effect'
TITLE = 'Global Equity Rotation Strategy Based on Seasonal Market Timing'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'SHY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `market-timing-using-lumber-gold-ratio`

**Title:** Market Timing Using Lumber/Gold Ratio  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `IWM, IEF`  
**QC original (preserved):** `backtest/strategies/qc_original/market-timing-using-lumber-gold-ratio.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — market-timing-using-lumber-gold-ratio
Title: Market Timing Using Lumber/Gold Ratio
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['IWM', 'IEF']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/market-timing-using-lumber-gold-ratio.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/market-timing-using-lumber-gold-ratio.py
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

SLUG = 'market-timing-using-lumber-gold-ratio'
TITLE = 'Market Timing Using Lumber/Gold Ratio'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['IWM', 'IEF'],
    "history_start": "2000-01-01",
}


ASSETS = ['IWM', 'IEF']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `market-timing-with-aggregate-and-idiosyncratic-stock-volatilities`

**Title:** Market Timing with Aggregate and Idiosyncratic Stock Volatilities  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/market-timing-with-aggregate-and-idiosyncratic-stock-volatilities.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — market-timing-with-aggregate-and-idiosyncratic-stock-volatilities
Title: Market Timing with Aggregate and Idiosyncratic Stock Volatilities
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/market-timing-with-aggregate-and-idiosyncratic-stock-volatilities.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/market-timing-with-aggregate-and-idiosyncratic-stock-volatilities.py
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

SLUG = 'market-timing-with-aggregate-and-idiosyncratic-stock-volatilities'
TITLE = 'Market Timing with Aggregate and Idiosyncratic Stock Volatilities'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'SHY']
SMA_DAYS = 63

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `market-timing-with-merton-rule-for-earnings-yield`

**Title:** Market Timing with Merton Rule for Earnings Yield  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, TIP`  
**QC original (preserved):** `backtest/strategies/qc_original/market-timing-with-merton-rule-for-earnings-yield.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — market-timing-with-merton-rule-for-earnings-yield
Title: Market Timing with Merton Rule for Earnings Yield
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'TIP']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/market-timing-with-merton-rule-for-earnings-yield.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/market-timing-with-merton-rule-for-earnings-yield.py
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

SLUG = 'market-timing-with-merton-rule-for-earnings-yield'
TITLE = 'Market Timing with Merton Rule for Earnings Yield'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'TIP'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'TIP']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `paired-switching-2`

**Title:** Paired Switching  
**Template:** `abs_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, AGG`  
**QC original (preserved):** `backtest/strategies/qc_original/paired-switching-2.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — paired-switching-2
Title: Paired Switching
Template: abs_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'AGG']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/paired-switching-2.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/paired-switching-2.py
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

SLUG = 'paired-switching-2'
TITLE = 'Paired Switching'
TEMPLATE = 'abs_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'AGG'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'AGG']
LOOKBACK = 252

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if rets.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        long = [s for s in cols if pd.notna(rets.at[dt, s]) and rets.at[dt, s] > 0]
        w = {} if not long else {s: 1.0 / len(long) for s in long}
        engine.set_target_weights(dt, w)

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `residual-momentum-factor`

**Title:** Residual Alpha Momentum Strategy on Large-Cap US Stocks  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/residual-momentum-factor.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — residual-momentum-factor
Title: Residual Alpha Momentum Strategy on Large-Cap US Stocks
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/residual-momentum-factor.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/residual-momentum-factor.py
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

SLUG = 'residual-momentum-factor'
TITLE = 'Residual Alpha Momentum Strategy on Large-Cap US Stocks'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `sharpe-sentiment-cycles`

**Title:** Conditional Sharpe Ratio Timing for Dynamic Equity Allocation  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `BIL, SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/sharpe-sentiment-cycles.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — sharpe-sentiment-cycles
Title: Conditional Sharpe Ratio Timing for Dynamic Equity Allocation
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['BIL', 'SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/sharpe-sentiment-cycles.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/sharpe-sentiment-cycles.py
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

SLUG = 'sharpe-sentiment-cycles'
TITLE = 'Conditional Sharpe Ratio Timing for Dynamic Equity Allocation'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['BIL', 'SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['BIL', 'SPY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `size-factor-vs-monetary-policy-regime`

**Title:** Size Factor vs. Monetary Policy Regime  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, IWM`  
**QC original (preserved):** `backtest/strategies/qc_original/size-factor-vs-monetary-policy-regime.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — size-factor-vs-monetary-policy-regime
Title: Size Factor vs. Monetary Policy Regime
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'IWM']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/size-factor-vs-monetary-policy-regime.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/size-factor-vs-monetary-policy-regime.py
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

SLUG = 'size-factor-vs-monetary-policy-regime'
TITLE = 'Size Factor vs. Monetary Policy Regime'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'IWM'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'IWM']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `stock-trading-rule-that-produces-higher-returns-with-lower-risk`

**Title:** Stock Trading Rule that Produces Higher Returns with Lower Risk  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/stock-trading-rule-that-produces-higher-returns-with-lower-risk.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — stock-trading-rule-that-produces-higher-returns-with-lower-risk
Title: Stock Trading Rule that Produces Higher Returns with Lower Risk
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/stock-trading-rule-that-produces-higher-returns-with-lower-risk.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/stock-trading-rule-that-produces-higher-returns-with-lower-risk.py
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

SLUG = 'stock-trading-rule-that-produces-higher-returns-with-lower-risk'
TITLE = 'Stock Trading Rule that Produces Higher Returns with Lower Risk'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
SMA_DAYS = 189

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `term-spread-and-term-premium-predict-us-government-bonds-returns`

**Title:** Term Spread and Term Premium Predict US Government Bonds Returns  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `IEF, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/term-spread-and-term-premium-predict-us-government-bonds-returns.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — term-spread-and-term-premium-predict-us-government-bonds-returns
Title: Term Spread and Term Premium Predict US Government Bonds Returns
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['IEF', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/term-spread-and-term-premium-predict-us-government-bonds-returns.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/term-spread-and-term-premium-predict-us-government-bonds-returns.py
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

SLUG = 'term-spread-and-term-premium-predict-us-government-bonds-returns'
TITLE = 'Term Spread and Term Premium Predict US Government Bonds Returns'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['IEF', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['IEF', 'BIL']
SMA_DAYS = 840

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `text-based-recession-detection-strategy`

**Title:** Text-Based Recession Detection Strategy  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/text-based-recession-detection-strategy.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — text-based-recession-detection-strategy
Title: Text-Based Recession Detection Strategy
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/text-based-recession-detection-strategy.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/text-based-recession-detection-strategy.py
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

SLUG = 'text-based-recession-detection-strategy'
TITLE = 'Text-Based Recession Detection Strategy'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `timing-sp500-using-full-vs-partial-employment-2`

**Title:** Timing S&P500 Using Full vs. Partial Employment  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, IEF`  
**QC original (preserved):** `backtest/strategies/qc_original/timing-sp500-using-full-vs-partial-employment-2.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — timing-sp500-using-full-vs-partial-employment-2
Title: Timing S&P500 Using Full vs. Partial Employment
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'IEF']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/timing-sp500-using-full-vs-partial-employment-2.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/timing-sp500-using-full-vs-partial-employment-2.py
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

SLUG = 'timing-sp500-using-full-vs-partial-employment-2'
TITLE = 'Timing S&P500 Using Full vs. Partial Employment'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'IEF'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'IEF']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `timing-the-small-cap-effect-ver-2`

**Title:** Timing the Small Cap Effect ver. 2  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, IWM`  
**QC original (preserved):** `backtest/strategies/qc_original/timing-the-small-cap-effect-ver-2.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — timing-the-small-cap-effect-ver-2
Title: Timing the Small Cap Effect ver. 2
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'IWM']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/timing-the-small-cap-effect-ver-2.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/timing-the-small-cap-effect-ver-2.py
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

SLUG = 'timing-the-small-cap-effect-ver-2'
TITLE = 'Timing the Small Cap Effect ver. 2'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'IWM'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'IWM']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `trading-commodity-etfs-versus-equity-etfs`

**Title:** Trading Commodity ETFs versus Equity ETFs  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, DBC`  
**QC original (preserved):** `backtest/strategies/qc_original/trading-commodity-etfs-versus-equity-etfs.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — trading-commodity-etfs-versus-equity-etfs
Title: Trading Commodity ETFs versus Equity ETFs
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'DBC']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/trading-commodity-etfs-versus-equity-etfs.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/trading-commodity-etfs-versus-equity-etfs.py
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

SLUG = 'trading-commodity-etfs-versus-equity-etfs'
TITLE = 'Trading Commodity ETFs versus Equity ETFs'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'DBC'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'DBC']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `trendfollowing-effect-within-reits`

**Title:** Trendfollowing Effect within REITs  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `VNQ, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/trendfollowing-effect-within-reits.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — trendfollowing-effect-within-reits
Title: Trendfollowing Effect within REITs
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['VNQ', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/trendfollowing-effect-within-reits.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/trendfollowing-effect-within-reits.py
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

SLUG = 'trendfollowing-effect-within-reits'
TITLE = 'Trendfollowing Effect within REITs'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['VNQ', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['VNQ', 'SHY']
SMA_DAYS = 504

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `variance-scaled-momentum-in-emerging-markets`

**Title:** Variance Scaled Momentum in Emerging Markets  
**Template:** `vol_target` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, TUR`  
**QC original (preserved):** `backtest/strategies/qc_original/variance-scaled-momentum-in-emerging-markets.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — variance-scaled-momentum-in-emerging-markets
Title: Variance Scaled Momentum in Emerging Markets
Template: vol_target
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'TUR']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/variance-scaled-momentum-in-emerging-markets.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/variance-scaled-momentum-in-emerging-markets.py
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

SLUG = 'variance-scaled-momentum-in-emerging-markets'
TITLE = 'Variance Scaled Momentum in Emerging Markets'
TEMPLATE = 'vol_target'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'TUR'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'TUR']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `yield-gap-predictive-allocation-strategy-for-equity-bond-forecasting`

**Title:** Yield Gap Regression Timing Strategy Using FED Model Signals Monthly  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, SHY`  
**QC original (preserved):** `backtest/strategies/qc_original/yield-gap-predictive-allocation-strategy-for-equity-bond-forecasting.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — yield-gap-predictive-allocation-strategy-for-equity-bond-forecasting
Title: Yield Gap Regression Timing Strategy Using FED Model Signals Monthly
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'SHY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/yield-gap-predictive-allocation-strategy-for-equity-bond-forecasting.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/yield-gap-predictive-allocation-strategy-for-equity-bond-forecasting.py
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

SLUG = 'yield-gap-predictive-allocation-strategy-for-equity-bond-forecasting'
TITLE = 'Yield Gap Regression Timing Strategy Using FED Model Signals Monthly'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'SHY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'SHY']
SMA_DAYS = 252

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `12-month-cycle-in-cross-section-of-stocks-returns`

**Title:** Top 30% Market Cap Stocks Momentum Long-Short Strategy  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/12-month-cycle-in-cross-section-of-stocks-returns.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — 12-month-cycle-in-cross-section-of-stocks-returns
Title: Top 30% Market Cap Stocks Momentum Long-Short Strategy
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/12-month-cycle-in-cross-section-of-stocks-returns.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/12-month-cycle-in-cross-section-of-stocks-returns.py
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

SLUG = '12-month-cycle-in-cross-section-of-stocks-returns'
TITLE = 'Top 30% Market Cap Stocks Momentum Long-Short Strategy'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `12-month-seasonal-reversals`

**Title:** 12 Month Seasonal Reversals  
**Template:** `mean_reversion` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/12-month-seasonal-reversals.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — 12-month-seasonal-reversals
Title: 12 Month Seasonal Reversals
Template: mean_reversion
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/12-month-seasonal-reversals.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/12-month-seasonal-reversals.py
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

SLUG = '12-month-seasonal-reversals'
TITLE = '12 Month Seasonal Reversals'
TEMPLATE = 'mean_reversion'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `52-weeks-high-effect-in-stocks`

**Title:** Industry Momentum Strategy: Monthly Long Stocks in Top Industries by Price-to-52-Week High, Short Bottom Industries  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/52-weeks-high-effect-in-stocks.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — 52-weeks-high-effect-in-stocks
Title: Industry Momentum Strategy: Monthly Long Stocks in Top Industries by Price-to-52-Week High, Short Bottom Industries
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/52-weeks-high-effect-in-stocks.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/52-weeks-high-effect-in-stocks.py
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

SLUG = '52-weeks-high-effect-in-stocks'
TITLE = 'Industry Momentum Strategy: Monthly Long Stocks in Top Industries by Price-to-52-Week High, Short Bottom Industries'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `a-multi-strategy-approach-to-trading-foreign-exchange-futures`

**Title:** A Multi Strategy Approach to Trading Foreign Exchange Futures  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `DBC, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/a-multi-strategy-approach-to-trading-foreign-exchange-futures.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — a-multi-strategy-approach-to-trading-foreign-exchange-futures
Title: A Multi Strategy Approach to Trading Foreign Exchange Futures
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['DBC', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/a-multi-strategy-approach-to-trading-foreign-exchange-futures.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/a-multi-strategy-approach-to-trading-foreign-exchange-futures.py
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

SLUG = 'a-multi-strategy-approach-to-trading-foreign-exchange-futures'
TITLE = 'A Multi Strategy Approach to Trading Foreign Exchange Futures'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['DBC', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['DBC', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `abnormal-volume-effect-in-the-stock-market`

**Title:** Abnormal Volume Effect in the Stock Market  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/abnormal-volume-effect-in-the-stock-market.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — abnormal-volume-effect-in-the-stock-market
Title: Abnormal Volume Effect in the Stock Market
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/abnormal-volume-effect-in-the-stock-market.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/abnormal-volume-effect-in-the-stock-market.py
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

SLUG = 'abnormal-volume-effect-in-the-stock-market'
TITLE = 'Abnormal Volume Effect in the Stock Market'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `active-collar-strategy`

**Title:** Active Collar Strategy  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `QQQ, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/active-collar-strategy.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — active-collar-strategy
Title: Active Collar Strategy
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['QQQ', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/active-collar-strategy.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/active-collar-strategy.py
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

SLUG = 'active-collar-strategy'
TITLE = 'Active Collar Strategy'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['QQQ', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['QQQ', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `adaptive-moving-averages-used-for-market-timing`

**Title:** Adaptive Moving Averages used for Market Timing  
**Template:** `sma_trend` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/adaptive-moving-averages-used-for-market-timing.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — adaptive-moving-averages-used-for-market-timing
Title: Adaptive Moving Averages used for Market Timing
Template: sma_trend
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/adaptive-moving-averages-used-for-market-timing.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/adaptive-moving-averages-used-for-market-timing.py
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

SLUG = 'adaptive-moving-averages-used-for-market-timing'
TITLE = 'Adaptive Moving Averages used for Market Timing'
TEMPLATE = 'sma_trend'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY']
SMA_DAYS = 252

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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `afternoon-reversal-trading-strategy`

**Title:** Afternoon Reversal Trading Strategy  
**Template:** `mean_reversion` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/afternoon-reversal-trading-strategy.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — afternoon-reversal-trading-strategy
Title: Afternoon Reversal Trading Strategy
Template: mean_reversion
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/afternoon-reversal-trading-strategy.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/afternoon-reversal-trading-strategy.py
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

SLUG = 'afternoon-reversal-trading-strategy'
TITLE = 'Afternoon Reversal Trading Strategy'
TEMPLATE = 'mean_reversion'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `announcement-adjusted-industry-relative-reversal-factor`

**Title:** Announcement-Adjusted Industry-Relative Reversal Factor  
**Template:** `mean_reversion` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY`  
**QC original (preserved):** `backtest/strategies/qc_original/announcement-adjusted-industry-relative-reversal-factor.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — announcement-adjusted-industry-relative-reversal-factor
Title: Announcement-Adjusted Industry-Relative Reversal Factor
Template: mean_reversion
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/announcement-adjusted-industry-relative-reversal-factor.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/announcement-adjusted-industry-relative-reversal-factor.py
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

SLUG = 'announcement-adjusted-industry-relative-reversal-factor'
TITLE = 'Announcement-Adjusted Industry-Relative Reversal Factor'
TEMPLATE = 'mean_reversion'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY']
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `buy-side-competition-and-momentum-profits`

**Title:** Buy-Side Competition and Momentum Profits  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/buy-side-competition-and-momentum-profits.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — buy-side-competition-and-momentum-profits
Title: Buy-Side Competition and Momentum Profits
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/buy-side-competition-and-momentum-profits.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/buy-side-competition-and-momentum-profits.py
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

SLUG = 'buy-side-competition-and-momentum-profits'
TITLE = 'Buy-Side Competition and Momentum Profits'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```

---

## `cash-hedged-momentum`

**Title:** Cash Hedged Momentum  
**Template:** `dual_momentum` · **Fidelity:** `reconstructed_etf_rules`  
**Data:** Yahoo Finance / yfinance adjusted close · symbols: `SPY, BIL`  
**QC original (preserved):** `backtest/strategies/qc_original/cash-hedged-momentum.qc.py`  

### In-house Python

```python
"""
Quant Buffet IN-HOUSE backtest — cash-hedged-momentum
Title: Cash Hedged Momentum
Template: dual_momentum
Fidelity: reconstructed_etf_rules

DATA SOURCE
-----------
Provider : Yahoo Finance via `yfinance` (auto_adjust=True → adjusted close)
Loader   : backtest.data.load_daily_prices
Cache    : backtest/data_cache/{SYMBOL}_2000-01-01_latest.csv
Symbols  : ['SPY', 'BIL']
Start    : 2000-01-01 (series begins at each ETF IPO; engine ffill after first print)
Costs    : 5 bps commission + 2 bps slippage per fill (EngineConfig)

ORIGINAL QUANTCONNECT CODE
--------------------------
Preserved unchanged at:
  backtest/strategies/qc_original/cash-hedged-momentum.qc.py

This file does NOT delete or replace QC libraries — it is the Quant Buffet port.
Run from repo root:
  python backtest/strategies/generated/cash-hedged-momentum.py
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

SLUG = 'cash-hedged-momentum'
TITLE = 'Cash Hedged Momentum'
TEMPLATE = 'dual_momentum'
FIDELITY = 'reconstructed_etf_rules'
DATA_SOURCE = {
    "provider": "Yahoo Finance",
    "library": "yfinance",
    "field": "adjusted close (auto_adjust=True)",
    "loader": "backtest.data.load_daily_prices",
    "cache_dir": "backtest/data_cache",
    "symbols": ['SPY', 'BIL'],
    "history_start": "2000-01-01",
}


ASSETS = ['SPY', 'BIL']
LOOKBACK = 252
CASH = 'BIL'

def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    if CASH not in cols and CASH in prices.columns:
        cols = cols + [CASH]
    risky = [c for c in cols if c != CASH]
    rets = prices[cols].pct_change(LOOKBACK)
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        scores = {
            s: float(rets.at[dt, s])
            for s in risky
            if s in rets.columns and pd.notna(rets.at[dt, s])
        }
        if not scores:
            engine.set_target_weights(dt, {CASH: 1.0} if CASH in cols else {})
            return
        best = max(scores, key=scores.get)
        if scores[best] > 0:
            engine.set_target_weights(dt, {best: 1.0})
        elif CASH in cols:
            engine.set_target_weights(dt, {CASH: 1.0})
        else:
            engine.set_target_weights(dt, {})

    ready = rets.dropna(how="all").index.min() if rets.notna().any().any() else None
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

    out = ROOT / "backtest" / "results" / "per_strategy" / f"{SLUG}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "slug": SLUG,
        "title": TITLE,
        "template": TEMPLATE,
        "fidelity": FIDELITY,
        "data_source": DATA_SOURCE,
        "metrics": metrics,
        "trades": len(result.trades),
        "qc_original": f"backtest/strategies/qc_original/{SLUG}.qc.py",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()

```
