/**
 * One-time fix: decode WordPress percent-encoded slugs in the database.
 * Run: npx tsx scripts/normalize-slugs.ts
 */

import { PrismaClient } from "@prisma/client";

import { canonicalSlug } from "../src/lib/slug";

const prisma = new PrismaClient();

async function main() {
  const rows = await prisma.strategy.findMany({ select: { id: true, slug: true } });
  let updated = 0;

  for (const row of rows) {
    const next = canonicalSlug(row.slug);
    if (next !== row.slug) {
      await prisma.strategy.update({
        where: { id: row.id },
        data: { slug: next },
      });
      updated++;
    }
  }

  console.log(`Normalized ${updated} / ${rows.length} strategy slugs.`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
