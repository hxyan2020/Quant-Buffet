import prisma from "@/lib/prisma";
import { collectDistinctTokens, splitFilterTokens, tokenMatchesField } from "@/lib/strategy-tokens";

export const STRATEGIES_PAGE_SIZE = 50;

export type StrategyListFilters = {
  locale: string;
  q?: string;
  page?: number;
  market?: string;
  region?: string;
  assetClass?: string;
  /** paid | free */
  plan?: string;
  /** collected | not_collected */
  collection?: string;
  collectedIds?: Set<string>;
};

const listSelect = {
  id: true,
  slug: true,
  title: true,
  annualisedReturn: true,
  sharpeRatio: true,
  region: true,
  market: true,
  assetClass: true,
  frequency: true,
  isPaywalled: true,
} as const;

export async function countPublishedStrategies(locale: string) {
  return prisma.strategy.count({
    where: { locale, published: true },
  });
}

export async function getLibraryFilterOptions(locale: string) {
  const rows = await prisma.strategy.findMany({
    where: { locale, published: true },
    select: { market: true, region: true, assetClass: true },
  });
  return {
    markets: collectDistinctTokens(rows.map((r) => ({ value: r.market }))),
    regions: collectDistinctTokens(rows.map((r) => ({ value: r.region }))),
    assetClasses: collectDistinctTokens(rows.map((r) => ({ value: r.assetClass }))),
  };
}

function matchesTextQuery(
  row: {
    title: string;
    slug: string;
    region: string | null;
    market: string | null;
    assetClass: string | null;
  },
  q: string,
) {
  const needle = q.trim().toLowerCase();
  if (!needle) return true;
  const hay = [
    row.title,
    row.slug,
    row.region ?? "",
    row.market ?? "",
    row.assetClass ?? "",
    ...splitFilterTokens(row.assetClass),
    ...splitFilterTokens(row.market),
  ]
    .join(" ")
    .toLowerCase();
  return hay.includes(needle);
}

export async function listStrategies({
  locale,
  q,
  page = 1,
  market,
  region,
  assetClass,
  plan,
  collection,
  collectedIds,
}: StrategyListFilters) {
  const safePage = Math.max(1, page);

  const rows = await prisma.strategy.findMany({
    where: { locale, published: true },
    orderBy: [{ sortOrder: "asc" }, { title: "asc" }],
    select: listSelect,
  });

  const filtered = rows.filter((row) => {
    if (!matchesTextQuery(row, q ?? "")) return false;
    if (market && !tokenMatchesField(row.market, market)) return false;
    if (region && !tokenMatchesField(row.region, region)) return false;
    if (assetClass && !tokenMatchesField(row.assetClass, assetClass)) return false;
    if (plan === "paid" && !row.isPaywalled) return false;
    if (plan === "free" && row.isPaywalled) return false;
    if (collection === "collected" && !collectedIds?.has(row.id)) return false;
    if (collection === "not_collected" && collectedIds?.has(row.id)) return false;
    return true;
  });

  const total = filtered.length;
  const start = (safePage - 1) * STRATEGIES_PAGE_SIZE;
  const pageRows = filtered.slice(start, start + STRATEGIES_PAGE_SIZE);

  return {
    rows: pageRows,
    total,
    page: safePage,
    pageSize: STRATEGIES_PAGE_SIZE,
    totalPages: Math.max(1, Math.ceil(total / STRATEGIES_PAGE_SIZE)),
    filterOptions: {
      markets: collectDistinctTokens(rows.map((r) => ({ value: r.market }))),
      regions: collectDistinctTokens(rows.map((r) => ({ value: r.region }))),
      assetClasses: collectDistinctTokens(rows.map((r) => ({ value: r.assetClass }))),
    },
  };
}
