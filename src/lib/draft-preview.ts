import fs from "fs";
import path from "path";

export type DraftPost = {
  slug: string;
  locale: string;
  published: boolean;
  draft: boolean;
  title: string;
  teaser: string;
  summary: string;
  economicRationale: string;
  paperTitle: string | null;
  paperAuthors: string | null;
  paperInstitute: string;
  academicLink: string | null;
  assetClass: string | null;
  region: string | null;
  market: string | null;
  frequency: string | null;
  isPaywalled: boolean;
  hasPythonCode: boolean;
  annualisedReturn: string | null;
  sharpeRatio: string | null;
  maxDrawdown: string | null;
  volatility: string | null;
  beta: string | null;
  sortinoRatio: string | null;
  winRate: string | null;
  pythonCodeHtml: string;
  contentHtml: string;
  template?: string;
  assets?: string[];
  params?: Record<string, unknown> | null;
  fidelity?: string;
  source?: "new100" | "library";
  file_key?: string | null;
  paperAffiliationsJson?: string;
  source_paper?: {
    year?: number | null;
    venue?: string | null;
    source?: string | null;
    citationCount?: number | null;
    query?: string | null;
    score?: number | null;
  };
  backtest?: {
    trades?: number | null;
    metrics?: Record<string, number | string | null>;
  };
};

export type LabIndexEntry = {
  id: string;
  source: "library" | "new100";
  slug: string;
  locale: string;
  title: string;
  file_key?: string | null;
  template?: string;
  assets?: string[];
  params?: Record<string, unknown> | null;
  fidelity?: string;
  has_qc_source?: boolean;
  assetClass?: string | null;
  region?: string | null;
  isPaywalled?: boolean;
  code_path?: string | null;
  annualisedReturn?: string | null;
  sharpeRatio?: string | null;
  maxDrawdown?: string | null;
  volatility?: string | null;
  beta?: string | null;
  sortinoRatio?: string | null;
  trades?: number | null;
  siteCagr?: string | null;
  backtest_status?: string;
  href: string;
  paperTitle?: string;
};

export type LabIndex = {
  count: number;
  library: number;
  new100: number;
  by_locale: { en: number; zh: number };
  note?: string;
  strategies: LabIndexEntry[];
};

const DRAFT_DIR = path.join(process.cwd(), "backtest", "drafts", "new_100", "posts");
const LAB_INDEX = path.join(process.cwd(), "backtest", "drafts", "lab_index.json");
const CATALOG_PATH = path.join(process.cwd(), "backtest", "catalog", "strategies_full.json");

let cachedIndex: LabIndex | null = null;
let cachedListJson: string | null = null;
let cachedCatalog: Map<string, CatalogSpec> | null = null;

export type CatalogSpec = {
  slug: string;
  locale: string;
  template?: string;
  assets?: string[];
  params?: Record<string, unknown> | null;
  fidelity?: string;
  site_annualisedReturn?: string | null;
  site_sharpeRatio?: string | null;
  has_qc_source?: boolean;
};

export function findCatalogSpec(locale: string, slug: string): CatalogSpec | null {
  if (!cachedCatalog) {
    cachedCatalog = new Map();
    if (fs.existsSync(CATALOG_PATH)) {
      try {
        const raw = JSON.parse(fs.readFileSync(CATALOG_PATH, "utf8")) as {
          strategies?: CatalogSpec[];
        };
        for (const s of raw.strategies || []) {
          if (!s?.slug) continue;
          cachedCatalog.set(`${s.locale || "en"}:${s.slug}`, s);
          if (!cachedCatalog.has(`*:${s.slug}`)) cachedCatalog.set(`*:${s.slug}`, s);
        }
      } catch {
        cachedCatalog = new Map();
      }
    }
  }
  return cachedCatalog.get(`${locale}:${slug}`) || cachedCatalog.get(`*:${slug}`) || null;
}

export function draftPreviewEnabled(): boolean {
  if (process.env.ENABLE_DRAFT_PREVIEW === "1") return true;
  if (process.env.NODE_ENV === "development") return true;
  return false;
}

