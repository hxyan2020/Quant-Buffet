import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { pageMetadata } from "@/lib/seo";

type PageProps = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "/terms",
    title: seo("termsTitle"),
    description: seo("termsDescription"),
  });
}

export default async function TermsPage({ params }: PageProps) {
  const { locale } = await params;
  const legal = await getTranslations({ locale, namespace: "legal" });
  const footer = await getTranslations({ locale, namespace: "footer" });

  return (
    <article className="qb-page qb-legal-page">
      <header className="qb-page-header">
        <p className="qb-page-eyebrow">{footer("terms")}</p>
        <h1 className="qb-page-title">{legal("termsTitle")}</h1>
      </header>
      <div className="qb-card qb-legal-body">
        {legal("termsBody")
          .split(/\n\n+/)
          .map((para) => (
            <p key={para.slice(0, 48)} className="qb-legal-copy">
              {para}
            </p>
          ))}
      </div>
    </article>
  );
}
