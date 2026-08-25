import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import ApiDocsShell from "@/components/api-docs/ApiDocsShell";
import { getAllDocSlugs, getDocPage } from "@/lib/api-docs";
import { pageMetadata } from "@/lib/seo";

type PageProps = { params: Promise<{ locale: string; slug: string }> };

export function generateStaticParams() {
  const slugs = getAllDocSlugs();
  return ["en", "zh"].flatMap((locale) => slugs.map((slug) => ({ locale, slug })));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  const page = getDocPage(locale, slug);
  if (!page) return {};
  return pageMetadata({
    locale,
    path: `/docs/${slug}`,
    title: `${page.title} | Quant Buffet API`,
    description: page.description,
  });
}

export default async function DocsSlugPage({ params }: PageProps) {
  const { locale, slug } = await params;
  const page = getDocPage(locale, slug);
  if (!page) notFound();

  const docs = await getTranslations({ locale, namespace: "docs" });

  return (
    <ApiDocsShell
      locale={locale}
      page={page}
      indexTitle={docs("indexTitle")}
      indexSubtitle={docs("indexSubtitle")}
      navLabel={docs("navLabel")}
    />
  );
}
