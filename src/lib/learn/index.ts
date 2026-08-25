import type { LearnLesson } from "./types";
import { EN_LESSONS, getEnLesson } from "./content/en";
import { ZH_LESSONS, getZhLesson } from "./content/zh";

export function getLessons(locale: string): LearnLesson[] {
  const list = locale === "zh" ? ZH_LESSONS : EN_LESSONS;
  return [...list].sort((a, b) => a.order - b.order);
}

export function getLesson(locale: string, slug: string): LearnLesson | undefined {
  return locale === "zh" ? getZhLesson(slug) : getEnLesson(slug);
}

export function getAllLessonSlugs(): string[] {
  return EN_LESSONS.map((l) => l.slug);
}

export const LEARN_BASE = "/learn";

export function learnPath(locale: string, slug?: string): string {
  const base = `/${locale}${LEARN_BASE}`;
  return slug ? `${base}/${slug}` : base;
}
