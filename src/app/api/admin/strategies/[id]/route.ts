import { NextResponse } from "next/server";
import { z } from "zod";

import { detectPythonCode, strategyCodeBlob } from "@/lib/detect-python";
import { requireAdminResponse } from "@/lib/authz";
import prisma from "@/lib/prisma";

function omitUndefined(record: Record<string, unknown>) {
  return Object.fromEntries(
    Object.entries(record).filter(([, value]) => value !== undefined),
  );
}

const updateSchema = z
  .object({
    slug: z.string().min(2).optional(),
    title: z.string().min(3).optional(),
    teaser: z.string().optional(),
    summary: z.string().optional(),
    contentHtml: z.string().optional(),
    backtestMetrics: z.string().optional(),
    annualisedReturn: z.string().optional().nullable(),
    sharpeRatio: z.string().optional().nullable(),
    volatility: z.string().optional().nullable(),
    beta: z.string().optional().nullable(),
    sortinoRatio: z.string().optional().nullable(),
    maxDrawdown: z.string().optional().nullable(),
    winRate: z.string().optional().nullable(),
    region: z.string().optional().nullable(),
    market: z.string().optional().nullable(),
    assetClass: z.string().optional().nullable(),
    frequency: z.string().optional().nullable(),
    isPaywalled: z.boolean().optional(),
    published: z.boolean().optional(),
    paperTitle: z.string().optional().nullable(),
    paperAuthors: z.string().optional().nullable(),
    paperInstitute: z.string().optional().nullable(),
    academicLink: z.string().optional().nullable(),
    economicRationale: z.string().optional(),
    pythonCodeHtml: z.string().optional(),
    metaTitle: z.string().optional().nullable(),
    metaDescription: z.string().optional().nullable(),
    sortOrder: z.number().int().optional(),
  })
  .strict();

type RouteContext = {
  params: Promise<{ id: string }>;
};

export async function GET(_request: Request, context: RouteContext) {
  const guard = await requireAdminResponse();
  if (guard) return guard;

  const { id } = await context.params;
  const strategy = await prisma.strategy.findUnique({
    where: { id },
  });

  if (!strategy) {
    return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
  }

  return NextResponse.json({ strategy });
}

export async function PATCH(request: Request, context: RouteContext) {
  const guard = await requireAdminResponse();
  if (guard) return guard;

  const { id } = await context.params;
  const parsed = updateSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
  }

  try {
    const patch = omitUndefined(parsed.data) as Record<string, unknown>;
    if (typeof patch.contentHtml === "string" || typeof patch.pythonCodeHtml === "string") {
      const existing = await prisma.strategy.findUnique({
        where: { id },
        select: { contentHtml: true, pythonCodeHtml: true },
      });
      patch.hasPythonCode = detectPythonCode(
        strategyCodeBlob(
          typeof patch.contentHtml === "string" ? patch.contentHtml : existing?.contentHtml,
          typeof patch.pythonCodeHtml === "string" ? patch.pythonCodeHtml : existing?.pythonCodeHtml,
        ),
      );
    }
    const strategy = await prisma.strategy.update({
      where: { id },
      data: patch,
    });
    return NextResponse.json({ strategy });
  } catch (error) {
    console.error("[admin.strategy.update]", error);
    return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
  }
}

export async function DELETE(_request: Request, context: RouteContext) {
  const guard = await requireAdminResponse();
  if (guard) return guard;

  const { id } = await context.params;
  try {
    await prisma.strategy.delete({
      where: { id },
    });
    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error("[admin.strategy.delete]", error);
    return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
  }
}
