/**
 * Archive all current production strategies (flag only — no deletes),
 * then publish every temp-lab strategy (lab_index: library + new100) as active.
 *
 * Usage:
 *   npx tsx scripts/promote-lab-to-production.ts
 *   npx tsx scripts/promote-lab-to-production.ts --dry-run
 *
 * Requires DATABASE_URL and prisma schema with Strategy.archived.
 */
import fs from "fs";
import path from "path";

import { PrismaClient } from "@prisma/client";

import { detectPythonCode, strategyCodeBlob } from "../src/lib/detect-python";
import {
  draftBacktestMetricsJson,
  findDraftPost,
  loadLabIndex,
  loadLabPythonSource,
  type DraftPost,
  type LabIndexEntry,
} from "../src/lib/draft-preview";
import { formatPythonCodeHtml } from "../src/lib/format-python";
import { applyFreeLibraryShare } from "../src/lib/paywall";

const dryRun = process.argv.includes("--dry-run");
const prisma = new PrismaClient();

type Snapshot = {
  slug: string;
  locale: string;
  title: string;
  teaser: string;
  summary: string;
  contentHtml: string;
  backtestMetrics: string;
  annualisedReturn: string | null;
  sharpeRatio: string | null;
  volatility: string | null;
  beta: string | null;
  sortinoRatio: string | null;
  maxDrawdown: string | null;
  winRate: string | null;
  region: string | null;
  market: string | null;
  assetClass: string | null;
  frequency: string | null;
  isPaywalled: boolean;
  hasPythonCode: boolean;
  paperTitle: string | null;
  paperAuthors: string | null;
  paperInstitute: string;
  paperAffiliationsJson: string;
  academicLink: string | null;
  paperImagesJson: string;
  economicRationale: string;
  pythonCodeHtml: string;
  metaTitle: string | null;
  metaDescription: string | null;
  sortOrder: number;
  published: boolean;
};

function keyOf(locale: string, slug: string) {
  return `${locale}::${slug}`;
}

function pythonHtmlFromLab(entry: LabIndexEntry, fallbackHtml = ""): string {
  const source = loadLabPythonSource(entry, fallbackHtml);
  return formatPythonCodeHtml(source) || fallbackHtml || "";
}

function fromDraft(post: DraftPost, entry: LabIndexEntry) {
  const pythonCodeHtml =
    post.pythonCodeHtml?.trim() || pythonHtmlFromLab(entry, post.pythonCodeHtml || "");
  return {
    slug: entry.slug,
    locale: entry.locale === "zh" ? "zh" : "en",
    title: post.title || entry.title,
    teaser: post.teaser || "",
    summary: post.summary || "",
    contentHtml: post.contentHtml || "",
    backtestMetrics: draftBacktestMetricsJson({
      ...post,
      annualisedReturn: entry.annualisedReturn ?? post.annualisedReturn,
      sharpeRatio: entry.sharpeRatio ?? post.sharpeRatio,
      maxDrawdown: entry.maxDrawdown ?? post.maxDrawdown,
      volatility: entry.volatility ?? post.volatility,
      beta: entry.beta ?? post.beta,
      sortinoRatio: entry.sortinoRatio ?? post.sortinoRatio,
    }),
    annualisedReturn: entry.annualisedReturn ?? post.annualisedReturn ?? null,
    sharpeRatio: entry.sharpeRatio ?? post.sharpeRatio ?? null,
    volatility: entry.volatility ?? post.volatility ?? null,
    beta: entry.beta ?? post.beta ?? null,
    sortinoRatio: entry.sortinoRatio ?? post.sortinoRatio ?? null,
    maxDrawdown: entry.maxDrawdown ?? post.maxDrawdown ?? null,
    winRate: post.winRate ?? null,
    region: post.region ?? entry.region ?? null,
    market: post.market ?? null,
    assetClass: post.assetClass ?? entry.assetClass ?? null,
    frequency: post.frequency ?? null,
    isPaywalled: post.isPaywalled ?? entry.isPaywalled ?? true,
    paperTitle: post.paperTitle ?? entry.paperTitle ?? null,
    paperAuthors: post.paperAuthors ?? null,
    paperInstitute: post.paperInstitute?.trim() || "N/A",
    paperAffiliationsJson: post.paperAffiliationsJson || "[]",
    academicLink: post.academicLink ?? null,
    paperImagesJson: "[]",
    economicRationale: post.economicRationale || "",
    pythonCodeHtml,
    metaTitle: null as string | null,
    metaDescription: null as string | null,
    sortOrder: 0,
    published: true,
    archived: false,
    hasPythonCode: detectPythonCode(strategyCodeBlob(post.contentHtml || "", pythonCodeHtml)),
  };
}

