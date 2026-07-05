import { Suspense } from "react";

import StrategyLibraryTable from "@/components/StrategyLibraryTable";
import { auth } from "@/auth";
import { getCollectedStrategyIdSet } from "@/lib/collections";
import { listStrategies } from "@/lib/strategies";
import { displayToken } from "@/lib/strategy-tokens";
import { getTranslations } from "next-intl/server";

type PageProps = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{
    page?: string;
    q?: string;
    market?: string;
    region?: string;
    assetClass?: string;
    plan?: string;
    collection?: string;
  }>;
};

async function LibraryContent({
  locale,
  pageParam,
  q,
  market,
  region,
  assetClass,
  plan,
  collection,
  userId,
}: {
  locale: string;
  pageParam?: string;
  q?: string;
  market?: string;
  region?: string;
  assetClass?: string;
  plan?: string;
  collection?: string;
  userId: string | null;
}) {
  const dictionary = await getTranslations({ locale, namespace: "library" });
  const page = Number(pageParam) || 1;
  const collectedIds = userId ? await getCollectedStrategyIdSet(userId) : new Set<string>();
  const result = await listStrategies({
    locale,
    page,
    q,
    market,
    region,
    assetClass,
    plan,
    collection,
    collectedIds,
  });

  const startNo = (result.page - 1) * result.pageSize + 1;
  const endNo =
    result.rows.length > 0 ? Math.min(startNo + result.rows.length - 1, result.total) : 0;

  return (
    <StrategyLibraryTable
      locale={locale}
      rows={result.rows}
      total={result.total}
      page={result.page}
      totalPages={result.totalPages}
      pageSize={result.pageSize}
      isLoggedIn={Boolean(userId)}
      collectedIds={[...collectedIds]}
      initialQuery={q ?? ""}
      initialMarket={market ?? ""}
      initialRegion={region ?? ""}
      initialAssetClass={assetClass ?? ""}
      initialPlan={plan ?? ""}
      initialCollection={collection ?? ""}
      filterOptions={result.filterOptions}
      labels={{
        colNo: dictionary("colNo"),
        colName: dictionary("colName"),
        colAnn: dictionary("colAnn"),
        colSharpe: dictionary("colSharpe"),
        colRegion: dictionary("colRegion"),
        colMarket: dictionary("colMarket"),
        colAsset: dictionary("colAsset"),
        colFreq: dictionary("colFreq"),
        colPlan: dictionary("colPlan"),
        colCollect: dictionary("colCollect"),
        colLink: dictionary("colLink"),
        planPaid: dictionary("planPaid"),
        planFree: dictionary("planFree"),
        collect: dictionary("collect"),
        collected: dictionary("collected"),
        open: dictionary("open"),
        searchPlaceholder: dictionary("searchPlaceholder"),
        showing: dictionary("showing", {
          start: result.rows.length ? startNo : 0,
          end: endNo,
          total: result.total,
        }),
        prev: dictionary("prev"),
        next: dictionary("next"),
        filterSearch: dictionary("filterSearch"),
        filterMarket: dictionary("filterMarket"),
        filterRegion: dictionary("filterRegion"),
        filterAsset: dictionary("filterAsset"),
        filterPlan: dictionary("filterPlan"),
        filterCollection: dictionary("filterCollection"),
        filterAll: dictionary("filterAll"),
        filterCollected: dictionary("filterCollected"),
        filterNotCollected: dictionary("filterNotCollected"),
        apply: dictionary("apply"),
        clear: dictionary("clear"),
      }}
    />
  );
}

export default async function StrategyLibrary({ params, searchParams }: PageProps) {
  const { locale } = await params;
  const query = await searchParams;
  const dictionary = await getTranslations({ locale, namespace: "library" });
  const session = await auth();

  return (
    <div className="qb-page">
      <header className="qb-page-header">
        <p className="qb-page-eyebrow">Quant Buffet</p>
        <h1 className="qb-page-title">{dictionary("title")}</h1>
        <p className="qb-page-subtitle">{dictionary("subtitle")}</p>
        <p className="qb-library-plan-note">{dictionary("planNote")}</p>
      </header>

      <Suspense fallback={<p className="qb-muted">Loading strategies…</p>}>
        <LibraryContent
          locale={locale}
          pageParam={query.page}
          q={query.q}
          market={query.market ? displayToken(query.market) : undefined}
          region={query.region ? displayToken(query.region) : undefined}
          assetClass={query.assetClass ? displayToken(query.assetClass) : undefined}
          plan={query.plan === "paid" || query.plan === "free" ? query.plan : undefined}
          collection={
            query.collection === "collected" || query.collection === "not_collected"
              ? query.collection
              : undefined
          }
          userId={session?.user?.id ?? null}
        />
      </Suspense>
    </div>
  );
}
