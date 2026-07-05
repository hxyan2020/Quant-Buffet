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
});

export async function POST(request: Request) {
  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "BAD_REQUEST" }, { status: 400 });
  }

  const { strategy } = parsed.data;
  const provider = resolveLlmProvider(request, strategy.locale);
  const lang = strategy.locale === "zh" ? "Chinese" : "English";

  const system = `You help retail investors understand quantitative trading strategies. Output ONLY a JSON array of exactly 4 short questions in ${lang}, no jargon, each under 90 characters. No markdown.`;

  const user = `Strategy: ${strategy.title}
Teaser: ${strategy.teaser ?? "N/A"}
Summary: ${strategy.summary ?? "N/A"}
Economic rationale: ${strategy.economicRationale ?? "N/A"}
Generate 4 specific questions a reader might ask about THIS strategy.`;

  try {
    const raw = await chatCompletion({ provider, system, user, maxTokens: 400 });
    const match = raw.match(/\[[\s\S]*\]/);
    const questions = match ? (JSON.parse(match[0]) as string[]) : [];
    if (!Array.isArray(questions) || questions.length === 0) {
      throw new Error("parse");
    }
    return NextResponse.json({ questions: questions.slice(0, 4), provider });
  } catch {
    return NextResponse.json({
      questions:
        strategy.locale === "zh"
          ? [
              "这个策略的核心逻辑是什么？",
              "最大的风险在哪里？",
              "适合什么样的市场环境？",
              "回测结果可靠吗？",
            ]
          : [
              "What is the core idea of this strategy?",
              "What is the main risk?",
              "When does it work best?",
              "How trustworthy is the backtest?",
            ],
      provider,
    });
  }
}
