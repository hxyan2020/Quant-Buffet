import { NextResponse } from "next/server";
import { z } from "zod";

import { chatCompletion, resolveLlmProvider } from "@/lib/llm-router";

const bodySchema = z.object({
  strategy: z.object({
    slug: z.string(),
    locale: z.string(),
    title: z.string(),
    teaser: z.string().optional(),
    summary: z.string().optional(),
    economicRationale: z.string().optional(),
  }),
  question: z.string().min(3).max(500),
});

export async function POST(request: Request) {
  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "BAD_REQUEST" }, { status: 400 });
  }

  const { strategy, question } = parsed.data;
  const provider = resolveLlmProvider(request, strategy.locale);
  const lang = strategy.locale === "zh" ? "Chinese" : "English";

  const system = `You explain quant strategies to non-experts in ${lang}. Use one concise paragraph (80-120 words), no jargon, no bullet lists, no markdown. Be practical and honest about limits.`;

  const user = `Strategy: ${strategy.title}
Teaser: ${strategy.teaser ?? "N/A"}
Summary: ${strategy.summary ?? "N/A"}
Economic rationale: ${strategy.economicRationale ?? "N/A"}

Question: ${question}`;

  try {
    const answer = await chatCompletion({ provider, system, user, maxTokens: 350 });
    return NextResponse.json({ answer, provider });
  } catch (error) {
    console.error("[strategy-ai.answer]", error);
    return NextResponse.json({ error: "MODEL_ERROR" }, { status: 502 });
  }
}
