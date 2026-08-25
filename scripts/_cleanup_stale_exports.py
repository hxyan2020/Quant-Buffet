"""Remove stale generated/qc files not in the full catalog INDEX."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = json.loads((ROOT / "backtest" / "strategies" / "INDEX.json").read_text(encoding="utf-8"))
keys = {s["file_key"] for s in INDEX["strategies"]}

gen = ROOT / "backtest" / "strategies" / "generated"
qc = ROOT / "backtest" / "strategies" / "qc_original"

removed = 0
for p in gen.glob("*.py"):
    if p.name == "__init__.py":
        continue
    key = p.stem
    if key not in keys:
        p.unlink()
        removed += 1

for p in list(qc.glob("*.qc.py")) + list(qc.glob("*.MISSING.txt")):
    key = p.name.replace(".qc.py", "").replace(".MISSING.txt", "")
    if key not in keys:
        p.unlink()
        removed += 1

print("removed stale", removed)
print("generated", len(list(gen.glob("*.py"))) - 1)
print("qc", len(list(qc.glob("*.qc.py"))))
print("missing", len(list(qc.glob("*.MISSING.txt"))))
