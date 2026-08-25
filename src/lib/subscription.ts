import prisma from "@/lib/prisma";
import { getLibraryPlan, isPlanId } from "@/lib/plans";

export type UserPlanState = {
  hasActivePlan: boolean;
  tier: string | null;
  tierLabel: string | null;
  expiresAt: Date | null;
  cancelAtPeriodEnd: boolean;
  stripeCustomerId: string | null;
  status: "none" | "active" | "canceling" | "expired";
};

function addOneMonth(from: Date) {
  const end = new Date(from);
  end.setMonth(end.getMonth() + 1);
  return end;
}

function labelForTier(tier: string | null, locale = "en"): string | null {
  if (!tier) return null;
  if (isPlanId(tier)) {
    const days = getLibraryPlan(tier).durationDays;
    if (locale === "zh") {
      if (days === 7) return "7 天通行证";
      if (days === 30) return "1 个月全库";
      if (days === 90) return "3 个月全库";
      if (days === 180) return "6 个月全库";
      if (days === 365) return "1 年全库";
    }
    if (days === 7) return "7-day pass";
    if (days === 30) return "1-month library";
    if (days === 90) return "3-month library";
    if (days === 180) return "6-month library";
    if (days === 365) return "1-year library";
  }
  return tier;
}

/** Reconcile libraryUnlocked with the best active subscription period end. */
export async function syncUserPlanAccess(
  userId: string,
  locale = "en",
): Promise<UserPlanState> {
  if (!userId?.trim()) {
    return {
      hasActivePlan: false,
      tier: null,
      tierLabel: null,
      expiresAt: null,
      cancelAtPeriodEnd: false,
      stripeCustomerId: null,
      status: "none",
    };
  }

  const now = new Date();

  const subs = await prisma.subscription.findMany({
    where: { userId },
    orderBy: [{ currentPeriodEnd: "desc" }, { id: "desc" }],
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

  if (subs.length === 0) {
    await prisma.user.update({
      where: { id: userId },
      data: { libraryUnlocked: false },
    });
    return {
      hasActivePlan: false,
      tier: null,
      tierLabel: null,
      expiresAt: null,
      cancelAtPeriodEnd: false,
      stripeCustomerId: null,
      status: "none",
    };
  }

  // Expire rows whose period has ended.
  for (const sub of subs) {
    let periodEnd = sub.currentPeriodEnd;
    if (!periodEnd && sub.status === "active") {
      periodEnd = addOneMonth(sub.createdAt ?? sub.updatedAt ?? now);
      await prisma.subscription.update({
        where: { id: sub.id },
        data: { currentPeriodEnd: periodEnd },
      });
      sub.currentPeriodEnd = periodEnd;
    }
    if (sub.status === "active" && periodEnd && periodEnd <= now) {
      await prisma.subscription.update({
        where: { id: sub.id },
        data: { status: "expired" },
      });
      sub.status = "expired";
    }
  }

  const active = subs
    .filter((s) => s.status === "active" && s.currentPeriodEnd && s.currentPeriodEnd > now)
    .sort((a, b) => (b.currentPeriodEnd!.getTime() - a.currentPeriodEnd!.getTime()))[0];

  const latestCustomer =
    subs.find((s) => s.stripeCustomerId)?.stripeCustomerId ?? null;

  if (active) {
    await prisma.user.update({
      where: { id: userId },
      data: { libraryUnlocked: true },
    });
    return {
      hasActivePlan: true,
      tier: active.tier,
      tierLabel: labelForTier(active.tier, locale),
      expiresAt: active.currentPeriodEnd,
      cancelAtPeriodEnd: active.cancelAtPeriodEnd,
      stripeCustomerId: active.stripeCustomerId ?? latestCustomer,
      status: active.cancelAtPeriodEnd ? "canceling" : "active",
    };
  }

  await prisma.user.update({
    where: { id: userId },
    data: { libraryUnlocked: false },
  });

  const last = subs[0];
  return {
    hasActivePlan: false,
    tier: last?.tier ?? null,
    tierLabel: labelForTier(last?.tier ?? null, locale),
    expiresAt: last?.currentPeriodEnd ?? null,
    cancelAtPeriodEnd: false,
    stripeCustomerId: latestCustomer,
    status: "expired",
  };
}

export async function cancelUserPlan(userId: string) {
  const sub = await prisma.subscription.findFirst({
    where: { userId, status: "active" },
    orderBy: { currentPeriodEnd: "desc" },
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

/** Undo a scheduled end-of-period cancellation while access is still active. */
export async function resumeUserPlan(userId: string) {
  const sub = await prisma.subscription.findFirst({
    where: { userId, status: "active", cancelAtPeriodEnd: true },
    orderBy: { currentPeriodEnd: "desc" },
    select: { id: true },
  });
  if (!sub) return { ok: false as const, error: "NO_CANCELING_PLAN" };

  await prisma.subscription.update({
    where: { id: sub.id },
    data: { cancelAtPeriodEnd: false },
  });

  const state = await syncUserPlanAccess(userId);
  return { ok: true as const, state };
}
