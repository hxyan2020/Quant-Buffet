"""Extract existing paper titles/links for deduplication."""
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import urlparse, parse_qs

DB = Path("prisma/dev.db")
OUT = Path("backtest/results/existing_papers_dedup.json")

con = sqlite3.connect(DB)
rows = con.execute(
    """
    SELECT slug, locale, title, paperTitle, academicLink
    FROM Strategy WHERE published=1
    """
).fetchall()

titles = set()
slugs = set()
ssrn_ids = set()
arxiv_ids = set()
dois = set()
links = set()

for slug, locale, title, paper_title, link in rows:
    slugs.add((slug or "").lower().strip())
    if title:
        titles.add(title.lower().strip())
    if paper_title:
        titles.add(paper_title.lower().strip())
    link = (link or "").strip()
    if not link:
        continue
    links.add(link.lower())
    low = link.lower()
    m = re.search(r"abstract_id=(\d+)", low)
    if m:
        ssrn_ids.add(m.group(1))
    m = re.search(r"ssrn\.com/abstract=(\d+)", low)
    if m:
        ssrn_ids.add(m.group(1))
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]+\.[0-9]+)", low)
    if m:
        arxiv_ids.add(m.group(1))
    m = re.search(r"doi\.org/(10\.[^\s/?#]+)", low)
    if m:
        dois.add(m.group(1).lower())
    m = re.search(r"10\.\d{4,9}/[^\s/?#]+", low)
    if m:
        dois.add(m.group(0).lower())

payload = {
    "n_rows": len(rows),
    "n_titles": len(titles),
    "n_slugs": len(slugs),
    "n_ssrn_ids": len(ssrn_ids),
    "n_arxiv_ids": len(arxiv_ids),
    "n_dois": len(dois),
    "n_links": len(links),
    "titles": sorted(titles),
    "slugs": sorted(slugs),
    "ssrn_ids": sorted(ssrn_ids),
    "arxiv_ids": sorted(arxiv_ids),
    "dois": sorted(dois),
    "links": sorted(links),
}
OUT.parent.mkdir(parents=True, exist_ok=True)
# Don't dump huge lists to stdout
slim = {k: payload[k] for k in payload if not isinstance(payload[k], list)}
OUT.write_text(json.dumps(payload), encoding="utf-8")
print(json.dumps(slim, indent=2))
