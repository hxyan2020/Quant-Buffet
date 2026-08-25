import { extractPythonPlainText } from "@/lib/format-python";

import { EXPORT_PLATFORMS, transformToPlatform, type ExportPlatformId } from "./emitters";
import { parseQbStrategy, patternLabel, type QbStrategySketch } from "./parse-qb";

export { EXPORT_PLATFORMS, transformToPlatform, parseQbStrategy, patternLabel };
export type { ExportPlatformId, QbStrategySketch };

export type PlatformExportResult = {
  platform: ExportPlatformId;
  code: string;
  pattern: string;
  assets: string[];
  warning?: string;
};

/** Prefer Quant Buffet lab source; fall back to HTML/plain Python. */
export function resolveExportSource(opts: {
  labPythonSource?: string | null;
  pythonCodeHtml?: string | null;
  title?: string;
}): { source: string; sketch: QbStrategySketch; warning?: string } {
  const lab = (opts.labPythonSource || "").trim();
  const fromHtml = extractPythonPlainText(opts.pythonCodeHtml || "");
  let source = lab;
  let warning: string | undefined;

  if (!source && fromHtml) {
    source = fromHtml;
    if (!/make_on_day|ASSETS\s*=/.test(fromHtml)) {
      warning =
        "Source looks like QuantConnect/other Python. Tickers were inferred; signal pattern may be approximate — review before running.";
    }
  }

  if (!source) {
    source = `ASSETS = ["SPY", "QQQ", "TLT", "GLD", "BIL"]\n\ndef make_on_day(prices):\n    cols = [c for c in ASSETS if c in prices.columns]\n    w = 1.0 / len(cols) if cols else 0.0\n    def on_day(engine, dt):\n        engine.set_target_weights(dt, {s: w for s in cols})\n    return on_day, prices.index.min()\n`;
    warning = "No strategy Python found — exported an equal-weight ETF scaffold.";
  }

  const sketch = parseQbStrategy(source, opts.title || "Quant Buffet strategy");
  return { source, sketch, warning };
}

export function buildPlatformExport(
  sourceOrOpts:
    | string
    | {
        labPythonSource?: string | null;
        pythonCodeHtml?: string | null;
        title?: string;
      },
  platform: ExportPlatformId,
  title = "Quant Buffet strategy",
): PlatformExportResult {
  const resolved =
    typeof sourceOrOpts === "string"
      ? { source: sourceOrOpts, sketch: parseQbStrategy(sourceOrOpts, title), warning: undefined }
      : resolveExportSource({ ...sourceOrOpts, title });

  const code = transformToPlatform(resolved.sketch, platform);
  return {
    platform,
    code,
    pattern: patternLabel(resolved.sketch.pattern),
    assets: resolved.sketch.assets,
    warning: resolved.warning,
  };
}
