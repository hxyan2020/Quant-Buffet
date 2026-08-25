import Link from "next/link";

import ApiDocRenderer from "@/components/api-docs/ApiDocRenderer";
import { docsPath, getDocPages } from "@/lib/api-docs";
import type { DocPage } from "@/lib/api-docs/types";

type Props = {
  locale: string;
  page: DocPage | null;
  indexTitle: string;
  indexSubtitle: string;
  navLabel: string;
};

export default function ApiDocsShell({ locale, page, indexTitle, indexSubtitle, navLabel }: Props) {
  const pages = getDocPages(locale);
  const isIndex = !page;

  return (
    <div className="qb-docs-layout">
      <aside className="qb-docs-sidebar" aria-label={navLabel}>
        <p className="qb-docs-sidebar-label">{navLabel}</p>
        <nav className="qb-docs-nav">
          <Link href={docsPath(locale)} className={`qb-docs-nav-link${isIndex ? " is-active" : ""}`}>
            {indexTitle}
          </Link>
          {pages.map((p) => (
            <Link
              key={p.slug}
              href={docsPath(locale, p.slug)}
              className={`qb-docs-nav-link${page?.slug === p.slug ? " is-active" : ""}`}
            >
              {p.title}
            </Link>
          ))}
        </nav>
      </aside>

      <article className="qb-docs-main">
        {isIndex ? (
          <>
            <header className="qb-docs-header">
              <p className="qb-page-eyebrow">Quant Buffet API</p>
              <h1 className="qb-docs-title">{indexTitle}</h1>
              <p className="qb-docs-lead">{indexSubtitle}</p>
            </header>
            <div className="qb-docs-card-grid">
              {pages.map((p) => (
                <Link key={p.slug} href={docsPath(locale, p.slug)} className="qb-docs-card">
                  <span className="qb-docs-card-order">{String(p.order).padStart(2, "0")}</span>
                  <h2 className="qb-docs-card-title">{p.title}</h2>
                  <p className="qb-docs-card-desc">{p.description}</p>
                </Link>
              ))}
            </div>
          </>
        ) : (
          <>
            <header className="qb-docs-header">
              <p className="qb-page-eyebrow">Quant Buffet API</p>
              <h1 className="qb-docs-title">{page.title}</h1>
              <p className="qb-docs-lead">{page.description}</p>
            </header>
            <div className="qb-docs-content qb-card">
              <ApiDocRenderer blocks={page.blocks} />
            </div>
            <footer className="qb-docs-footer-nav">
              {(() => {
                const idx = pages.findIndex((p) => p.slug === page.slug);
                const prev = idx > 0 ? pages[idx - 1] : null;
                const next = idx >= 0 && idx < pages.length - 1 ? pages[idx + 1] : null;
                return (
                  <>
                    {prev ? (
                      <Link href={docsPath(locale, prev.slug)} className="qb-docs-pager qb-docs-pager-prev">
                        ← {prev.title}
                      </Link>
                    ) : (
                      <span />
                    )}
                    {next ? (
                      <Link href={docsPath(locale, next.slug)} className="qb-docs-pager qb-docs-pager-next">
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
