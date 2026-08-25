import type { Metadata } from "next";
import { redirect } from "next/navigation";
import { getTranslations } from "next-intl/server";

import { pageMetadata } from "@/lib/seo";

type PageProps = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ next?: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "/login",
    title: seo("loginTitle"),
    description: seo("loginDescription"),
    noIndex: true,
  });
}

export default async function LoginPage({ params, searchParams }: PageProps) {
  const { locale } = await params;
  const query = await searchParams;
  const next = query.next ? `&next=${encodeURIComponent(query.next)}` : "";
  redirect(`/${locale}?auth=login${next}`);
}
