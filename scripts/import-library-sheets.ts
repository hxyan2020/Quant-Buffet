/**
 * Sync strategy library metadata from public Google Sheets (EN + ZH).
 *
 *   npx tsx scripts/import-library-sheets.ts
 *   npx tsx scripts/import-library-sheets.ts --dry-run
 */

import { PrismaClient } from "@prisma/client";

import { canonicalSlug } from "../src/lib/slug";

const prisma = new PrismaClient();

const SHEETS = {
  en: "https://docs.google.com/spreadsheets/d/1gpe5SURpGTMOLlQrlgAYskK-2d8kBXM9EBPuhVDQJhA/export?format=csv&gid=0",
  zh: "https://docs.google.com/spreadsheets/d/17UhZ36pfNod5teyvwFAcMx1MsF__ekMFwkdNGtVf-4U/export?format=csv&gid=0",
} as const;

type SheetRow = {
  sortOrder: number;
  title: string;
  assetClass: string | null;
  market: string | null;
  region: string | null;
  frequency: string | null;
  annualisedReturn: string | null;
  url: string;
};

function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    const next = text[i + 1];

    if (inQuotes) {
      if (ch === '"' && next === '"') {
        cell += '"';
        i++;
      } else if (ch === '"') {
        inQuotes = false;
      } else {
        cell += ch;
      }
      continue;
    }

    if (ch === '"') {
      inQuotes = true;
    } else if (ch === ",") {
      row.push(cell);
      cell = "";
    } else if (ch === "\n" || (ch === "\r" && next === "\n")) {
      row.push(cell);
      if (row.some((c) => c.trim())) rows.push(row);
      row = [];
      cell = "";
      if (ch === "\r") i++;
    } else if (ch !== "\r") {
      cell += ch;
    }
  }

  if (cell.length || row.length) {
    row.push(cell);
    if (row.some((c) => c.trim())) rows.push(row);
  }

  return rows;
}

function slugFromUrl(url: string): string | null {
  try {
    const parsed = new URL(url.trim());
    const parts = parsed.pathname.split("/").filter(Boolean);
    const last = parts[parts.length - 1];
    return last ? canonicalSlug(last) : null;
  } catch {
    return null;
  }
}

function normalizePercent(value: string): string | null {
  const trimmed = value.trim();
  if (!trimmed || /^n\/?a$/i.test(trimmed)) return null;
  if (trimmed.includes("%")) return trimmed;
  const num = Number(trimmed);
  if (!Number.isFinite(num)) return trimmed;
  return `${(num * 100).toFixed(2)}%`;
}

function mapRows(csv: string[][]): SheetRow[] {
  if (csv.length < 2) return [];
  const header = csv[0].map((h) => h.trim().toLowerCase());
  const idx = (aliases: string[]) =>
    header.findIndex((h) => aliases.some((a) => h.includes(a)));

  let colSeq = idx(["seq", "序号"]);
  let colName = idx(["strategy name", "策略名称", "strategy", "策略"]);
  let colAsset = idx(["asset class", "资产类别", "asset", "资产"]);
  let colMarket = idx(["market", "市场"]);
  let colRegion = idx(["region", "地区", "区域"]);
  let colFreq = idx(["frequency", "交易频率", "freq", "频率"]);
  let colAnn = idx(["annul", "年化", "annual", "收益"]);
  let colUrl = idx(["open strategy", "打开", "link", "url", "策略链接"]);

  // Fallback: both official sheets share column order A–J
  if (colUrl < 0) {
    colSeq = 0;
    colName = 1;
    colAsset = 2;
    colMarket = 3;
    colRegion = 4;
    colFreq = 5;
    colAnn = 7;
    colUrl = 9;
  }

  const out: SheetRow[] = [];
  for (let i = 1; i < csv.length; i++) {
    const row = csv[i];
    const url = row[colUrl]?.trim() ?? "";
    if (!url.startsWith("http")) continue;

    const seq = Number(row[colSeq]?.trim());
    out.push({
      sortOrder: Number.isFinite(seq) ? seq : i,
      title: row[colName]?.trim() ?? "",
      assetClass: row[colAsset]?.trim() || null,
      market: row[colMarket]?.trim() || null,
      region: row[colRegion]?.trim() || null,
      frequency: row[colFreq]?.trim() || null,
      annualisedReturn: normalizePercent(row[colAnn]?.trim() ?? ""),
      url,
    });
  }
  return out;
}

async function fetchSheet(locale: keyof typeof SHEETS): Promise<SheetRow[]> {
  const res = await fetch(SHEETS[locale]);
  if (!res.ok) throw new Error(`Failed to fetch ${locale} sheet: ${res.status}`);
  const text = await res.text();
  return mapRows(parseCsv(text));
}

async function main() {
  const dryRun = process.argv.includes("--dry-run");
  let updated = 0;
  let missed = 0;

  for (const locale of ["en", "zh"] as const) {
    const rows = await fetchSheet(locale);
    const strategies = await prisma.strategy.findMany({
      where: { locale },
      select: { id: true, slug: true, academicLink: true },
    });
    const bySlug = new Map(
      strategies.map((s) => [canonicalSlug(s.slug), s]),
    );

    for (const row of rows) {
      const key = slugFromUrl(row.url);
      if (!key) {
        missed++;
        continue;
      }
      const match = bySlug.get(key);
      if (!match) {
        missed++;
        continue;
      }

      if (!dryRun) {
        await prisma.strategy.update({
          where: { id: match.id },
          data: {
            sortOrder: row.sortOrder,
            ...(row.title ? { title: row.title } : {}),
            assetClass: row.assetClass,
            market: row.market,
            region: row.region,
            frequency: row.frequency,
            annualisedReturn: row.annualisedReturn,
            ...(!match.academicLink ? { academicLink: row.url } : {}),
          },
        });
      }
      updated++;
    }
    console.log(`${locale}: processed ${rows.length} sheet rows`);
  }

  console.log(
    dryRun
      ? `[dry-run] Would update ${updated} strategies (${missed} unmatched)`
      : `Updated ${updated} strategies (${missed} unmatched)`,
  );
}

main()
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
