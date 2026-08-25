"""Summarize scrape provenance for the new 100 papers."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

raw = json.loads(Path("backtest/drafts/new_100/papers_raw.json").read_text(encoding="utf-8"))
papers = raw["papers"]
print("count", len(papers))
print("sources", dict(Counter(p.get("source") for p in papers)))
print("years", dict(sorted(Counter(p.get("year") for p in papers).items())))
print("--- queries ---")
for q, n in Counter(p.get("_query") for p in papers).most_common():
    print(f"{n:3d}  {q}")
print("--- sample ---")
for p in papers[:8]:
    print(p.get("source"), p.get("year"), p.get("_query"), "|", (p.get("title") or "")[:70], "|", p.get("url"))
