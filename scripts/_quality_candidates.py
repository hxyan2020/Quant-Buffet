"""Extract high-quality ETF strategy candidates with a ticker whitelist."""
from __future__ import annotations

import json
import re
import sqlite3
from html import unescape
from pathlib import Path

DB = Path("prisma/dev.db")

# Liquid ETFs / majors we can actually backtest via yfinance
WHITELIST = {
    "SPY", "QQQ", "IWM", "DIA", "VOO", "VTI", "IWB", "IJH", "IJR",
    "EFA", "EEM", "VEA", "VWO", "VGK", "EWJ", "EWZ", "FXI", "EWU", "EWG",
    "EWQ", "EWI", "EWP", "EWN", "EWK", "EWD", "EWL", "EWC", "EWA", "EWH",
    "EWT", "EWY", "EWS", "EIDO", "THD", "EPHE", "ECH", "EPOL", "EZA",
    "ARGT", "TUR", "ASHR", "ACWX", "ACWI", "URTH",
    "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLC", "XLRE",
    "VNQ", "IYR", "RWX",
    "TLT", "IEF", "IEI", "SHY", "SHV", "BIL", "BND", "AGG", "LQD", "HYG", "TIP", "MBB",
    "GLD", "SLV", "DBC", "GSG", "DBA", "USO", "UNG",
    "VIXY", "SVXY",
    "MDY", "OEF", "RSP",
}

SKIP_SLUG = {"__trashed"}


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<[^>]+>", "\n", t)
    return t


def extract_tickers(text: str) -> list[str]:
    found = []
    for m in re.findall(r"[\"']([A-Z]{2,5})[\"']", text):
        if m in WHITELIST and m not in found:
            found.append(m)
    for m in re.findall(r"\b([A-Z]{2,5})\b", text):
        if m in WHITELIST and m not in found:
            found.append(m)
    return found


con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = con.execute(
    """
    SELECT slug, title, teaser, summary, annualisedReturn, sharpeRatio, maxDrawdown,
           pythonCodeHtml, contentHtml, isPaywalled
    FROM Strategy
    WHERE locale='en' AND published=1 AND hasPythonCode=1 AND isPaywalled=0
    ORDER BY slug
    """
).fetchall()

cands = []
for r in rows:
    if r["slug"] in SKIP_SLUG:
        continue
    code = strip_html(r["pythonCodeHtml"])
    content = strip_html(r["contentHtml"] or "")[:8000]
    teaser = r["teaser"] or ""
    title = r["title"] or ""
    blob = "\n".join([title, teaser, content, code])

    # Skip clearly non-ETF / alt-data
    low = blob.lower()
    if any(
        k in low
        for k in (
            "option chain",
            "add_option",
            "addoption",
            "lunar",
            "box office",
            "employee sentiment",
            "cryptocurrenc",
            "bitcoin",
            "intraday momentum",
            "minute resolution",
            "futures contract",
            "cointegration",
            "pairs trading",
        )
    ):
        continue

    tickers = extract_tickers(blob)
    # Prefer code equities first
    code_eq = []
    for pat in [
        r"add_equity\(\s*[\"']([A-Z]{2,5})[\"']",
        r"AddEquity\(\s*[\"']([A-Z]{2,5})[\"']",
    ]:
        for m in re.findall(pat, code, flags=re.I):
            u = m.upper()
            if u in WHITELIST and u not in code_eq:
                code_eq.append(u)
    assets = code_eq if len(code_eq) >= 2 else tickers

    if len(assets) < 2:
        # allow single-asset absolute momentum / SMA timing on SPY/QQQ/etc.
        if len(assets) == 1 and assets[0] in {"SPY", "QQQ", "IWM", "DIA", "VTI"}:
            pass
        else:
            continue

    # Classify
    template = None
    if re.search(r"dual.?momentum|absolute.?momentum", low):
        template = "dual_momentum"
        if "BIL" not in assets and "SHY" not in assets:
            assets = assets + ["BIL"]
    elif re.search(r"risk parity", low):
        template = "risk_parity"
    elif re.search(r"mean.?revert|bollinger", low):
        template = "mean_reversion"
    elif re.search(r"golden.?cross|dual moving|50.?200", low):
        template = "dual_ma"
    elif re.search(r"trend.?follow|sma|moving average filter|price above", low):
        template = "sma_trend"
    elif re.search(r"sector.?rotat|asset.?alloc|rotation", low):
        template = "momentum_rotation"
    elif re.search(r"volatility.?target|managed volatility", low):
        template = "vol_target"
    elif re.search(r"momentum", low) and len(assets) >= 3:
        template = "momentum_rotation"
    elif re.search(r"momentum", low) and len(assets) <= 2:
        template = "abs_momentum"
    elif len(assets) >= 3:
        template = "equal_weight"
    elif len(assets) == 1:
        template = "sma_trend"
    else:
        template = "equal_weight"

    # Skip stock-cross-section titles that only proxy to SPY (misleading)
    if len(assets) <= 2 and assets[0] == "SPY" and re.search(
        r"long-short|long short|top \d+%|accruals|earnings|industry momentum|cross-section|stock splits",
        low,
    ):
        continue

    cands.append(
        {
            "slug": r["slug"],
            "title": title,
            "site_annualisedReturn": r["annualisedReturn"],
            "site_sharpeRatio": r["sharpeRatio"],
            "site_maxDrawdown": r["maxDrawdown"],
            "template": template,
            "assets": assets[:12],
            "n_assets": len(assets),
        }
    )

# Prefer multi-asset
cands.sort(key=lambda x: (-x["n_assets"], x["slug"]))
print("candidates", len(cands))
from collections import Counter
print(Counter(c["template"] for c in cands))
print("multi>=3", sum(1 for c in cands if c["n_assets"] >= 3))
for c in cands[:30]:
    print(f"{c['n_assets']:2} {c['template']:18} {c['slug'][:45]:45} {c['assets']}")

Path("backtest/results/quality_candidates.json").write_text(
    json.dumps(cands, indent=2), encoding="utf-8"
)
