"""Build canvas payload + TSX from batch_100_summary.json."""
from __future__ import annotations

import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "backtest" / "results" / "batch_100_summary.json"
EQUITY = ROOT / "backtest" / "results" / "equity_curves"
PAYLOAD = ROOT / "backtest" / "results" / "canvas_100_payload.json"
CANVAS = Path.home() / ".cursor" / "projects" / "c-Users-Hansel-Yan-Projects-quant-buffet" / "canvases" / "inhouse-backtest-100.canvas.tsx"


def is_ascii_slug(slug: str) -> bool:
    return bool(re.fullmatch(r"[a-z0-9\-]+", slug or ""))


def load_curve(name: str) -> dict:
    p = EQUITY / name
    if not p.exists():
        return {"equity": [], "benchmark": []}
    return json.loads(p.read_text(encoding="utf-8"))


def downsample_cats(eq: list[dict], n: int = 48) -> tuple[list[str], list[float], list[float]]:
    if not eq:
        return [], [], []
    step = max(1, len(eq) // n)
    pts = eq[::step]
    if pts[-1] is not eq[-1]:
        pts = pts + [eq[-1]]
    cats = []
    for i, p in enumerate(pts):
        cats.append(p["date"][:7] if i % 4 == 0 or i == len(pts) - 1 else "")
    return cats, [round(p["equity"] / 1000, 1) for p in pts], cats


def main() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    board = summary["leaderboard"]

    # Prefer ASCII slugs; drop Chinese duplicates of same title/template/metrics
    seen_keys = set()
    unique = []
    for r in board:
        key = (
            round(r["cagr"], 4),
            round(r["sharpe"], 4),
            round(r["max_drawdown"], 4),
            r["template"],
            tuple(r.get("assets") or [])[:6],
        )
        if key in seen_keys and not is_ascii_slug(r["slug"]):
            continue
        if not is_ascii_slug(r["slug"]) and any(
            is_ascii_slug(x["slug"])
            and round(x["cagr"], 4) == key[0]
            and round(x["sharpe"], 4) == key[1]
            for x in board
        ):
            continue
        seen_keys.add(key)
        unique.append(r)

    # Keep top unique ranking
    unique.sort(key=lambda r: r["sharpe"], reverse=True)
    for i, r in enumerate(unique, 1):
        r["rank"] = i

    ok = [r for r in summary["results"] if r.get("status") == "ok"]
    sharpes = [r["metrics"]["sharpe"] for r in ok]
    cagrs = [r["metrics"]["cagr"] for r in ok]
    dds = [r["metrics"]["max_drawdown"] for r in ok]

    def avg(xs):
        return sum(xs) / len(xs) if xs else 0.0

    top = unique[:15]
    bottom = list(reversed(unique[-5:]))

    # Equity curves for top 3
    top_curves = []
    for r in unique[:3]:
        # find curve file
        full = next((x for x in ok if x["slug"] == r["slug"]), None)
        if not full:
            continue
        curve = load_curve(full["curve_file"])
        cats, eq_k, _ = downsample_cats(curve.get("equity") or [])
        _, bh_k, _ = downsample_cats(curve.get("benchmark") or [])
        # align lengths
        n = min(len(eq_k), len(bh_k), len(cats))
        top_curves.append(
            {
                "slug": r["slug"],
                "title": r["title"][:80],
                "categories": cats[:n],
                "equity_k": eq_k[:n],
                "bench_k": bh_k[:n],
                "cagr": r["cagr"],
                "sharpe": r["sharpe"],
                "max_dd": r["max_drawdown"],
            }
        )

    from collections import Counter

    tmpl = Counter(r["template"] for r in unique)

    payload = {
        "requested": summary["requested"],
        "succeeded": summary["succeeded"],
        "unique_shown": len(unique),
        "elapsed_sec": summary["elapsed_sec"],
        "aggregate": {
            "avg_cagr": round(avg(cagrs), 4),
            "median_cagr": round(sorted(cagrs)[len(cagrs) // 2], 4),
            "avg_sharpe": round(avg(sharpes), 4),
            "median_sharpe": round(sorted(sharpes)[len(sharpes) // 2], 4),
            "avg_max_dd": round(avg(dds), 4),
            "beat_spy_count": sum(
                1
                for r in ok
                if r["metrics"].get("cagr", 0) > r["metrics"].get("benchmark_cagr", 0)
            ),
            "positive_sharpe": sum(1 for s in sharpes if s > 0),
        },
        "templates": dict(tmpl),
        "leaderboard": top,
        "laggards": bottom,
        "top_curves": top_curves,
    }
    PAYLOAD.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Generate canvas TSX
    lb_rows = [
        [
            str(r["rank"]),
            r["slug"][:42],
            r["template"],
            f"{r['cagr']*100:.1f}%",
            f"{r['sharpe']:.2f}",
            f"{r['max_drawdown']*100:.1f}%",
            str(r.get("site_sharpe") or "—"),
        ]
        for r in top
    ]
    lag_rows = [
        [
            r["slug"][:42],
            r["template"],
            f"{r['cagr']*100:.1f}%",
            f"{r['sharpe']:.2f}",
            f"{r['max_drawdown']*100:.1f}%",
        ]
        for r in bottom
    ]

    charts_tsx = []
    for i, c in enumerate(top_curves):
        charts_tsx.append(
            f"""
      <Stack gap={{8}}>
        <H2>#{i+1} {c['slug']}</H2>
        <Text tone="secondary" size="small">
          {c['title'].replace('"', "'")} · CAGR {c['cagr']*100:.1f}% · Sharpe {c['sharpe']:.2f} · MaxDD {c['max_dd']*100:.1f}%
        </Text>
        <LineChart
          height={{220}}
          categories={{{json.dumps(c['categories'])}}}
          series={{[
            {{ name: "Strategy", data: {json.dumps(c['equity_k'])}, tone: "info" }},
            {{ name: "SPY buy-hold", data: {json.dumps(c['bench_k'])}, tone: "neutral" }},
          ]}}
          beginAtZero={{false}}
          fill
          valuePrefix="$"
          valueSuffix="k"
        />
      </Stack>"""
        )

    tmpl_rows = [[k, str(v)] for k, v in sorted(tmpl.items(), key=lambda x: -x[1])]

    tsx = f"""import {{
  Callout,
  Divider,
  H1,
  H2,
  LineChart,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
}} from "cursor/canvas";

const LB_ROWS = {json.dumps(lb_rows)};
const LAG_ROWS = {json.dumps(lag_rows)};
const TMPL_ROWS = {json.dumps(tmpl_rows)};

export default function InhouseBacktest100() {{
  return (
    <Stack gap={{20}} style={{{{ padding: 24, maxWidth: 1200 }}}}>
      <Stack gap={{6}}>
        <H1>In-house backtest — 100 strategies</H1>
        <Text tone="secondary">
          Quant Buffet daily engine · yfinance adj. closes · 5 bps commission + 2 bps slip
        </Text>
        <Row gap={{8}} style={{{{ flexWrap: "wrap" }}}}>
          <Pill tone="success">{summary['succeeded']}/{summary['requested']} ran</Pill>
          <Pill tone="info">{len(unique)} unique after de-dupe</Pill>
          <Pill tone="neutral">~{summary['elapsed_sec']}s wall time</Pill>
        </Row>
      </Stack>

      <Callout tone="warning" title="How to read this">
        These are reconstructed ETF rules (SMA trend, dual momentum, momentum rotation, equal-weight,
        etc.), not bit-identical QuantConnect/LEAN runs. 18 entries are ETF-universe proxies for
        fundamental papers. Site card Sharpe/CAGR often differ — different sample, friction, and signal.
      </Callout>

      <Row gap={{12}} style={{{{ flexWrap: "wrap" }}}}>
        <Stat value="{payload['aggregate']['median_cagr']*100:.1f}%" label="Median CAGR" tone="info" />
        <Stat value="{payload['aggregate']['median_sharpe']:.2f}" label="Median Sharpe" />
        <Stat value="{payload['aggregate']['avg_max_dd']*100:.0f}%" label="Avg max DD" tone="danger" />
        <Stat value="{payload['aggregate']['beat_spy_count']}" label="Beat SPY CAGR" tone="success" />
        <Stat value="{payload['aggregate']['positive_sharpe']}" label="Sharpe > 0" />
      </Row>

      <Stack gap={{8}}>
        <H2>Template mix</H2>
        <Table headers={{["Template", "Count"]}} rows={{TMPL_ROWS}} />
      </Stack>

      <Divider />
      <H2>Top 15 by Sharpe</H2>
      <Table
        headers={{["#", "Slug", "Template", "CAGR", "Sharpe", "MaxDD", "Site Sharpe"]}}
        rows={{LB_ROWS}}
      />

      <Divider />
      <H2>Equity curves — top 3 by Sharpe</H2>
      {"".join(charts_tsx)}

      <Divider />
      <H2>Bottom 5 by Sharpe</H2>
      <Table
        headers={{["Slug", "Template", "CAGR", "Sharpe", "MaxDD"]}}
        rows={{LAG_ROWS}}
      />

      <Callout tone="info" title="Reproduce">
        python scripts/_build_catalog_100.py && python backtest/run_batch_100.py
        Results: backtest/results/batch_100_summary.json
      </Callout>
    </Stack>
  );
}}
"""
    CANVAS.parent.mkdir(parents=True, exist_ok=True)
    CANVAS.write_text(tsx, encoding="utf-8")
    print("unique", len(unique), "payload", PAYLOAD, "canvas", CANVAS)
    print("TOP5:")
    for r in unique[:5]:
        print(
            f"  {r['rank']:2} {r['sharpe']:.2f} {r['cagr']*100:5.1f}% {r['slug'][:50]}"
        )


if __name__ == "__main__":
    main()
