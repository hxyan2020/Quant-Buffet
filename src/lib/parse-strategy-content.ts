/**
 * Parse Quant Buffet WordPress strategy posts into structured fields.
 */

import { extractPythonPlainText, formatPythonCodeHtml } from "@/lib/format-python";
import { detectPythonCode, strategyCodeBlob } from "@/lib/detect-python";
import { emptyToNa, sanitizePlainText, stripHtmlToText } from "@/lib/sanitize-text";

export type BacktestMetrics = {
  annualisedReturn?: string;
  volatility?: string;
  beta?: string;
  sharpeRatio?: string;
  sortinoRatio?: string;
  maxDrawdown?: string;
  winRate?: string;
  [key: string]: string | undefined;
};

export type ParsedStrategyContent = {
  teaser: string;
  summary: string;
  economicRationale: string;
  paperTitle: string;
  paperAuthors: string;
  paperInstitute: string;
  academicLink: string | null;
  backtestMetrics: BacktestMetrics;
  pythonCodeHtml: string;
  contentHtml: string;
  hasPythonCode: boolean;
};

const INVALID_PAPER_TITLE =
  /^(I{1,3}|IV|VI{0,3}|V|VI{0,3})\.\s|BACKTEST|PERFORMANCE|NUTSHELL|RATIONALE|PYTHON|SOURCE\s+PAPER|策略概要|经济|回测|论文|代码|^abstract$|^&lt;abstract&gt;$|^<abstract>$/i;

const INSTITUTE_RE =
  /university|institute|school|college|business\s+school|nber|laboratory|商学院|大学|研究所|经济学院/i;

type SectionKey = "nutshell" | "rationale" | "paper" | "backtest" | "python";

const SECTION_START: { key: SectionKey; re: RegExp }[] = [
  {
    key: "nutshell",
    re: /(?:^|[\s>])(?:I\.\s*)?(?:<[^>]+>)*\s*(?:<strong>\s*)?STRATEGY\s+IN\s+A\s+NUTSHELL|策略\s*概要|策略简介/i,
  },
  {
    key: "rationale",
    re: /(?:^|[\s>])(?:II\.\s*)?(?:<[^>]+>)*\s*(?:<strong>\s*)?ECONOMIC\s+RATIONALE|经济\s*逻辑|经济\s*原理/i,
  },
  {
    key: "paper",
    re: /(?:^|[\s>])(?:III\.\s*)?(?:<[^>]+>)*\s*(?:<strong>\s*)?SOURCE\s+PAPER|来源\s*论文|学术论文/i,
  },
  {
    key: "backtest",
    re: /(?:^|[\s>])(?:IV\.\s*)?(?:<[^>]+>)*\s*(?:<strong>\s*)?BACKTEST\s+PERFORMANCE|回测\s*表现|回测\s*绩效/i,
  },
  {
    key: "python",
    re: /(?:^|[\s>])(?:V\.\s*)?(?:<[^>]+>)*\s*(?:<strong>\s*)?(?:FULL\s+)?PYTHON\s+CODE|完整\s*python|Python\s*代码/i,
  },
];

function splitSections(html: string): Partial<Record<SectionKey, string>> {
  const hits: { key: SectionKey; index: number }[] = [];
  for (const { key, re } of SECTION_START) {
    const m = html.search(re);
    if (m >= 0) hits.push({ key, index: m });
  }
  hits.sort((a, b) => a.index - b.index);

  const out: Partial<Record<SectionKey, string>> = {};
  for (let i = 0; i < hits.length; i++) {
    const start = hits[i].index;
    const end = i + 1 < hits.length ? hits[i + 1].index : html.length;
    out[hits[i].key] = html.slice(start, end);
  }
  return out;
}

function sectionBodyText(sectionHtml: string, headerRe: RegExp): string {
  let chunk = sectionHtml.replace(headerRe, "");
  chunk = chunk.replace(/<p[^>]*>\s*<strong>\s*&lt;Abstract&gt;\s*<\/strong>\s*<\/p>/gi, "");
  chunk = chunk.replace(/<p[^>]*>\s*<strong>\s*Abstract\s*<\/strong>\s*<\/p>/gi, "");
  return sanitizePlainText(chunk);
}

