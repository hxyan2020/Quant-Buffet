import { PrismaClient } from "@prisma/client";

/** Bump when Prisma schema changes so dev HMR does not reuse a stale client. */
const PRISMA_CLIENT_GENERATION = 7;

type GlobalPrisma = {
  prismaClient?: PrismaClient;
  prismaClientGen?: number;
  /** Legacy singleton — remove after hot reload */
  prisma?: PrismaClient;
};

const globalStore = globalThis as unknown as GlobalPrisma;

if (globalStore.prisma) {
  void globalStore.prisma.$disconnect().catch(() => {});
  delete globalStore.prisma;
}

function createPrismaClient() {
  return new PrismaClient({
    log: process.env.NODE_ENV === "development" ? ["error", "warn"] : ["error"],
  });
}

function needsFreshClient() {
  return (
    !globalStore.prismaClient ||
    globalStore.prismaClientGen !== PRISMA_CLIENT_GENERATION
  );
}

if (needsFreshClient()) {
  if (globalStore.prismaClient) {
    void globalStore.prismaClient.$disconnect().catch(() => {});
  }
  globalStore.prismaClient = createPrismaClient();
  globalStore.prismaClientGen = PRISMA_CLIENT_GENERATION;
}

export const prisma = globalStore.prismaClient!;

if (process.env.NODE_ENV !== "production") {
  globalStore.prismaClient = prisma;
  globalStore.prismaClientGen = PRISMA_CLIENT_GENERATION;
}

export default prisma;
