/**
 * Route strategy AI to Gemini or DeepSeek based on user region.
 */

import OpenAI from "openai";

const GEMINI_BANNED_COUNTRIES = new Set(["CN"]);

export type LlmProvider = "gemini" | "deepseek";

export function resolveLlmProvider(request: Request, locale?: string): LlmProvider {
  const country =
    request.headers.get("x-vercel-ip-country") ??
    request.headers.get("cf-ipcountry") ??
    request.headers.get("x-country-code") ??
    "";

  const countryCode = country.toUpperCase();

  if (GEMINI_BANNED_COUNTRIES.has(countryCode)) {
    return "deepseek";
  }

  // Local dev / missing geo headers: zh locale often means mainland China users
  if (!countryCode && locale === "zh" && process.env.DEEPSEEK_API_KEY) {
    return "deepseek";
  }

  if (locale === "zh" && !process.env.GEMINI_API_KEY) {
    return "deepseek";
  }

  if (process.env.GEMINI_API_KEY) return "gemini";
  if (process.env.DEEPSEEK_API_KEY) return "deepseek";
  return "deepseek";
}

export async function chatCompletion(opts: {
  provider: LlmProvider;
  system: string;
  user: string;
  maxTokens?: number;
}): Promise<string> {
  const { provider, system, user, maxTokens = 600 } = opts;

  if (provider === "gemini" && process.env.GEMINI_API_KEY) {
    const model = process.env.GEMINI_MODEL ?? "gemini-2.0-flash";
    const url = `https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${process.env.GEMINI_API_KEY}`;
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        contents: [
          {
            parts: [{ text: `${system}\n\n${user}` }],
          },
        ],
        generationConfig: { maxOutputTokens: maxTokens, temperature: 0.35 },
      }),
      signal: AbortSignal.timeout(45_000),
    });
    if (!res.ok) {
      const err = await res.text();
      throw new Error(`Gemini error: ${res.status} ${err.slice(0, 200)}`);
    }
    const json = (await res.json()) as {
      candidates?: { content?: { parts?: { text?: string }[] } }[];
    };
    return json.candidates?.[0]?.content?.parts?.[0]?.text?.trim() ?? "";
  }

  const apiKey = process.env.DEEPSEEK_API_KEY ?? process.env.OPENAI_API_KEY;
  if (!apiKey) throw new Error("MODEL_UNAVAILABLE");

  const client = new OpenAI({
    apiKey,
    baseURL:
      process.env.DEEPSEEK_API_KEY
        ? (process.env.DEEPSEEK_BASE_URL ?? "https://api.deepseek.com")
        : undefined,
  });

  const model =
    process.env.DEEPSEEK_API_KEY
      ? (process.env.DEEPSEEK_MODEL ?? "deepseek-chat")
      : (process.env.OPENAI_MODEL ?? "gpt-4o-mini");

  const completion = await client.chat.completions.create({
    model,
    temperature: 0.35,
    max_tokens: maxTokens,
    messages: [
      { role: "system", content: system },
      { role: "user", content: user },
    ],
  });

  return completion.choices[0]?.message?.content?.trim() ?? "";
}
