"""Generate canvas documenting in-house libs, data sources, and code paths."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "backtest" / "strategies" / "INDEX.json"
CANVAS = (
    Path.home()
    / ".cursor"
    / "projects"
    / "c-Users-Hansel-Yan-Projects-quant-buffet"
    / "canvases"
    / "inhouse-code-and-data.canvas.tsx"
)

# Embed library source (truncated to keep canvas readable; full files on disk)
LIBS = {
    "data.py": (ROOT / "backtest" / "data.py").read_text(encoding="utf-8"),
    "engine.py": (ROOT / "backtest" / "engine.py").read_text(encoding="utf-8"),
    "metrics.py": (ROOT / "backtest" / "metrics.py").read_text(encoding="utf-8"),
    "templates.py": (ROOT / "backtest" / "templates.py").read_text(encoding="utf-8"),
}

EXAMPLE_SLUG = "asset-class-trend-following"
EXAMPLE_IH = (ROOT / "backtest" / "strategies" / "generated" / f"{EXAMPLE_SLUG}.py").read_text(
    encoding="utf-8"
)
EXAMPLE_QC = (
    ROOT / "backtest" / "strategies" / "qc_original" / f"{EXAMPLE_SLUG}.qc.py"
).read_text(encoding="utf-8")
# Cap QC for canvas display
if len(EXAMPLE_QC) > 6000:
    EXAMPLE_QC_SHOW = EXAMPLE_QC[:6000] + "\n\n# … truncated in canvas — full file on disk …\n"
else:
    EXAMPLE_QC_SHOW = EXAMPLE_QC


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")


def main() -> None:
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    rows = []
    for s in idx["strategies"]:
        rows.append(
            [
                s["slug"][:40],
                s["template"],
                ", ".join(s["assets"][:6]) + ("…" if len(s["assets"]) > 6 else ""),
                "Yahoo Finance / yfinance adj.close",
                s["in_house_python"].replace("backtest/strategies/", "…/"),
                s["quantconnect_python"].replace("backtest/strategies/", "…/"),
            ]
        )

    # Sample a few more in-house snippets for collapsible (short body only)
    samples = []
    for slug in [
        "antonaccis-dual-momentum",
        "lethargic-asset-allocation",
        "adaptive-asset-allocation",
    ]:
        p = ROOT / "backtest" / "strategies" / "generated" / f"{slug}.py"
        if p.exists():
            samples.append((slug, p.read_text(encoding="utf-8")))

    lib_sections = []
    for name, src in LIBS.items():
        show = src if len(src) < 12000 else src[:12000] + "\n# … truncated …\n"
        lib_sections.append(
            f"""
      <CollapsibleSection title="backtest/{name}" count={{{len(src.splitlines())}}}>
        <Text size="small" tone="secondary">Full file: backtest/{name}</Text>
        <Text style={{{{ whiteSpace: "pre-wrap", fontFamily: "ui-monospace, monospace", fontSize: 11 }}}}>
          {json.dumps(show)}
        </Text>
      </CollapsibleSection>"""
        )

    sample_sections = []
    for slug, src in samples:
        sample_sections.append(
            f"""
      <CollapsibleSection title="{slug} (in-house)" count={{{len(src.splitlines())}}}>
        <Text size="small" tone="secondary">
          backtest/strategies/generated/{slug}.py · QC preserved at qc_original/{slug}.qc.py
        </Text>
        <Text style={{{{ whiteSpace: "pre-wrap", fontFamily: "ui-monospace, monospace", fontSize: 11 }}}}>
          {json.dumps(src)}
        </Text>
      </CollapsibleSection>"""
        )

    tsx = f"""import {{
  Callout,
  CollapsibleSection,
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

const ROWS = {json.dumps(rows)};

export default function InhouseCodeAndData() {{
  return (
    <Stack gap={{20}} style={{{{ padding: 24, maxWidth: 1200 }}}}>
      <Stack gap={{6}}>
        <H1>In-house libraries, strategy code & data sources</H1>
        <Text tone="secondary">
          QuantConnect originals preserved · Quant Buffet runners generated alongside
        </Text>
        <Row gap={{8}} style={{{{ flexWrap: "wrap" }}}}>
          <Pill tone="success">{idx['count']} in-house runners</Pill>
          <Pill tone="info">{idx['count']} QC originals kept</Pill>
          <Pill tone="neutral">Data: Yahoo Finance / yfinance</Pill>
        </Row>
      </Stack>

      <Callout tone="info" title="Where to browse everything">
        All 100 in-house Python files: backtest/strategies/generated/*.py{"\\n"}
        All 100 QuantConnect originals (unchanged): backtest/strategies/qc_original/*.qc.py{"\\n"}
        One-file codebook: backtest/strategies/CODEBOOK.md{"\\n"}
        Machine index (paths + per-strategy data sources): backtest/strategies/INDEX.json
      </Callout>

      <Row gap={{12}} style={{{{ flexWrap: "wrap" }}}}>
        <Stat value="4" label="Core library modules" tone="info" />
        <Stat value="{idx['count']}" label="Strategy pairs (IH + QC)" />
        <Stat value="yfinance" label="Primary data provider" />
        <Stat value="adj.close" label="Price field" />
      </Row>

      <Divider />
      <H2>Quant Buffet in-house libraries</H2>
      <Text tone="secondary" size="small">
        Classes: Trade, BacktestResult, EngineConfig, PortfolioEngine · helpers: load_daily_prices,
        compute_metrics, build_strategy / templates
      </Text>
      {"".join(lib_sections)}

      <Divider />
      <H2>Data source (every strategy)</H2>
      <Callout tone="neutral" title="Uniform market data path">
        Provider: Yahoo Finance via the yfinance Python package.{"\\n"}
        Field: adjusted close (auto_adjust=True).{"\\n"}
        Loader: backtest.data.load_daily_prices / load_price_panel.{"\\n"}
        Cache: backtest/data_cache/{{SYMBOL}}_2000-01-01_latest.csv{"\\n"}
        History start request: 2000-01-01 (actual start = max(IPO, signal warmup)).{"\\n"}
        Costs in engine: 5 bps commission + 2 bps slippage per fill.
      </Callout>
      <Text size="small" tone="secondary">
        Per-strategy symbol lists differ — see table below and DATA_SOURCE dict inside each generated file.
      </Text>

      <Divider />
      <H2>Example pair — asset-class-trend-following</H2>
      <CollapsibleSection title="In-house Python (full)" defaultOpen count={{{len(EXAMPLE_IH.splitlines())}}}>
        <Text style={{{{ whiteSpace: "pre-wrap", fontFamily: "ui-monospace, monospace", fontSize: 11 }}}}>
          {json.dumps(EXAMPLE_IH)}
        </Text>
      </CollapsibleSection>
      <CollapsibleSection title="QuantConnect original (preserved)" count={{{len(EXAMPLE_QC.splitlines())}}}>
        <Text size="small" tone="secondary">
          backtest/strategies/qc_original/{EXAMPLE_SLUG}.qc.py — not erased or overwritten by the port
        </Text>
        <Text style={{{{ whiteSpace: "pre-wrap", fontFamily: "ui-monospace, monospace", fontSize: 11 }}}}>
          {json.dumps(EXAMPLE_QC_SHOW)}
        </Text>
      </CollapsibleSection>

      <Divider />
      <H2>More in-house examples</H2>
      {"".join(sample_sections)}

      <Divider />
      <H2>All 100 — code paths & data source</H2>
      <Text size="small" tone="secondary">
        Source: backtest/strategies/INDEX.json · Data provider column is Yahoo Finance for every row
      </Text>
      <Table
        headers={{["Slug", "Template", "Symbols", "Data source", "In-house path", "QC path"]}}
        rows={{ROWS}}
      />
    </Stack>
  );
}}
"""
    CANVAS.parent.mkdir(parents=True, exist_ok=True)
    CANVAS.write_text(tsx, encoding="utf-8")
    print("wrote", CANVAS, "bytes", CANVAS.stat().st_size)


if __name__ == "__main__":
    main()
