import { NextResponse } from "next/server";
import OpenAI from "openai";
import { z } from "zod";

import { auth } from "@/auth";

const messageSchema = z.object({
  role: z.enum(["user", "assistant", "system"]),
  content: z.string().max(6000),
});

const bodySchema = z.object({
  strategy: z.object({
    slug: z.string(),
    locale: z.string(),
    title: z.string(),
    summary: z.string().optional(),
    contentHtml: z.string().optional(),
  }),
  messages: z.array(messageSchema).min(1).max(40),
});

function stripHtml(input: string) {
  return input.replace(/<[^>]*>/g, " ").slice(0, 12000);
}

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user) {
    return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
  }

  const openaiKey = process.env.OPENAI_API_KEY;
  if (!openaiKey) {
    return NextResponse.json({ error: "MODEL_UNAVAILABLE" }, { status: 503 });
  }

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "BAD_REQUEST" }, { status: 400 });
  }

  const { strategy, messages } = parsed.data;

  const context = `
You advise a disciplined portfolio allocator about the empirical strategy excerpt below.
Be explicit where data is insufficient. Respond in the user's language (${strategy.locale}).
Slug: ${strategy.slug}
Title: ${strategy.title}
Summary: ${strategy.summary ?? "n/a"}
Body excerpt:
${stripHtml(strategy.contentHtml ?? "")}
`.trim();

  const client = new OpenAI({
    apiKey: openaiKey,
  });

  const model = process.env.OPENAI_MODEL ?? "gpt-4o-mini";

  try {
    const completion = await client.chat.completions.create({
      model,
      temperature: 0.35,
      messages: [
        { role: "system", content: context },
        ...messages.map((msg) => ({
          role: msg.role,
          content: msg.content,
        })),
      ],
    });

    const reply =
      completion.choices[0]?.message?.content?.trim()
      ?? "The model returned an empty reply.";
    return NextResponse.json({ reply });
  } catch (error) {
    console.error("[strategy-bot]", error);
    return NextResponse.json({ error: "MODEL_ERROR" }, { status: 502 });
  }
}
