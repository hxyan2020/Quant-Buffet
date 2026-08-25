import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import LiveTradingGuidePanel from "@/components/LiveTradingGuide";
import StrategyArticleSections from "@/components/StrategyArticleSections";
import StrategyBacktestLab from "@/components/StrategyBacktestLab";
import {
  draftBacktestMetricsJson,
  draftPreviewEnabled,
  findCatalogSpec,
  findDraftPost,
  findLabEntry,
  loadDraftEquityCurve,
  loadLabPythonSource,
} from "@/lib/draft-preview";
import { findPublishedStrategy } from "@/lib/slug";
import { buildStrategyImprovements, parseMetricNumber } from "@/lib/strategy-improvements";
import { buildLiveTradingGuide } from "@/lib/live-trading-guide";

type PageProps = {
  params: Promise<{ locale: string; slug: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  const entry = findLabEntry(locale, slug) || findLabEntry("en", slug);
  return {
    title: entry ? `[LAB] ${entry.title}` : "Lab strategy",
    robots: { index: false, follow: false },
  };
}

export default async function DraftPreviewArticle({ params }: PageProps) {
  const { locale, slug } = await params;
  if (!draftPreviewEnabled()) notFound();

  const entry = findLabEntry(locale, slug) || findLabEntry("en", slug) || findLabEntry("zh", slug);
  if (!entry) notFound();

  const draft = findDraftPost(slug);
  const published =
    entry.source === "library"
      ? await findPublishedStrategy(entry.locale, slug)
      : null;

  const dictionary = await getTranslations({ locale, namespace: "strategy" });
  const curve = loadDraftEquityCurve(slug);
  const initialCode = loadLabPythonSource(entry, draft?.pythonCodeHtml || published?.pythonCodeHtml || "");

  const title = draft?.title || published?.title || entry.title;
  const teaser = draft?.teaser || published?.teaser || "";
  const summary = draft?.summary || published?.summary || "";
  const economicRationale = draft?.economicRationale || published?.economicRationale || "";
  const paperTitle = draft?.paperTitle || published?.paperTitle || null;
  const paperAuthors = draft?.paperAuthors || published?.paperAuthors || null;
  const paperInstitute = draft?.paperInstitute || published?.paperInstitute || "";
  const academicLink = draft?.academicLink || published?.academicLink || null;
  const pythonCodeHtml = draft?.pythonCodeHtml || published?.pythonCodeHtml || "";
  const paperAffiliationsJson =
    draft?.paperAffiliationsJson || published?.paperAffiliationsJson || "[]";

  const metricsPost = {
    annualisedReturn: draft?.annualisedReturn ?? entry.annualisedReturn ?? published?.annualisedReturn ?? null,
    volatility: draft?.volatility ?? entry.volatility ?? published?.volatility ?? null,
    beta: draft?.beta ?? entry.beta ?? published?.beta ?? null,
    sharpeRatio: draft?.sharpeRatio ?? entry.sharpeRatio ?? published?.sharpeRatio ?? null,
    sortinoRatio: draft?.sortinoRatio ?? entry.sortinoRatio ?? published?.sortinoRatio ?? null,
    maxDrawdown: draft?.maxDrawdown ?? entry.maxDrawdown ?? published?.maxDrawdown ?? null,
    winRate: draft?.winRate ?? published?.winRate ?? null,
  };

  const sectionLabels = {
    teaser: dictionary("teaser"),
    summary: dictionary("summary"),
    economicRationale: dictionary("economicRationale"),
    backtestPerformance: dictionary("backtestPerformance"),
    pythonCode: dictionary("pythonCode"),
    paperTitle: dictionary("academicPaper"),
    paperAuthors: dictionary("paperAuthors"),
    paperInstitute: dictionary("paperInstitute"),
    paperLink: dictionary("paperLink"),
    paperScreenshot: dictionary("paperScreenshot"),
    metrics: {
      annualisedReturn: dictionary("metricAnnualisedReturn"),
      volatility: dictionary("metricVolatility"),
      beta: dictionary("metricBeta"),
      sharpeRatio: dictionary("metricSharpe"),
      sortinoRatio: dictionary("metricSortino"),
      maxDrawdown: dictionary("metricMaxDrawdown"),
      winRate: dictionary("metricWinRate"),
    },
    platformExport: {
      title: dictionary("platformExportTitle"),
      subtitle: dictionary("platformExportSubtitle"),
      platform: dictionary("platformExportPlatform"),
      copy: dictionary("platformExportCopy"),
      copied: dictionary("platformExportCopied"),
      pattern: dictionary("platformExportPattern"),
      assets: dictionary("platformExportAssets"),
      ide: dictionary("platformExportIde"),
      warning: dictionary("platformExportWarning"),
    },
  };

  const market = draft?.market || published?.market || null;
  const region = draft?.region || published?.region || entry.region || null;
  const assetClass = draft?.assetClass || published?.assetClass || entry.assetClass || null;
  const frequency = draft?.frequency || published?.frequency || null;
  const assetBits = [assetClass, frequency, region].filter(Boolean).join(" · ");

  const catalog = entry.source === "library" ? findCatalogSpec(entry.locale, slug) : null;
  const assets = draft?.assets || entry.assets || catalog?.assets || [];
  const template = draft?.template || entry.template || catalog?.template || null;
  const strategyParams = draft?.params || entry.params || catalog?.params || null;
  const fidelity = draft?.fidelity || entry.fidelity || catalog?.fidelity || null;
  const trades =
    draft?.backtest?.trades ??
    (typeof draft?.backtest?.metrics?.trades === "number" ? draft.backtest.metrics.trades : null) ??
    entry.trades ??
    null;

  const liveGuide = buildLiveTradingGuide({
    locale,
    title,
    assets,
    template,
    region,
  });

  const improvements = buildStrategyImprovements({
    locale,
    title,
    paperTitle,
    template,
    assets,
    params: strategyParams,
    fidelity,
    source: entry.source,
    assetClass,
    region,
    cagr: parseMetricNumber(metricsPost.annualisedReturn),
    sharpe: parseMetricNumber(metricsPost.sharpeRatio),
    maxDd: parseMetricNumber(metricsPost.maxDrawdown),
    vol: parseMetricNumber(metricsPost.volatility),
    trades: typeof trades === "number" ? trades : null,
    siteCagr: parseMetricNumber(catalog?.site_annualisedReturn || entry.siteCagr),
    hasQc: entry.has_qc_source ?? catalog?.has_qc_source,
  });

  return (
    <article className="qb-article">
      <div
        style={{
          marginBottom: 16,
          padding: "10px 14px",
          border: "1px solid var(--qb-border, #d4a017)",
          borderRadius: 6,
          background: "color-mix(in srgb, #d4a017 12%, transparent)",
          fontSize: 14,
        }}
      >
        <strong>TEMP LAB</strong> — not published production URL.{" "}
        <Link href={`/${locale}/draft-preview`}>← Full list</Link>
        {" · "}
        <a href="#backtest-lab">Jump to interactive lab</a>
        {" · "}
        <a href="#live-trading">Live trading</a>
        <span style={{ opacity: 0.75 }}>
          {" "}
          · source: {entry.source}
          {entry.fidelity ? ` · fidelity: ${entry.fidelity}` : ""}
          {entry.template ? ` · template: ${entry.template}` : ""}
        </span>
      </div>

      <header className="qb-article-header">
        <p className="qb-article-meta">
          {market ?? "—"} · {region ?? "—"}
          {assetBits ? ` · ${assetBits}` : ""}
          <span className="qb-article-badge qb-article-badge-paid">
            {entry.source === "new100" ? " New draft " : " Library lab "}
          </span>
        </p>
        <h1 className="qb-article-title">{title}</h1>
        {entry.assets?.length ? (
          <p className="qb-article-summary-text" style={{ fontSize: 13, opacity: 0.75 }}>
            Assets: {entry.assets.join(", ")}
          </p>
        ) : null}
      </header>

      <StrategyBacktestLab
        locale={locale}
        slug={entry.slug}
        title={title}
        initialCode={initialCode}
        baselineMetrics={{
          annualisedReturn: metricsPost.annualisedReturn,
          volatility: metricsPost.volatility,
          sharpeRatio: metricsPost.sharpeRatio,
          sortinoRatio: metricsPost.sortinoRatio,
          maxDrawdown: metricsPost.maxDrawdown,
          beta: metricsPost.beta,
          winRate: metricsPost.winRate,
        }}
        baselineEquity={curve.equity}
        baselineBenchmark={curve.benchmark}
      />

      {entry.source === "new100" && draft?.source_paper ? (
        <section className="qb-strategy-section" style={{ marginBottom: 24 }}>
          <h2 className="qb-strategy-section-title">How this paper was scraped</h2>
          <div className="qb-strategy-section-body" style={{ fontSize: 14, lineHeight: 1.55 }}>
            <p>
              Official scholarly APIs only (no SSRN HTML scrape). Script:{" "}
              <code>scripts/scrape_new_strategy_papers.py</code>. Deduped against the live Quant Buffet
              library, then scored for ETF/rules implementability.
            </p>
            <ul>
              <li>
                <strong>API:</strong> {draft.source_paper.source || "—"}
              </li>
              <li>
                <strong>Search query:</strong> {draft.source_paper.query || "—"}
              </li>
              <li>
                <strong>Implementability score:</strong> {draft.source_paper.score ?? "—"}
              </li>
              <li>
                <strong>Venue / year:</strong> {draft.source_paper.venue || "—"} ·{" "}
                {draft.source_paper.year ?? "—"}
                {draft.source_paper.citationCount != null
                  ? ` · citations ${draft.source_paper.citationCount}`
                  : ""}
              </li>
              <li>
                <strong>Paper URL:</strong>{" "}
                {academicLink ? (
                  <a href={academicLink} target="_blank" rel="noreferrer">
                    {academicLink}
                  </a>
                ) : (
                  "—"
                )}
              </li>
            </ul>
            <p>
              <Link href={`/${locale}/draft-preview/scrape`}>Full scrape method + all 100 sources</Link>
            </p>
          </div>
        </section>
      ) : null}

      <StrategyArticleSections
        locale={locale}
        strategyTitle={title}
        labels={sectionLabels}
        teaser={teaser}
        summary={summary}
        economicRationale={economicRationale}
        backtestMetricsJson={draftBacktestMetricsJson({
          ...metricsPost,
          slug: entry.slug,
          locale: entry.locale,
          published: false,
          draft: true,
          title,
          teaser,
          summary,
          economicRationale,
          paperTitle,
          paperAuthors,
          paperInstitute,
          academicLink,
          assetClass,
          region,
          market,
          frequency,
          isPaywalled: true,
          hasPythonCode: true,
          pythonCodeHtml,
          contentHtml: "",
        })}
        pythonCodeHtml={pythonCodeHtml}
        labPythonSource={initialCode}
        showPlatformExport={false}
        paperTitle={paperTitle}
        paperAuthors={paperAuthors}
        paperInstitute={paperInstitute}
        paperAffiliationsJson={paperAffiliationsJson}
        academicLink={academicLink}
        paperImagesJson={published?.paperImagesJson ?? "[]"}
        improvements={improvements}
      />

      <LiveTradingGuidePanel locale={locale} guide={liveGuide} />
    </article>
  );
}
