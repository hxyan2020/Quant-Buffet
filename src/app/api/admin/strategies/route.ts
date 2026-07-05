import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";

import { listAdminStrategies, loadAdminFilterOptionSets } from "@/lib/admin-strategies";
import { requireAdminResponse } from "@/lib/authz";
import prisma from "@/lib/prisma";

const createSchema = z.object({
  slug: z.string().min(2),
  locale: z.enum(["en", "zh"]),
  title: z.string().min(3),
  teaser: z.string().optional(),
  summary: z.string().optional(),
  contentHtml: z.string().optional(),
  backtestMetrics: z.string().optional(),
  annualisedReturn: z.string().optional(),
  sharpeRatio: z.string().optional(),
  volatility: z.string().optional(),
  beta: z.string().optional(),
  sortinoRatio: z.string().optional(),
  maxDrawdown: z.string().optional(),
  winRate: z.string().optional(),
  region: z.string().optional(),
  market: z.string().optional(),
  assetClass: z.string().optional(),
  frequency: z.string().optional(),
  isPaywalled: z.boolean().optional(),
  published: z.boolean().optional(),
  paperTitle: z.string().optional(),
  paperAuthors: z.string().optional(),
  paperInstitute: z.string().optional(),
  academicLink: z.string().optional(),
  economicRationale: z.string().optional(),
  pythonCodeHtml: z.string().optional(),
  metaTitle: z.string().optional(),
  metaDescription: z.string().optional(),
  sortOrder: z.number().int().optional(),
});

export async function GET(request: NextRequest) {
  const guard = await requireAdminResponse();
  if (guard) return guard;

  const params = request.nextUrl.searchParams;
  const filters = {
    q: params.get("q") ?? undefined,
    locale: params.get("locale") ?? undefined,
    paywall: (params.get("paywall") ?? "") as "" | "yes" | "no",
    published: (params.get("published") ?? "") as "" | "yes" | "no",
    region: params.get("region") ?? undefined,
    market: params.get("market") ?? undefined,
    assetClass: params.get("assetClass") ?? undefined,
    python: (params.get("python") ?? "") as "" | "yes" | "no",
    createdMin: params.get("createdMin") ?? undefined,
    createdMax: params.get("createdMax") ?? undefined,
    updatedMin: params.get("updatedMin") ?? undefined,
    updatedMax: params.get("updatedMax") ?? undefined,
  };

  const [strategies, filterOptions] = await Promise.all([
    listAdminStrategies(filters),
    loadAdminFilterOptionSets(),
  ]);

  return NextResponse.json({ strategies, filterOptions, total: strategies.length });
}

export async function POST(request: Request) {
  const guard = await requireAdminResponse();
  if (guard) return guard;

  const parsed = createSchema.safeParse(await request.json());
  if (!parsed.success) {
    return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
  }

  const data = parsed.data;
  const { detectPythonCode, strategyCodeBlob } = await import("@/lib/detect-python");

  try {
    const created = await prisma.strategy.create({
      data: {
        slug: data.slug,
        locale: data.locale,
        title: data.title,
        teaser: data.teaser ?? "",
        summary: data.summary ?? "",
        contentHtml: data.contentHtml ?? "",
        backtestMetrics: data.backtestMetrics ?? "{}",
        annualisedReturn: data.annualisedReturn,
        sharpeRatio: data.sharpeRatio,
        volatility: data.volatility,
        beta: data.beta,
        sortinoRatio: data.sortinoRatio,
        maxDrawdown: data.maxDrawdown,
        winRate: data.winRate,
        region: data.region,
        market: data.market,
        assetClass: data.assetClass,
        frequency: data.frequency,
        isPaywalled: data.isPaywalled ?? true,
        published: data.published ?? false,
        hasPythonCode: detectPythonCode(
          strategyCodeBlob(data.contentHtml ?? "", data.pythonCodeHtml ?? ""),
        ),
        paperTitle: data.paperTitle,
        paperAuthors: data.paperAuthors,
        paperInstitute: data.paperInstitute?.trim() || "N/A",
        academicLink: data.academicLink,
        economicRationale: data.economicRationale ?? "",
        pythonCodeHtml: data.pythonCodeHtml ?? "",
        metaTitle: data.metaTitle,
        metaDescription: data.metaDescription,
        sortOrder: data.sortOrder ?? 0,
      },
    });
    return NextResponse.json({ strategy: created }, { status: 201 });
  } catch (error) {
    console.error("[admin.strategy.create]", error);
    return NextResponse.json({ error: "CONFLICT_OR_DB" }, { status: 409 });
  }
}
