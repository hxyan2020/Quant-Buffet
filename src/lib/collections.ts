import prisma from "@/lib/prisma";

export async function getCollectedStrategyIdSet(userId: string) {
  const rows = await prisma.strategyCollection.findMany({
    where: { userId },
    select: { strategyId: true },
  });
  return new Set(rows.map((r) => r.strategyId));
}

export async function isStrategyCollected(userId: string, strategyId: string) {
  const row = await prisma.strategyCollection.findUnique({
    where: { userId_strategyId: { userId, strategyId } },
    select: { id: true },
  });
  return Boolean(row);
}

/** All collected strategies (English + Chinese). */
export async function listCollectedStrategies(userId: string) {
  const rows = await prisma.strategyCollection.findMany({
    where: {
      userId,
      strategy: { published: true },
    },
    orderBy: { createdAt: "desc" },
    include: {
      strategy: {
        select: {
          id: true,
          slug: true,
          locale: true,
          title: true,
          market: true,
          region: true,
          annualisedReturn: true,
          sharpeRatio: true,
          isPaywalled: true,
        },
      },
    },
  });
  return rows.map((r) => ({ ...r.strategy, collectionId: r.id }));
}

export async function collectStrategy(userId: string, strategyId: string) {
  const strategy = await prisma.strategy.findFirst({
    where: { id: strategyId, published: true },
    select: { id: true },
  });
  if (!strategy) return { ok: false as const, error: "NOT_FOUND" };
  await prisma.strategyCollection.upsert({
    where: { userId_strategyId: { userId, strategyId } },
    create: { userId, strategyId },
    update: {},
  });
  return { ok: true as const };
}

export async function uncollectStrategy(userId: string, strategyId: string) {
  await prisma.strategyCollection.deleteMany({
    where: { userId, strategyId },
  });
  return { ok: true as const };
}
