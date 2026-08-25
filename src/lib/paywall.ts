import prisma from "@/lib/prisma";

/** Share of published strategies that stay free (no paid plan required). */
export const FREE_LIBRARY_SHARE = 0.2;

const UPDATE_CHUNK = 400;

export function freeCountFor(total: number, share = FREE_LIBRARY_SHARE): number {
  if (total <= 0) return 0;
  return Math.round(total * share);
}

async function updatePaywallFlags(ids: string[], isPaywalled: boolean) {
  for (let i = 0; i < ids.length; i += UPDATE_CHUNK) {
    await prisma.strategy.updateMany({
      where: { id: { in: ids.slice(i, i + UPDATE_CHUNK) } },
      data: { isPaywalled },
    });
  }
}

export type PaywallMixLocale = {
  locale: string;
  total: number;
  free: number;
  paid: number;
};

/** Mark ~20% of published strategies free per locale; the rest require a paid plan. */
export async function applyFreeLibraryShare(share = FREE_LIBRARY_SHARE): Promise<{
  updated: number;
  locales: PaywallMixLocale[];
}> {
  const locales: PaywallMixLocale[] = [];
  let updated = 0;

  for (const locale of ["en", "zh"] as const) {
    const rows = await prisma.strategy.findMany({
      where: { locale, published: true, archived: false },
      orderBy: [{ sortOrder: "asc" }, { createdAt: "asc" }],
      select: { id: true },
    });
    const freeCount = freeCountFor(rows.length, share);
    const freeIds = rows.slice(0, freeCount).map((row) => row.id);
    const paidIds = rows.slice(freeCount).map((row) => row.id);
    await updatePaywallFlags(freeIds, false);
    await updatePaywallFlags(paidIds, true);
    updated += rows.length;
    locales.push({
      locale,
      total: rows.length,
      free: freeIds.length,
      paid: paidIds.length,
    });
  }

  return { updated, locales };
}
