/**
 * Restructure every strategy from WordPress WXR (sections, metrics, Python, SEO, paper URLs).
 *   npx tsx scripts/restructure-all-strategies.ts
 *   npx tsx scripts/restructure-all-strategies.ts --skip-url-fetch
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { PrismaClient } from "@prisma/client";

import { fetchPaperMetaFromUrl, mergePaperMeta } from "../src/lib/fetch-paper-meta";
import { generateStrategySeo } from "../src/lib/generate-seo";
import {
  backtestMetricsToJson,
  parseStrategyContent,
} from "../src/lib/parse-strategy-content";
import { canonicalSlug } from "../src/lib/slug";

const prisma = new PrismaClient();
const skipUrlFetch = process.argv.includes("--skip-url-fetch");

function decodeCdata(raw: string): string {
  return raw
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&amp;/g, "&")
    .trim();
}

function extractTag(block: string, tag: string): string {
  const cdata = new RegExp(`<${tag}><!\\[CDATA\\[([\\s\\S]*?)\\]\\]></${tag}>`, "i");
  const plain = new RegExp(`<${tag}>([^<]*)</${tag}>`, "i");
  const m = block.match(cdata) ?? block.match(plain);
  return m ? decodeCdata(m[1] ?? m[0]) : "";
}

function detectLocale(block: string, link: string): "en" | "zh" {
  const re = /<category domain="language" nicename="(en|zh)">/i;
  const m = block.match(re);
  if (m?.[1] === "en" || m?.[1] === "zh") return m[1];
  if (/\/zh\//i.test(link)) return "zh";
  return "en";
}

function loadWxrPosts(filePath: string) {
  const xml = readFileSync(filePath, "utf8");
  const chunks = xml.split("<item>").slice(1);
  const map = new Map<string, { content: string; excerpt: string }>();

  for (const chunk of chunks) {
    const block = chunk.split("</item>")[0] ?? "";
    if (extractTag(block, "wp:post_type") !== "post") continue;
    const slug = canonicalSlug(extractTag(block, "wp:post_name"));
    const link = extractTag(block, "link");
    const locale = detectLocale(block, link);
    const content = extractTag(block, "content:encoded");
    const excerpt = extractTag(block, "excerpt:encoded");
    if (!slug) continue;
    map.set(`${slug}::${locale}`, { content, excerpt });
  }
  return map;
}

async function main() {
  const wxrPath = resolve(process.cwd(), "data/quantbuffet.WordPress.xml");
  console.log(`Loading WXR from ${wxrPath}…`);
  const wxr = loadWxrPosts(wxrPath);

  const rows = await prisma.strategy.findMany({
    select: {
      id: true,
      slug: true,
      locale: true,
      title: true,
      market: true,
      region: true,
      assetClass: true,
      frequency: true,
    },
  });

  const BATCH = 12;
  let n = 0;
  let urlFetched = 0;

  async function processRow(row: (typeof rows)[0]) {
    const key = `${row.slug}::${row.locale}`;
    const wxrRow = wxr.get(key);
    const sourceHtml = wxrRow?.content ?? "";
    const parsed = parseStrategyContent(sourceHtml, { excerpt: wxrRow?.excerpt });

    let paper = mergePaperMeta(
      {
        paperTitle: parsed.paperTitle === "N/A" ? null : parsed.paperTitle,
        paperAuthors: parsed.paperAuthors === "N/A" ? null : parsed.paperAuthors,
        paperInstitute: parsed.paperInstitute === "N/A" ? null : parsed.paperInstitute,
        academicLink: parsed.academicLink,
      },
      null,
    );

    if (!skipUrlFetch && parsed.academicLink) {
      const fromUrl = await fetchPaperMetaFromUrl(parsed.academicLink);
      if (fromUrl?.paperTitle) urlFetched++;
      paper = mergePaperMeta(
        {
          paperTitle: parsed.paperTitle === "N/A" ? null : parsed.paperTitle,
          paperAuthors: parsed.paperAuthors === "N/A" ? null : parsed.paperAuthors,
          paperInstitute: parsed.paperInstitute === "N/A" ? null : parsed.paperInstitute,
          academicLink: parsed.academicLink,
        },
        fromUrl,
      );
    }

    const seo = generateStrategySeo({
      title: row.title,
      locale: row.locale,
      market: row.market,
      region: row.region,
      assetClass: row.assetClass,
      frequency: row.frequency,
      paperTitle: paper.paperTitle === "N/A" ? null : paper.paperTitle,
      backtestMetrics: parsed.backtestMetrics,
    });

    await prisma.strategy.update({
      where: { id: row.id },
      data: {
        teaser: parsed.teaser,
        summary: parsed.summary,
        economicRationale: parsed.economicRationale,
        contentHtml: parsed.contentHtml,
        pythonCodeHtml: parsed.pythonCodeHtml,
        hasPythonCode: parsed.hasPythonCode,
        paperTitle: paper.paperTitle,
        paperAuthors: paper.paperAuthors,
        paperInstitute: paper.paperInstitute,
        paperAffiliationsJson: paper.paperAffiliationsJson,
        academicLink: paper.academicLink,
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

  }

  for (let i = 0; i < rows.length; i += BATCH) {
    const batch = rows.slice(i, i + BATCH);
    await Promise.all(batch.map(processRow));
    n += batch.length;
    console.log(`Updated ${n}/${rows.length}…`);
  }

  const badTitles = await prisma.strategy.count({
    where: {
      OR: [
        { paperTitle: { contains: "Abstract" } },
        { paperTitle: { contains: "BACKTEST" } },
        { paperTitle: { contains: "NUTSHELL" } },
      ],
    },
  });

  console.log(`Done: ${n} strategies. URL titles improved: ~${urlFetched}. Bad paper titles: ${badTitles}.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
