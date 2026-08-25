import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import ApiDocsShell from "@/components/api-docs/ApiDocsShell";
import { pageMetadata } from "@/lib/seo";

type PageProps = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "/docs",
    title: seo("docsTitle"),
    description: seo("docsDescription"),
  });
}

export default async function DocsIndexPage({ params }: PageProps) {
  const { locale } = await params;
  const docs = await getTranslations({ locale, namespace: "docs" });

  return (
    <ApiDocsShell
      locale={locale}
      page={null}
      indexTitle={docs("indexTitle")}
      indexSubtitle={docs("indexSubtitle")}
      navLabel={docs("navLabel")}
    />
  );
}
