import type { ReactNode } from "react";

import {
  metricDisplay,
  parseBacktestMetricsJson,
  type BacktestMetrics,
} from "@/lib/parse-strategy-content";
import { parsePaperImagesJson } from "@/lib/paper-images";
import { parseAffiliationsJson } from "@/components/InstituteList";
import { hasMeaningfulContent, naOr } from "@/lib/sanitize-text";

import InstituteList from "./InstituteList";
import PlatformCodeExport from "./PlatformCodeExport";
import PythonCodeExplainer from "./PythonCodeExplainer";

type Props = {
  locale: string;
  strategyTitle?: string;
  labels: {
    teaser: string;
    summary: string;
    economicRationale: string;
    backtestPerformance: string;
    pythonCode: string;
    paperTitle: string;
    paperAuthors: string;
    paperInstitute: string;
    paperLink: string;
    paperScreenshot?: string;
    metrics: Record<string, string>;
    platformExport?: {
      title: string;
      subtitle: string;
      platform: string;
      copy: string;
      copied: string;
      pattern: string;
      assets: string;
      ide: string;
      warning: string;
    };
  };
  teaser: string;
  summary: string;
  economicRationale: string;
  backtestMetricsJson: string;
  pythonCodeHtml: string;
  /** Quant Buffet native lab source (ASSETS + make_on_day) when available. */
  labPythonSource?: string;
  paperTitle: string | null;
  paperAuthors: string | null;
  paperInstitute: string;
  paperAffiliationsJson: string;
  academicLink: string | null;
  paperImagesJson?: string | null;
  improvements?: string[];
  /** Set false when a parent (e.g. live lab) already renders the export panel. */
  showPlatformExport?: boolean;
};

const METRIC_ORDER: { key: keyof BacktestMetrics; labelKey: string }[] = [
  { key: "annualisedReturn", labelKey: "annualisedReturn" },
  { key: "volatility", labelKey: "volatility" },
  { key: "beta", labelKey: "beta" },
  { key: "sharpeRatio", labelKey: "sharpeRatio" },
  { key: "sortinoRatio", labelKey: "sortinoRatio" },
  { key: "maxDrawdown", labelKey: "maxDrawdown" },
  { key: "winRate", labelKey: "winRate" },
];

function SectionBox({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="qb-strategy-section">
      <h2 className="qb-strategy-section-title">{title}</h2>
      <div className="qb-strategy-section-body">{children}</div>
    </section>
  );
}

function TextSection({ title, body }: { title: string; body: string }) {
  if (!hasMeaningfulContent(body)) return null;
  const text = naOr(body);
  return (
    <SectionBox title={title}>
      {text.split(/\n{2,}/).map((para, i) => (
        <p key={i}>{para}</p>
      ))}
    </SectionBox>
  );
}

function hasInstituteContent(affiliationsJson: string, fallbackText: string): boolean {
  const rows = parseAffiliationsJson(affiliationsJson);
  if (rows.length > 0) {
    return rows.some((r) => hasMeaningfulContent(r.institute));
  }
  return hasMeaningfulContent(fallbackText);
}

