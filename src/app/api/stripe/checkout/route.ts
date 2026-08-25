import { NextResponse } from "next/server";

import { auth } from "@/auth";
import prisma from "@/lib/prisma";
import { getLibraryPlan, isPlanId } from "@/lib/plans";
import { stripeServer } from "@/lib/stripe";

const ALLOWED_LOCALES = new Set(["en", "zh"]);

const PRODUCT_COPY: Record<
  string,
  { en: string; zh: string; enDesc: string; zhDesc: string }
> = {
  "library-7d": {
    en: "Quant Buffet — 7-day library pass",
    zh: "Quant Buffet — 7 天全库通行证",
    enDesc: "One-time payment. Full EN + zh paid library for 7 days.",
    zhDesc: "一次性付款，解锁中英文付费策略全文，有效期 7 天。",
  },
  "library-1m": {
    en: "Quant Buffet — 1-month library unlock",
    zh: "Quant Buffet — 1 个月全库解锁",
    enDesc: "One-time payment. Full EN + zh paid library for 1 month.",
    zhDesc: "一次性付款，解锁中英文付费策略全文，有效期 1 个月。",
  },
  "library-3m": {
    en: "Quant Buffet — 3-month library unlock",
    zh: "Quant Buffet — 3 个月全库解锁",
    enDesc: "One-time payment. Full EN + zh paid library for 3 months (~10% off).",
    zhDesc: "一次性付款，解锁中英文付费策略全文，有效期 3 个月（约九折）。",
  },
  "library-6m": {
    en: "Quant Buffet — 6-month library unlock",
    zh: "Quant Buffet — 6 个月全库解锁",
    enDesc: "One-time payment. Full EN + zh paid library for 6 months (~15% off).",
    zhDesc: "一次性付款，解锁中英文付费策略全文，有效期 6 个月（约八五折）。",
  },
  "library-1y": {
    en: "Quant Buffet — 1-year library unlock",
    zh: "Quant Buffet — 1 年全库解锁",
    enDesc: "One-time payment. Full EN + zh paid library for 1 year (~20% off).",
    zhDesc: "一次性付款，解锁中英文付费策略全文，有效期 1 年（约八折）。",
  },
};

export async function POST(request: Request) {
  try {
    const session = await auth();
    if (!session?.user?.id) {
      return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
    }

    const body = await request.json().catch(() => ({}));
    const localeCandidate = typeof body.locale === "string" ? body.locale : "";
    const locale = ALLOWED_LOCALES.has(localeCandidate) ? localeCandidate : "";
    const planIdRaw = typeof body.planId === "string" ? body.planId : "";

    if (!locale) {
      return NextResponse.json({ error: "BAD_LOCALE" }, { status: 400 });
    }
    if (!isPlanId(planIdRaw)) {
      return NextResponse.json({ error: "BAD_PLAN" }, { status: 400 });
    }

    const plan = getLibraryPlan(planIdRaw);
    const stripe = stripeServer();
    if (!stripe) {
      return NextResponse.json({ error: "STRIPE_NOT_CONFIGURED" }, { status: 500 });
    }

    const origin = process.env.AUTH_URL ?? request.headers.get("origin") ?? "";
    if (!origin) {
      return NextResponse.json({ error: "MISSING_ORIGIN" }, { status: 500 });
    }

    const isZh = locale === "zh";
    const copy = PRODUCT_COPY[plan.id];
    const email = session.user.email?.trim().toLowerCase() || undefined;

    const prior = await prisma.subscription.findFirst({
      where: { userId: session.user.id, stripeCustomerId: { not: null } },
      orderBy: { id: "desc" },
      select: { stripeCustomerId: true },
    });

    let customerId = prior?.stripeCustomerId ?? null;
    if (customerId) {
      try {
        await stripe.customers.retrieve(customerId);
      } catch {
        customerId = null;
      }
    }

    if (!customerId) {
      const customer = await stripe.customers.create({
        email,
        name: session.user.name ?? undefined,
        metadata: { userId: session.user.id },
      });
      customerId = customer.id;
    }

    const checkout = await stripe.checkout.sessions.create({
      mode: "payment",
      customer: customerId,
      client_reference_id: session.user.id,
      metadata: {
        userId: session.user.id,
        locale,
        planId: plan.id,
        durationDays: String(plan.durationDays),
      },
      line_items: [
        {
          price_data: {
            currency: "usd",
            unit_amount: plan.unitAmount,
            product_data: {
              name: isZh ? copy.zh : copy.en,
              description: isZh ? copy.zhDesc : copy.enDesc,
            },
          },
          quantity: 1,
        },
      ],
      payment_intent_data: {
        setup_future_usage: "off_session",
        metadata: {
          userId: session.user.id,
          planId: plan.id,
        },
      },
      saved_payment_method_options: {
        payment_method_save: "enabled",
      },
      success_url: `${origin}/${locale}/account/plan?stripe=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${origin}/${locale}/pricing?stripe=canceled`,
    });

    if (!checkout.url) {
      return NextResponse.json({ error: "STRIPE_NO_URL" }, { status: 500 });
    }

    return NextResponse.json({ url: checkout.url });
  } catch (error) {
    console.error("[stripe-checkout]", error);
    return NextResponse.json({ error: "STRIPE_ERROR" }, { status: 500 });
  }
}
