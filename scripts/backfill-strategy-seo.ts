/**
 * Backfill strategy metaTitle / metaDescription with SEO-ready copy.
 *
 * Usage:
 *   npx tsx scripts/backfill-strategy-seo.ts
 *   npx tsx scripts/backfill-strategy-seo.ts --dry-run
 */
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();
const dryRun = process.argv.includes("--dry-run");
const SITE = "Quant Buffet";

function clip(text: string, max: number): string {
  const clean = text.replace(/\s+/g, " ").trim();
  if (clean.length <= max) return clean;
  const sliced = clean.slice(0, max - 1);
  const lastSpace = sliced.lastIndexOf(" ");
  return `${(lastSpace > 40 ? sliced.slice(0, lastSpace) : sliced).trim()}…`;
}

function metric(label: string, value?: string | null) {
  if (!value?.trim() || value.trim().toUpperCase() === "N/A") return null;
  return `${label} ${value.trim()}`;
}

function build(row: {
  title: string;
  locale: string;
  teaser: string;
  assetClass: string | null;
  region: string | null;
  market: string | null;
  frequency: string | null;
  annualisedReturn: string | null;
  sharpeRatio: string | null;
}) {
  const isZh = row.locale === "zh";
  const asset = row.assetClass?.split(",")[0]?.trim() || (isZh ? "多资产" : "multi-asset");
  const region = row.region?.trim() || (isZh ? "全球" : "global");
  const market = row.market?.trim() || (isZh ? "市场" : "markets");
  const title = clip(
    isZh ? `${row.title}｜${asset}量化策略 · ${SITE}` : `${row.title} | ${asset} Quant Strategy · ${SITE}`,
    65,
  );
  const teaserBit = row.teaser?.trim();
  const usefulTeaser =
    teaserBit && teaserBit.toUpperCase() !== "N/A" && teaserBit.length > 40 ? clip(teaserBit, 90) : null;
  const bits = [
    usefulTeaser,
    isZh ? `${region}${market}量化交易策略（${asset}）` : `${region} ${market} quant strategy (${asset})`,
    row.frequency ? (isZh ? `调仓：${row.frequency}` : `${row.frequency} rebalance`) : null,
    metric(isZh ? "年化" : "ann.", row.annualisedReturn),
    metric(isZh ? "夏普" : "Sharpe", row.sharpeRatio),
    isZh ?
      "含学术依据与 QuantConnect/LEAN Python 实现。"
    : "Academic rationale + QuantConnect/LEAN Python.",
  ].filter(Boolean) as string[];
  return { title, description: clip(bits.join(" · "), 160) };
}

async function main() {
  const rows = await prisma.strategy.findMany({
    where: { published: true },
    select: {
      id: true,
      title: true,
      locale: true,
      teaser: true,
      assetClass: true,
      region: true,
      market: true,
      frequency: true,
      annualisedReturn: true,
      sharpeRatio: true,
      metaTitle: true,
      metaDescription: true,
    },
  });

  let updated = 0;
  for (const row of rows) {
    const next = build(row);
    if (row.metaTitle === next.title && row.metaDescription === next.description) continue;
    updated += 1;
    if (dryRun) {
      if (updated <= 3) {
        console.log("---", row.locale, row.title);
        console.log("NEW title", next.title);
        console.log("NEW desc", next.description);
      }
      continue;
    }
    await prisma.strategy.update({
      where: { id: row.id },
      data: { metaTitle: next.title, metaDescription: next.description },
    });
  }
  console.log(`${dryRun ? "Would update" : "Updated"} ${updated} / ${rows.length} strategies`);
}

main()
  .catch((err) => {
    console.error(err);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
