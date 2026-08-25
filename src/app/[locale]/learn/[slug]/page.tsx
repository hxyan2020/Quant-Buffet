import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTranslations } from "next-intl/server";

import LearnShell from "@/components/learn/LearnShell";
import { getAllLessonSlugs, getLesson } from "@/lib/learn";
import { pageMetadata } from "@/lib/seo";

type PageProps = { params: Promise<{ locale: string; slug: string }> };

export function generateStaticParams() {
  const slugs = getAllLessonSlugs();
  return ["en", "zh"].flatMap((locale) => slugs.map((slug) => ({ locale, slug })));
}

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale, slug } = await params;
  const lesson = getLesson(locale, slug);
  if (!lesson) return {};
  return pageMetadata({
    locale,
    path: `/learn/${slug}`,
    title: `${lesson.title} | Quant Buffet Academy`,
    description: lesson.subtitle,
  });
}

export default async function LearnLessonPage({ params }: PageProps) {
  const { locale, slug } = await params;
  const lesson = getLesson(locale, slug);
  if (!lesson) notFound();

  const learn = await getTranslations({ locale, namespace: "learn" });

  return (
    <LearnShell
      locale={locale}
      lesson={lesson}
      indexTitle={learn("indexTitle")}
      indexSubtitle={learn("indexSubtitle")}
      navLabel={learn("navLabel")}
      lessonLabel={learn("lessonLabel")}
      durationLabel={learn("durationLabel")}
      startLabel={learn("startLabel")}
    />
  );
}
