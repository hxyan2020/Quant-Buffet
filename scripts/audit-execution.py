"""
Audit all lab strategy runners through sandbox_runner (with lab sanitize).

  python scripts/audit-execution.py
  python scripts/audit-execution.py 100          # first 100 only
  python scripts/audit-execution.py --source=new100
"""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = json.loads((ROOT / "backtest" / "drafts" / "lab_index.json").read_text(encoding="utf-8"))
OUT = ROOT / "backtest" / "drafts" / "execution_audit.json"

# Import helpers from same folder
sys.path.insert(0, str(ROOT / "scripts"))
from _audit_execution import load_code, run_code  # noqa: E402


def main() -> None:
    limit = None
    source_filter = None
    for arg in sys.argv[1:]:
        if arg.isdigit():
            limit = int(arg)
        elif arg.startswith("--source="):
            source_filter = arg.split("=", 1)[1]

    entries = LAB["strategies"]
    if source_filter:
        entries = [e for e in entries if e.get("source") == source_filter]
    if limit:
        entries = entries[:limit]

    failures = []
    ok = 0
    missing = 0
    err_types: Counter = Counter()

    for i, entry in enumerate(entries):
        code, src = load_code(entry)
        if not code.strip():
            missing += 1
            failures.append({"slug": entry["slug"], "error_type": "MissingCode"})
            continue
        result = run_code(code)
        if result.get("ok"):
            ok += 1
            continue
        err = result.get("error") or {}
        et = err.get("type") or "Unknown"
        err_types[et] += 1
        failures.append(
            {
                "slug": entry["slug"],
                "source": entry.get("source"),
                "template": entry.get("template"),
                "code_path": src,
                "error_type": et,
                "message": err.get("message"),
                "line": err.get("line"),
            }
        )
        if (i + 1) % 200 == 0:
            print(f"... {i + 1}/{len(entries)} ok={ok} fail={len(failures)}", flush=True)

    summary = {
        "total": len(entries),
        "ok": ok,
        "failed": len(failures) - missing,
        "missing_code": missing,
        "error_types": dict(err_types),
        "failures": failures,
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("total", "ok", "failed", "missing_code", "error_types")}, indent=2))
    if failures[:5]:
        print("sample failures:", json.dumps(failures[:5], indent=2))


if __name__ == "__main__":
    main()
