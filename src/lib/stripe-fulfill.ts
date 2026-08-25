import type Stripe from "stripe";

import prisma from "@/lib/prisma";
import { computePlanPeriodEnd, getLibraryPlan, isPlanId, type PlanId } from "@/lib/plans";

export type FulfillResult =
  | { ok: true; alreadyFulfilled: boolean; userId: string; planId: PlanId; periodEnd: Date }
  | { ok: false; error: string };

function extractCustomerId(session: Stripe.Checkout.Session): string | null {
  const customer = session.customer;
  if (typeof customer === "string") return customer;
  if (customer && typeof customer === "object" && "deleted" in customer && customer.deleted) {
    return null;
  }
  if (customer && typeof customer === "object" && "id" in customer && typeof customer.id === "string") {
    return customer.id;
  }
  return null;
}

function extractPaymentIntentId(session: Stripe.Checkout.Session): string | null {
  const pi = session.payment_intent;
  if (typeof pi === "string") return pi;
  if (pi && typeof pi === "object" && "id" in pi && typeof pi.id === "string") {
    return pi.id;
  }
  return null;
}

async function resolveUserId(session: Stripe.Checkout.Session): Promise<string | null> {
  let userId: string | null = session.metadata?.userId ?? session.client_reference_id ?? null;
  const emailFallback = session.customer_details?.email ?? session.customer_email;

  if (!userId && emailFallback) {
    const fallbackUser = await prisma.user.findUnique({
      where: { email: emailFallback.toLowerCase() },
      select: { id: true },
    });
    userId = fallbackUser?.id ?? null;
  }

  return userId;
}

/**
 * Idempotent entitlement grant after a paid Checkout Session.
 * Safe to call from webhooks and the success-page confirm endpoint.
 */
export async function fulfillCheckoutSession(session: Stripe.Checkout.Session): Promise<FulfillResult> {
  if (session.mode !== "payment") {
    return { ok: false, error: "UNSUPPORTED_MODE" };
  }

  const paid =
    session.payment_status === "paid" ||
    session.payment_status === "no_payment_required" ||
    session.status === "complete";

  if (!paid) {
    return { ok: false, error: "NOT_PAID" };
  }

  const userId = await resolveUserId(session);
  if (!userId) {
    console.warn("[stripe-fulfill] missing user reference", session.id);
    return { ok: false, error: "MISSING_USER" };
  }

  const duplicate = await prisma.subscription.findFirst({
    where: { stripeCheckoutSession: session.id },
    select: { id: true, tier: true, currentPeriodEnd: true },
  });
  if (duplicate) {
    const planId = isPlanId(duplicate.tier) ? duplicate.tier : "library-1m";
    return {
      ok: true,
      alreadyFulfilled: true,
      userId,
      planId,
      periodEnd: duplicate.currentPeriodEnd ?? new Date(),
    };
  }

  const planIdMeta = session.metadata?.planId;
  const plan = isPlanId(planIdMeta) ? getLibraryPlan(planIdMeta) : getLibraryPlan("library-1m");

  const existing = await prisma.subscription.findFirst({
    where: { userId, status: "active" },
    orderBy: { currentPeriodEnd: "desc" },
    select: { currentPeriodEnd: true },
  });

  const periodEnd = computePlanPeriodEnd(
    plan.durationDays,
    new Date(),
    existing?.currentPeriodEnd ?? null,
  );

  const customerId = extractCustomerId(session);

  await prisma.$transaction(async (tx) => {
    await tx.user.update({
      where: { id: userId },
      data: { libraryUnlocked: true },
    });
    await tx.subscription.create({
      data: {
        userId,
        stripeCustomerId: customerId,
        stripeCheckoutSession: session.id,
        stripePaymentIntentId: extractPaymentIntentId(session),
        status: "active",
        tier: plan.id,
        currentPeriodEnd: periodEnd,
        cancelAtPeriodEnd: false,
      },
    });

    // Keep older active rows, but clear cancel flags when renewing.
    if (existing) {
      await tx.subscription.updateMany({
        where: { userId, status: "active", cancelAtPeriodEnd: true },
        data: { cancelAtPeriodEnd: false },
      });
    }
  });

  return { ok: true, alreadyFulfilled: false, userId, planId: plan.id, periodEnd };
}
