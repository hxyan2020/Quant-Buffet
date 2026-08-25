"""Generate canvas + equity-only leaderboard for new_100 drafts review."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DRAFT = ROOT / "backtest" / "drafts" / "new_100"
LB = json.loads((DRAFT / "leaderboard.json").read_text(encoding="utf-8"))
SUMMARY = json.loads((DRAFT / "backtest_summary.json").read_text(encoding="utf-8"))
CATALOG = json.loads((DRAFT / "catalog.json").read_text(encoding="utf-8"))
PAPERS = json.loads((DRAFT / "papers_raw.json").read_text(encoding="utf-8"))

CANVAS = Path.home() / ".cursor" / "projects" / "c-Users-Hansel-Yan-Projects-quant-buffet" / "canvases" / "new-100-drafts.canvas.tsx"


def is_crypto(row: dict) -> bool:
    assets = row.get("assets") or []
    return any("BTC" in a or "ETH" in a for a in assets)


def fmt_pct(x, d=1):
    return f"{x*100:.{d}f}%" if x is not None else "—"


def fmt_n(x, d=2):
    return f"{x:.{d}f}" if x is not None else "—"


# Deduplicate identical (template, assets, metrics) clusters for display
seen_sig = set()
unique_lb = []
for r in LB:
    sig = (r["template"], tuple(r.get("assets") or []), round(r.get("sharpe") or 0, 4))
    if sig in seen_sig:
        continue
    seen_sig.add(sig)
    unique_lb.append(r)

equity_lb = [r for r in LB if not is_crypto(r)]
equity_unique = []
seen2 = set()
for r in equity_lb:
    sig = (r["template"], tuple(r.get("assets") or []), round(r.get("sharpe") or 0, 4))
    if sig in seen2:
        continue
    seen2.add(sig)
    equity_unique.append(r)

sources = Counter(p.get("source") for p in PAPERS["papers"])
years = Counter(str(p.get("year") or "?") for p in PAPERS["papers"])

# Load top 3 equity curves
curves = []
for r in equity_unique[:3]:
    slug = r["slug"]
    path = DRAFT / "equity_curves" / f"{slug}.json"
    if not path.exists():
        continue
    data = json.loads(path.read_text(encoding="utf-8"))
    eq = data.get("equity") or []
    bh = data.get("benchmark") or []
    # downsample further for canvas
    step = max(1, len(eq) // 60)
    eq_s = eq[::step]
    bh_s = bh[::step]
    if eq and eq_s[-1]["date"] != eq[-1]["date"]:
        eq_s.append(eq[-1])
    if bh and bh_s and bh[-1] and bh_s[-1]["date"] != bh[-1]["date"]:
        bh_s.append(bh[-1])
    # normalize to 100
    e0 = eq_s[0]["equity"] or 1
    b0 = (bh_s[0]["equity"] if bh_s else 1) or 1
    cats = []
    for i, pt in enumerate(eq_s):
        cats.append(pt["date"][:7] if i % 8 == 0 or i == len(eq_s) - 1 else "")
    curves.append(
        {
            "slug": slug,
            "title": r["title"],
            "cagr": r["cagr"],
            "sharpe": r["sharpe"],
            "max_drawdown": r["max_drawdown"],
            "categories": cats,
            "equity": [round(pt["equity"] / e0 * 100, 1) for pt in eq_s],
            "bench": [round((bh_s[min(i, len(bh_s)-1)]["equity"] / b0) * 100, 1) for i in range(len(eq_s))] if bh_s else [],
        }
    )

# Sample post snippets
sample_slugs = [r["slug"] for r in equity_unique[:5]]
samples = []
for slug in sample_slugs:
    post = json.loads((DRAFT / "posts" / f"{slug}.json").read_text(encoding="utf-8"))
    samples.append(
        {
            "slug": slug,
            "title": post["title"],
            "paper": post["paperTitle"][:80],
            "authors": (post["paperAuthors"] or "")[:60],
            "link": post["academicLink"],
            "template": post["template"],
            "assets": ", ".join(post["assets"]),
            "cagr": post["annualisedReturn"],
            "sharpe": post["sharpeRatio"],
            "maxdd": post["maxDrawdown"],
            "teaser": (post["teaser"] or "")[:160],
            "fidelity": post["fidelity"],
        }
    )

tmpl_rows = [[k, str(v)] for k, v in sorted(SUMMARY["by_template"].items(), key=lambda x: -x[1])]
top_all = [
    [
        str(r["rank"]),
        r["slug"][:42],
        r["template"],
        fmt_pct(r["cagr"]),
        fmt_n(r["sharpe"]),
        fmt_pct(r["max_drawdown"]),
    ]
    for r in unique_lb[:12]
]
top_eq = [
    [
        str(i),
        r["slug"][:42],
        r["template"],
        fmt_pct(r["cagr"]),
        fmt_n(r["sharpe"]),
        fmt_pct(r["max_drawdown"]),
        ", ".join((r.get("assets") or [])[:4]),
    ]
    for i, r in enumerate(equity_unique[:15], 1)
]

# serialize for JS
def j(x):
    return json.dumps(x, ensure_ascii=False)


canvas = f'''import {{
  Callout,
  Divider,
  H1,
  H2,
  H3,
  LineChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
}} from "cursor/canvas";

const TMPL_ROWS = {j(tmpl_rows)};
const TOP_UNIQUE = {j(top_all)};
const TOP_EQUITY = {j(top_eq)};
const SAMPLES = {j(samples)};
const CURVES = {j(curves)};
const SOURCES = {j([[k, str(v)] for k, v in sources.items()])};
const YEARS = {j([[k, str(v)] for k, v in sorted(years.items(), reverse=True)[:8]])};

export default function New100Drafts() {{
  return (
    <Stack gap={{20}} style={{{{ padding: 24, maxWidth: 1200 }}}}>
      <Stack gap={{6}}>
        <H1>New 100 strategy drafts — review only</H1>
        <Text tone="secondary">
          Scraped academic papers → Quant Buffet post JSON + in-house backtests. Not published to Prisma.
        </Text>
        <Row gap={{8}} style={{{{ flexWrap: "wrap" }}}}>
          <Pill tone="success">100/100 backtests OK</Pill>
          <Pill tone="warning">published=false</Pill>
          <Pill tone="info">OpenAlex + arXiv</Pill>
          <Pill tone="neutral">Drafts in backtest/drafts/new_100/</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="How to read these drafts">
        Each post maps a paper theme to a liquid ETF rule (SMA, dual momentum, rotation, vol-target, etc.).
        Crypto papers often share the same BTC/ETH abs-momentum proxy — use the equity-ex-crypto table for cleaner ranking.
        Fidelity labels mark theme proxies vs extracted tickers. Approve before any DB insert.
      </Callout>

      <Row gap={{12}} style={{{{ flexWrap: "wrap" }}}}>
        <Stat value="{SUMMARY['ok']}" label="Drafts + backtests" tone="success" />
        <Stat value="{fmt_pct(SUMMARY['median_cagr'])}" label="Median CAGR" tone="info" />
        <Stat value="{fmt_n(SUMMARY['median_sharpe'])}" label="Median Sharpe" />
        <Stat value="{len(unique_lb)}" label="Unique rule signatures" />
        <Stat value="{len(equity_unique)}" label="Non-crypto unique" />
      </Row>

      <Stack gap={{8}}>
        <H2>Paper sources</H2>
        <Table headers={{["Source API", "Count"]}} rows={{SOURCES}} />
        <Table headers={{["Year", "Count"]}} rows={{YEARS}} />
      </Stack>

      <Stack gap={{8}}>
        <H2>Template mix</H2>
        <Table headers={{["Template", "Count"]}} rows={{TMPL_ROWS}} />
      </Stack>

      <Divider />
      <H2>Top unique rules (deduped identical backtests)</H2>
      <Table
        headers={{["#", "Slug", "Template", "CAGR", "Sharpe", "MaxDD"]}}
        rows={{TOP_UNIQUE}}
      />

      <Divider />
      <H2>Top non-crypto unique (preferred review list)</H2>
      <Table
        headers={{["#", "Slug", "Template", "CAGR", "Sharpe", "MaxDD", "Assets"]}}
        rows={{TOP_EQUITY}}
      />

      <Divider />
      <H2>Equity curves — top 3 non-crypto unique</H2>
      {{CURVES.map((c) => (
        <Stack key={{c.slug}} gap={{8}}>
          <H3>{{c.title}}</H3>
          <Text tone="secondary" size="small">
            {{c.slug}} · CAGR {{(c.cagr * 100).toFixed(1)}}% · Sharpe {{c.sharpe.toFixed(2)}} · MaxDD{{" "}}
            {{(c.max_drawdown * 100).toFixed(1)}}% · indexed to 100 · source: in-house engine
          </Text>
          <LineChart
            height={{200}}
            categories={{c.categories}}
            series={{[
              {{ name: "Strategy", data: c.equity, tone: "info" }},
              {{ name: "SPY buy-hold", data: c.bench, tone: "neutral" }},
            ]}}
            beginAtZero={{false}}
          />
        </Stack>
      ))}}

      <Divider />
      <H2>Sample draft posts (first 5 non-crypto unique)</H2>
      {{SAMPLES.map((s) => (
        <Stack key={{s.slug}} gap={{4}}>
          <H3>{{s.title}}</H3>
          <Text size="small" tone="secondary">
            Paper: {{s.paper}} · {{s.authors}}
          </Text>
          <Text size="small">
            {{s.template}} · {{s.assets}} · {{s.cagr}} / Sharpe {{s.sharpe}} / DD {{s.maxdd}} · fidelity:{{" "}}
            {{s.fidelity}}
          </Text>
          <Text>{{s.teaser}}</Text>
          <Text size="small" tone="secondary">
            {{s.link}} · file: posts/{{s.slug}}.json
          </Text>
        </Stack>
      ))}}

      <Callout tone="info" title="Next step">
        Review posts under backtest/drafts/new_100/posts/. When ready, ask to publish selected slugs
        (DB insert with published=true or staged false).
      </Callout>
    </Stack>
  );
}}
'''

CANVAS.write_text(canvas, encoding="utf-8")
print(f"Wrote {CANVAS}")
print(f"unique={len(unique_lb)} equity_unique={len(equity_unique)}")
print("Top equity unique:")
for i, r in enumerate(equity_unique[:10], 1):
    print(f"  {i}. {fmt_n(r['sharpe'])} {fmt_pct(r['cagr'])} {r['slug'][:50]}")
