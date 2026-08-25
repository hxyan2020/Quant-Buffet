"""Inventory all published EN strategies for full-catalog expansion."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

con = sqlite3.connect("prisma/dev.db")
con.row_factory = sqlite3.Row

for locale in ("en", "zh"):
    rows = con.execute(
        "SELECT COUNT(*) c FROM Strategy WHERE locale=? AND published=1", (locale,)
    ).fetchone()["c"]
    code = con.execute(
        """
        SELECT COUNT(*) c FROM Strategy
        WHERE locale=? AND published=1 AND hasPythonCode=1 AND length(pythonCodeHtml)>50
        """,
        (locale,),
    ).fetchone()["c"]
    print(f"{locale}: published={rows} with_code={code} no_code={rows-code}")

rows = con.execute(
    """
    SELECT slug, title, hasPythonCode, length(pythonCodeHtml) AS n,
           isPaywalled, assetClass, region, market, frequency
    FROM Strategy WHERE locale='en' AND published=1
    ORDER BY slug
    """
).fetchall()

ascii_ok = [r for r in rows if re.fullmatch(r"[a-z0-9\-]+", r["slug"] or "")]
non_ascii = [r for r in rows if not re.fullmatch(r"[a-z0-9\-]+", r["slug"] or "")]
no_code = [r for r in ascii_ok if not r["hasPythonCode"] or (r["n"] or 0) < 50]
with_code = [r for r in ascii_ok if r["hasPythonCode"] and (r["n"] or 0) >= 50]

print("en ascii", len(ascii_ok), "nonascii", len(non_ascii))
print("ascii with_code", len(with_code), "ascii no_code", len(no_code))
print("assetClass top:", end=" ")
from collections import Counter

print(Counter((r["assetClass"] or "?") for r in ascii_ok).most_common(15))
print("sample no_code:")
for r in no_code[:20]:
    print(f"  {r['slug'][:55]:55} {(r['title'] or '')[:55]}")

Path("backtest/results/full_inventory_meta.json").write_text(
    json.dumps(
        {
            "ascii_total": len(ascii_ok),
            "with_code": len(with_code),
            "no_code": len(no_code),
            "non_ascii": len(non_ascii),
            "no_code_slugs": [r["slug"] for r in no_code],
            "all_ascii_slugs": [r["slug"] for r in ascii_ok],
        },
        indent=2,
    ),
    encoding="utf-8",
)
print("wrote backtest/results/full_inventory_meta.json")
