import fs from "fs";
import path from "path";
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";

import { draftPreviewEnabled } from "@/lib/draft-preview";

type PageProps = { params: Promise<{ locale: string }> };

export const metadata: Metadata = {
  title: "How the new 100 papers were scraped",
  robots: { index: false, follow: false },
};

type RawPaper = {
  title?: string;
  year?: number;
  venue?: string;
  url?: string;
  source?: string;
  _query?: string;
  _score?: number;
  _slug?: string;
  citationCount?: number;
};

export default async function ScrapeMethodPage({ params }: PageProps) {
  const { locale } = await params;
  if (!draftPreviewEnabled()) notFound();

  const rawPath = path.join(process.cwd(), "backtest", "drafts", "new_100", "papers_raw.json");
  const raw = JSON.parse(fs.readFileSync(rawPath, "utf8")) as { papers: RawPaper[] };
  const papers = raw.papers || [];
  const bySource: Record<string, number> = {};
  for (const p of papers) {
    const s = p.source || "unknown";
    bySource[s] = (bySource[s] || 0) + 1;
  }

  return (
    <div className="qb-article" style={{ maxWidth: 960, margin: "0 auto", padding: "24px 16px 64px" }}>
      <p className="qb-article-meta">
        <Link href={`/${locale}/draft-preview`}>← Full list</Link>
        {" · "}
        TEMP LAB · not published
      </p>
      <h1 className="qb-article-title">How the new 100 strategies were scraped</h1>

      <section className="qb-strategy-section">
        <h2 className="qb-strategy-section-title">Where</h2>
        <p>
          Official APIs only — no brittle SSRN HTML. Existing Quant Buffet papers are ~67% SSRN
          links; those pages CAPTCHA and change layout, so discovery used:
        </p>
        <ul>
          <li>
            <strong>OpenAlex</strong> <code>https://api.openalex.org/works</code> — {bySource.openalex ?? 0}{" "}
            papers (DOI, venue, institutions, OA PDF)
          </li>
          <li>
            <strong>arXiv</strong> <code>http://export.arxiv.org/api/query</code> — {bySource.arxiv ?? 0}{" "}
            papers, categories <code>q-fin.PM</code> (portfolio management) and{" "}
            <code>q-fin.TR</code> (trading)
          </li>
          <li>
            <strong>Semantic Scholar</strong> — {bySource.semanticscholar ?? 0} papers kept from an earlier
            pass; later queries hit HTTP 429 so OpenAlex + arXiv filled the rest
          </li>
        </ul>
      </section>

      <section className="qb-strategy-section">
        <h2 className="qb-strategy-section-title">How</h2>
        <ol>
          <li>
            Dedup against the live library: titles, slugs, SSRN IDs, DOIs, arXiv IDs, links (
            <code>backtest/results/existing_papers_dedup.json</code>).
          </li>
          <li>
            Run theme queries (momentum, dual momentum, sector rotation, vol-managed, carry, risk
            parity, trend following, ETF allocation, crypto momentum, …).
          </li>
          <li>
            Score title+abstract for implementability (ETF / strategy / portfolio keywords; penalize
            surveys, HFT, order-book). Recency and citations add a small bonus.
          </li>
          <li>
            Keep the top 100 novel papers → <code>backtest/drafts/new_100/papers_raw.json</code>.
          </li>
          <li>
            Map each paper to a Quant Buffet template + liquid ETF book, generate post JSON + in-house
            backtest (<code>scripts/generate_new_100_drafts.py</code>). Not inserted into Prisma.
          </li>
        </ol>
        <p>
          Runner: <code>python scripts/scrape_new_strategy_papers.py</code>
        </p>
      </section>

      <section className="qb-strategy-section">
        <h2 className="qb-strategy-section-title">All 100 papers (API · query · link)</h2>
        <div style={{ overflowX: "auto" }}>
          <table className="qb-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ textAlign: "left", borderBottom: "1px solid rgba(159,179,207,0.35)" }}>
                <th style={{ padding: "8px 6px" }}>#</th>
                <th style={{ padding: "8px 6px" }}>API</th>
                <th style={{ padding: "8px 6px" }}>Year</th>
                <th style={{ padding: "8px 6px" }}>Title</th>
                <th style={{ padding: "8px 6px" }}>Matched query</th>
              </tr>
            </thead>
            <tbody>
              {papers.map((p, i) => (
                <tr key={`${p._slug || i}`} style={{ borderBottom: "1px solid rgba(159,179,207,0.12)" }}>
                  <td style={{ padding: "7px 6px", opacity: 0.65 }}>{i + 1}</td>
                  <td style={{ padding: "7px 6px" }}>{p.source}</td>
                  <td style={{ padding: "7px 6px" }}>{p.year ?? "—"}</td>
                  <td style={{ padding: "7px 6px" }}>
                    {p._slug ? (
                      <Link href={`/${locale}/draft-preview/${encodeURIComponent(p._slug)}`}>
                        {p.title}
                      </Link>
                    ) : (
                      p.title
                    )}
                    {p.url ? (
                      <div style={{ fontSize: 11, opacity: 0.65, marginTop: 2 }}>
                        <a href={p.url} target="_blank" rel="noreferrer">
                          {p.url}
                        </a>
                      </div>
                    ) : null}
                  </td>
                  <td style={{ padding: "7px 6px", fontSize: 12 }}>{p._query || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
