"""Quick sandbox smoke test using lab-style source."""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

raw = Path("backtest/drafts/new_100/code/volatilitymanaged-portfolios.py").read_text(encoding="utf-8")
main = raw.find("\ndef main")
if main > 0:
    raw = raw[:main]
lines = []
for line in raw.splitlines():
    t = line.strip()
    if t.startswith(("import sys", "from pathlib", "ROOT", "from __future__")):
        continue
    if "sys.path" in t:
        continue
    if t.startswith(("SLUG", "TITLE", "TEMPLATE", "FIDELITY", "DATA_SOURCE")):
        continue
    lines.append(line)
body = "\n".join(lines)
body = re.sub(r'^"""[\s\S]*?"""\s*', "", body)
body = re.sub(r"^import numpy as np\s*$", "", body, flags=re.M)
body = re.sub(r"^import pandas as pd\s*$", "", body, flags=re.M)
body = re.sub(r"^from backtest\..*$", "", body, flags=re.M)
body = re.sub(r"^import json\s*$", "", body, flags=re.M)
header = '''from __future__ import annotations
import numpy as np
import pandas as pd
from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics

'''
src = header + body.strip() + "\n"
payload = json.dumps({"code": src, "start": "2015-01-01", "max_points": 40})
p = subprocess.run(
    ["python", "backtest/sandbox_runner.py"],
    input=payload,
    text=True,
    capture_output=True,
    timeout=180,
)
print("exit", p.returncode)
print("stderr_tail", (p.stderr or "")[-300:])
obj = json.loads(p.stdout.strip().splitlines()[-1])
print("ok", obj.get("ok"))
if obj.get("ok"):
    print("sharpe", obj["metrics"].get("sharpe"), "cagr", obj["metrics"].get("cagr"))
else:
    print("err", obj.get("error"))
