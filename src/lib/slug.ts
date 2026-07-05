import prisma from "@/lib/prisma";

/**
 * WordPress exports often store post_name as percent-encoded UTF-8 (%e8%82%a1...).
 * URLs must use a single encoding pass; lookups must compare canonical (decoded) forms.
 */
export function canonicalSlug(slug: string): string {
  let current = slug.trim();
  for (let attempt = 0; attempt < 5; attempt++) {
    if (!/%[0-9A-Fa-f]{2}/.test(current)) {
      break;
    }
    try {
      const decoded = decodeURIComponent(current.replace(/\+/g, " "));
      if (decoded === current) {
        break;
      }
      current = decoded;
    } catch {
      break;
    }
  }
  return current;
}

/** Build a strategy detail URL path segment (encoded once). */
export function strategyHref(locale: string, slug: string): string {
  const canonical = canonicalSlug(slug);
  return `/${locale}/strategies/${encodeURIComponent(canonical)}`;
}

const strategySelect = {
  id: true,
  slug: true,
  locale: true,
  title: true,
  teaser: true,
  summary: true,
  contentHtml: true,
  backtestMetrics: true,
  volatility: true,
  beta: true,
  sortinoRatio: true,
  maxDrawdown: true,
  winRate: true,
  annualisedReturn: true,
  sharpeRatio: true,
  region: true,
  market: true,
  assetClass: true,
  frequency: true,
  metaTitle: true,
  metaDescription: true,
  isPaywalled: true,
  paperTitle: true,
  paperAuthors: true,
  paperInstitute: true,
  paperAffiliationsJson: true,
  academicLink: true,
  economicRationale: true,
  pythonCodeHtml: true,
  sortOrder: true,
  published: true,
} as const;

/** Resolve a strategy by locale + slug from the URL (handles WP encoding + double-encoding). */
export async function findPublishedStrategy(locale: string, slugParam: string) {
  const target = canonicalSlug(slugParam);

  const exact = await prisma.strategy.findFirst({
    where: {
      locale,
      published: true,
      OR: [{ slug: slugParam }, { slug: target }],
    },
    select: strategySelect,
  });
  if (exact && canonicalSlug(exact.slug) === target) {
    return exact;
  }

  const candidates = await prisma.strategy.findMany({
    where: { locale, published: true },
    select: strategySelect,
  });

  return candidates.find((row) => canonicalSlug(row.slug) === target) ?? null;
}
