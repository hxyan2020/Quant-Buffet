import Link from "next/link";

import LearnRenderer from "@/components/learn/LearnRenderer";
import { getLessons, learnPath } from "@/lib/learn";
import type { LearnLesson } from "@/lib/learn/types";

type Props = {
  locale: string;
  lesson: LearnLesson | null;
  indexTitle: string;
  indexSubtitle: string;
  navLabel: string;
  lessonLabel: string;
  durationLabel: string;
  startLabel: string;
};

export default function LearnShell({
  locale,
  lesson,
  indexTitle,
  indexSubtitle,
  navLabel,
  lessonLabel,
  durationLabel,
  startLabel,
}: Props) {
  const lessons = getLessons(locale);
  const isIndex = !lesson;

  return (
    <div className="qb-learn-layout">
      <aside className="qb-learn-sidebar" aria-label={navLabel}>
        <p className="qb-learn-sidebar-label">{navLabel}</p>
        <nav className="qb-learn-nav">
          <Link href={learnPath(locale)} className={`qb-learn-nav-link${isIndex ? " is-active" : ""}`}>
            {indexTitle}
          </Link>
          {lessons.map((l) => (
            <Link
              key={l.slug}
              href={learnPath(locale, l.slug)}
              className={`qb-learn-nav-link${lesson?.slug === l.slug ? " is-active" : ""}`}
            >
              <span className="qb-learn-nav-num">{l.order}</span>
              {l.title}
            </Link>
          ))}
        </nav>
        <Link href={`/${locale}/docs`} className="qb-learn-api-link">
          API reference →
        </Link>
      </aside>

      <article className="qb-learn-main">
        {isIndex ? (
          <>
            <header className="qb-learn-hero">
              <p className="qb-page-eyebrow">Quant Buffet Academy</p>
              <h1 className="qb-learn-hero-title">{indexTitle}</h1>
              <p className="qb-learn-hero-sub">{indexSubtitle}</p>
            </header>
            <div className="qb-learn-lesson-grid">
              {lessons.map((l) => (
                <Link key={l.slug} href={learnPath(locale, l.slug)} className="qb-learn-lesson-card">
                  <div className="qb-learn-lesson-card-head">
                    <span className="qb-learn-lesson-badge">
                      {lessonLabel} {l.order}
                    </span>
                    <span className="qb-learn-lesson-duration">
                      {durationLabel}: {l.duration}
                    </span>
                  </div>
                  <h2 className="qb-learn-lesson-title">{l.title}</h2>
                  <p className="qb-learn-lesson-sub">{l.subtitle}</p>
                  <ul className="qb-learn-lesson-topics">
                    {l.topics.map((t) => (
                      <li key={t}>{t}</li>
                    ))}
                  </ul>
                  <span className="qb-learn-lesson-cta">{startLabel} →</span>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <>
            <header className="qb-learn-lesson-header">
              <p className="qb-page-eyebrow">
                {lessonLabel} {lesson.order} · {lesson.duration}
              </p>
              <h1 className="qb-learn-lesson-page-title">{lesson.title}</h1>
              <p className="qb-learn-lesson-page-sub">{lesson.subtitle}</p>
              <div className="qb-learn-topic-pills">
                {lesson.topics.map((t) => (
                  <span key={t} className="qb-learn-topic-pill">
                    {t}
                  </span>
                ))}
              </div>
            </header>
            <div className="qb-learn-content qb-card">
              <LearnRenderer blocks={lesson.blocks} />
            </div>
            <footer className="qb-docs-footer-nav">
              {(() => {
                const idx = lessons.findIndex((l) => l.slug === lesson.slug);
                const prev = idx > 0 ? lessons[idx - 1] : null;
                const next = idx >= 0 && idx < lessons.length - 1 ? lessons[idx + 1] : null;
                return (
                  <>
                    {prev ? (
                      <Link href={learnPath(locale, prev.slug)} className="qb-docs-pager qb-docs-pager-prev">
                        ← {prev.title}
                      </Link>
                    ) : (
                      <span />
                    )}
                    {next ? (
                      <Link href={learnPath(locale, next.slug)} className="qb-docs-pager qb-docs-pager-next">
                        {next.title} →
                      </Link>
                    ) : null}
                  </>
                );
              })()}
            </footer>
          </>
        )}
      </article>
    </div>
  );
}
