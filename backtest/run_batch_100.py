"""Batch-run the 100-strategy Quant Buffet in-house catalog."""

from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.data import load_price_panel
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics
from backtest.templates import build_strategy

CATALOG = Path(__file__).resolve().parent / "catalog" / "strategies_100.json"
OUT_DIR = Path(__file__).resolve().parent / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY = OUT_DIR / "batch_100_summary.json"
EQUITY_DIR = OUT_DIR / "equity_curves"
EQUITY_DIR.mkdir(parents=True, exist_ok=True)


def downsample(equity: pd.Series, max_points: int = 120) -> list[dict]:
    if equity.empty:
        return []
    step = max(1, len(equity) // max_points)
    pts = [
        {"date": dt.strftime("%Y-%m-%d"), "equity": round(float(v), 2)}
        for dt, v in equity.iloc[::step].items()
    ]
    last_dt, last_v = equity.index[-1], float(equity.iloc[-1])
    if not pts or pts[-1]["date"] != last_dt.strftime("%Y-%m-%d"):
        pts.append({"date": last_dt.strftime("%Y-%m-%d"), "equity": round(last_v, 2)})
    return pts


def run_one(spec: dict, price_cache: dict[str, pd.Series]) -> dict:
    assets = list(spec["assets"])
    # Ensure required series present
    missing = [a for a in assets if a not in price_cache]
    if missing:
        return {
            "slug": spec["slug"],
            "status": "error",
            "error": f"missing prices: {missing}",
        }
    prices = pd.concat({a: price_cache[a] for a in assets}, axis=1).sort_index()
    prices = prices.apply(lambda c: c.ffill())
    # Drop leading all-NaN
    prices = prices.dropna(how="all")

    on_day, ready = build_strategy(spec["template"], prices, assets, spec.get("params") or {})
    if ready is None or pd.isna(ready):
        return {"slug": spec["slug"], "status": "error", "error": "signal never ready"}

    engine = PortfolioEngine(
        prices,
        EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0),
    )
    result = engine.run(on_day, start=ready)
    if result.equity.empty or len(result.equity) < 20:
        return {"slug": spec["slug"], "status": "error", "error": "equity too short"}

    # Benchmark SPY if available else first asset
    bench_sym = "SPY" if "SPY" in price_cache else assets[0]
    spy = price_cache[bench_sym].reindex(result.equity.index).ffill()
    bh = float(result.equity.iloc[0]) * (spy / spy.iloc[0])

    metrics = compute_metrics(
        result.equity,
        benchmark=bh,
        trades_count=len(result.trades),
    )

    # Persist compact equity for top charts later
    curve_path = EQUITY_DIR / f"{spec['slug']}.json"
    curve_path.write_text(
        json.dumps(
            {
                "equity": downsample(result.equity),
                "benchmark": downsample(bh),
            }
        ),
        encoding="utf-8",
    )

    return {
        "slug": spec["slug"],
        "title": spec["title"],
        "template": spec["template"],
        "assets": assets,
        "params": spec.get("params"),
        "fidelity": spec.get("fidelity"),
        "site_annualisedReturn": spec.get("site_annualisedReturn"),
        "site_sharpeRatio": spec.get("site_sharpeRatio"),
        "site_maxDrawdown": spec.get("site_maxDrawdown"),
        "status": "ok",
        "metrics": metrics,
        "trades": len(result.trades),
        "curve_file": str(curve_path.name),
    }


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    strategies = catalog["strategies"]
    all_assets = sorted({a for s in strategies for a in s["assets"]} | {"SPY"})
    print(f"Loading {len(all_assets)} symbols for {len(strategies)} strategies…")
    t0 = time.time()
    panel, missing = load_price_panel(all_assets, start="2000-01-01")
    print(f"Loaded {list(panel.columns)} in {time.time()-t0:.1f}s; missing={missing}")

    price_cache = {c: panel[c] for c in panel.columns}

    results = []
    ok = 0
    for i, spec in enumerate(strategies, 1):
        print(f"[{i}/{len(strategies)}] {spec['slug'].encode('ascii','replace').decode()} ({spec['template']})...", flush=True)
        try:
            row = run_one(spec, price_cache)
        except Exception as exc:  # noqa: BLE001
            row = {
                "slug": spec["slug"],
                "title": spec.get("title"),
                "template": spec.get("template"),
                "status": "error",
                "error": f"{exc}",
                "trace": traceback.format_exc()[-500:],
            }
        results.append(row)
        if row.get("status") == "ok":
            ok += 1
            m = row["metrics"]
            print(
                f"  CAGR={m['cagr']*100:.2f}% Sharpe={m['sharpe']:.2f} "
                f"MaxDD={m['max_drawdown']*100:.1f}% trades={m['trades']}"
            )
        else:
            print(f"  FAIL: {row.get('error')}")

    # Rank OK results
    ok_rows = [r for r in results if r.get("status") == "ok"]
    ok_rows.sort(key=lambda r: r["metrics"]["sharpe"], reverse=True)

    summary = {
        "engine": "Quant Buffet in-house daily backtester",
        "costs": {"commission_bps": 5, "slippage_bps": 2},
        "catalog_note": catalog.get("note"),
        "requested": len(strategies),
        "succeeded": ok,
        "failed": len(strategies) - ok,
        "missing_symbols": missing,
        "elapsed_sec": round(time.time() - t0, 1),
        "leaderboard": [
            {
                "rank": i + 1,
                "slug": r["slug"],
                "title": r["title"],
                "template": r["template"],
                "cagr": r["metrics"]["cagr"],
                "sharpe": r["metrics"]["sharpe"],
                "max_drawdown": r["metrics"]["max_drawdown"],
                "total_return": r["metrics"]["total_return"],
                "years": r["metrics"]["years"],
                "trades": r["metrics"]["trades"],
                "site_sharpe": r.get("site_sharpeRatio"),
                "site_cagr": r.get("site_annualisedReturn"),
                "assets": r["assets"],
            }
            for i, r in enumerate(ok_rows)
        ],
        "results": results,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nDone: {ok}/{len(strategies)} ok → {SUMMARY}")


if __name__ == "__main__":
    main()
