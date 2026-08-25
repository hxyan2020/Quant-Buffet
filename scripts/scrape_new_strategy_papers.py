"""
Supplement paper discovery to reach 100 using OpenAlex + expanded arXiv.
Official APIs only. Dedup against existing Quant Buffet papers + prior scrape.
"""
from __future__ import annotations

import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEDUP = ROOT / "backtest" / "results" / "existing_papers_dedup.json"
PRIOR = ROOT / "backtest" / "drafts" / "new_100" / "papers_raw.json"
OUT = ROOT / "backtest" / "drafts" / "new_100" / "papers_raw.json"

UA = "QuantBuffetResearchBot/1.0 (mailto:research@quantbuffet.com)"


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s\-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return re.sub(r"-{2,}", "-", s)[:80]


def http_get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def http_get_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode("utf-8")


def load_dedup():
    raw = json.loads(DEDUP.read_text(encoding="utf-8"))
    return {
        "titles": set(raw["titles"]),
        "slugs": set(raw["slugs"]),
        "ssrn_ids": set(raw["ssrn_ids"]),
        "arxiv_ids": set(raw["arxiv_ids"]),
        "dois": set(raw["dois"]),
        "links": set(raw["links"]),
    }


def is_dup(title: str, url: str, doi: str | None, arxiv: str | None, dedup: dict, seen_titles: set) -> bool:
    t = title.lower().strip()
    if t in dedup["titles"] or t in seen_titles:
        return True
    if url and url.lower() in dedup["links"]:
        return True
    if doi and doi.lower() in dedup["dois"]:
        return True
    if arxiv and arxiv in dedup["arxiv_ids"]:
        return True
    m = re.search(r"abstract[_/=](\d+)", (url or "").lower())
    if m and m.group(1) in dedup["ssrn_ids"]:
        return True
    return False


def score(title: str, abstract: str, year: int | None, cites: int) -> float:
    blob = f"{title} {abstract}".lower()
    s = 0.0
    for kw, w in [
        ("momentum", 3), ("trend following", 3), ("trend-following", 3),
        ("moving average", 2.5), ("asset allocation", 2.5), ("sector rotation", 2.5),
        ("mean reversion", 2), ("reversal", 1.5), ("carry", 2), ("risk parity", 2),
        ("volatility", 1.5), ("etf", 3), ("portfolio", 1.5), ("trading strategy", 3),
        ("market timing", 2.5), ("dual momentum", 4), ("factor", 1), ("anomaly", 1),
        ("equity", 1), ("bond", 1), ("commodity", 1), ("strategy", 2),
    ]:
        if kw in blob:
            s += w
    for kw, w in [
        ("literature review", -5), ("survey of", -4), ("high-frequency", -3),
        ("order book", -3), ("option pricing formula", -2), ("private equity", -2),
    ]:
        if kw in blob:
            s += w
    s += min(5.0, cites / 50.0)
    if year and year >= 2018:
        s += 1.5
    if year and year >= 2022:
        s += 1.0
    if abstract:
        s += 1.0
    return s


