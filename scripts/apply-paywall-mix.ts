import { applyFreeLibraryShare } from "../src/lib/paywall";
import prisma from "../src/lib/prisma";

applyFreeLibraryShare()
  .then((result) => {
    console.log(`Updated paywall flags on ${result.updated} published strategies (~20% free per locale).`);
    for (const row of result.locales) {
      const pct = row.total ? ((row.free / row.total) * 100).toFixed(1) : "0.0";
      console.log(`  ${row.locale}: ${row.free} free / ${row.paid} paid (${pct}% free of ${row.total})`);
    }
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
