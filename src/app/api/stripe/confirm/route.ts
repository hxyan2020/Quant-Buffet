import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { fulfillCheckoutSession } from "@/lib/stripe-fulfill";
import { stripeServer } from "@/lib/stripe";
import { syncUserPlanAccess } from "@/lib/subscription";

export const runtime = "nodejs";

/** Confirm a Checkout Session after redirect (covers webhook lag). */
export async function POST(request: Request) {
  const authSession = await auth();
  if (!authSession?.user?.id) {
    return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
  }

  const body = await request.json().catch(() => ({}));
  const sessionId = typeof body.sessionId === "string" ? body.sessionId.trim() : "";
  if (!sessionId.startsWith("cs_")) {
    return NextResponse.json({ error: "BAD_SESSION" }, { status: 400 });
  }

  const stripe = stripeServer();
  if (!stripe) {
    return NextResponse.json({ error: "STRIPE_NOT_CONFIGURED" }, { status: 500 });
  }

  try {
    const checkout = await stripe.checkout.sessions.retrieve(sessionId);
    const owner =
      checkout.metadata?.userId ??
      checkout.client_reference_id ??
      null;
    if (owner && owner !== authSession.user.id) {
      return NextResponse.json({ error: "FORBIDDEN" }, { status: 403 });
    }

    const result = await fulfillCheckoutSession(checkout);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 400 });
    }

    const state = await syncUserPlanAccess(authSession.user.id);
    return NextResponse.json({
      ok: true,
      alreadyFulfilled: result.alreadyFulfilled,
      planId: result.planId,
      periodEnd: result.periodEnd.toISOString(),
      hasActivePlan: state.hasActivePlan,
    });
  } catch (error) {
    console.error("[stripe-confirm]", error);
    return NextResponse.json({ error: "STRIPE_ERROR" }, { status: 500 });
  }
}