export function loadLabIndex(): LabIndex {
  if (cachedIndex) return cachedIndex;
  if (!fs.existsSync(LAB_INDEX)) {
    return {
      count: 0,
      library: 0,
      new100: 0,
      by_locale: { en: 0, zh: 0 },
      strategies: [],
    };
  }
  cachedIndex = JSON.parse(fs.readFileSync(LAB_INDEX, "utf8")) as LabIndex;
  return cachedIndex;
}

/** Pre-serialized list payload for the temp lab API. */
export function loadLabListResponseJson(): string {
  if (cachedListJson) return cachedListJson;
  const idx = loadLabIndex();
  cachedListJson = JSON.stringify({
    count: idx.count,
    library: idx.library,
    new100: idx.new100,
    by_locale: idx.by_locale,
    strategies: idx.strategies.map((s) => ({
      source: s.source,
      locale: s.locale,
      slug: s.slug,
      title: s.title,
      template: s.template,
      annualisedReturn: s.annualisedReturn,
      sharpeRatio: s.sharpeRatio,
      maxDrawdown: s.maxDrawdown,
      href: s.href,
      assetClass: s.assetClass,
    })),
  });
  return cachedListJson;
}

/** Invalidate cache after rebuild (dev HMR). */
export function clearLabIndexCache() {
  cachedIndex = null;
  cachedListJson = null;
}

export function listLabStrategies(opts?: {
  locale?: string;
  source?: "library" | "new100" | "all";
}): LabIndexEntry[] {
  const idx = loadLabIndex();
  let rows = idx.strategies;
  if (opts?.locale) rows = rows.filter((r) => r.locale === opts.locale);
  if (opts?.source && opts.source !== "all") {
    rows = rows.filter((r) => r.source === opts.source);
  }
  return rows;
}

export function findLabEntry(locale: string, slug: string): LabIndexEntry | null {
  const safe = slug.replace(/[^a-zA-Z0-9\-._]/g, "");
  // Keep original slug for lookup — Chinese/encoded handled via catalog slug as stored
  const target = slug.trim();
  const idx = loadLabIndex();
  return (
    idx.strategies.find((s) => s.locale === locale && s.slug === target) ||
    idx.strategies.find((s) => s.slug === target) ||
    (safe === slug ? idx.strategies.find((s) => s.slug === safe) : undefined) ||
    null
  );
}

export function labStrategyExists(slug: string): boolean {
  const idx = loadLabIndex();
  return idx.strategies.some((s) => s.slug === slug);
}

export function listDraftPosts(): DraftPost[] {
  return listLabStrategies({ source: "new100" }).map((e) => ({
    slug: e.slug,
    locale: e.locale,
    published: false,
    draft: true,
    title: e.title,
    teaser: "",
    summary: "",
    economicRationale: "",
    paperTitle: e.paperTitle ?? null,
    paperAuthors: null,
    paperInstitute: "",
    academicLink: null,
    assetClass: e.assetClass ?? null,
    region: e.region ?? null,
    market: null,
    frequency: null,
    isPaywalled: Boolean(e.isPaywalled),
    hasPythonCode: true,
    annualisedReturn: e.annualisedReturn ?? null,
    sharpeRatio: e.sharpeRatio ?? null,
    maxDrawdown: e.maxDrawdown ?? null,
    volatility: e.volatility ?? null,
    beta: e.beta ?? null,
    sortinoRatio: e.sortinoRatio ?? null,
    winRate: null,
    pythonCodeHtml: "",
    contentHtml: "",
    template: e.template,
    assets: e.assets,
    fidelity: e.fidelity,
    source: "new100",
  }));
}

export function findDraftPost(slug: string): DraftPost | null {
  const safe = slug.replace(/[^a-zA-Z0-9\-]/g, "");
  if (!safe || safe !== slug) {
    // still try file for unusual slugs
  }
  const file = path.join(DRAFT_DIR, `${slug}.json`);
  if (fs.existsSync(file)) {
    try {
      const raw = JSON.parse(fs.readFileSync(file, "utf8")) as DraftPost;
      return { ...raw, source: "new100" };
    } catch {
      return null;
    }
  }
  return null;
}