export default function StrategyArticleSections({
  locale,
  strategyTitle = "Quant Buffet strategy",
  labels,
  teaser,
  summary,
  economicRationale,
  backtestMetricsJson,
  pythonCodeHtml,
  labPythonSource = "",
  paperTitle,
  paperAuthors,
  paperInstitute,
  paperAffiliationsJson,
  academicLink,
  paperImagesJson,
  improvements,
  showPlatformExport = true,
}: Props) {
  const metrics = parseBacktestMetricsJson(backtestMetricsJson);
  const paperImages = parsePaperImagesJson(paperImagesJson);
  const hasBacktest = METRIC_ORDER.some(
    ({ key }) => metricDisplay(metrics[key]) !== "N/A",
  );
  const hasPython = Boolean(pythonCodeHtml?.trim());
  const hasExportSource = Boolean(labPythonSource?.trim() || pythonCodeHtml?.trim());
  const paperTitleText = naOr(paperTitle);
  const paperAuthorsText = naOr(paperAuthors);
  const showPaperBlock =
    hasMeaningfulContent(paperTitle) ||
    hasMeaningfulContent(paperAuthors) ||
    hasInstituteContent(paperAffiliationsJson, paperInstitute) ||
    Boolean(academicLink?.trim()) ||
    paperImages.length > 0;

  return (
    <>
      {showPaperBlock ?
        <SectionBox title={labels.paperTitle}>
          {hasMeaningfulContent(paperTitle) ?
            academicLink ?
              <p>
                <a
                  className="qb-accent-link"
                  href={academicLink}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {paperTitleText}
                </a>
              </p>
            : <p>{paperTitleText}</p>
          : null}
          {hasMeaningfulContent(paperAuthors) ?
            <p>
              <span className="qb-paper-meta-label">{labels.paperAuthors}</span>
              {paperAuthorsText}
            </p>
          : null}
          {hasInstituteContent(paperAffiliationsJson, paperInstitute) ?
            <InstituteList
              affiliationsJson={paperAffiliationsJson}
              fallbackText={paperInstitute}
              label={labels.paperInstitute}
            />
          : null}
          {academicLink?.trim() && (!hasMeaningfulContent(paperTitle) || paperTitleText !== academicLink) ?
            <p className="qb-paper-link-row">
              <span className="qb-paper-meta-label">{labels.paperLink}</span>
              <a
                className="qb-accent-link qb-paper-link-url"
                href={academicLink}
                target="_blank"
                rel="noopener noreferrer"
              >
                {academicLink}
              </a>
            </p>
          : null}
          {paperImages.length > 0 ?
            <div className="qb-paper-screenshots">
              <p className="qb-paper-meta-label">
                {labels.paperScreenshot ??
                  (locale === "zh" ? "论文截图" : "Paper screenshot")}
              </p>
              {paperImages.map((img) => (
                <figure key={img.src} className="qb-paper-figure">
                  <img src={img.src} alt={img.alt} loading="lazy" decoding="async" />
                </figure>
              ))}
            </div>
          : null}
        </SectionBox>
      : null}

      {hasMeaningfulContent(teaser) ?
        <SectionBox title={labels.teaser}>
          <p>{naOr(teaser)}</p>
        </SectionBox>
      : null}

      <TextSection title={labels.summary} body={summary} />
      <TextSection title={labels.economicRationale} body={economicRationale} />

      {hasBacktest ?
        <section className="qb-strategy-section qb-backtest-section">
          <h2 className="qb-strategy-section-title">{labels.backtestPerformance}</h2>
          <div className="qb-backtest-grid">
            {METRIC_ORDER.map(({ key, labelKey }) => {
              const value = metricDisplay(metrics[key]);
              if (value === "N/A") return null;
              return (
                <div key={key} className="qb-backtest-metric">
                  <span className="qb-backtest-metric-label">
                    {labels.metrics[labelKey] ?? key}
                  </span>
                  <span className="qb-backtest-metric-value">{value}</span>
                </div>
              );
            })}
          </div>
          {improvements?.length ? (
            <div className="qb-improve">
              <h3 className="qb-improve-title">
                {locale === "zh" ? "如何改进本策略" : "How to improve this strategy"}
              </h3>
              <ul className="qb-improve-list">
                {improvements.map((b, i) => (
                  <li key={i}>{b}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </section>
      : improvements?.length ? (
        <section className="qb-strategy-section">
          <h2 className="qb-strategy-section-title">
            {locale === "zh" ? "如何改进本策略" : "How to improve this strategy"}
          </h2>
          <ul className="qb-improve-list">
            {improvements.map((b, i) => (
              <li key={i}>{b}</li>
            ))}
          </ul>
        </section>
      ) : null}

      {hasPython ?
        <section className="qb-strategy-section qb-strategy-python">
          <h2 className="qb-strategy-section-title">{labels.pythonCode}</h2>
          <PythonCodeExplainer codeHtml={pythonCodeHtml} locale={locale} />
        </section>
      : null}

      {hasExportSource && showPlatformExport ?
        <PlatformCodeExport
          locale={locale}
          title={strategyTitle}
          labPythonSource={labPythonSource}
          pythonCodeHtml={pythonCodeHtml}
          labels={labels.platformExport}
        />
      : null}
    </>
  );
}
