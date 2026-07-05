import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { auth } from "@/auth";
import CollectStrategyButton from "@/components/CollectStrategyButton";
import { isStrategyCollected } from "@/lib/collections";
import { hasMeaningfulContent } from "@/lib/sanitize-text";
import StrategyAiPanel from "@/components/StrategyAiPanel";
import StrategyArticleSections from "@/components/StrategyArticleSections";
import { viewerCanSeeFullArticle } from "@/lib/access";
import { findPublishedStrategy } from "@/lib/slug";
import { getTranslations } from "next-intl/server";

type PageProps = {
  params: Promise<{ locale: string; slug: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  const strategy = await findPublishedStrategy(locale, slug);
  if (!strategy) {
    return { title: "Strategy" };
  }
  const title = strategy.metaTitle?.trim() || `${strategy.title} — Quant Buffet`;
  const description =
    strategy.metaDescription?.trim() || strategy.teaser?.slice(0, 160) || strategy.summary?.slice(0, 160) || undefined;
  return {
    title,
    description,
    openGraph: { title, description },
  };
}

export default async function StrategyArticle({ params }: PageProps) {
  const { locale, slug } = await params;
  const dictionary = await getTranslations({ locale, namespace: "strategy" });

  const strategy = await findPublishedStrategy(locale, slug);

  if (!strategy) {
    notFound();
  }

  const session = await auth();
  const userId = session?.user?.id;
  const initialCollected = userId ? await isStrategyCollected(userId, strategy.id) : false;
  const isGated = strategy.isPaywalled;
  const canRead = viewerCanSeeFullArticle(session?.user, { articlePaywalled: isGated });
  const loginHref = `/${locale}?auth=login&next=/${locale}/strategies/${encodeURIComponent(slug)}`;

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
    metrics: {
      annualisedReturn: dictionary("metricAnnualisedReturn"),
      volatility: dictionary("metricVolatility"),
      beta: dictionary("metricBeta"),
      sharpeRatio: dictionary("metricSharpe"),
      sortinoRatio: dictionary("metricSortino"),
      maxDrawdown: dictionary("metricMaxDrawdown"),
      winRate: dictionary("metricWinRate"),
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

  return (
    <article className="qb-article qb-article-with-ai">
      <header className="qb-article-header">
        <p className="qb-article-meta">
          {strategy.market ?? "—"} · {strategy.region ?? "—"}
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
        <StrategyAiPanel strategy={aiContext} variant="prominent" />
      </header>

      {isGated && !canRead ?
        <section className="qb-paywall-notice">
          <p className="qb-paywall-notice-title">{dictionary("paywallTitle")}</p>
          <p className="qb-paywall-notice-body">{dictionary("paywallBody")}</p>
          {hasMeaningfulContent(strategy.teaser) ?
            <p className="qb-paywall-teaser">{strategy.teaser}</p>
          : null}
          <Link className="qb-pill-primary" href={`/${locale}/pricing`}>
            {dictionary("unlockCta")}
          </Link>
        </section>
      : (
        <StrategyArticleSections
          locale={locale}
          labels={sectionLabels}
          teaser={strategy.teaser}
          summary={strategy.summary}
          economicRationale={strategy.economicRationale}
          backtestMetricsJson={strategy.backtestMetrics}
          pythonCodeHtml={strategy.pythonCodeHtml}
          paperTitle={strategy.paperTitle}
          paperAuthors={strategy.paperAuthors}
          paperInstitute={strategy.paperInstitute}
          paperAffiliationsJson={strategy.paperAffiliationsJson}
          academicLink={strategy.academicLink}
        />
      )}
    </article>
  );
}
