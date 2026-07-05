"use client";

import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

type StrategyContext = {
  slug: string;
  locale: string;
  title: string;
  teaser?: string;
  summary?: string;
  economicRationale?: string;
};

type Props = {
  strategy: StrategyContext;
  /** prominent = full-width bar under title; fab = fixed corner (legacy) */
  variant?: "prominent" | "fab";
};

export default function StrategyAiPanel({ strategy, variant = "prominent" }: Props) {
  const t = useTranslations("strategy");
  const [open, setOpen] = useState(false);
  const [questions, setQuestions] = useState<string[]>([]);
  const [loadingQ, setLoadingQ] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loadingA, setLoadingA] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQuestions = useCallback(async () => {
    setLoadingQ(true);
    setError(null);
    try {
      const res = await fetch("/api/strategy-ai/questions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ strategy }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error ?? "failed");
      setQuestions(data.questions ?? []);
    } catch {
      setError(t("aiError"));
      setQuestions([t("aiFallbackQ1"), t("aiFallbackQ2"), t("aiFallbackQ3")]);
    } finally {
      setLoadingQ(false);
    }
  }, [strategy, t]);

  useEffect(() => {
    if (open && questions.length === 0 && !loadingQ) {
      void loadQuestions();
    }
  }, [open, questions.length, loadingQ, loadQuestions]);

  async function ask(question: string) {
    setLoadingA(true);
    setError(null);
    setAnswer(null);
    try {
      const res = await fetch("/api/strategy-ai/answer", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ strategy, question }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error ?? "failed");
      setAnswer(data.answer ?? "");
    } catch {
      setError(t("aiError"));
    } finally {
      setLoadingA(false);
    }
  }

  const triggerClass =
    variant === "prominent" ? "qb-ai-prominent-btn" : "qb-ai-fab";

  const panelClass =
    variant === "prominent" ? "qb-ai-panel qb-ai-panel-prominent" : "qb-ai-panel";

  return (
    <div className={variant === "prominent" ? "qb-ai-prominent-wrap" : undefined}>
      <button
        type="button"
        className={triggerClass}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        title={t("aiFabTitle")}
      >
        <span className="qb-ai-fab-icon">✦</span>
        <span className="qb-ai-prominent-text">
          <span className="qb-ai-prominent-title">{t("aiFabTitle")}</span>
          <span className="qb-ai-prominent-sub">{t("aiPanelSub")}</span>
        </span>
        <span className="qb-ai-prominent-chevron" aria-hidden>
          {open ? "▲" : "▼"}
        </span>
      </button>

      {open ?
        <div className={panelClass} role="dialog" aria-label={t("aiPanelTitle")}>
          {variant === "fab" ?
            <div className="qb-ai-panel-head">
              <h2 className="qb-strategy-section-title">{t("aiPanelTitle")}</h2>
              <button type="button" className="qb-ai-close" onClick={() => setOpen(false)}>
                ×
              </button>
            </div>
          : <h2 className="qb-strategy-section-title">{t("aiPanelTitle")}</h2>}

          {variant === "fab" ?
            <p className="qb-ai-panel-sub">{t("aiPanelSub")}</p>
          : null}

          {loadingQ ?
            <p className="qb-admin-muted">{t("aiLoading")}</p>
          : <ul className="qb-ai-questions">
              {questions.map((q) => (
                <li key={q}>
                  <button
                    type="button"
                    className="qb-ai-question-btn"
                    disabled={loadingA}
                    onClick={() => void ask(q)}
                  >
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          }

          {loadingA ?
            <p className="qb-admin-muted">{t("aiAnswering")}</p>
          : null}
          {answer ?
            <div className="qb-ai-answer">
              <p>{answer}</p>
            </div>
          : null}
          {error ?
            <p className="text-xs text-yellow-400">{error}</p>
          : null}
        </div>
      : null}
    </div>
  );
}
