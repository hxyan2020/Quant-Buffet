# Scrape strategy for new Quant Buffet papers

## Why this design

Existing library papers are mostly SSRN HTML links (~67% have academic links; SSRN dominates).
HTML scraping of SSRN is brittle (CAPTCHA, layout churn). Prefer **official scholarly APIs**.

## Pipeline

1. **Dedup baseline** — load titles, slugs, SSRN IDs, DOIs, arXiv IDs, links from the live DB
   (`backtest/results/existing_papers_dedup.json`).
2. **Query banks** aligned to Quant Buffet themes:
   - momentum / dual momentum / sector rotation / time-series momentum
   - volatility-managed / low vol / factor momentum
   - mean reversion / carry / risk parity / trend following / ETF allocation
3. **Sources (APIs only)**
   - **OpenAlex** — works, DOI + OA PDF links, institution metadata
   - **arXiv** (`q-fin.PM`, `q-fin.TR`) — reliable XML API
   - Semantic Scholar — optional; hit rate limits (429) in practice
4. **Score** for implementability (ETF / portfolio / strategy keywords; penalize HFT / order-book / pure surveys).
5. **Select top 100** novel papers → `papers_raw.json`.
6. **Classify** → in-house template + liquid ETF book.
7. **Draft posts** (sections I–V) + backtest → `backtest/drafts/new_100/` with `published=false`.

## Commands

```text
python scripts/scrape_new_strategy_papers.py
python scripts/generate_new_100_drafts.py
python scripts/_gen_new_100_canvas.py
```

## Do not publish until approved

No Prisma inserts. Review canvas + `posts/*.json` first.
