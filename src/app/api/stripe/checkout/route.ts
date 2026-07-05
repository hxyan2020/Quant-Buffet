import { NextResponse } from "next/server";
import { auth } from "@/auth";

import { stripeServer } from "@/lib/stripe";

const ALLOWED_LOCALES = new Set(["en", "zh"]);

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
    }

    const body = await request.json().catch(() => ({}));
    const localeCandidate = typeof body.locale === "string" ? body.locale : "";
    const locale =
      ALLOWED_LOCALES.has(localeCandidate) ?
        localeCandidate
      : "";

    if (!locale) {
      return NextResponse.json({ error: "BAD_LOCALE" }, { status: 400 });
    }

    const stripe = stripeServer();
    if (!stripe) {
      return NextResponse.json({ error: "STRIPE_NOT_CONFIGURED" }, { status: 500 });
    }

    const origin = process.env.AUTH_URL ?? request.headers.get("origin") ?? "";

    const checkout = await stripe.checkout.sessions.create({
      mode: "payment",
      customer_email: session.user.email ?? undefined,
      metadata: {
        userId: session.user.id,
        locale,
      },
      client_reference_id: session.user.id,
      payment_method_types: ["card"],
      line_items: [
        {
          price_data: {
            currency: "usd",
            unit_amount: 9900,
            product_data: {
              name:
                locale === "zh"
                  ? "Quant Buffet — 全库策略解锁（中英）"
                  : "Quant Buffet — full library (EN + zh)",
              description:
                locale === "zh"
                  ? "一次性付款，1 个月内解锁本站中英文全部付费策略正文。"
                  : "One-time payment. Unlocks every paid strategy in English and Chinese for 1 month.",
            },
          },
          quantity: 1,
        },
      ],
      success_url: `${origin}/${locale}/account/plan?stripe=success`,
      cancel_url: `${origin}/${locale}/pricing?stripe=canceled`,
    });

    return NextResponse.json({ url: checkout.url });
  } catch (error) {
    console.error("[stripe-checkout]", error);
    return NextResponse.json({ error: "STRIPE_ERROR" }, { status: 500 });
  }
}
