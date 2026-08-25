import json
from pathlib import Path

lb = json.loads(Path("backtest/drafts/new_100/leaderboard.json").read_text(encoding="utf-8"))
s = json.loads(Path("backtest/drafts/new_100/backtest_summary.json").read_text(encoding="utf-8"))
print("ok", s["ok"], "median_cagr", round(s["median_cagr"] * 100, 2), "median_sharpe", round(s["median_sharpe"], 2))
print("templates", s["by_template"])
print("---TOP15---")
for r in lb[:15]:
    print(
        f"{r['rank']:2d} sharpe={r['sharpe']:.2f} cagr={r['cagr']*100:5.1f}% "
        f"dd={r['max_drawdown']*100:6.1f}% {r['template']:18s} {r['slug'][:55]}"
    )
print("---BOTTOM5---")
for r in lb[-5:]:
    print(f"{r['rank']:2d} sharpe={r['sharpe']:.2f} cagr={r['cagr']*100:5.1f}% {r['slug'][:55]}")
