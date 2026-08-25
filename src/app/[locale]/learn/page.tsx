import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import LearnShell from "@/components/learn/LearnShell";
import { pageMetadata } from "@/lib/seo";

type PageProps = { params: Promise<{ locale: string }> };

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "/learn",
    title: seo("learnTitle"),
    description: seo("learnDescription"),
  });
}

export default async function LearnIndexPage({ params }: PageProps) {
  const { locale } = await params;
  const learn = await getTranslations({ locale, namespace: "learn" });

  return (
    <LearnShell
      locale={locale}
      lesson={null}
      indexTitle={learn("indexTitle")}
      indexSubtitle={learn("indexSubtitle")}
      navLabel={learn("navLabel")}
      lessonLabel={learn("lessonLabel")}
      durationLabel={learn("durationLabel")}
      startLabel={learn("startLabel")}
    />
  );
}
