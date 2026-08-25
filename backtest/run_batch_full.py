"""Batch-run the FULL Quant Buffet in-house catalog."""

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

CATALOG = Path(__file__).resolve().parent / "catalog" / "strategies_full.json"
OUT_DIR = Path(__file__).resolve().parent / "results"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SUMMARY = OUT_DIR / "batch_full_summary.json"
LEADERBOARD = OUT_DIR / "batch_full_leaderboard.json"


def run_one(spec: dict, price_cache: dict[str, pd.Series]) -> dict:
    assets = [a for a in spec["assets"] if a in price_cache]
    missing = [a for a in spec["assets"] if a not in price_cache]
    if len(assets) < 1:
        return {
            "file_key": spec["file_key"],
            "slug": spec["slug"],
            "locale": spec["locale"],
            "status": "error",
            "error": f"no prices for {spec['assets']}",
        }

    prices = pd.concat({a: price_cache[a] for a in assets}, axis=1).sort_index()
    prices = prices.apply(lambda c: c.ffill()).dropna(how="all")

    on_day, ready = build_strategy(spec["template"], prices, assets, spec.get("params") or {})
    if ready is None or pd.isna(ready):
        return {
            "file_key": spec["file_key"],
            "slug": spec["slug"],
            "locale": spec["locale"],
            "status": "error",
            "error": "signal never ready",
            "missing_symbols": missing,
        }

    engine = PortfolioEngine(
        prices,
        EngineConfig(initial_cash=100_000, commission_bps=5.0, slippage_bps=2.0),
    )
    result = engine.run(on_day, start=ready)
    if result.equity.empty or len(result.equity) < 20:
        return {
            "file_key": spec["file_key"],
            "slug": spec["slug"],
            "locale": spec["locale"],
            "status": "error",
            "error": "equity too short",
        }

    bench_sym = "SPY" if "SPY" in price_cache else assets[0]
    spy = price_cache[bench_sym].reindex(result.equity.index).ffill()
    bh = float(result.equity.iloc[0]) * (spy / spy.iloc[0])
    metrics = compute_metrics(
        result.equity, benchmark=bh, trades_count=len(result.trades)
    )

    return {
        "file_key": spec["file_key"],
        "slug": spec["slug"],
        "locale": spec["locale"],
        "title": spec["title"],
        "template": spec["template"],
        "fidelity": spec.get("fidelity"),
        "has_qc_source": spec.get("has_qc_source"),
        "assets_used": assets,
        "missing_symbols": missing,
        "site_annualisedReturn": spec.get("site_annualisedReturn"),
        "site_sharpeRatio": spec.get("site_sharpeRatio"),
        "status": "ok",
        "metrics": metrics,
        "trades": len(result.trades),
    }


def main() -> None:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    strategies = catalog["strategies"]
    all_assets = sorted({a for s in strategies for a in s["assets"]} | {"SPY", "BIL"})
    print(f"Loading {len(all_assets)} symbols for {len(strategies)} strategies…", flush=True)
    t0 = time.time()
    panel, missing = load_price_panel(all_assets, start="2000-01-01")
    print(
        f"Loaded {len(panel.columns)} series in {time.time()-t0:.1f}s; missing={missing}",
        flush=True,
    )
    price_cache = {c: panel[c] for c in panel.columns}

    results = []
    ok = 0
    for i, spec in enumerate(strategies, 1):
        key = spec["file_key"]
        if i % 50 == 1 or i == len(strategies):
            print(f"[{i}/{len(strategies)}] {key}…", flush=True)
        try:
            row = run_one(spec, price_cache)
        except Exception as exc:  # noqa: BLE001
            row = {
                "file_key": key,
                "slug": spec.get("slug"),
                "locale": spec.get("locale"),
                "status": "error",
                "error": str(exc),
                "trace": traceback.format_exc()[-400:],
            }
        results.append(row)
        if row.get("status") == "ok":
            ok += 1

    ok_rows = [r for r in results if r.get("status") == "ok"]
    ok_rows.sort(key=lambda r: r["metrics"]["sharpe"], reverse=True)

    leaderboard = [
        {
            "rank": i + 1,
            "file_key": r["file_key"],
            "slug": r["slug"],
            "locale": r["locale"],
            "title": r.get("title"),
            "template": r["template"],
            "fidelity": r.get("fidelity"),
            "has_qc_source": r.get("has_qc_source"),
            "cagr": r["metrics"]["cagr"],
            "sharpe": r["metrics"]["sharpe"],
            "max_drawdown": r["metrics"]["max_drawdown"],
            "total_return": r["metrics"]["total_return"],
            "years": r["metrics"]["years"],
            "trades": r["metrics"]["trades"],
            "site_sharpe": r.get("site_sharpeRatio"),
            "site_cagr": r.get("site_annualisedReturn"),
        }
        for i, r in enumerate(ok_rows)
    ]

    summary = {
        "engine": "Quant Buffet in-house daily backtester",
        "costs": {"commission_bps": 5, "slippage_bps": 2},
        "catalog_note": catalog.get("note"),
        "catalog_stats": catalog.get("stats"),
        "requested": len(strategies),
        "succeeded": ok,
        "failed": len(strategies) - ok,
        "missing_symbols_global": missing,
        "elapsed_sec": round(time.time() - t0, 1),
        "leaderboard_top50": leaderboard[:50],
        "leaderboard_bottom20": list(reversed(leaderboard[-20:])),
        "results": results,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    LEADERBOARD.write_text(
        json.dumps(leaderboard, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nDone: {ok}/{len(strategies)} ok → {SUMMARY}", flush=True)
    if ok_rows:
        print("TOP5:", flush=True)
        for r in leaderboard[:5]:
            print(
                f"  {r['rank']:3} sharpe={r['sharpe']:.2f} cagr={r['cagr']*100:.1f}% {r['file_key']}",
                flush=True,
            )


if __name__ == "__main__":
    main()
