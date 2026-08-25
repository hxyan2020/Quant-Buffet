/**
 * Restore original-paper screenshots from the WordPress WXR export.
 *
 * Images are rewritten to https://quantbuffet.files.wordpress.com/...
 * (live quantbuffet.com/wp-content URLs 404 after the WP migration).
 *
 *   npx tsx scripts/restore-paper-screenshots.ts
 *   npx tsx scripts/restore-paper-screenshots.ts --check   # HEAD-validate URLs
 *   npx tsx scripts/restore-paper-screenshots.ts --dry-run
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";

import { PrismaClient } from "@prisma/client";

import {
  extractPaperImages,
  paperImagesToJson,
  type PaperImage,
} from "../src/lib/paper-images";
import { canonicalSlug } from "../src/lib/slug";

const prisma = new PrismaClient();
const dryRun = process.argv.includes("--dry-run");
const checkUrls = process.argv.includes("--check");

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

function loadWxrBodies(filePath: string) {
  const xml = readFileSync(filePath, "utf8");
  const chunks = xml.split("<item>").slice(1);
  const map = new Map<string, string>();

  for (const chunk of chunks) {
    const block = chunk.split("</item>")[0] ?? "";
    if (extractTag(block, "wp:post_type") !== "post") continue;
    const slug = canonicalSlug(extractTag(block, "wp:post_name"));
    const link = extractTag(block, "link");
    const locale = detectLocale(block, link);
    const content = extractTag(block, "content:encoded");
    if (!slug || !content) continue;
    map.set(`${slug}::${locale}`, content);
  }
  return map;
}

const urlCache = new Map<string, boolean>();

async function urlOk(src: string): Promise<boolean> {
  if (urlCache.has(src)) return urlCache.get(src)!;
  try {
    const res = await fetch(src, {
      method: "HEAD",
      redirect: "follow",
      headers: { "User-Agent": "QuantBuffetScreenshotRestore/1.0" },
      signal: AbortSignal.timeout(12_000),
    });
    let ok = res.ok && (res.headers.get("content-type") ?? "").includes("image");
    if (!ok && (res.status === 405 || res.status === 403)) {
      const get = await fetch(src, {
        method: "GET",
        headers: {
          "User-Agent": "QuantBuffetScreenshotRestore/1.0",
          Range: "bytes=0-64",
        },
        signal: AbortSignal.timeout(12_000),
      });
      ok = get.ok || get.status === 206;
    }
    urlCache.set(src, ok);
    return ok;
  } catch {
    urlCache.set(src, false);
    return false;
  }
}

async function filterLive(images: PaperImage[]): Promise<PaperImage[]> {
  if (!checkUrls || images.length === 0) return images;
  const kept: PaperImage[] = [];
  for (const img of images) {
    if (await urlOk(img.src)) kept.push(img);
  }
  return kept;
}

async function main() {
  const wxrPath = resolve(process.cwd(), "data/quantbuffet.WordPress.xml");
  console.log(`Loading WXR from ${wxrPath}`);
  const wxr = loadWxrBodies(wxrPath);
  console.log(`WXR posts with bodies: ${wxr.size}`);

  const rows = await prisma.strategy.findMany({
    select: { id: true, slug: true, locale: true, title: true },
  });

  let withImages = 0;
  let updated = 0;
  let missingWxr = 0;
  let empty = 0;
  let totalImgs = 0;

  for (const row of rows) {
    const key = `${canonicalSlug(row.slug)}::${row.locale}`;
    const body = wxr.get(key);
    if (!body) {
      missingWxr++;
      if (!dryRun) {
        await prisma.strategy.update({
          where: { id: row.id },
          data: { paperImagesJson: "[]" },
        });
      }
      continue;
    }

    let images = extractPaperImages(body);
    images = await filterLive(images);
    const json = paperImagesToJson(images);

    if (images.length === 0) {
      empty++;
    } else {
      withImages++;
      totalImgs += images.length;
    }

    if (!dryRun) {
      await prisma.strategy.update({
        where: { id: row.id },
        data: { paperImagesJson: json },
      });
      updated++;
    }
  }

  console.log(
    JSON.stringify(
      {
        dryRun,
        checkUrls,
        strategies: rows.length,
        updated,
        withImages,
        emptyPaperImages: empty,
        missingWxr,
        totalImgs,
        avgImgs: withImages ? (totalImgs / withImages).toFixed(2) : 0,
      },
      null,
      2,
    ),
  );
}

main()
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
