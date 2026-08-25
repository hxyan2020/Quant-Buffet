import type { MetadataRoute } from "next";

import { getAllDocSlugs } from "@/lib/api-docs";
import { getAllLessonSlugs } from "@/lib/learn";
import prisma from "@/lib/prisma";
import { SITE_URL, LOCALES, INDEXABLE_PATHS, absoluteUrl, localePath } from "@/lib/seo";
import { canonicalSlug } from "@/lib/slug";

export const dynamic = "force-dynamic";
export const revalidate = 3600;

function hreflangLinks(path: string) {
  return [
    ...LOCALES.map((locale) => ({
      language: locale,
      url: absoluteUrl(localePath(locale, path)),
    })),
    { language: "x-default", url: absoluteUrl(localePath("en", path)) },
  ];
}

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date();
  const entries: MetadataRoute.Sitemap = [];

  for (const path of INDEXABLE_PATHS) {
    for (const locale of LOCALES) {
      entries.push({
        url: absoluteUrl(localePath(locale, path)),
        lastModified: now,
        changeFrequency: path === "" || path === "/strategy-library" ? "daily" : "weekly",
        priority: path === "" ? 1 : path === "/strategy-library" ? 0.9 : 0.7,
        alternates: { languages: Object.fromEntries(hreflangLinks(path).map((l) => [l.language, l.url])) },
      });
    }
  }

  for (const slug of getAllDocSlugs()) {
    const path = `/docs/${slug}`;
    for (const locale of LOCALES) {
      entries.push({
        url: absoluteUrl(localePath(locale, path)),
        lastModified: now,
        changeFrequency: "monthly",
        priority: 0.65,
        alternates: { languages: Object.fromEntries(hreflangLinks(path).map((l) => [l.language, l.url])) },
      });
    }
  }

  for (const slug of getAllLessonSlugs()) {
    const path = `/learn/${slug}`;
    for (const locale of LOCALES) {
      entries.push({
        url: absoluteUrl(localePath(locale, path)),
        lastModified: now,
        changeFrequency: "monthly",
        priority: 0.75,
        alternates: { languages: Object.fromEntries(hreflangLinks(path).map((l) => [l.language, l.url])) },
      });
    }
  }

  const strategies = await prisma.strategy.findMany({
    where: { published: true, archived: false },
    select: { slug: true, locale: true, updatedAt: true },
    orderBy: { updatedAt: "desc" },
  });

  // Pair EN/ZH by canonical slug when both exist for hreflang clusters.
  const bySlug = new Map<string, { en?: string; zh?: string; updatedAt: Date }>();
  for (const row of strategies) {
    const key = canonicalSlug(row.slug);
    const cur = bySlug.get(key) ?? { updatedAt: row.updatedAt };
    if (row.locale === "zh") cur.zh = key;
    else cur.en = key;
    if (row.updatedAt > cur.updatedAt) cur.updatedAt = row.updatedAt;
    bySlug.set(key, cur);
  }

  for (const row of strategies) {
    const key = canonicalSlug(row.slug);
    const pair = bySlug.get(key);
    const path = `/strategies/${encodeURIComponent(key)}`;
    const languages: Record<string, string> = {};
    if (pair?.en) languages.en = absoluteUrl(localePath("en", `/strategies/${encodeURIComponent(pair.en)}`));
    if (pair?.zh) languages.zh = absoluteUrl(localePath("zh", `/strategies/${encodeURIComponent(pair.zh)}`));
    if (languages.en) languages["x-default"] = languages.en;
    else if (languages.zh) languages["x-default"] = languages.zh;

    entries.push({
      url: absoluteUrl(localePath(row.locale, path)),
      lastModified: row.updatedAt,
      changeFrequency: "weekly",
      priority: 0.8,
      alternates: { languages },
    });
  }

  // Touch SITE_URL so bundlers keep the constant referenced.
  void SITE_URL;
  return entries;
}
