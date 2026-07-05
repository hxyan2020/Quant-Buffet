import Link from "next/link";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { countPublishedStrategies } from "@/lib/strategies";

type PageProps = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const brand = await getTranslations({ locale, namespace: "brand" });

  return {
    title: `${brand("name")} — ${brand("tagline")}`,
    description: `${brand("name")}: quantitative strategy research backed by academic papers.`,
  };
}

export default async function LocaleHome({ params }: PageProps) {
  const { locale } = await params;
  const home = await getTranslations({ locale, namespace: "home" });
  const count = await countPublishedStrategies(locale);
  const heroCount = count >= 800 ? "800+" : `${count}+`;
  const lines = home("heroTitle").split("\n");

  return (
    <section className="qb-hero">
      <div className="qb-hero-glow" aria-hidden />
      <div className="qb-hero-inner">
        <div className="qb-hero-title-wrap">
          <span className="qb-hero-badge">{heroCount}</span>
          <span className="qb-hero-lines">
            {lines.map((line) => (
              <span key={line} className="qb-hero-line">
                {line}
              </span>
            ))}
          </span>
        </div>

        <div className="qb-hero-cta">
          <Link href={`/${locale}/strategy-library`} className="qb-pill-primary">
            {home("browse")}
          </Link>
        </div>

        <p className="qb-hero-sub">
          {locale === "zh"
            ? `当前语料库已收录 ${count.toLocaleString()} 篇可浏览策略。`
            : `${count.toLocaleString()} published strategies available in this language.`}
        </p>
      </div>
    </section>
  );
}
