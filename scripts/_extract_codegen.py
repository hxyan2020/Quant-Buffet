from pathlib import Path

src = Path("scripts/_export_strategy_code.py").read_text(encoding="utf-8")
start = src.index("def render_strategy_body")
end = src.index("def build_header")
chunk = src[start:end]
header = '''"""Code generation helpers for in-house strategy runners."""
from __future__ import annotations

import textwrap

'''
Path("backtest/codegen.py").write_text(header + chunk, encoding="utf-8")
print("ok", len((header + chunk).splitlines()))