function fromLibrarySnapshot(entry: LabIndexEntry, snap: Snapshot | undefined) {
  const pythonCodeHtml = pythonHtmlFromLab(entry, snap?.pythonCodeHtml || "");
  const contentHtml = snap?.contentHtml || "";
  return {
    slug: entry.slug,
    locale: entry.locale === "zh" ? "zh" : "en",
    title: snap?.title || entry.title,
    teaser: snap?.teaser || "",
    summary: snap?.summary || "",
    contentHtml,
    backtestMetrics: JSON.stringify({
      annualisedReturn: entry.annualisedReturn ?? snap?.annualisedReturn ?? undefined,
      volatility: entry.volatility ?? snap?.volatility ?? undefined,
      beta: entry.beta ?? snap?.beta ?? undefined,
      sharpeRatio: entry.sharpeRatio ?? snap?.sharpeRatio ?? undefined,
      sortinoRatio: entry.sortinoRatio ?? snap?.sortinoRatio ?? undefined,
      maxDrawdown: entry.maxDrawdown ?? snap?.maxDrawdown ?? undefined,
      winRate: snap?.winRate ?? undefined,
    }),
    annualisedReturn: entry.annualisedReturn ?? snap?.annualisedReturn ?? null,
    sharpeRatio: entry.sharpeRatio ?? snap?.sharpeRatio ?? null,
    volatility: entry.volatility ?? snap?.volatility ?? null,
    beta: entry.beta ?? snap?.beta ?? null,
    sortinoRatio: entry.sortinoRatio ?? snap?.sortinoRatio ?? null,
    maxDrawdown: entry.maxDrawdown ?? snap?.maxDrawdown ?? null,
    winRate: snap?.winRate ?? null,
    region: entry.region ?? snap?.region ?? null,
    market: snap?.market ?? null,
    assetClass: entry.assetClass ?? snap?.assetClass ?? null,
    frequency: snap?.frequency ?? null,
    isPaywalled: snap?.isPaywalled ?? entry.isPaywalled ?? true,
    paperTitle: snap?.paperTitle ?? entry.paperTitle ?? null,
    paperAuthors: snap?.paperAuthors ?? null,
    paperInstitute: snap?.paperInstitute?.trim() || "N/A",
    paperAffiliationsJson: snap?.paperAffiliationsJson || "[]",
    academicLink: snap?.academicLink ?? null,
    paperImagesJson: snap?.paperImagesJson || "[]",
    economicRationale: snap?.economicRationale || "",
    pythonCodeHtml,
    metaTitle: snap?.metaTitle ?? null,
    metaDescription: snap?.metaDescription ?? null,
    sortOrder: snap?.sortOrder ?? 0,
    published: true,
    archived: false,
    hasPythonCode: detectPythonCode(strategyCodeBlob(contentHtml, pythonCodeHtml)),
  };
}

async function main() {
  const idx = loadLabIndex();
  if (!idx.strategies.length) {
    throw new Error("lab_index.json empty or missing — aborting");
  }

  console.log(
    `Lab strategies: ${idx.count} (library=${idx.library}, new100=${idx.new100}) dryRun=${dryRun}`,
  );

  const existing = await prisma.strategy.findMany();
  console.log(`DB strategies before: ${existing.length}`);

  const snapshot = new Map<string, Snapshot>();
  for (const row of existing) {
    // Prefer non-archived snapshot when both exist
    const k = keyOf(row.locale, row.slug);
    const prev = snapshot.get(k);
    if (!prev || (prev && row.archived === false)) {
      snapshot.set(k, row);
    }
  }

  if (!dryRun) {
    const alreadyArchived = await prisma.strategy.count({ where: { archived: true } });
    if (alreadyArchived === 0) {
      const archived = await prisma.strategy.updateMany({
        where: { archived: false },
        data: { archived: true },
      });
      console.log(`First run — archived (flag only): ${archived.count} strategies`);
    } else {
      const removed = await prisma.strategy.deleteMany({
        where: { archived: false },
      });
      console.log(
        `Re-run — removed ${removed.count} prior active lab publishes; kept ${alreadyArchived} archived originals`,
      );
    }
  } else {
    const wouldArchive = existing.filter((r) => !r.archived).length;
    const alreadyArchived = existing.filter((r) => r.archived).length;
    console.log(
      `[dry-run] archived already=${alreadyArchived}; would archive or replace ${wouldArchive} active rows`,
    );
  }

  let created = 0;
  let failed = 0;
  const failures: { slug: string; locale: string; error: string }[] = [];

  for (const entry of idx.strategies) {
    const locale = entry.locale === "zh" ? "zh" : "en";
    try {
      let data;
      if (entry.source === "new100") {
        const draft = findDraftPost(entry.slug);
        if (!draft) {
          data = fromLibrarySnapshot(entry, snapshot.get(keyOf(locale, entry.slug)));
        } else {
          data = fromDraft(draft, entry);
        }
      } else {
        data = fromLibrarySnapshot(entry, snapshot.get(keyOf(locale, entry.slug)));
      }

      if (dryRun) {
        created += 1;
        continue;
      }

      await prisma.strategy.create({ data });
      created += 1;
      if (created % 100 === 0) {
        console.log(`… created ${created}/${idx.strategies.length}`);
      }
    } catch (e) {
      failed += 1;
      failures.push({
        slug: entry.slug,
        locale,
        error: e instanceof Error ? e.message : String(e),
      });
    }
  }

  if (!dryRun) {
    console.log("Applying 20% free / 80% paid mix on active published strategies…");
    const mix = await applyFreeLibraryShare();
    console.log("Paywall mix:", JSON.stringify(mix));
  }

  const active = dryRun
    ? created
    : await prisma.strategy.count({ where: { archived: false, published: true } });
  const archivedCount = dryRun
    ? existing.filter((r) => !r.archived).length
    : await prisma.strategy.count({ where: { archived: true } });

  const report = {
    dryRun,
    labTotal: idx.strategies.length,
    created,
    failed,
    activePublic: active,
    archivedKept: archivedCount,
    failures: failures.slice(0, 30),
  };
  const outPath = path.join(process.cwd(), "backtest", "drafts", "promote_lab_report.json");
  fs.writeFileSync(outPath, JSON.stringify(report, null, 2), "utf8");
  console.log(JSON.stringify(report, null, 2));
  console.log(`Report written to ${outPath}`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