const METRIC_KEY_MAP: [RegExp, keyof BacktestMetrics][] = [
  [/annualis|年化收益/i, "annualisedReturn"],
  [/volatility|波动率/i, "volatility"],
  [/^beta$|贝塔/i, "beta"],
  [/sharpe|夏普/i, "sharpeRatio"],
  [/sortino|索提诺/i, "sortinoRatio"],
  [/maximum\s+drawdown|max\s+drawdown|最大回撤/i, "maxDrawdown"],
  [/win\s*rate|胜率/i, "winRate"],
];

function normalizeMetricValue(raw: string): string {
  return sanitizePlainText(raw.replace(/<[^>]+>/g, " "));
}

export function parseBacktestMetricsFromHtml(html: string): BacktestMetrics {
  const metrics: BacktestMetrics = {};
  const tableMatch = html.match(/<table[\s\S]*?<\/table>/i);
  const table = tableMatch?.[0] ?? html;
  const rows = [...table.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/gi)];

  for (const row of rows) {
    const cells = [...(row[1]?.matchAll(/<t[dh][^>]*>([\s\S]*?)<\/t[dh]>/gi) ?? [])].map((c) =>
      normalizeMetricValue(c[1] ?? ""),
    );
    if (cells.length < 2) continue;
    const label = cells[0] ?? "";
    const value = cells[1] ?? "";
    if (!label || !value || /^n\/a$/i.test(value)) continue;

    for (const [re, key] of METRIC_KEY_MAP) {
      if (re.test(label)) {
        metrics[key] = value;
        break;
      }
    }
  }

  return metrics;
}

function isValidPaperTitle(title: string | null | undefined): boolean {
  if (!title?.trim()) return false;
  const t = title.trim();
  if (t.length < 10) return false;
  if (INVALID_PAPER_TITLE.test(t)) return false;
  if (/^&lt;|&gt;|^<|>$/i.test(t)) return false;
  return true;
}

function splitTickAuthorsInstitutes(parts: string[]): {
  paperAuthors: string | null;
  paperInstitute: string | null;
} {
  const authors: string[] = [];
  const institutes: string[] = [];
  for (const part of parts) {
    if (INSTITUTE_RE.test(part)) institutes.push(part);
    else if (part.length > 2) authors.push(part);
  }
  return {
    paperAuthors: authors.length ? authors.join("; ") : null,
    paperInstitute: institutes.length ? institutes.join("; ") : null,
  };
}

function parsePaperFromSection(sectionHtml: string): {
  paperTitle: string | null;
  paperAuthors: string | null;
  paperInstitute: string | null;
  academicLink: string | null;
} {
  const block = sectionHtml.slice(0, 16_000);

  let academicLink: string | null = null;
  let paperTitle: string | null = null;

  const anchorTitle = block.match(
    /<a[^>]+href="([^"]+)"[^>]*>[\s\S]*?<strong>([^<]+)<\/strong>/i,
  );
  if (anchorTitle) {
    academicLink = anchorTitle[1]?.trim() ?? null;
    const candidate = anchorTitle[2]?.replace(/\[Click to open PDF\]/gi, "").trim() ?? null;
    if (isValidPaperTitle(candidate)) paperTitle = candidate;
  }

  if (!paperTitle) {
    for (const m of block.matchAll(/<a[^>]+href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi)) {
      const href = m[1]?.trim() ?? "";
      const inner = stripHtmlToText(m[2] ?? "").replace(/\[Click to open PDF\]/gi, "").trim();
      if (!href || inner.length < 10) continue;
      if (/\.pdf|ssrn|doi|arxiv|nber|edu|semanticscholar/i.test(href) || inner.length > 15) {
        academicLink = academicLink ?? href;
        if (isValidPaperTitle(inner)) {
          paperTitle = inner;
          break;
        }
      }
    }
  }

  const tickParts = [...block.matchAll(/''([^'']+)''/g)].map((m) => m[1]?.trim()).filter(Boolean);
  let paperAuthors: string | null = null;
  let paperInstitute: string | null = null;

  if (tickParts.length > 0) {
    const split = splitTickAuthorsInstitutes(tickParts);
    paperAuthors = split.paperAuthors;
    paperInstitute = split.paperInstitute;
  }

  if (!paperAuthors && !paperInstitute) {
    const lines = [...block.matchAll(/<p[^>]*>([\s\S]*?)<\/p>/gi)]
      .map((m) => sanitizePlainText(m[1] ?? ""))
      .filter((line) => line.length > 3 && !/^abstract$/i.test(line) && !isValidPaperTitle(line));

    for (const line of lines) {
      if (INSTITUTE_RE.test(line)) {
        paperInstitute = paperInstitute ? `${paperInstitute}; ${line}` : line;
      } else if (!paperAuthors && line.length < 80 && !line.includes("http")) {
        paperAuthors = line;
      }
    }
  }

  return { paperTitle, paperAuthors, paperInstitute, academicLink };
}