/** Resolve any lab strategy (new100 JSON or library index entry shell). */
export function findLabPostShell(locale: string, slug: string): DraftPost | null {
  const draft = findDraftPost(slug);
  if (draft) return draft;

  const entry = findLabEntry(locale, slug);
  if (!entry) return null;

  return {
    slug: entry.slug,
    locale: entry.locale,
    published: false,
    draft: true,
    title: entry.title,
    teaser: "",
    summary: "",
    economicRationale: "",
    paperTitle: entry.paperTitle ?? null,
    paperAuthors: null,
    paperInstitute: "",
    academicLink: null,
    assetClass: entry.assetClass ?? null,
    region: entry.region ?? null,
    market: null,
    frequency: null,
    isPaywalled: Boolean(entry.isPaywalled),
    hasPythonCode: true,
    annualisedReturn: entry.annualisedReturn ?? null,
    sharpeRatio: entry.sharpeRatio ?? null,
    maxDrawdown: entry.maxDrawdown ?? null,
    volatility: entry.volatility ?? null,
    beta: entry.beta ?? null,
    sortinoRatio: entry.sortinoRatio ?? null,
    winRate: null,
    pythonCodeHtml: "",
    contentHtml: "",
    template: entry.template,
    assets: entry.assets,
    fidelity: entry.fidelity,
    source: entry.source,
    file_key: entry.file_key,
    paperAffiliationsJson: "[]",
  };
}

export function draftBacktestMetricsJson(post: DraftPost): string {
  return JSON.stringify({
    annualisedReturn: post.annualisedReturn ?? undefined,
    volatility: post.volatility ?? undefined,
    beta: post.beta ?? undefined,
    sharpeRatio: post.sharpeRatio ?? undefined,
    sortinoRatio: post.sortinoRatio ?? undefined,
    maxDrawdown: post.maxDrawdown ?? undefined,
    winRate: post.winRate ?? undefined,
  });
}

export type CurvePoint = { date: string; equity: number };

export function loadDraftEquityCurve(slug: string): {
  equity: CurvePoint[];
  benchmark: CurvePoint[];
} {
  const candidates = [
    path.join(process.cwd(), "backtest", "drafts", "new_100", "equity_curves", `${slug}.json`),
    path.join(process.cwd(), "backtest", "results", "equity_curves", `${slug}.json`),
  ];
  for (const file of candidates) {
    if (!fs.existsSync(file)) continue;
    try {
      const raw = JSON.parse(fs.readFileSync(file, "utf8")) as {
        equity?: CurvePoint[];
        benchmark?: CurvePoint[];
      };
      return {
        equity: Array.isArray(raw.equity) ? raw.equity : [],
        benchmark: Array.isArray(raw.benchmark) ? raw.benchmark : [],
      };
    } catch {
      // try next
    }
  }
  return { equity: [], benchmark: [] };
}

export function loadLabPythonSource(entry: LabIndexEntry, pythonCodeHtml = ""): string {
  const candidates: string[] = [];
  if (entry.code_path) {
    candidates.push(path.join(process.cwd(), entry.code_path));
  }
  if (entry.file_key) {
    candidates.push(
      path.join(process.cwd(), "backtest", "strategies", "generated", `${entry.file_key}.py`),
    );
  }
  candidates.push(
    path.join(process.cwd(), "backtest", "drafts", "new_100", "code", `${entry.slug}.py`),
  );

  let raw = "";
  for (const py of candidates) {
    if (fs.existsSync(py)) {
      try {
        raw = fs.readFileSync(py, "utf8");
        break;
      } catch {
        // continue
      }
    }
  }
  if (!raw && pythonCodeHtml) {
    const pre = pythonCodeHtml.match(/<pre[^>]*>([\s\S]*?)<\/pre>/i)?.[1];
    raw = (pre || pythonCodeHtml)
      .replace(/<[^>]+>/g, "")
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&#039;/g, "'")
      .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
      .trim();
  }
  return toLabPythonSource(entry.slug, raw || `# Missing code for ${entry.slug}\nASSETS = ['SPY', 'BIL']\n\ndef make_on_day(prices):\n    raise RuntimeError('No strategy code found')\n`);
}

