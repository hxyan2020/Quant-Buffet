"""Generate canvas for full-library coverage results."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "backtest" / "results" / "batch_full_summary.json"
INDEX = ROOT / "backtest" / "strategies" / "INDEX.json"
CANVAS = (
    Path.home()
    / ".cursor"
    / "projects"
    / "c-Users-Hansel-Yan-Projects-quant-buffet"
    / "canvases"
    / "inhouse-full-library.canvas.tsx"
)


def main() -> None:
    summary = json.loads(SUMMARY.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))

    ok = [r for r in summary["results"] if r.get("status") == "ok"]
    fail = [r for r in summary["results"] if r.get("status") != "ok"]
    no_qc = [s for s in index["strategies"] if not s.get("has_qc_source")]
    with_qc = [s for s in index["strategies"] if s.get("has_qc_source")]

    sharpes = [r["metrics"]["sharpe"] for r in ok]
    cagrs = [r["metrics"]["cagr"] for r in ok]

    def med(xs):
        xs = sorted(xs)
        return xs[len(xs) // 2] if xs else 0.0

    top = summary.get("leaderboard_top50") or []
    bottom = summary.get("leaderboard_bottom20") or []

    top_rows = [
        [
            str(r["rank"]),
            (r.get("file_key") or "")[:42],
            r.get("template") or "",
            "QC" if r.get("has_qc_source") else "no-QC",
            f"{r['cagr']*100:.1f}%",
            f"{r['sharpe']:.2f}",
            f"{r['max_drawdown']*100:.0f}%",
        ]
        for r in top[:20]
    ]
    bot_rows = [
        [
            (r.get("file_key") or "")[:42],
            r.get("template") or "",
            "QC" if r.get("has_qc_source") else "no-QC",
            f"{r['cagr']*100:.1f}%",
            f"{r['sharpe']:.2f}",
            f"{r['max_drawdown']*100:.0f}%",
        ]
        for r in bottom[:10]
    ]

    fid = Counter(s.get("fidelity") for s in index["strategies"])
    tmpl = Counter(s.get("template") for s in index["strategies"])
    fid_rows = [[k, str(v)] for k, v in fid.most_common()]
    tmpl_rows = [[k, str(v)] for k, v in tmpl.most_common()]

    # Sample no-QC strategy paths
    no_qc_samples = [
        [
            s["file_key"][:40],
            s["template"],
            ",".join(s["assets"][:4]),
            s["in_house_python"].replace("backtest/strategies/", "…/"),
            s["quantconnect_python"].replace("backtest/strategies/", "…/"),
        ]
        for s in no_qc[:15]
    ]

    fail_rows = [
        [
            (r.get("file_key") or "")[:40],
            (r.get("error") or "")[:60],
        ]
        for r in fail[:15]
    ]

    tsx = f"""import {{
  Callout,
  Divider,
  H1,
  H2,
  Pill,
  Row,
  Stack,
  Stat,
  Table,
  Text,
}} from "cursor/canvas";

const TOP = {json.dumps(top_rows)};
const BOT = {json.dumps(bot_rows)};
const FID = {json.dumps(fid_rows)};
const TMPL = {json.dumps(tmpl_rows)};
const NOQC = {json.dumps(no_qc_samples)};
const FAIL = {json.dumps(fail_rows)};

export default function InhouseFullLibrary() {{
  return (
    <Stack gap={{20}} style={{{{ padding: 24, maxWidth: 1200 }}}}>
      <Stack gap={{6}}>
        <H1>Full library in-house backtests</H1>
        <Text tone="secondary">
          Every published EN + ZH strategy — QC preserved when present; theme proxies when missing
        </Text>
        <Row gap={{8}} style={{{{ flexWrap: "wrap" }}}}>
          <Pill tone="success">{summary['succeeded']}/{summary['requested']} ran</Pill>
          <Pill tone="info">{len(with_qc)} with QC source</Pill>
          <Pill tone="warning">{len(no_qc)} without QC (proxied)</Pill>
          <Pill tone="neutral">~{summary.get('elapsed_sec')}s</Pill>
        </Row>
      </Stack>

      <Callout tone="info" title="Code locations">
        In-house runners: backtest/strategies/generated/*.py ({len(index['strategies'])} files){"\\n"}
        QC originals: backtest/strategies/qc_original/*.qc.py ({len(with_qc)}){"\\n"}
        Missing QC markers: *.MISSING.txt ({len(no_qc)}){"\\n"}
        Index + data sources: backtest/strategies/INDEX.json{"\\n"}
        Catalog table: backtest/strategies/CATALOG.md
      </Callout>

      <Row gap={{12}} style={{{{ flexWrap: "wrap" }}}}>
        <Stat value="{med(cagrs)*100:.1f}%" label="Median CAGR" tone="info" />
        <Stat value="{med(sharpes):.2f}" label="Median Sharpe" />
        <Stat value="{sum(1 for s in sharpes if s>0)}" label="Sharpe > 0" tone="success" />
        <Stat value="{len(fail)}" label="Failed runs" tone={{len(fail) ? "danger" : "success"}} />
      </Row>

      <Divider />
      <H2>Fidelity mix (how each strategy was mapped)</H2>
      <Table headers={{["Fidelity", "Count"]}} rows={{FID}} />

      <H2>Template mix</H2>
      <Table headers={{["Template", "Count"]}} rows={{TMPL}} />

      <Divider />
      <H2>Top 20 by Sharpe</H2>
      <Table
        headers={{["#", "file_key", "Template", "QC?", "CAGR", "Sharpe", "MaxDD"]}}
        rows={{TOP}}
      />

      <H2>Bottom 10 by Sharpe</H2>
      <Table
        headers={{["file_key", "Template", "QC?", "CAGR", "Sharpe", "MaxDD"]}}
        rows={{BOT}}
      />

      <Divider />
      <H2>Sample strategies that had NO QuantConnect code</H2>
      <Text size="small" tone="secondary">
        These still have full in-house Python; QC side is a .MISSING.txt marker (not invented QC).
      </Text>
      <Table
        headers={{["file_key", "Template", "Symbols", "In-house", "QC marker"]}}
        rows={{NOQC}}
      />

      {f'''
      <Divider />
      <H2>Failed runs (sample)</H2>
      <Table headers={{["file_key", "Error"]}} rows={{FAIL}} />
      ''' if fail_rows else ""}

      <Callout tone="warning" title="How to read fidelity">
        reconstructed_etf_rules = QC present, tickers extracted.{"\\n"}
        no_qc_theme_proxy = no QC in DB; ETF book + rule from title/assetClass.{"\\n"}
        signal_unavailable_etf_proxy = paper needs ML/alt-data/options; ETF proxy only.{"\\n"}
        Data for all: Yahoo Finance adjusted closes via yfinance.
      </Callout>
    </Stack>
  );
}}
"""
    CANVAS.write_text(tsx, encoding="utf-8")
    print("wrote", CANVAS)


if __name__ == "__main__":
    main()
