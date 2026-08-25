import { NextResponse } from "next/server";
import { z } from "zod";

import { draftPreviewEnabled, findDraftPost, labStrategyExists, loadLabIndex } from "@/lib/draft-preview";
import { heuristicLabAdvice, mergeLabAdvice, stripCodeFence, type LabSnippet } from "@/lib/lab-debug";
import { chatCompletion, resolveLlmProvider } from "@/lib/llm-router";

export const runtime = "nodejs";

const bodySchema = z.object({
  slug: z.string().min(1).max(120),
  locale: z.string().optional(),
  code: z.string().min(1).max(80_000),
  error: z
    .object({
      type: z.string().optional(),
      message: z.string(),
      line: z.number().nullable().optional(),
      column: z.number().nullable().optional(),
      traceback: z.string().optional(),
    })
    .optional(),
});

export async function POST(request: Request) {
  if (!draftPreviewEnabled()) {
    return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
  }

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "BAD_REQUEST" }, { status: 400 });
  }

  const { slug, locale = "en", code, error } = parsed.data;
  if (!labStrategyExists(slug) && !findDraftPost(slug)) {
    return NextResponse.json({ error: "UNKNOWN_DRAFT" }, { status: 404 });
  }
  const entry = loadLabIndex().strategies.find((s) => s.slug === slug);
  const title = entry?.title || findDraftPost(slug)?.title || slug;

  const runError = error || {
    type: "Help",
    message: "User asked for Quant Buffet syntax help (no runtime error yet).",
    line: null,
    traceback: "",
  };
  const fallback = heuristicLabAdvice(runError, code);

  const provider = resolveLlmProvider(request, locale);
  const lang = locale === "zh" ? "Chinese" : "English";
  const lineHint = runError.line ? ` at line ${runError.line}` : "";

  const system = `You are a Quant Buffet backtest coding tutor. Reply in ${lang}.
The user edits Python that may ONLY use Quant Buffet libraries:
- backtest.data.load_daily_prices
- backtest.engine.PortfolioEngine, EngineConfig
- backtest.metrics.compute_metrics
- numpy / pandas / math / typing

Contract: define ASSETS = [...] and def make_on_day(prices): return (on_day, ready)
where on_day(engine, dt) calls engine.set_target_weights(dt, weights).

Respond with STRICT JSON only (no markdown fences around the JSON):
{
  "where": "one sentence locating the bug${lineHint}",
  "why": "one sentence cause in plain language",
  "steps": ["numbered action the user should take", "next action", "then run backtest"],
  "snippets": [
    {
      "title": "short label",
      "hint": "where to paste this",
      "code": "paste-ready Python fragment, not a full essay"
    }
  ],
  "fixedCode": "full corrected Python file if the fix is clear, else empty string"
}

Rules:
- snippets[].code must be valid Python the user can copy-paste into the editor.
- Prefer small fragments (imports, ASSETS, make_on_day, set_target_weights) over rewriting everything unless the file is short.
- Do not suggest os, requests, yfinance, QuantConnect, eval, or file I/O.`;

  const user = `Strategy: ${title} (${slug})
Error type: ${runError.type ?? "Error"}
Error message: ${runError.message}
Line: ${runError.line ?? "unknown"}
Traceback:
${(runError.traceback || "").slice(0, 1800)}

Code:
\`\`\`python
${code.slice(0, 12000)}
\`\`\``;

  try {
    const raw = await chatCompletion({
      provider,
      system,
      user,
      maxTokens: 2200,
    });
    const start = raw.indexOf("{");
    const end = raw.lastIndexOf("}");
    let llm: {
      where?: string;
      why?: string;
      steps?: string[];
      fixes?: string[];
      snippets?: LabSnippet[];
      fixedCode?: string;
    } = {};
    if (start >= 0 && end > start) {
      try {
        llm = JSON.parse(raw.slice(start, end + 1)) as typeof llm;
      } catch {
        llm = {
          where: fallback.where,
          why: fallback.why,
          steps: [stripCodeFence(raw).slice(0, 600)],
        };
      }
    } else if (raw.trim()) {
      llm = { steps: [stripCodeFence(raw).slice(0, 600)] };
    }

    const merged = mergeLabAdvice(fallback, llm, provider);
    return NextResponse.json(merged);
  } catch {
    return NextResponse.json({ ...fallback, provider: "heuristic" });
  }
}
