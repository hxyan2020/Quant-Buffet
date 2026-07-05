import { scanAllStrategiesForPython } from "../src/lib/admin-strategies";
import prisma from "../src/lib/prisma";

scanAllStrategiesForPython()
  .then((result) => {
    console.log(`Scanned ${result.total} strategies — ${result.withPython} with Python code.`);
  })
  .catch((err) => {
    console.error(err);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
