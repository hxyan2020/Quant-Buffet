import type { BacktestMetrics } from "@/lib/parse-strategy-content";

type SeoInput = {
  title: string;
  locale: string;
  market?: string | null;
  region?: string | null;
  assetClass?: string | null;
  frequency?: string | null;
  paperTitle?: string | null;
  backtestMetrics?: BacktestMetrics;
};

function keyPhrases(input: SeoInput): string[] {
  const phrases = new Set<string>();
  if (input.market) phrases.add(input.market);
  if (input.region) phrases.add(input.region);
  if (input.assetClass) phrases.add(input.assetClass);
  if (input.frequency) phrases.add(input.frequency);

  if (input.locale === "zh") {
    phrases.add("量化策略");
    phrases.add("学术论文");
    phrases.add("Python回测");
    phrases.add("回测绩效");
  } else {
    phrases.add("quantitative trading");
    phrases.add("academic paper");
    phrases.add("Python backtest");
    phrases.add("backtest performance");
  }
  return [...phrases].slice(0, 6);
}

function trimDescription(text: string, max = 158): string {
  if (text.length <= max) return text;
  return `${text.slice(0, max - 1).trim()}…`;
}

export function generateStrategySeo(input: SeoInput): {
  metaTitle: string;
  metaDescription: string;
} {
  const ann = input.backtestMetrics?.annualisedReturn;
  const sharpe = input.backtestMetrics?.sharpeRatio;
  const phrases = keyPhrases(input);
  const phraseStr = phrases.join(input.locale === "zh" ? "、" : ", ");

  if (input.locale === "zh") {
    const metaTitle = `${input.title} | ${input.market ?? "量化"}策略 — Quant Buffet`;
    const parts = [
      `基于学术论文的「${input.title}」量化策略解读，含经济逻辑与完整 Python 实现。`,
      phraseStr ? `关键词：${phraseStr}。` : "",
      ann || sharpe ?
        `回测年化收益 ${ann ?? "—"}，夏普比率 ${sharpe ?? "—"}。`
      : "",
      input.paperTitle ? `来源论文：${input.paperTitle.slice(0, 60)}。` : "",
    ];
    return {
      metaTitle: metaTitle.slice(0, 70),
      metaDescription: trimDescription(parts.filter(Boolean).join("")),
    };
  }

  const metaTitle = `${input.title} | ${input.market ?? "Quant"} Strategy — Quant Buffet`;
  const parts = [
    `Academic ${input.title} strategy with economic rationale, backtest metrics, and Python code.`,
    phraseStr ? `Topics: ${phraseStr}.` : "",
    ann || sharpe ?
      `Backtest: ${ann ?? "—"} annualised return, Sharpe ${sharpe ?? "—"}.`
    : "",
    input.paperTitle ? `Paper: ${input.paperTitle.slice(0, 72)}.` : "",
  ];

  return {
    metaTitle: metaTitle.slice(0, 70),
    metaDescription: trimDescription(parts.filter(Boolean).join(" ")),
  };
}
