import json
from pathlib import Path

idx = json.loads(Path("backtest/drafts/lab_index.json").read_text(encoding="utf-8"))
print("TOTAL", idx["count"])
print("LIBRARY", idx["library"], "NEW100", idx["new100"])
print("EN", idx["by_locale"]["en"], "ZH", idx["by_locale"]["zh"])
print("--- NEW100 first 12 ---")
for i, e in enumerate([x for x in idx["strategies"] if x["source"] == "new100"][:12], 1):
    print(f"{i:2d}. [{e['locale']}] {e['title'][:55]} | sharpe={e.get('sharpeRatio')} | {e['slug']}")
print("--- LIBRARY first 15 ---")
for i, e in enumerate([x for x in idx["strategies"] if x["source"] == "library"][:15], 1):
    print(f"{i:2d}. [{e['locale']}] {e['title'][:55]} | sharpe={e.get('sharpeRatio')} | {e['slug']}")
