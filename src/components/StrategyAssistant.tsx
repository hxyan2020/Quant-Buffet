"use client";

import type { JSX } from "react";
import { useCallback, useState } from "react";
import { useTranslations } from "next-intl";

type Props = {
  strategy: {
    slug: string;
    locale: string;
    title: string;
    summary: string | null | undefined;
    contentHtml?: string | null;
  };
};

export default function StrategyAssistant({ strategy }: Props) {
  const dictionary = useTranslations("strategy");
  const [messages, setMessages] =
    useState<{ role: "user" | "assistant" | "system"; content: string }[]>([]);

  const [input, setInput] = useState("");
  const [isSubmitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dispatchMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isSubmitting) return;

      const history = [...messages, { role: "user", content: trimmed } as const];

      setSubmitting(true);
      setError(null);

      try {
        const response = await fetch("/api/strategy-bot", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            strategy,
            messages: history.slice(-15),
          }),
        });

        const payload = (await response.json()) as {
          reply?: string;
          error?: string;
        };

        if (!response.ok || payload?.error === "MODEL_UNAVAILABLE") {
          throw new Error("MODEL_UNAVAILABLE");
        }

        const reply =
          payload.reply ??
          "The assistant could not formulate a reply. Please refine your prompt.";
        setMessages([...history, { role: "assistant", content: reply }]);
        setInput("");
      } catch (err) {
        console.error(err);
        setError(dictionary("botEmptyModel"));
      } finally {
        setSubmitting(false);
      }
    },
    [dictionary, isSubmitting, messages, strategy],
  );

  return (
    <section className="space-y-6 rounded-[32px] border border-[#55e0ff]/30 bg-gradient-to-br from-black via-black to-[#02202b] p-6">
      <div>
        <h2 className="text-xl font-semibold text-white">{dictionary("botTitle")}</h2>
        <p className="text-xs uppercase tracking-[0.5em] text-[#81e7ff]/80">Powered by GPT + curated context</p>
      </div>
      {messages.length === 0 ?
        <p className="rounded-2xl border border-dashed border-white/10 p-6 text-sm text-[#9fb9d7]">{dictionary("botPlaceholder")}</p>
      : (
        <div className="qb-snippet flex max-h-[360px] flex-col gap-3 overflow-y-auto text-sm text-[#d7eaff]">
          {messages.map((msg, idx) => (
            <div key={`${idx}-${msg.role}-${msg.content.slice(0, 12)}`} className="space-y-1">
              <p className="text-[10px] uppercase tracking-[0.4em] text-[#5ddcff]">{msg.role}</p>
              <p className="whitespace-pre-wrap leading-relaxed text-[13px] text-[#e6f4ff]">{msg.content}</p>
            </div>
          ))}
        </div>
      )}
      <div className="space-y-2">
        <textarea
          className="qb-input font-mono text-sm"
          rows={3}
          value={input}
          placeholder={dictionary("botPlaceholder")}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && !event.shiftKey) {
              event.preventDefault();
              void dispatchMessage(input);
            }
          }}
        />
        <div className="flex flex-wrap gap-4">
          <button className="qb-pill-primary" type="button" disabled={isSubmitting} onClick={() => dispatchMessage(input)}>
            {dictionary("botSend")}
          </button>
          {error ? <p className="text-xs text-yellow-400">{error}</p> : null}
        </div>
      </div>
    </section>
  );
}
