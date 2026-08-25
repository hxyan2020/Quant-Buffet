"""Analyze paper sources / academic links across Quant Buffet EN strategies."""
from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse

DB = Path("prisma/dev.db")
OUT = Path("backtest/results/paper_source_patterns.json")


def host_of(link: str) -> str:
    try:
        host = (urlparse(link.strip()).netloc or "").lower()
    except Exception:
        return "invalid"
    if not host:
        return "invalid"
    return host[4:] if host.startswith("www.") else host


def kind_of(link: str) -> str:
    low = (link or "").lower()
    if "ssrn.com" in low:
        return "ssrn"
    if "arxiv.org" in low:
        return "arxiv"
    if "doi.org" in low or "/doi/" in low:
        return "doi"
    if any(
        x in low
        for x in (
            "jstor",
            "wiley",
            "springer",
            "sciencedirect",
            "tandfonline",
            "oxfordacademic",
            "nature.com",
            "aeaweb",
            "cambridge",
            "ieee",
            "acm.org",
            "informs",
            "sagepub",
            "oup.com",
            "elsevier",
            "emerald",
            "mdpi",
            "hindawi",
            "nber.org",
        )
    ):
        return "journal_publisher"
    if "quantpedia" in low:
        return "quantpedia"
    if "github.com" in low:
        return "github"
    if "researchgate" in low:
        return "researchgate"
    if "semanticscholar" in low:
        return "semanticscholar"
    return "other"


con = sqlite3.connect(DB)
con.row_factory = sqlite3.Row
rows = con.execute(
    """
    SELECT slug, title, teaser, academicLink, paperTitle, paperAuthors,
           paperInstitute, assetClass, region, market, frequency, hasPythonCode
    FROM Strategy
    WHERE published = 1 AND locale = 'en'
    """
).fetchall()

link_kinds = Counter()
domains = Counter()
institutes = Counter()
asset_classes = Counter()
regions = Counter()
frequencies = Counter()
title_kw = Counter()
link_examples = defaultdict(list)
has_link = 0
has_paper_title = 0

kw_list = [
    "momentum",
    "reversal",
    "value",
    "trend",
    "volatility",
    "carry",
    "seasonality",
    "pairs",
    "mean reversion",
    "factor",
    "timing",
    "allocation",
    "risk",
    "option",
    "futures",
    "crypto",
    "bond",
    "sector",
    "anomaly",
    "machine learning",
    "predict",
]

for r in rows:
    asset_classes[(r["assetClass"] or "?").strip() or "?"] += 1
    regions[(r["region"] or "?").strip() or "?"] += 1
    frequencies[(r["frequency"] or "?").strip() or "?"] += 1
    institutes[(r["paperInstitute"] or "").strip() or "N/A"] += 1

    if (r["paperTitle"] or "").strip():
        has_paper_title += 1

    t = ((r["title"] or "") + " " + (r["teaser"] or "")).lower()
    for k in kw_list:
        if k in t:
            title_kw[k] += 1

    link = (r["academicLink"] or "").strip()
    if not link:
        link_kinds["missing"] += 1
        continue
    has_link += 1
    kind = kind_of(link)
    link_kinds[kind] += 1
    domains[host_of(link)] += 1
    if len(link_examples[kind]) < 8:
        link_examples[kind].append(
            {
                "slug": r["slug"],
                "link": link,
                "paper": (r["paperTitle"] or "")[:160],
            }
        )

payload = {
    "total_en": len(rows),
    "has_academic_link": has_link,
    "has_paper_title": has_paper_title,
    "pct_with_link": round(100.0 * has_link / max(len(rows), 1), 1),
    "pct_with_paper_title": round(100.0 * has_paper_title / max(len(rows), 1), 1),
    "link_kinds": dict(link_kinds.most_common()),
    "top_domains": domains.most_common(30),
    "top_institutes": institutes.most_common(25),
    "title_keywords": title_kw.most_common(),
    "link_examples": dict(link_examples),
    "asset_classes": asset_classes.most_common(25),
    "regions": regions.most_common(20),
    "frequencies": frequencies.most_common(15),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(
    json.dumps(
        {
            k: payload[k]
            for k in (
                "total_en",
                "has_academic_link",
                "has_paper_title",
                "pct_with_link",
                "link_kinds",
            )
        },
        indent=2,
    )
)
print("top_domains", payload["top_domains"][:15])
print("institutes", payload["top_institutes"][:12])
print("keywords", payload["title_keywords"][:15])
print("asset_classes", payload["asset_classes"][:10])
print("regions", payload["regions"][:10])
print("frequencies", payload["frequencies"][:10])
