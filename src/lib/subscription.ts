import prisma from "@/lib/prisma";

export type UserPlanState = {
  hasActivePlan: boolean;
  tier: string | null;
  expiresAt: Date | null;
  cancelAtPeriodEnd: boolean;
  stripeCustomerId: string | null;
};

function addOneMonth(from: Date) {
  const end = new Date(from);
  end.setMonth(end.getMonth() + 1);
  return end;
}

/** Reconcile libraryUnlocked with subscription period end. */
export async function syncUserPlanAccess(userId: string): Promise<UserPlanState> {
  if (!userId?.trim()) {
    return {
      hasActivePlan: false,
      tier: null,
      expiresAt: null,
      cancelAtPeriodEnd: false,
      stripeCustomerId: null,
    };
  }

  const sub = await prisma.subscription.findFirst({
    where: { userId },
    orderBy: { id: "desc" },
    select: {
      id: true,
      tier: true,
      status: true,
      stripeCustomerId: true,
      currentPeriodEnd: true,
      cancelAtPeriodEnd: true,
      createdAt: true,
      updatedAt: true,
    },
  });

  const now = new Date();

  if (!sub) {
    await prisma.user.update({
      where: { id: userId },
      data: { libraryUnlocked: false },
    });
    return {
      hasActivePlan: false,
      tier: null,
      expiresAt: null,
      cancelAtPeriodEnd: false,
      stripeCustomerId: null,
    };
  }

  let periodEnd = sub.currentPeriodEnd;
  if (!periodEnd && sub.status === "active") {
    const anchor = sub.createdAt ?? sub.updatedAt ?? new Date();
    periodEnd = addOneMonth(anchor);
    await prisma.subscription.update({
      where: { id: sub.id },
      data: { currentPeriodEnd: periodEnd },
    });
  }

  const stillActive = periodEnd ? periodEnd > now : sub.status === "active";

  if (stillActive) {
    await prisma.user.update({
      where: { id: userId },
      data: { libraryUnlocked: true },
    });
    return {
      hasActivePlan: true,
      tier: sub.tier,
      expiresAt: periodEnd,
      cancelAtPeriodEnd: sub.cancelAtPeriodEnd,
      stripeCustomerId: sub.stripeCustomerId,
    };
  }

  await prisma.$transaction([
    prisma.user.update({
      where: { id: userId },
      data: { libraryUnlocked: false },
    }),
    prisma.subscription.update({
      where: { id: sub.id },
      data: { status: "expired" },
    }),
  ]);

  return {
    hasActivePlan: false,
    tier: sub.tier,
    expiresAt: periodEnd,
    cancelAtPeriodEnd: sub.cancelAtPeriodEnd,
    stripeCustomerId: sub.stripeCustomerId,
  };
}

export async function cancelUserPlan(userId: string) {
  const sub = await prisma.subscription.findFirst({
    where: { userId, status: "active" },
    orderBy: { id: "desc" },
    select: { id: true, cancelAtPeriodEnd: true },
  });
  if (!sub) return { ok: false as const, error: "NO_PLAN" };

  await prisma.subscription.update({
    where: { id: sub.id },
    data: { cancelAtPeriodEnd: true },
  });

  const state = await syncUserPlanAccess(userId);
  return { ok: true as const, state };
}
