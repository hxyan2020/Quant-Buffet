# Quant Buffet in-house backtester

Pilot + batch stack to run library strategies **without QuantConnect / AlgoLib**.

## Quick start

```bash
# Rebuild 100-strategy catalog from prisma/dev.db
python scripts/_build_catalog_100.py

# Run all catalog strategies
python backtest/run_batch_100.py

# Single pilot
python backtest/run_pilot.py
```

Outputs under `backtest/results/` (`batch_100_summary.json`, equity curves, etc.).

## Layout

| Path | Role |
|------|------|
| `data.py` | yfinance adjusted closes + CSV cache |
| `engine.py` | Daily portfolio, target weights, commissions/slippage |
| `metrics.py` | CAGR, Sharpe, Sortino, drawdown, alpha/beta |
| `templates.py` | Parameterized rules (SMA, momentum, dual mom, etc.) |
| `catalog/strategies_100.json` | 100 mapped library strategies |
| `run_batch_100.py` | Batch runner |
| `run_pilot.py` | Single strategy pilot |

## Notes

- Catalog entries are **rule reconstructions** on liquid ETFs, not bit-identical LEAN ports.
- Some papers are marked `etf_universe_proxy` when the original signal needs fundamentals/alt-data.
- Expect divergence from site-listed Sharpe/CAGR.
