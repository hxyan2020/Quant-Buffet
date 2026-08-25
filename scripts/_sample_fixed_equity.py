"""Deeper sample of strategy codes for port planning."""
from __future__ import annotations

import json
import re
import sqlite3
from html import unescape
from pathlib import Path

DB = Path("prisma/dev.db")


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<[^>]+>", "\n", t)
    return t


def extract_equities(code: str) -> list[str]:
    pats = [
        r"add_equity\(\s*[\"']([A-Z][A-Z0-9.\-]{1,8})[\"']",
        r"AddEquity\(\s*[\"']([A-Z][A-Z0-9.\-]{1,8})[\"']",
        r"self\.add_equity\(\s*[\"']([A-Z][A-Z0-9.\-]{1,8})[\"']",
        r"self\.AddEquity\(\s*[\"']([A-Z][A-Z0-9.\-]{1,8})[\"']",
    ]
    out: list[str] = []
    for p in pats:
        for m in re.findall(p, code, flags=re.I):
            if m not in out:
                out.append(m)
    return out


con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# Prefer free, fixed-equity strategies
rows = con.execute(
    """
    SELECT slug, title, isPaywalled, annualisedReturn, sharpeRatio, pythonCodeHtml
    FROM Strategy
    WHERE locale='en' AND published=1 AND hasPythonCode=1
    ORDER BY isPaywalled ASC, slug
    """
).fetchall()

fixed = []
for r in rows:
    code = strip_html(r["pythonCodeHtml"])
    eqs = extract_equities(code)
    has_universe = bool(re.search(r"universe|coarse|fine_selection", code, re.I))
    has_opt = bool(re.search(r"add_option|AddOption|option_chain", code, re.I))
    has_fut = bool(re.search(r"add_future|AddFuture", code, re.I))
    has_algo = bool(re.search(r"AlgoLib|algolib", code, re.I))
    if eqs and not has_universe and not has_opt and not has_fut:
        # classify template hint from title+code
        blob = (r["title"] + " " + code[:3000]).lower()
        template = "unknown"
        if "trend" in blob or "sma" in blob or "moving average" in blob:
            template = "sma_trend"
        elif "momentum" in blob or "relative strength" in blob:
            template = "momentum"
        elif "mean reversion" in blob or "rsi" in blob or "bollinger" in blob:
            template = "mean_reversion"
        elif "dual" in blob and "momentum" in blob:
            template = "dual_momentum"
        elif "risk parity" in blob or "equal weight" in blob or "60/40" in blob:
            template = "static_weights"
        elif "rotation" in blob or "sector" in blob:
            template = "rotation"
        elif "volatility" in blob or "vol target" in blob:
            template = "vol_target"
        elif "buy and hold" in blob or "buy-and-hold" in blob:
            template = "buy_hold"
        fixed.append(
            {
                "slug": r["slug"],
                "title": r["title"],
                "isPaywalled": bool(r["isPaywalled"]),
                "annualisedReturn": r["annualisedReturn"],
                "sharpeRatio": r["sharpeRatio"],
                "equities": eqs,
                "algolib": has_algo,
                "template_hint": template,
                "code_chars": len(code),
            }
        )

print("fixed-equity strategies", len(fixed))
by_tmpl = {}
for f in fixed:
    by_tmpl.setdefault(f["template_hint"], []).append(f["slug"])
print({k: len(v) for k, v in sorted(by_tmpl.items(), key=lambda x: -len(x[1]))})

# show first 40
for f in fixed[:40]:
    print(f"{f['slug'][:40]:40} {f['template_hint']:16} {f['equities']} paywall={f['isPaywalled']}")

Path("backtest/results/fixed_equity_candidates.json").write_text(
    json.dumps(fixed, indent=2), encoding="utf-8"
)
print("candidates", len(fixed))