def search_openalex(query: str, per_page: int = 25) -> list[dict]:
    params = urllib.parse.urlencode(
        {
            "search": query,
            "per_page": str(per_page),
            "filter": "from_publication_date:2015-01-01,type:article|preprint",
            "sort": "relevance_score:desc",
            "mailto": "research@quantbuffet.com",
        }
    )
    url = f"https://api.openalex.org/works?{params}"
    try:
        data = http_get_json(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  OpenAlex fail: {exc}")
        return []
    papers = []
    for w in data.get("results") or []:
        title = (w.get("display_name") or "").strip()
        abstract_inv = w.get("abstract_inverted_index") or {}
        # Reconstruct abstract
        abstract = ""
        if abstract_inv:
            positions = []
            for word, idxs in abstract_inv.items():
                for i in idxs:
                    positions.append((i, word))
            abstract = " ".join(word for _, word in sorted(positions))
        year = w.get("publication_year")
        cites = w.get("cited_by_count") or 0
        doi = None
        if w.get("doi"):
            doi = w["doi"].replace("https://doi.org/", "")
        # best OA / landing URL
        primary = (w.get("primary_location") or {})
        landing = (primary.get("landing_page_url") or w.get("id") or "")
        oa = ((w.get("open_access") or {}).get("oa_url")) or (
            (primary.get("pdf_url")) if primary else None
        )
        authors = []
        for a in w.get("authorships") or []:
            name = ((a.get("author") or {}).get("display_name") or "").strip()
            if name:
                authors.append({"name": name})
        institutions = []
        for a in w.get("authorships") or []:
            for inst in a.get("institutions") or []:
                dn = (inst.get("display_name") or "").strip()
                if dn and dn not in institutions:
                    institutions.append(dn)
        papers.append(
            {
                "paperId": w.get("id"),
                "title": title,
                "abstract": abstract,
                "year": year,
                "venue": ((primary.get("source") or {}).get("display_name") if primary else None),
                "citationCount": cites,
                "authors": authors,
                "institutions": institutions,
                "externalIds": {"DOI": doi} if doi else {},
                "url": landing,
                "openAccessPdf": {"url": oa} if oa else {},
                "source": "openalex",
            }
        )
    return papers


def search_arxiv(query: str, max_results: int = 30) -> list[dict]:
    q = urllib.parse.quote(query)
    url = (
        "http://export.arxiv.org/api/query?"
        f"search_query={q}&start=0&max_results={max_results}&sortBy=relevance&sortOrder=descending"
    )
    try:
        xml = http_get_text(url)
    except Exception as exc:  # noqa: BLE001
        print(f"  arXiv fail: {exc}")
        return []
    ns = {"a": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    papers = []
    for entry in root.findall("a:entry", ns):
        title = re.sub(r"\s+", " ", (entry.findtext("a:title", default="", namespaces=ns) or "").strip())
        summary = re.sub(r"\s+", " ", (entry.findtext("a:summary", default="", namespaces=ns) or "").strip())
        published = entry.findtext("a:published", default="", namespaces=ns) or ""
        year = int(published[:4]) if published[:4].isdigit() else None
        arxiv_id = (entry.findtext("a:id", default="", namespaces=ns) or "").split("/abs/")[-1]
        authors = [
            {"name": (a.findtext("a:name", default="", namespaces=ns) or "").strip()}
            for a in entry.findall("a:author", ns)
        ]
        papers.append(
            {
                "paperId": f"arxiv:{arxiv_id}",
                "title": title,
                "abstract": summary,
                "year": year,
                "venue": "arXiv",
                "citationCount": 0,
                "authors": authors,
                "institutions": [],
                "externalIds": {"ArXiv": arxiv_id},
                "url": f"https://arxiv.org/abs/{arxiv_id}",
                "openAccessPdf": {"url": f"https://arxiv.org/pdf/{arxiv_id}.pdf"},
                "source": "arxiv",
            }
        )
    return papers


def main() -> None:
    dedup = load_dedup()
    prior = []
    if PRIOR.exists():
        prior = (json.loads(PRIOR.read_text(encoding="utf-8")).get("papers") or [])

    seen_titles = set(dedup["titles"])
    seen_ids = set()
    candidates = []

    for p in prior:
        title = (p.get("title") or "").strip()
        pid = p.get("paperId")
        if not title or not pid:
            continue
        if is_dup(title, p.get("url") or "", (p.get("externalIds") or {}).get("DOI"), (p.get("externalIds") or {}).get("ArXiv"), dedup, seen_titles):
            continue
        if pid in seen_ids:
            continue
        p["_score"] = p.get("_score") or score(title, p.get("abstract") or "", p.get("year"), p.get("citationCount") or 0)
        p["_slug"] = p.get("_slug") or slugify(title)
        candidates.append(p)
        seen_ids.add(pid)
        seen_titles.add(title.lower())

    openalex_queries = [
        "cross-sectional momentum trading strategy equities",
        "time-series momentum trend following portfolio",
        "dual momentum Gary Antonacci asset allocation",
        "sector rotation momentum ETF strategy",
        "volatility-managed portfolio equity factors",
        "mean reversion short-term reversal stocks",
        "currency carry trade crash risk",
        "risk parity multi-asset allocation",
        "commodity futures trend following",
        "bond risk premium momentum timing",
        "defensive momentum asset allocation",
        "moving average market timing equity",
        "low volatility anomaly investing",
        "factor momentum industry portfolios",
        "quality minus junk factor strategy",
        "ETF relative strength rotation",
        "tail hedging equity put strategy",
        "cryptocurrency momentum effect",
        "value and momentum everywhere",
        "adaptive asset allocation ETFs",
    ]

    print("=== OpenAlex ===")
    for q in openalex_queries:
        print("OA:", q)
        for p in search_openalex(q, per_page=25):
            title = (p.get("title") or "").strip()
            pid = p.get("paperId")
            if not title or not pid or pid in seen_ids:
                continue
            doi = (p.get("externalIds") or {}).get("DOI")
            if is_dup(title, p.get("url") or "", doi, None, dedup, seen_titles):
                continue
            blob = f"{title} {p.get('abstract') or ''}".lower()
            if not any(k in blob for k in ("strategy", "portfolio", "trading", "momentum", "anomaly", "factor", "allocation", "timing", "return")):
                continue
            p["_score"] = score(title, p.get("abstract") or "", p.get("year"), p.get("citationCount") or 0)
            p["_query"] = q
            p["_slug"] = slugify(title)
            if p["_slug"] in dedup["slugs"]:
                continue
            candidates.append(p)
            seen_ids.add(pid)
            seen_titles.add(title.lower())
        time.sleep(0.3)

    arxiv_queries = [
        'all:"trend following" AND (cat:q-fin.PM OR cat:q-fin.TR)',
        'all:"dual momentum" AND cat:q-fin.PM',
        'all:"sector rotation" AND (cat:q-fin.PM OR cat:q-fin.TR)',
        'all:"time series momentum" AND cat:q-fin.PM',
        'all:"volatility managed" AND cat:q-fin.PM',
        'all:"asset allocation" AND momentum AND cat:q-fin.PM',
        'all:"mean reversion" AND (portfolio OR strategy) AND (cat:q-fin.PM OR cat:q-fin.TR)',
        'all:"carry trade" AND cat:q-fin.PM',
        'all:"risk parity" AND cat:q-fin.PM',
        'all:"market timing" AND "moving average" AND cat:q-fin.PM',
        'all:"low volatility" AND anomaly AND cat:q-fin.PM',
        'all:"factor momentum" AND cat:q-fin.PM',
        'all:"ETF" AND momentum AND cat:q-fin.PM',
        'all:"commodity" AND "trend following" AND cat:q-fin.PM',
        'ti:"momentum" AND ti:"strategy" AND cat:q-fin.PM',
    ]
    print("=== arXiv expanded ===")
    for q in arxiv_queries:
        print("arXiv:", q)
        for p in search_arxiv(q, max_results=30):
            title = (p.get("title") or "").strip()
            pid = p.get("paperId")
            arxiv = (p.get("externalIds") or {}).get("ArXiv")
            if not title or not pid or pid in seen_ids:
                continue
            if is_dup(title, p.get("url") or "", None, arxiv, dedup, seen_titles):
                continue
            p["_score"] = score(title, p.get("abstract") or "", p.get("year"), 0) + 0.5
            p["_query"] = q
            p["_slug"] = slugify(title)
            if p["_slug"] in dedup["slugs"]:
                continue
            candidates.append(p)
            seen_ids.add(pid)
            seen_titles.add(title.lower())
        time.sleep(3.0)

    candidates.sort(key=lambda p: p.get("_score", 0), reverse=True)
    selected = []
    used_slugs = set(dedup["slugs"])
    for p in candidates:
        slug = p.get("_slug") or slugify(p.get("title") or "paper")
        base = slug
        n = 2
        while slug in used_slugs:
            slug = f"{base}-{n}"
            n += 1
        p["_slug"] = slug
        used_slugs.add(slug)
        selected.append(p)
        if len(selected) >= 100:
            break

    OUT.write_text(json.dumps({"count": len(selected), "papers": selected}, indent=2), encoding="utf-8")
    print(f"candidates={len(candidates)} selected={len(selected)} → {OUT}")
    for p in selected[:12]:
        print(f"  {p.get('_score',0):.1f} | {p.get('year')} | {(p.get('title') or '')[:75]}")


if __name__ == "__main__":
    main()
