import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import CollectStrategyButton from "@/components/CollectStrategyButton";
import JsonLd from "@/components/JsonLd";
import { isStrategyCollected } from "@/lib/collections";
import { hasMeaningfulContent } from "@/lib/sanitize-text";
import StrategyAiPanel from "@/components/StrategyAiPanel";
import StrategyArticleSections from "@/components/StrategyArticleSections";
import { viewerCanSeeFullArticle } from "@/lib/access";
import { findPublishedStrategy, strategyHref } from "@/lib/slug";
import { resolveStrategyLabSource } from "@/lib/strategy-lab-source";
import {
  breadcrumbJsonLd,
  buildStrategySeo,
  pageMetadata,
  strategyJsonLd,
} from "@/lib/seo";
import { syncUserPlanAccess } from "@/lib/subscription";
import { getTranslations } from "next-intl/server";

type PageProps = {
  params: Promise<{ locale: string; slug: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  const strategy = await findPublishedStrategy(locale, slug);
  if (!strategy) {
    return { title: "Strategy", robots: { index: false } };
  }

  const seo = buildStrategySeo(strategy);
  const path = `/strategies/${encodeURIComponent(strategy.slug)}`;
  return {
    ...pageMetadata({
      locale,
      path,
      title: seo.title,
      description: seo.description,
      keywords: seo.keywords,
    }),
    openGraph: {
      type: "article",
      locale: locale === "zh" ? "zh_CN" : "en_US",
      title: seo.title,
      description: seo.description,
      url: undefined,
    },
  };
}

export default async function StrategyArticle({ params }: PageProps) {
  const { locale, slug } = await params;
  const dictionary = await getTranslations({ locale, namespace: "strategy" });
  const nav = await getTranslations({ locale, namespace: "nav" });

  const strategy = await findPublishedStrategy(locale, slug);

  if (!strategy) {
    notFound();
  }

  const session = await auth();
  const userId = session?.user?.id;
  const plan = userId ? await syncUserPlanAccess(userId, locale) : null;
  const initialCollected = userId ? await isStrategyCollected(userId, strategy.id) : false;
  const isGated = strategy.isPaywalled;
  const canRead = viewerCanSeeFullArticle(
    session?.user ?
      { ...session.user, libraryUnlocked: plan?.hasActivePlan ?? session.user.libraryUnlocked }
    : null,
    { articlePaywalled: isGated },
  );
  const loginHref = `/${locale}?auth=login&next=${encodeURIComponent(strategyHref(locale, strategy.slug))}`;

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

  const aiContext = {
    slug: strategy.slug,
    locale: strategy.locale,
    title: strategy.title,
    teaser: canRead ? strategy.teaser : strategy.teaser,
    summary: canRead ? strategy.summary : strategy.teaser,
    economicRationale: canRead ? strategy.economicRationale : "",
  };

  const assetBits = [strategy.assetClass, strategy.frequency, strategy.region]
    .filter(Boolean)
    .join(" · ");

  return (
    <article className="qb-article qb-article-with-ai">
      <JsonLd data={strategyJsonLd(strategy)} />
      <JsonLd
        data={breadcrumbJsonLd(
          [
            { name: nav("home"), path: "" },
            { name: nav("library"), path: "/strategy-library" },
            {
              name: strategy.title,
              path: `/strategies/${encodeURIComponent(strategy.slug)}`,
            },
          ],
          locale,
        )}
      />
      <header className="qb-article-header">
        <p className="qb-article-meta">
          {strategy.market ?? "—"} · {strategy.region ?? "—"}
          {assetBits ? ` · ${assetBits}` : ""}
          {isGated ?
            <span className="qb-article-badge qb-article-badge-paid"> Paid </span>
          : <span className="qb-article-badge qb-article-badge-free"> Free </span>}
        </p>
        <div className="qb-article-title-row">
          <h1 className="qb-article-title">{strategy.title}</h1>
          <CollectStrategyButton
            strategyId={strategy.id}
            locale={locale}
            initialCollected={initialCollected}
            isLoggedIn={Boolean(userId)}
            loginHref={loginHref}
          />
        </div>
        {canRead ?
          <StrategyAiPanel strategy={aiContext} variant="prominent" />
        : null}
      </header>

      {isGated && !canRead ?
        <section className="qb-paywall-notice">
          <p className="qb-paywall-notice-title">{dictionary("paywallTitle")}</p>
          <p className="qb-paywall-notice-body">{dictionary("paywallBody")}</p>
          {hasMeaningfulContent(strategy.teaser) ?
            <p className="qb-paywall-teaser">{strategy.teaser}</p>
          : null}
          <div className="qb-paywall-actions">
            <Link className="qb-pill-primary" href={`/${locale}/pricing`}>
              {dictionary("unlockCta")}
            </Link>
            {!userId ?
              <Link className="qb-paywall-login" href={loginHref}>
                {dictionary("paywallLogin")}
              </Link>
            : null}
          </div>
        </section>
      : (
        <StrategyArticleSections
          locale={locale}
          strategyTitle={strategy.title}
          labels={sectionLabels}
          teaser={strategy.teaser}
          summary={strategy.summary}
          economicRationale={strategy.economicRationale}
          backtestMetricsJson={strategy.backtestMetrics}
          pythonCodeHtml={strategy.pythonCodeHtml}
          labPythonSource={resolveStrategyLabSource({
            slug: strategy.slug,
            locale: strategy.locale,
            pythonCodeHtml: strategy.pythonCodeHtml,
          })}
          paperTitle={strategy.paperTitle}
          paperAuthors={strategy.paperAuthors}
          paperInstitute={strategy.paperInstitute}
          paperAffiliationsJson={strategy.paperAffiliationsJson}
          academicLink={strategy.academicLink}
          paperImagesJson={strategy.paperImagesJson}
        />
      )}
    </article>
  );
}
