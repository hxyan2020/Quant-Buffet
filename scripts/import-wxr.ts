/**
 * Import WordPress WXR export into Prisma Strategy rows.
 *
 * Usage:
 *   npx tsx scripts/import-wxr.ts
 *   npx tsx scripts/import-wxr.ts --file data/quantbuffet.WordPress.xml --dry-run
 *   npx tsx scripts/import-wxr.ts --replace   # delete existing strategies first
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { PrismaClient } from "@prisma/client";

import { generateStrategySeo } from "../src/lib/generate-seo";
import {
  backtestMetricsToJson,
  parseStrategyContent,
} from "../src/lib/parse-strategy-content";
import { canonicalSlug } from "../src/lib/slug";

const prisma = new PrismaClient();

type ParsedPost = {
  wpId: string;
  slug: string;
  locale: "en" | "zh";
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
  metaTitle: string;
  metaDescription: string;
  region: string | null;
  market: string | null;
  frequency: string | null;
  paperTitle: string | null;
  paperAuthors: string | null;
  paperInstitute: string | null;
  academicLink: string | null;
  economicRationale: string;
  pythonCodeHtml: string;
  hasPythonCode: boolean;
  published: boolean;
  isPaywalled: boolean;
  sortOrder: number;
  wpCreatedAt: Date;
  wpUpdatedAt: Date;
};

function parseWpDate(raw: string): Date | null {
  if (!raw.trim()) return null;
  const d = new Date(raw.replace(" ", "T") + "Z");
  return Number.isNaN(d.getTime()) ? null : d;
}

function decodeCdata(raw: string): string {
  return raw
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .trim();
}

function extractTag(block: string, tag: string): string {
  const cdata = new RegExp(`<${tag}><!\\[CDATA\\[([\\s\\S]*?)\\]\\]></${tag}>`, "i");
  const plain = new RegExp(`<${tag}>([^<]*)</${tag}>`, "i");
  const m = block.match(cdata) ?? block.match(plain);
  return m ? decodeCdata(m[1] ?? m[0]) : "";
}

function extractCategories(block: string): { language?: string; categories: string[] } {
  const categories: string[] = [];
  let language: string | undefined;
  const re = /<category domain="([^"]+)" nicename="([^"]+)">/gi;
  let match: RegExpExecArray | null;
  while ((match = re.exec(block)) !== null) {
    const domain = match[1]?.toLowerCase();
    const nicename = match[2]?.toLowerCase();
    if (domain === "language" && (nicename === "en" || nicename === "zh")) {
      language = nicename;
    }
    categories.push(nicename);
  }
  return { language, categories };
}

function detectLocale(block: string, link: string): "en" | "zh" {
  const { language } = extractCategories(block);
  if (language === "en" || language === "zh") return language;
  if (/\/zh\//i.test(link) || link.includes("%e4%b8%ad")) return "zh";
  if (/\/en\//i.test(link)) return "en";
  return "en";
}

function parseMetadataLine(html: string): {
  region: string | null;
  market: string | null;
  frequency: string | null;
} {
  const match = html.match(
    /REGION:\s*([^|]+)\|\s*FREQUENCY:\s*([^|]+)\|\s*MARKET:\s*([^|<]+)/i,
  );
  if (!match) {
    return { region: null, market: null, frequency: null };
  }
  return {
    region: match[1]?.trim() ?? null,
    market: match[3]?.trim() ?? null,
    frequency: match[2]?.trim() ?? null,
  };
}

function parseBacktestTable(html: string): {
  annualisedReturn: string | null;
  sharpeRatio: string | null;
} {
  let annualisedReturn: string | null = null;
  let sharpeRatio: string | null = null;

  const ann = html.match(/Annualised\s+Return<\/strong><\/td><td><strong>([^<]+)</i);
  if (ann) annualisedReturn = ann[1].replace(/&nbsp;/g, " ").trim();

  const sharpeRow = html.match(
    /Sharpe\s+Ratio<\/strong><\/td><td>([\s\S]*?)<\/td>/i,
  );
  if (sharpeRow) {
    sharpeRatio = sharpeRow[1]
      .replace(/<[^>]+>/g, "")
      .replace(/&nbsp;/g, " ")
      .trim();
  }

  return { annualisedReturn, sharpeRatio };
}

function isPaywalledFromMeta(block: string): boolean {
  const restriction = block.match(
    /um_content_restriction[\s\S]*?<wp:meta_value><!\[CDATA\[([\s\S]*?)\]\]><\/wp:meta_value>/i,
  );
  if (!restriction) return true;
  const blob = restriction[1] ?? "";
  if (/_um_custom_access_settings";b:0/.test(blob)) return true;
  const accessible = blob.match(/_um_accessible";i:(\d)/);
  if (accessible) return accessible[1] === "2" || accessible[1] === "1";
  return true;
}

function parseItem(block: string, index: number): ParsedPost | null {
  const postType = extractTag(block, "wp:post_type");
  if (postType !== "post") return null;

  const status = extractTag(block, "wp:status");
  const title = extractTag(block, "title");
  const slug = extractTag(block, "wp:post_name");
  const link = extractTag(block, "link");
  const excerpt = extractTag(block, "excerpt:encoded");
  const content = extractTag(block, "content:encoded");
  const wpId = extractTag(block, "wp:post_id");

  if (!slug || !title) return null;

  const locale = detectLocale(block, link);
  const normalizedSlug = canonicalSlug(slug);
  const meta = parseMetadataLine(content);
  const parsed = parseStrategyContent(content, { excerpt });
  const seo = generateStrategySeo({
    title,
    locale,
    market: meta.market,
    region: meta.region,
    assetClass: null,
    frequency: meta.frequency,
    paperTitle: parsed.paperTitle,
    backtestMetrics: parsed.backtestMetrics,
  });
  const wpCreatedAt =
    parseWpDate(extractTag(block, "wp:post_date_gmt") || extractTag(block, "wp:post_date")) ??
    new Date();
  const wpUpdatedAt =
    parseWpDate(
      extractTag(block, "wp:post_modified_gmt") || extractTag(block, "wp:post_modified"),
    ) ?? wpCreatedAt;

  return {
    wpId,
    slug: normalizedSlug,
    locale,
    title,
    teaser: parsed.teaser,
    summary: parsed.summary,
    contentHtml: parsed.contentHtml,
    backtestMetrics: backtestMetricsToJson(parsed.backtestMetrics),
    annualisedReturn: parsed.backtestMetrics.annualisedReturn ?? null,
    sharpeRatio: parsed.backtestMetrics.sharpeRatio ?? null,
    volatility: parsed.backtestMetrics.volatility ?? null,
    beta: parsed.backtestMetrics.beta ?? null,
    sortinoRatio: parsed.backtestMetrics.sortinoRatio ?? null,
    maxDrawdown: parsed.backtestMetrics.maxDrawdown ?? null,
    winRate: parsed.backtestMetrics.winRate ?? null,
    region: meta.region,
    market: meta.market,
    frequency: meta.frequency,
    paperTitle: parsed.paperTitle,
    paperAuthors: parsed.paperAuthors,
    paperInstitute: parsed.paperInstitute,
    academicLink: parsed.academicLink,
    economicRationale: parsed.economicRationale,
    pythonCodeHtml: parsed.pythonCodeHtml,
    hasPythonCode: parsed.hasPythonCode,
    metaTitle: seo.metaTitle,
    metaDescription: seo.metaDescription,
    published: status === "publish",
    isPaywalled: isPaywalledFromMeta(block),
    sortOrder: Number(wpId) || index,
    wpCreatedAt,
    wpUpdatedAt,
  };
}

function splitItems(xml: string): string[] {
  const parts = xml.split("<item>");
  return parts.slice(1).map((chunk) => chunk.split("</item>")[0] ?? "");
}

async function main() {
  const args = process.argv.slice(2);
  const dryRun = args.includes("--dry-run");
  const replace = args.includes("--replace");
  const fileArg = args.find((a) => a.startsWith("--file="));
  const filePath = resolve(
    process.cwd(),
    fileArg?.split("=")[1] ?? "data/quantbuffet.WordPress.xml",
  );

  console.log(`Reading ${filePath} …`);
  const xml = readFileSync(filePath, "utf8");
  const chunks = splitItems(xml);
  console.log(`Found ${chunks.length} <item> blocks`);

  const parsed: ParsedPost[] = [];
  for (let i = 0; i < chunks.length; i++) {
    const row = parseItem(chunks[i] ?? "", i);
    if (row) parsed.push(row);
  }

  const byLocale = parsed.reduce(
    (acc, row) => {
      acc[row.locale] = (acc[row.locale] ?? 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  console.log(`Importable posts: ${parsed.length}`);
  console.log("By locale:", byLocale);

  if (dryRun) {
    console.log("\nSample (first 3):");
    for (const row of parsed.slice(0, 3)) {
      console.log(`- [${row.locale}] ${row.title} (${row.slug})`);
      console.log(`  ann=${row.annualisedReturn} sharpe=${row.sharpeRatio} region=${row.region}`);
    }
    return;
  }

  if (replace) {
    const deleted = await prisma.strategy.deleteMany();
    console.log(`Cleared ${deleted.count} existing strategies`);
  }

  let created = 0;
  let updated = 0;
  let skipped = 0;

  for (const row of parsed) {
    try {
      const existing = await prisma.strategy.findUnique({
        where: { slug_locale: { slug: row.slug, locale: row.locale } },
        select: { id: true },
      });

      const data = {
        slug: row.slug,
        locale: row.locale,
        title: row.title,
        teaser: row.teaser,
        summary: row.summary,
        contentHtml: row.contentHtml,
        backtestMetrics: row.backtestMetrics,
        annualisedReturn: row.annualisedReturn,
        sharpeRatio: row.sharpeRatio,
        volatility: row.volatility,
        beta: row.beta,
        sortinoRatio: row.sortinoRatio,
        maxDrawdown: row.maxDrawdown,
        winRate: row.winRate,
        region: row.region,
        market: row.market,
        frequency: row.frequency,
        paperTitle: row.paperTitle,
        paperAuthors: row.paperAuthors,
        paperInstitute: row.paperInstitute || "N/A",
        academicLink: row.academicLink,
        economicRationale: row.economicRationale,
        pythonCodeHtml: row.pythonCodeHtml,
        hasPythonCode: row.hasPythonCode,
        metaTitle: row.metaTitle,
        metaDescription: row.metaDescription,
        isPaywalled: row.isPaywalled,
        published: row.published,
        sortOrder: row.sortOrder,
        createdAt: row.wpCreatedAt,
        updatedAt: row.wpUpdatedAt,
      };

      if (existing) {
        await prisma.strategy.update({ where: { id: existing.id }, data });
        updated++;
      } else {
        await prisma.strategy.create({ data });
        created++;
      }
    } catch (error) {
      skipped++;
      console.warn(`Skip ${row.slug} (${row.locale}):`, error);
    }
  }

  console.log(`Done. created=${created} updated=${updated} skipped=${skipped}`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
