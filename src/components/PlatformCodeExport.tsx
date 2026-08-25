"use client";

import { useMemo, useState } from "react";

import {
  EXPORT_PLATFORMS,
  buildPlatformExport,
  type ExportPlatformId,
} from "@/lib/platform-export";

type Props = {
  locale: string;
  title: string;
  labPythonSource?: string;
  pythonCodeHtml?: string;
  /** When provided (e.g. from live lab editor), overrides static sources. */
  liveCode?: string;
  labels?: {
    title?: string;
    subtitle?: string;
    platform?: string;
    generate?: string;
    copy?: string;
    copied?: string;
    pattern?: string;
    assets?: string;
    ide?: string;
    warning?: string;
  };
};

const DEFAULT_LABELS = {
  title: "Export to your platform",
  subtitle:
    "Transform Quant Buffet lab code (ASSETS + make_on_day / PortfolioEngine) into native classes for a third-party IDE — then copy and paste.",
  platform: "Target platform",
  generate: "Generate code",
  copy: "Copy for IDE",
  copied: "Copied",
  pattern: "Detected pattern",
  assets: "Assets",
  ide: "Run in",
  warning: "Note",
};

export default function PlatformCodeExport({
  locale,
  title,
  labPythonSource = "",
  pythonCodeHtml = "",
  liveCode,
  labels: labelOverrides,
}: Props) {
  const labels = { ...DEFAULT_LABELS, ...labelOverrides };
  const [platform, setPlatform] = useState<ExportPlatformId>("quantconnect");
  const [copied, setCopied] = useState(false);

  const source = (liveCode?.trim() || labPythonSource || "").trim();

  const result = useMemo(
    () =>
      buildPlatformExport(
        {
          labPythonSource: source || labPythonSource,
          pythonCodeHtml: source ? "" : pythonCodeHtml,
          title,
        },
        platform,
        title,
      ),
    [source, labPythonSource, pythonCodeHtml, platform, title],
  );

  const meta = EXPORT_PLATFORMS.find((p) => p.id === platform);

  async function copyCode() {
    try {
      await navigator.clipboard.writeText(result.code);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      // ignore
    }
  }

  const isZh = locale === "zh";

  return (
    <section className="qb-strategy-section qb-platform-export" id="platform-export">
      <h2 className="qb-strategy-section-title">{labels.title}</h2>
      <p className="qb-platform-export-sub">{labels.subtitle}</p>

      <div className="qb-platform-export-controls">
        <label className="qb-platform-export-label">
          <span>{labels.platform}</span>
          <select
            className="qb-platform-export-select"
            value={platform}
            onChange={(e) => setPlatform(e.target.value as ExportPlatformId)}
          >
            {EXPORT_PLATFORMS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <button type="button" className="qb-pill-primary" onClick={copyCode}>
          {copied ? labels.copied : labels.copy}
        </button>
      </div>

      {meta ? (
        <p className="qb-platform-export-meta">
          <strong>{labels.ide}:</strong> {meta.ide}
          {" · "}
          {meta.blurb}
        </p>
      ) : null}

      <div className="qb-platform-export-tags">
        <span className="qb-platform-export-tag">
          <strong>{labels.pattern}:</strong> {result.pattern}
        </span>
        <span className="qb-platform-export-tag">
          <strong>{labels.assets}:</strong> {result.assets.join(", ")}
        </span>
      </div>

      {result.warning ? (
        <aside className="qb-docs-callout qb-docs-callout-warn" role="note">
          <strong>{labels.warning}.</strong> {result.warning}
        </aside>
      ) : null}

      <pre className="qb-platform-export-pre">
        <code>{result.code}</code>
      </pre>

      <p className="qb-platform-export-foot">
        {isZh
          ? "导出代码使用目标平台的原生类与库。请在第三方 IDE 中安装依赖后运行；实盘前请自行验证。"
          : "Exported code uses the platform’s native classes and libraries. Install dependencies in your third-party IDE, then run. Validate before live trading."}
      </p>
    </section>
  );
}
