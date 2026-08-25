import type { Metadata } from "next";

export const SITE_URL = (process.env.AUTH_URL ?? "https://www.quantbuffet.com").replace(/\/$/, "");
export const SITE_NAME = "Quant Buffet";
export const DEFAULT_OG_IMAGE = `${SITE_URL}/icon.svg`;

export const LOCALES = ["en", "zh"] as const;
export type SeoLocale = (typeof LOCALES)[number];

/** Static public paths under /[locale]/… (no leading locale). Account routes are noindex. */
export const INDEXABLE_PATHS = [
  "",
  "/strategy-library",
  "/learn",
  "/docs",
  "/pricing",
  "/contact",
  "/terms",
] as const;

export function absoluteUrl(path: string): string {
  if (!path || path === "/") return SITE_URL;
  return `${SITE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function localePath(locale: string, path = ""): string {
  const clean = path === "/" ? "" : path;
  return `/${locale}${clean}`;
}

export function buildAlternates(locale: string, path = "") {
  const languages: Record<string, string> = {};
  for (const loc of LOCALES) {
    languages[loc] = absoluteUrl(localePath(loc, path));
  }
  languages["x-default"] = absoluteUrl(localePath("en", path));
  return {
    canonical: absoluteUrl(localePath(locale, path)),
    languages,
  };
}

function clip(text: string, max: number): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  const sliced = clean.slice(0, max - 1);
  const lastSpace = sliced.lastIndexOf(" ");
  return `${(lastSpace > 40 ? sliced.slice(0, lastSpace) : sliced).trim()}…`;
}

export type StrategySeoInput = {
  title: string;
  locale: string;
  slug: string;
  teaser?: string | null;
  summary?: string | null;
  assetClass?: string | null;
  region?: string | null;
  market?: string | null;
  frequency?: string | null;
  annualisedReturn?: string | null;
  sharpeRatio?: string | null;
  metaTitle?: string | null;
  metaDescription?: string | null;
  paperTitle?: string | null;
};

function metricBit(label: string, value?: string | null): string | null {
  if (!value?.trim() || value.trim().toUpperCase() === "N/A") return null;
  return `${label} ${value.trim()}`;
}

function looksWeakMetaTitle(title: string, strategyTitle: string): boolean {
  const t = title.trim();
  if (t.length < 24) return true;
  if (/Academic .+\|/.test(t) && t.length < 40) return true;
  // Truncated mid-token (e.g. "… | Equi", "… | bo")
  if (/\|\s*[A-Za-z]{1,6}$/.test(t) && !/\bQuant Buffet\b/i.test(t)) return true;
  if (t === strategyTitle) return true;
  return false;
}

function looksWeakMetaDescription(desc: string): boolean {
  const d = desc.trim();
  if (d.length < 80) return true;
  if (/^n\/a$/i.test(d)) return true;
  if (/Academic .+ strategy with economic rationale/i.test(d)) return true;
  if (/Topics:\s*$/i.test(d) || /Topics:\s*\w+\.\.\.?$/i.test(d)) return true;
  return false;
}

/**
 * Build keyword-rich strategy title/description from research fields.
 * Regenerates when stored WordPress/legacy meta is truncated or templated.
 */
export function buildStrategySeo(strategy: StrategySeoInput): {
  title: string;
  description: string;
  keywords: string[];
} {
  const isZh = strategy.locale === "zh";
  const asset = strategy.assetClass?.split(",")[0]?.trim() || (isZh ? "多资产" : "multi-asset");
  const region = strategy.region?.trim() || (isZh ? "全球" : "global");
  const market = strategy.market?.trim() || (isZh ? "市场" : "markets");
  const freq = strategy.frequency?.trim();

  const sharpe = metricBit(isZh ? "夏普" : "Sharpe", strategy.sharpeRatio);
  const ann = metricBit(isZh ? "年化" : "ann.", strategy.annualisedReturn);

  // Always compose titles from structured fields so brand is never truncated/doubled.
  const core = clip(
    isZh ? `${strategy.title}｜${asset}量化策略` : `${strategy.title} | ${asset} Quant Strategy`,
    48,
  );
  const title = `${core} | ${SITE_NAME}`;

  const storedDesc = strategy.metaDescription?.trim();
  let description: string;
  if (storedDesc && !looksWeakMetaDescription(storedDesc)) {
    description = clip(storedDesc, 160);
  } else {
    const teaserBit = strategy.teaser?.trim();
    const usefulTeaser =
      teaserBit && teaserBit.toUpperCase() !== "N/A" && teaserBit.length > 40 ?
        clip(teaserBit, 90)
      : null;
    const bits = [
      usefulTeaser,
      isZh ?
        `${region}${market}量化交易策略（${asset}）`
      : `${region} ${market} quant strategy (${asset})`,
      freq ? (isZh ? `调仓：${freq}` : `${freq} rebalance`) : null,
      ann,
      sharpe,
      isZh ?
        "含学术依据、经济逻辑与 QuantConnect/LEAN Python 实现。"
      : "Academic rationale + QuantConnect/LEAN Python implementation.",
    ].filter(Boolean) as string[];
    description = clip(bits.join(" · "), 160);
  }

  const keywords = [
    strategy.title,
    isZh ? "量化交易策略" : "quantitative trading strategy",
    isZh ? "算法交易回测" : "algorithmic trading backtest",
    isZh ? "QuantConnect策略" : "QuantConnect LEAN strategy",
    isZh ? "动量均值回归" : "momentum mean reversion",
    asset,
    region,
    market,
    freq,
    strategy.paperTitle,
  ].filter((k): k is string => Boolean(k && k.trim() && k.trim().toUpperCase() !== "N/A"));

  return { title, description, keywords: [...new Set(keywords)].slice(0, 12) };
}

export function pageMetadata(options: {
  locale: string;
  path?: string;
  title: string;
  description: string;
  keywords?: string[];
  noIndex?: boolean;
}): Metadata {
  const path = options.path ?? "";
  const alternates = buildAlternates(options.locale, path);
  const rawTitle = options.title.trim();
  const title =
    /\bQuant Buffet\b/i.test(rawTitle) ? rawTitle : `${clip(rawTitle, 48)} | ${SITE_NAME}`;

  return {
    title,
    description: options.description,
    keywords: options.keywords,
    alternates,
    robots: options.noIndex ?
      { index: false, follow: false, googleBot: { index: false, follow: false } }
    : { index: true, follow: true },
    openGraph: {
      type: "website",
      locale: options.locale === "zh" ? "zh_CN" : "en_US",
      url: alternates.canonical,
      siteName: SITE_NAME,
      title,
      description: options.description,
      images: [{ url: DEFAULT_OG_IMAGE, alt: SITE_NAME }],
    },
    twitter: {
      card: "summary_large_image",
      title,
      description: options.description,
      images: [DEFAULT_OG_IMAGE],
    },
  };
}

export function strategyJsonLd(strategy: StrategySeoInput & { updatedAt?: Date | string | null }) {
  const seo = buildStrategySeo(strategy);
  const url = absoluteUrl(localePath(strategy.locale, `/strategies/${encodeURIComponent(strategy.slug)}`));
  return {
    "@context": "https://schema.org",
    "@type": "TechArticle",
    headline: strategy.title,
    name: seo.title,
    description: seo.description,
    inLanguage: strategy.locale === "zh" ? "zh-CN" : "en",
    url,
    mainEntityOfPage: url,
    author: { "@type": "Organization", name: SITE_NAME, url: SITE_URL },
    publisher: {
      "@type": "Organization",
      name: SITE_NAME,
      url: SITE_URL,
      logo: { "@type": "ImageObject", url: DEFAULT_OG_IMAGE },
    },
    about: [
      strategy.assetClass,
      strategy.market,
      strategy.region,
      "quantitative finance",
      "algorithmic trading",
    ].filter(Boolean),
    keywords: seo.keywords.join(", "),
    ...(strategy.updatedAt ?
      { dateModified: new Date(strategy.updatedAt).toISOString() }
    : {}),
  };
}

export function breadcrumbJsonLd(
  items: Array<{ name: string; path: string }>,
  locale: string,
) {
  return {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    itemListElement: items.map((item, index) => ({
      "@type": "ListItem",
      position: index + 1,
      name: item.name,
      item: absoluteUrl(localePath(locale, item.path)),
    })),
  };
}

export function organizationJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "Organization",
    name: SITE_NAME,
    url: SITE_URL,
    logo: DEFAULT_OG_IMAGE,
    email: "hola@quantbuffet.com",
    description:
      "Bilingual library of academic quantitative trading strategies with backtests and QuantConnect/LEAN Python implementations.",
    sameAs: [] as string[],
  };
}

export function websiteJsonLd() {
  return {
    "@context": "https://schema.org",
    "@type": "WebSite",
    name: SITE_NAME,
    url: SITE_URL,
    inLanguage: ["en", "zh-CN"],
    potentialAction: {
      "@type": "SearchAction",
      target: {
        "@type": "EntryPoint",
        urlTemplate: `${SITE_URL}/en/strategy-library?q={search_term_string}`,
      },
      "query-input": "required name=search_term_string",
    },
  };
}

export function faqJsonLd(faqs: Array<{ question: string; answer: string }>) {
  return {
    "@context": "https://schema.org",
    "@type": "FAQPage",
    mainEntity: faqs.map((faq) => ({
      "@type": "Question",
      name: faq.question,
      acceptedAnswer: { "@type": "Answer", text: faq.answer },
    })),
  };
}
