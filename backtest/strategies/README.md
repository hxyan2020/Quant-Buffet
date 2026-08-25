# Strategy code — full library

Coverage: **all published EN + ZH strategies** from `prisma/dev.db`.

| Path | Contents |
|------|----------|
| `generated/{locale}__{slug}.py` | Full **Quant Buffet in-house** Python (1764 files) |
| `qc_original/{locale}__{slug}.qc.py` | Original **QuantConnect** Python when present |
| `qc_original/{locale}__{slug}.MISSING.txt` | Explicit marker when the DB had **no** QC code |
| `INDEX.json` | Per-strategy assets, fidelity, data source, paths |
| `CATALOG.md` | Human-readable table of all strategies |

## Data source (every strategy)

- **Provider:** Yahoo Finance  
- **Library:** `yfinance`  
- **Field:** adjusted close (`auto_adjust=True`)  
- **Loader:** `backtest.data.load_daily_prices`  
- **Cache:** `backtest/data_cache/`

## In-house libraries

| Module | Role |
|--------|------|
| `backtest/data.py` | Price download + CSV cache |
| `backtest/engine.py` | `PortfolioEngine`, `Trade`, `EngineConfig` |
| `backtest/metrics.py` | Performance metrics |
| `backtest/templates.py` | Shared rule builders (batch path) |
| `backtest/universes.py` | Theme ETF books for no-code strategies |
| `backtest/codegen.py` | Emits per-strategy runner source |

## Fidelity labels

| Label | Meaning |
|-------|---------|
| `reconstructed_etf_rules` | QC present; assets extracted; rule templated |
| `qc_present_theme_assets` | QC present; assets from theme book |
| `no_qc_theme_proxy` | No QC in DB; theme ETF proxy from title/assetClass |
| `signal_unavailable_etf_proxy` | Paper needs ML/alt-data/options; ETF proxy only |

## Regenerate

```bash
python scripts/build_full_catalog.py
python scripts/export_full_strategy_code.py
python backtest/run_batch_full.py
```
