"""Strip CLI/bootstrap imports so generated runners execute in the Quant Buffet sandbox."""

from __future__ import annotations

import re

_LAB_HEADER = '''"""
Quant Buffet interactive lab
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics

'''

_START_RE = re.compile(
    r"^(?:ASSETS\s*=|from backtest\.|import numpy|import pandas|TARGET_|LOOKBACK|SMA_|FAST|SLOW|VOL_|INVERT|TOP_N|REBALANCE|ENTRY_Z|EXIT_Z|CASH\s*=)",
    re.M,
)

_DROP_LINE = (
    lambda t: t.startswith("import sys")
    or t.startswith("from pathlib")
    or t.startswith("ROOT =")
    or "sys.path" in t
    or t.startswith("if str(ROOT)")
    or t.startswith("from __future__")
)


def sanitize_lab_code(source: str, *, slug: str = "strategy") -> str:
    """Mirror src/lib/draft-preview.ts toLabPythonSource (Python side for sandbox/API)."""
    body = (source or "").replace("\r\n", "\n")
    main_idx = body.find("\ndef main(")
    if main_idx >= 0:
        body = body[:main_idx]

    m = _START_RE.search(body)
    if m:
        body = body[m.start() :]

    body = "\n".join(line for line in body.split("\n") if not _DROP_LINE(line.strip())).strip()

    for pat in (
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
    ):
        body = re.sub(pat, "", body, flags=re.M)

    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    if not body:
        return _LAB_HEADER + f"# Missing strategy body for {slug}\nASSETS = ['SPY', 'BIL']\n"
    return f"{_LAB_HEADER}{body}\n"
