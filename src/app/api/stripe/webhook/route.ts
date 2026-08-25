import { headers } from "next/headers";
import { NextResponse } from "next/server";

import { fulfillCheckoutSession } from "@/lib/stripe-fulfill";
import { stripeServer } from "@/lib/stripe";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const stripe = stripeServer();
  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;

  if (!stripe || !webhookSecret) {
    return NextResponse.json({ received: false, error: "not_configured" }, { status: 500 });
  }

  const body = await request.text();
  const headerStore = await headers();
  const signature = headerStore.get("stripe-signature");
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

  try {
    switch (event.type) {
      case "checkout.session.completed":
      case "checkout.session.async_payment_succeeded": {
        const session = event.data.object as import("stripe").Stripe.Checkout.Session;
        const result = await fulfillCheckoutSession(session);
        if (!result.ok && result.error !== "NOT_PAID") {
          console.warn("[stripe-webhook-fulfill]", event.type, session.id, result.error);
        }
        break;
      }
      case "checkout.session.async_payment_failed": {
        const session = event.data.object as import("stripe").Stripe.Checkout.Session;
        console.warn("[stripe-webhook] async payment failed", session.id);
        break;
      }
      default:
        break;
    }
  } catch (err) {
    console.error("[stripe-webhook-handler]", err);
    return NextResponse.json({ error: "handler_failed" }, { status: 500 });
  }

  return NextResponse.json({ received: true });
}
