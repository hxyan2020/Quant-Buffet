import type { DocLocale, DocPage } from "./types";
import { EN_DOC_PAGES, getEnDocPage } from "./content/en";
import { ZH_DOC_PAGES, getZhDocPage } from "./content/zh";

export function getDocPages(locale: string): DocPage[] {
  return locale === "zh" ? [...ZH_DOC_PAGES].sort((a, b) => a.order - b.order) : [...EN_DOC_PAGES].sort((a, b) => a.order - b.order);
}

export function getDocPage(locale: string, slug: string): DocPage | undefined {
  return locale === "zh" ? getZhDocPage(slug) : getEnDocPage(slug);
}

export function getAllDocSlugs(): string[] {
  return EN_DOC_PAGES.map((p) => p.slug);
}

export function docLocale(locale: string): DocLocale {
  return locale === "zh" ? "zh" : "en";
}

export const DOCS_BASE = "/docs";

export function docsPath(locale: string, slug?: string): string {
  const base = `/${locale}${DOCS_BASE}`;
  return slug ? `${base}/${slug}` : base;
}
