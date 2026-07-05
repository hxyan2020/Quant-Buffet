import { detectPythonCode, strategyCodeBlob } from "@/lib/detect-python";
import prisma from "@/lib/prisma";
import { canonicalTokenKey, tokenMatchesField } from "@/lib/strategy-tokens";

export type AdminStrategyFilters = {
  q?: string;
  locale?: string;
  paywall?: "" | "yes" | "no";
  published?: "" | "yes" | "no";
  python?: "" | "yes" | "no";
  region?: string;
  market?: string;
  assetClass?: string;
  createdMin?: string;
  createdMax?: string;
  updatedMin?: string;
  updatedMax?: string;
};

function parseDayStart(isoDate: string): Date | null {
  if (!isoDate.trim()) return null;
  const d = new Date(`${isoDate}T00:00:00.000Z`);
  return Number.isNaN(d.getTime()) ? null : d;
}

function parseDayEnd(isoDate: string): Date | null {
  if (!isoDate.trim()) return null;
  const d = new Date(`${isoDate}T23:59:59.999Z`);
  return Number.isNaN(d.getTime()) ? null : d;
}

export async function listAdminStrategies(filters: AdminStrategyFilters = {}) {
  const where: Record<string, unknown> = {};

  if (filters.locale === "en" || filters.locale === "zh") {
    where.locale = filters.locale;
  }
  if (filters.paywall === "yes") where.isPaywalled = true;
  if (filters.paywall === "no") where.isPaywalled = false;
  if (filters.published === "yes") where.published = true;
  if (filters.published === "no") where.published = false;
  if (filters.python === "yes") where.hasPythonCode = true;
  if (filters.python === "no") where.hasPythonCode = false;

  const createdGte = filters.createdMin ? parseDayStart(filters.createdMin) : null;
  const createdLte = filters.createdMax ? parseDayEnd(filters.createdMax) : null;
  if (createdGte || createdLte) {
    where.createdAt = {
      ...(createdGte ? { gte: createdGte } : {}),
      ...(createdLte ? { lte: createdLte } : {}),
    };
  }

  const updatedGte = filters.updatedMin ? parseDayStart(filters.updatedMin) : null;
  const updatedLte = filters.updatedMax ? parseDayEnd(filters.updatedMax) : null;
  if (updatedGte || updatedLte) {
    where.updatedAt = {
      ...(updatedGte ? { gte: updatedGte } : {}),
      ...(updatedLte ? { lte: updatedLte } : {}),
    };
  }

  const rows = await prisma.strategy.findMany({
    where,
    orderBy: [{ updatedAt: "desc" }, { title: "asc" }],
  });

  const needle = filters.q?.trim().toLowerCase() ?? "";

  return rows.filter((row) => {
    if (needle && !row.title.toLowerCase().includes(needle) && !row.slug.toLowerCase().includes(needle)) {
      return false;
    }
    if (filters.region && !tokenMatchesField(row.region, filters.region)) return false;
    if (filters.market && !tokenMatchesField(row.market, filters.market)) return false;
    if (filters.assetClass && !tokenMatchesField(row.assetClass, filters.assetClass)) return false;
    return true;
  });
}

export async function scanAllStrategiesForPython() {
  const rows = await prisma.strategy.findMany({
    select: { id: true, contentHtml: true },
  });
  let yes = 0;
  for (const row of rows) {
    const has = detectPythonCode(strategyCodeBlob(row.contentHtml));
    await prisma.strategy.update({
      where: { id: row.id },
      data: { hasPythonCode: has },
    });
    if (has) yes++;
  }
  return { total: rows.length, withPython: yes };
}

export async function setHalfFreePerLocale() {
  let updated = 0;
  for (const locale of ["en", "zh"] as const) {
    const rows = await prisma.strategy.findMany({
      where: { locale, published: true },
      orderBy: [{ sortOrder: "asc" }, { createdAt: "asc" }],
      select: { id: true },
    });
    const freeCount = Math.ceil(rows.length / 2);
    for (let i = 0; i < rows.length; i++) {
      await prisma.strategy.update({
        where: { id: rows[i].id },
        data: { isPaywalled: i >= freeCount },
      });
      updated++;
    }
  }
  return updated;
}

export function getAdminFilterOptions(rows: Awaited<ReturnType<typeof listAdminStrategies>>) {
  const regions = new Set<string>();
  const markets = new Set<string>();
  const assetClasses = new Set<string>();
  for (const row of rows) {
    if (row.region) regions.add(row.region);
    if (row.market) markets.add(row.market);
    if (row.assetClass) assetClasses.add(row.assetClass);
  }
  return {
    regions: [...regions].sort(),
    markets: [...markets].sort(),
    assetClasses: [...assetClasses].sort(),
  };
}

/** Distinct canonical filter labels from all strategies (for dropdowns). */
export async function loadAdminFilterOptionSets() {
  const rows = await prisma.strategy.findMany({
    select: { region: true, market: true, assetClass: true },
  });
  const { collectDistinctTokens } = await import("@/lib/strategy-tokens");
  return {
    regions: collectDistinctTokens(rows.map((r) => ({ value: r.region }))),
    markets: collectDistinctTokens(rows.map((r) => ({ value: r.market }))),
    assetClasses: collectDistinctTokens(rows.map((r) => ({ value: r.assetClass }))),
  };
}
