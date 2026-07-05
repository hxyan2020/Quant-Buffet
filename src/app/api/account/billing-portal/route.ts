import { NextResponse } from "next/server";

import { auth } from "@/auth";
import prisma from "@/lib/prisma";
import { stripeServer } from "@/lib/stripe";

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
  }

  const stripe = stripeServer();
  if (!stripe) {
    return NextResponse.json({ error: "STRIPE_NOT_CONFIGURED" }, { status: 500 });
  }

  const sub = await prisma.subscription.findFirst({
    where: { userId: session.user.id, stripeCustomerId: { not: null } },
    orderBy: { id: "desc" },
    select: { stripeCustomerId: true },
  });

  if (!sub?.stripeCustomerId) {
    return NextResponse.json({ error: "NO_CUSTOMER" }, { status: 400 });
  }

  const body = await request.json().catch(() => ({}));
  const locale = typeof body.locale === "string" ? body.locale : "en";
  const origin = process.env.AUTH_URL ?? request.headers.get("origin") ?? "";

  const portalSession = await stripe.billingPortal.sessions.create({
    customer: sub.stripeCustomerId,
    return_url: `${origin}/${locale}/account/payment`,
  });

  return NextResponse.json({ url: portalSession.url });
}
