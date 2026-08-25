"""Sample strategy content structure from DB."""
from __future__ import annotations

import json
import re
import sqlite3
from html import unescape
from pathlib import Path

DB = Path("prisma/dev.db")


def strip_html(h: str) -> str:
    t = unescape(h or "")
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</h([1-6])>", r"\n", t, flags=re.I)
    t = re.sub(r"<h([1-6])[^>]*>", r"\n## ", t, flags=re.I)
    t = re.sub(r"<li[^>]*>", "\n- ", t, flags=re.I)
    t = re.sub(r"<p[^>]*>", "\n", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row

# Prefer strategies with rich paper metadata
rows = con.execute(
    """
    SELECT slug, title, teaser, summary, economicRationale, academicLink,
           paperTitle, paperAuthors, paperInstitute, assetClass, region, market,
           frequency, annualisedReturn, sharpeRatio, maxDrawdown, volatility,
           beta, sortinoRatio, winRate, hasPythonCode,
           length(contentHtml) AS content_len,
           length(pythonCodeHtml) AS code_len,
           substr(contentHtml, 1, 2500) AS content_head,
           substr(economicRationale, 1, 800) AS rationale_head
    FROM Strategy
    WHERE locale='en' AND published=1
      AND academicLink IS NOT NULL AND academicLink != ''
      AND paperTitle IS NOT NULL AND paperTitle != ''
    ORDER BY length(contentHtml) DESC
    LIMIT 5
    """
).fetchall()

out = []
for r in rows:
    out.append(
        {
            "slug": r["slug"],
            "title": r["title"],
            "paperTitle": r["paperTitle"],
            "paperAuthors": r["paperAuthors"],
            "paperInstitute": r["paperInstitute"],
            "academicLink": r["academicLink"],
            "assetClass": r["assetClass"],
            "region": r["region"],
            "market": r["market"],
            "frequency": r["frequency"],
            "metrics": {
                "annualisedReturn": r["annualisedReturn"],
                "sharpeRatio": r["sharpeRatio"],
                "maxDrawdown": r["maxDrawdown"],
                "volatility": r["volatility"],
                "beta": r["beta"],
                "sortinoRatio": r["sortinoRatio"],
                "winRate": r["winRate"],
            },
            "teaser": r["teaser"],
            "summary": (r["summary"] or "")[:500],
            "content_len": r["content_len"],
            "code_len": r["code_len"],
            "content_text_sample": strip_html(r["content_head"])[:1500],
            "rationale_sample": r["rationale_head"],
        }
    )

Path("backtest/results/strategy_content_samples.json").write_text(
    json.dumps(out, indent=2), encoding="utf-8"
)
for o in out:
    print("=" * 60)
    print(o["slug"])
    print("paper:", o["paperTitle"])
    print("link:", o["academicLink"])
    print("asset/region/freq:", o["assetClass"], o["region"], o["frequency"])
    print("content_len", o["content_len"], "code_len", o["code_len"])
    print("teaser:", (o["teaser"] or "")[:200])
    print("content sample:\n", o["content_text_sample"][:700])