function extractPythonFromSection(sectionHtml: string, fullHtml: string): string {
  let raw =
    sectionHtml.match(/<pre[\s\S]*?<\/pre>/i)?.[0] ??
    sectionHtml.match(/<code[\s\S]*?<\/code>/i)?.[0] ??
    "";

  if (!raw || extractPythonPlainText(raw).length < 20) {
    for (const re of [/V\.\s*FULL\s+PYTHON/i, /完整\s*python/i, /FULL\s+PYTHON\s+CODE/i]) {
      const idx = fullHtml.search(re);
      if (idx < 0) continue;
      const tail = fullHtml.slice(idx);
      raw =
        tail.match(/<pre[\s\S]*?<\/pre>/i)?.[0] ?? tail.match(/<code[\s\S]*?<\/code>/i)?.[0] ?? "";
      if (raw) break;
    }
  }

  return formatPythonCodeHtml(raw);
}

function preambleHtml(html: string, firstSectionIndex: number): string {
  if (firstSectionIndex <= 0) return "";
  return html.slice(0, firstSectionIndex).trim();
}

export function parseStrategyContent(
  contentHtml: string,
  options?: { excerpt?: string | null },
): ParsedStrategyContent {
  const html = contentHtml ?? "";
  const sections = splitSections(html);

  const firstIdx = Math.min(
    ...SECTION_START.map(({ re }) => {
      const i = html.search(re);
      return i >= 0 ? i : Number.MAX_SAFE_INTEGER;
    }),
  );
  const extra = preambleHtml(html, Number.isFinite(firstIdx) ? firstIdx : 0);

  const summary = sections.nutshell
    ? sectionBodyText(sections.nutshell, SECTION_START[0].re)
    : "";
  const economicRationale = sections.rationale
    ? sectionBodyText(sections.rationale, SECTION_START[1].re)
    : "";

  const paper = parsePaperFromSection(sections.paper ?? "");
  const backtestMetrics = parseBacktestMetricsFromHtml(sections.backtest ?? "");
  const pythonCodeHtml = extractPythonFromSection(sections.python ?? "", html);

  const excerptClean = options?.excerpt ? sanitizePlainText(options.excerpt) : "";
  const teaser = excerptClean.length > 0 ? excerptClean : "N/A";

  const bodyParts: string[] = [];
  if (extra) bodyParts.push(extra);

  return {
    teaser,
    summary: summary.length > 0 ? summary : "N/A",
    economicRationale: economicRationale.length > 0 ? economicRationale : "N/A",
    paperTitle: paper.paperTitle && isValidPaperTitle(paper.paperTitle) ? paper.paperTitle : "N/A",
    paperAuthors: paper.paperAuthors?.trim() ? sanitizePlainText(paper.paperAuthors) : "N/A",
    paperInstitute: paper.paperInstitute?.trim() ? sanitizePlainText(paper.paperInstitute) : "N/A",
    academicLink: paper.academicLink,
    backtestMetrics,
    pythonCodeHtml,
    contentHtml: bodyParts.join("\n\n").trim(),
    hasPythonCode: detectPythonCode(strategyCodeBlob(html, pythonCodeHtml)),
  };
}

export function backtestMetricsToJson(metrics: BacktestMetrics): string {
  return JSON.stringify(metrics);
}

export function parseBacktestMetricsJson(raw: string | null | undefined): BacktestMetrics {
  if (!raw?.trim()) return {};
  try {
    return JSON.parse(raw) as BacktestMetrics;
  } catch {
    return {};
  }
}

/** Display metric value or N/A */
export function metricDisplay(value: string | undefined | null): string {
  const v = value?.trim();
  return v && !/^n\/a$/i.test(v) ? v : "N/A";
}
