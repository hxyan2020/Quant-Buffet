import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { pageMetadata } from "@/lib/seo";

type PageProps = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "/contact",
    title: seo("contactTitle"),
    description: seo("contactDescription"),
  });
}

export default async function ContactPage({ params }: PageProps) {
  const { locale } = await params;
  const legal = await getTranslations({ locale, namespace: "legal" });
  const footer = await getTranslations({ locale, namespace: "footer" });

  return (
    <article className="qb-page qb-legal-page">
      <header className="qb-page-header">
        <p className="qb-page-eyebrow">{footer("contact")}</p>
        <h1 className="qb-page-title">{legal("contactTitle")}</h1>
      </header>
      <div className="qb-card qb-legal-body">
        <p className="qb-legal-copy">{legal("contactBody")}</p>
        <ul className="qb-legal-contacts">
          <li>
            <span className="qb-paper-meta-label">Telegram</span>
            <a className="qb-accent-link" href="https://t.me/+6588023346">
              +65 88023346
            </a>
          </li>
          <li>
            <span className="qb-paper-meta-label">Email</span>
            <a className="qb-accent-link" href="mailto:hola@quantbuffet.com">
              hola@quantbuffet.com
            </a>
          </li>
        </ul>
      </div>
    </article>
  );
}
