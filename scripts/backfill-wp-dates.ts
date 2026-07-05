/**
 * Set strategy createdAt/updatedAt from WordPress wp:post_date in the WXR export.
 *   npx tsx scripts/backfill-wp-dates.ts
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { PrismaClient } from "@prisma/client";

import { canonicalSlug } from "../src/lib/slug";

const prisma = new PrismaClient();

function extractTag(block: string, tag: string): string {
  const re = new RegExp(`<${tag}>([\\s\\S]*?)<\\/${tag}>`, "i");
  const m = block.match(re);
  if (!m?.[1]) return "";
  return m[1]
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, "$1")
    .trim();
}

function parseWpDate(raw: string): Date | null {
  if (!raw.trim()) return null;
  const d = new Date(raw.replace(" ", "T") + "Z");
  return Number.isNaN(d.getTime()) ? null : d;
}

async function main() {
  const filePath = resolve(process.cwd(), "data/quantbuffet.WordPress.xml");
  const xml = readFileSync(filePath, "utf8");
  const chunks = xml.split("<item>").slice(1);

  let updated = 0;
  let missed = 0;

  for (const chunk of chunks) {
    const block = chunk.split("</item>")[0] ?? "";
    if (extractTag(block, "wp:post_type") !== "post") continue;

    const slug = canonicalSlug(extractTag(block, "wp:post_name"));
    const link = extractTag(block, "link");
    const locale = /\/zh\//i.test(link) || /%e4%b8%ad/i.test(link) ? "zh" : "en";
    const created = parseWpDate(extractTag(block, "wp:post_date_gmt") || extractTag(block, "wp:post_date"));
    const modified = parseWpDate(
      extractTag(block, "wp:post_modified_gmt") || extractTag(block, "wp:post_modified"),
    );

    if (!slug || !created) {
      missed++;
      continue;
    }

    const result = await prisma.strategy.updateMany({
      where: { slug, locale },
      data: {
        createdAt: created,
        updatedAt: modified ?? created,
      },
    });

    if (result.count > 0) updated += result.count;
  }

  console.log(`Updated createdAt/updatedAt on ${updated} strategies (${missed} WXR items skipped).`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
