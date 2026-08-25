import type { Metadata } from "next";
import fs from "fs";
import path from "path";
import Link from "next/link";
import { notFound } from "next/navigation";

import LabStrategyList from "@/components/LabStrategyList";
import { draftPreviewEnabled, loadLabIndex } from "@/lib/draft-preview";

type PageProps = {
  params: Promise<{ locale: string }>;
};

export const metadata: Metadata = {
  title: "Lab preview — full strategy list (unpublished)",
  robots: { index: false, follow: false },
};

function loadSlimRows() {
  const staticPath = path.join(process.cwd(), "public", "draft-lab-list.json");
  if (fs.existsSync(staticPath)) {
    try {
      return JSON.parse(fs.readFileSync(staticPath, "utf8")) as {
        library: number;
        new100: number;
        strategies: Array<{
          source: "library" | "new100";
          slug: string;
          locale: string;
          title: string;
          template?: string | null;
          annualisedReturn?: string | null;
          sharpeRatio?: string | null;
          maxDrawdown?: string | null;
          href: string;
        }>;
      };
    } catch {
      // fall through
    }
  }
  const idx = loadLabIndex();
  return {
    library: idx.library,
    new100: idx.new100,
    strategies: idx.strategies.map((s) => ({
      source: s.source,
      slug: s.slug,
      locale: s.locale,
      title: s.title,
      template: s.template,
      annualisedReturn: s.annualisedReturn,
      sharpeRatio: s.sharpeRatio,
      maxDrawdown: s.maxDrawdown,
      href: s.href,
    })),
  };
}

export default async function DraftPreviewIndex({ params }: PageProps) {
  const { locale } = await params;
  if (!draftPreviewEnabled()) notFound();

  const idx = loadLabIndex();
  const slim = loadSlimRows();

  return (
    <div className="qb-article" style={{ maxWidth: 1100, margin: "0 auto", padding: "24px 16px 64px" }}>
      <header className="qb-article-header">
        <p className="qb-article-meta">
          <span className="qb-article-badge qb-article-badge-paid">TEMP LAB PREVIEW</span>
          {" · "}
          Not published · noindex · Quant Buffet backtest lab on every strategy
        </p>
        <h1 className="qb-article-title">Full strategy list</h1>
        <p className="qb-article-summary-text">
          <strong>{idx.count}</strong> strategies (
          <strong>{idx.library}</strong> library + <strong>{idx.new100}</strong> new academic drafts).
          Open any row for the onsite IDE: edit Python, run backtests, and view live equity /
          drawdown / metrics charts. Production library URLs are untouched.{" "}
          <Link href={`/${locale}/draft-preview/scrape`}>How the new 100 papers were scraped</Link>
        </p>
      </header>

      <LabStrategyList
        rows={slim.strategies}
        libraryCount={slim.library}
        new100Count={slim.new100}
      />
    </div>
  );
}
