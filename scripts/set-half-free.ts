import { setHalfFreePerLocale } from "../src/lib/admin-strategies";
import prisma from "../src/lib/prisma";

setHalfFreePerLocale()
  .then((count) => {
    console.log(`Updated paywall flag on ${count} strategies (≈50% free per locale).`);
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
