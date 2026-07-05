import { headers } from "next/headers";
import { NextResponse } from "next/server";

import prisma from "@/lib/prisma";
import { stripeServer } from "@/lib/stripe";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const stripe = stripeServer();
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!stripe || !webhookSecret) {
    return NextResponse.json({ received: false, error: "not_configured" }, { status: 500 });
  }

  const body = await request.text();
  const headerBag = await headers();
  const signature = headerBag.get("stripe-signature");
  if (!signature) {
    return NextResponse.json({ error: "missing_signature" }, { status: 400 });
  }

  let event: import("stripe").Stripe.Event;

  try {
    event = stripe.webhooks.constructEvent(body, signature, webhookSecret);
  } catch (err) {
    console.error("[stripe-webhook-verify]", err);
    return NextResponse.json({ error: "invalid_signature" }, { status: 400 });
  }

  switch (event.type) {
    case "checkout.session.completed": {
      const session = event.data.object as import("stripe").Stripe.Checkout.Session;
      let userId: string | null = session.metadata?.userId ?? session.client_reference_id ?? null;
      const emailFallback = session.customer_details?.email;

      if (!userId && emailFallback) {
        const fallbackUser = await prisma.user.findUnique({
          where: { email: emailFallback.toLowerCase() },
          select: { id: true },
        });
        userId = fallbackUser?.id ?? null;
      }

      if (!userId) {
        console.warn("[stripe-webhook] missing user reference", session.id);
        break;
      }

      const duplicate = await prisma.subscription.findFirst({
        where: { stripeCheckoutSession: session.id },
        select: { id: true },
      });
      if (duplicate) {
        break;
      }

      const periodEnd = new Date();
      periodEnd.setMonth(periodEnd.getMonth() + 1);

      await prisma.$transaction(async (tx) => {
        await tx.user.update({
          where: { id: userId },
          data: {
            libraryUnlocked: true,
          },
        });
        await tx.subscription.create({
          data: {
            userId,
            stripeCustomerId: extractCustomerId(session),
            stripeCheckoutSession: session.id,
            stripePaymentIntentId: extractPaymentIntentId(session),
            status: "active",
            tier: "full-library",
            currentPeriodEnd: periodEnd,
            cancelAtPeriodEnd: false,
          },
        });
      });
      break;
    }
    default:
      break;
  }

  return NextResponse.json({ received: true });
}

function extractCustomerId(session: import("stripe").Stripe.Checkout.Session) {
  const customer = session.customer;
  if (typeof customer === "string") return customer;
  if (
    customer &&
    typeof customer === "object" &&
    "deleted" in customer &&
    customer.deleted
  ) {
    return null;
  }
  if (
    customer &&
    typeof customer === "object" &&
    "id" in customer &&
    typeof customer.id === "string"
  ) {
    return customer.id;
  }
  return null;
}

function extractPaymentIntentId(session: import("stripe").Stripe.Checkout.Session) {
  const pi = session.payment_intent;
  if (typeof pi === "string") return pi;
  if (pi && typeof pi === "object" && "id" in pi && typeof pi.id === "string") {
    return pi.id;
  }
  return null;
}