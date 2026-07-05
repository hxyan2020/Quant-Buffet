/**
 * Backfill structured fields from existing contentHtml.
 * Prefer: npx tsx scripts/restructure-all-strategies.ts
 */

import { PrismaClient } from "@prisma/client";

import { generateStrategySeo } from "../src/lib/generate-seo";
import {
  backtestMetricsToJson,
  parseStrategyContent,
} from "../src/lib/parse-strategy-content";

const prisma = new PrismaClient();

async function main() {
  const rows = await prisma.strategy.findMany({
    select: { id: true, title: true, locale: true, market: true, region: true, assetClass: true, frequency: true, summary: true, contentHtml: true },
  });

  let n = 0;
  for (const row of rows) {
    const parsed = parseStrategyContent(row.contentHtml, {
      excerpt: row.summary.length <= 360 ? row.summary : undefined,
    });
    const seo = generateStrategySeo({
      title: row.title,
      locale: row.locale,
      market: row.market,
      region: row.region,
      assetClass: row.assetClass,
      frequency: row.frequency,
      paperTitle: parsed.paperTitle,
      backtestMetrics: parsed.backtestMetrics,
    });

    await prisma.strategy.update({
      where: { id: row.id },
      data: {
        teaser: parsed.teaser,
        summary: parsed.summary || row.summary.slice(0, 8000),
        economicRationale: parsed.economicRationale,
        paperTitle: parsed.paperTitle,
        paperAuthors: parsed.paperAuthors,
        paperInstitute: parsed.paperInstitute || "N/A",
        academicLink: parsed.academicLink,
        pythonCodeHtml: parsed.pythonCodeHtml,
        hasPythonCode: parsed.hasPythonCode,
        contentHtml: parsed.contentHtml,
        backtestMetrics: backtestMetricsToJson(parsed.backtestMetrics),
        annualisedReturn: parsed.backtestMetrics.annualisedReturn ?? null,
        sharpeRatio: parsed.backtestMetrics.sharpeRatio ?? null,
        volatility: parsed.backtestMetrics.volatility ?? null,
        beta: parsed.backtestMetrics.beta ?? null,
        sortinoRatio: parsed.backtestMetrics.sortinoRatio ?? null,
        maxDrawdown: parsed.backtestMetrics.maxDrawdown ?? null,
        winRate: parsed.backtestMetrics.winRate ?? null,
        metaTitle: seo.metaTitle,
        metaDescription: seo.metaDescription,
      },
    });
    n++;
    if (n % 200 === 0) console.log(`Enriched ${n}/${rows.length}…`);
  }
  console.log(`Enriched ${n} strategies.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