/** Prefer plain .py twin; fall back to HTML extraction. Strip CLI bootstrap for lab. */
export function loadDraftPythonSource(slug: string, pythonCodeHtml: string): string {
  const entry = findLabEntry("en", slug) || findLabEntry("zh", slug);
  if (entry) return loadLabPythonSource(entry, pythonCodeHtml);

  const py = path.join(process.cwd(), "backtest", "drafts", "new_100", "code", `${slug}.py`);
  let raw = "";
  if (fs.existsSync(py)) {
    try {
      raw = fs.readFileSync(py, "utf8");
    } catch {
      raw = "";
    }
  }
  if (!raw) {
    const pre = pythonCodeHtml.match(/<pre[^>]*>([\s\S]*?)<\/pre>/i)?.[1];
    raw = (pre || pythonCodeHtml)
      .replace(/<[^>]+>/g, "")
      .replace(/&nbsp;/gi, " ")
      .replace(/&amp;/g, "&")
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&#039;/g, "'")
      .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)))
      .trim();
  }
  return toLabPythonSource(slug, raw);
}

/** Drop sys/pathlib bootstrap + main(); keep strategy body for sandbox. */
export function toLabPythonSource(slug: string, source: string): string {
  let body = source.replace(/\r\n/g, "\n");
  const mainIdx = body.search(/\ndef main\s*\(/);
  if (mainIdx >= 0) body = body.slice(0, mainIdx);
  body = body.replace(
    /^[\s\S]*?(?=^(?:ASSETS\s*=|from backtest\.|import numpy|import pandas|TARGET_|LOOKBACK|SMA_|FAST|SLOW|VOL_|INVERT|TOP_N|REBALANCE|ENTRY_Z|EXIT_Z|CASH\s*=))/m,
    "",
  );
  body = body
    .split("\n")
    .filter((line) => {
      const t = line.trim();
      if (/^import\s+sys\b/.test(t)) return false;
      if (/^from\s+pathlib\b/.test(t)) return false;
      if (/^ROOT\s*=/.test(t)) return false;
      if (/sys\.path/.test(t)) return false;
      if (/^if\s+str\(ROOT\)/.test(t)) return false;
      if (/^from\s+__future__/.test(t)) return false;
      return true;
    })
    .join("\n")
    .trim();

  const header = `"""
Quant Buffet interactive lab — ${slug}
Allowed: backtest.data / backtest.engine / backtest.metrics, numpy, pandas.
Required: ASSETS = [...] and def make_on_day(prices): -> (on_day, ready)
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics

`;

  let cleaned = body;
  for (const pat of [
    /^"""[\s\S]*?"""\s*/m,
    /^'''[\s\S]*?'''\s*/m,
    /^from\s+__future__\s+import\s+.+$/gm,
    /^import\s+numpy\s+as\s+np\s*$/gm,
    /^import\s+pandas\s+as\s+pd\s*$/gm,
    /^from\s+backtest\.data\s+import .*$/gm,
    /^from\s+backtest\.engine\s+import .*$/gm,
    /^from\s+backtest\.metrics\s+import .*$/gm,
    /^import\s+json\s*$/gm,
    /^SLUG\s*=.*$/gm,
    /^LOCALE\s*=.*$/gm,
    /^FILE_KEY\s*=.*$/gm,
    /^TITLE\s*=.*$/gm,
    /^TEMPLATE\s*=.*$/gm,
    /^FIDELITY\s*=.*$/gm,
    /^DATA_SOURCE\s*=[\s\S]*?\n(?=[A-Z])/m,
  ]) {
    cleaned = cleaned.replace(pat, "");
  }
  cleaned = cleaned.replace(/\n{3,}/g, "\n\n").trim();
  return `${header}${cleaned}\n`;
}
