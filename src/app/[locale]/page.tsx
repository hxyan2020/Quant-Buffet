import Link from "next/link";
import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import JsonLd from "@/components/JsonLd";
import SeoFaqSection from "@/components/SeoFaqSection";
import { countPublishedStrategies } from "@/lib/strategies";
import {
  breadcrumbJsonLd,
  faqJsonLd,
  organizationJsonLd,
  pageMetadata,
  websiteJsonLd,
} from "@/lib/seo";

type PageProps = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "",
    title: seo("homeTitle"),
    description: seo("homeDescription"),
    keywords: seo("homeKeywords").split(",").map((k) => k.trim()),
  });
}

export default async function LocaleHome({ params }: PageProps) {
  const { locale } = await params;
  const home = await getTranslations({ locale, namespace: "home" });
  const seo = await getTranslations({ locale, namespace: "seo" });
  const nav = await getTranslations({ locale, namespace: "nav" });
  const count = await countPublishedStrategies(locale);
  const heroCount = count >= 800 ? "800+" : `${count}+`;
  const lines = home("heroTitle").split("\n");

  const faqs = [1, 2, 3, 4, 5].map((n) => ({
    question: seo(`faq${n}q`),
    answer: seo(`faq${n}a`),
  }));

  return (
    <>
      <JsonLd data={[organizationJsonLd(), websiteJsonLd(), faqJsonLd(faqs)]} />
      <JsonLd
        data={breadcrumbJsonLd(
          [
            { name: nav("home"), path: "" },
          ],
          locale,
        )}
      />
      <section className="qb-hero">
        <div className="qb-hero-glow" aria-hidden />
        <div className="qb-hero-inner">
          <p className="qb-hero-cadence">{home("mondayDrop")}</p>
          <div className="qb-hero-title-wrap">
            <span className="qb-hero-badge">{heroCount}</span>
            <h1 className="qb-hero-lines">
              {lines.map((line) => (
                <span key={line} className="qb-hero-line">
                  {line}
                </span>
              ))}
            </h1>
          </div>

          <p className="qb-hero-seo-sub">{home("heroSub")}</p>

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

      <SeoFaqSection title={seo("faqTitle")} faqs={faqs} />
    </>
  );
}
