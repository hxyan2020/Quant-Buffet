"""Batch-run lab code (after toLabPythonSource strip) through sandbox_runner."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAB = json.loads((ROOT / "backtest" / "drafts" / "lab_index.json").read_text(encoding="utf-8"))
OUT = ROOT / "backtest" / "drafts" / "execution_audit.json"


def to_lab_python_source(slug: str, source: str) -> str:
    body = source.replace("\r\n", "\n")
    main_idx = body.find("\ndef main(")
    if main_idx >= 0:
        body = body[:main_idx]
    m = re.search(
        r"^(?:ASSETS\s*=|from backtest\.|import numpy|import pandas|TARGET_|LOOKBACK|SMA_|FAST|SLOW|VOL_|INVERT|TOP_N)",
        body,
        re.M,
    )
    if m:
        body = body[m.start() :]
    drop = (
        lambda t: t.startswith("import sys")
        or t.startswith("from pathlib")
        or t.startswith("ROOT =")
        or "sys.path" in t
        or t.startswith("if str(ROOT)")
        or t.startswith("from __future__")
    )
    body = "\n".join(line for line in body.split("\n") if not drop(line.strip())).strip()
    header = '''"""
Quant Buffet interactive lab
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics

'''
    for pat in [
        r'^"""[\s\S]*?"""\s*',
        r"^'''[\s\S]*?'''\s*",
        r"^from __future__ import .+$",
        r"^import numpy as np\s*$",
        r"^import pandas as pd\s*$",
        r"^from backtest\.data import .*$",
        r"^from backtest\.engine import .*$",
        r"^from backtest\.metrics import .*$",
        r"^import json\s*$",
        r"^SLUG\s*=.*$",
        r"^LOCALE\s*=.*$",
        r"^FILE_KEY\s*=.*$",
        r"^TITLE\s*=.*$",
        r"^TEMPLATE\s*=.*$",
        r"^FIDELITY\s*=.*$",
        r"^DATA_SOURCE\s*=[\s\S]*?\n(?=[A-Z])",
    ]:
        body = re.sub(pat, "", body, flags=re.M)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return f"{header}{body}\n"


def load_code(entry: dict) -> tuple[str, str]:
    paths = []
    if entry.get("code_path"):
        paths.append(ROOT / entry["code_path"])
    fk = entry.get("file_key")
    if fk:
        paths.append(ROOT / "backtest" / "strategies" / "generated" / f"{fk}.py")
    paths.append(ROOT / "backtest" / "drafts" / "new_100" / "code" / f"{entry['slug']}.py")
    for p in paths:
        if p.exists():
            return to_lab_python_source(entry["slug"], p.read_text(encoding="utf-8", errors="replace")), str(p)
    return "", "MISSING"


def run_code(code: str) -> dict:
    payload = json.dumps({"code": code, "start": "2000-01-01", "max_points": 90})
    proc = subprocess.run(
        [sys.executable, str(ROOT / "backtest" / "sandbox_runner.py")],
        input=payload,
        text=True,
        capture_output=True,
        timeout=120,
    )
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"ok": False, "error": {"type": "BadJson", "message": (proc.stdout or proc.stderr)[-500:]}}


def main() -> None:
    limit = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    source_filter = None
    for arg in sys.argv[1:]:
        if arg.startswith("--source="):
            source_filter = arg.split("=", 1)[1]
    all_entries = LAB["strategies"]
    if source_filter:
        all_entries = [e for e in all_entries if e.get("source") == source_filter]
    entries = all_entries[:limit] if limit else all_entries
    failures = []
    ok = 0
    missing = 0
    err_types = Counter()
    err_msgs = Counter()

    for i, entry in enumerate(entries):
        code, src = load_code(entry)
        if not code.strip():
            missing += 1
            failures.append({"id": entry["id"], "slug": entry["slug"], "error_type": "MissingCode"})
            continue
        result = run_code(code)
        if result.get("ok"):
            ok += 1
            continue
        err = result.get("error") or {}
        et = err.get("type") or "Unknown"
        msg = err.get("message") or ""
        err_types[et] += 1
        err_msgs[msg[:140]] += 1
        failures.append(
            {
                "id": entry["id"],
                "slug": entry["slug"],
                "source": entry["source"],
                "template": entry.get("template"),
                "assets": entry.get("assets"),
                "code_path": src,
                "error_type": et,
                "message": msg,
                "line": err.get("line"),
            }
        )
        if (i + 1) % 300 == 0:
            print(f"... {i+1}/{len(entries)} ok={ok} fail={len(failures)}", flush=True)

    summary = {
        "total": len(entries),
        "ok": ok,
        "failed": len(failures) - missing,
        "missing_code": missing,
        "error_types": dict(err_types),
        "top_messages": err_msgs.most_common(25),
        "failures": failures,
    }
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("total", "ok", "failed", "missing_code", "error_types", "top_messages")}, indent=2))


if __name__ == "__main__":
    main()
