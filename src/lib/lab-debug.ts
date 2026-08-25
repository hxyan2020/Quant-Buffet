/** Heuristic Quant Buffet lab debugger — used on draft-preview only. */

export type LabRunError = {
  type?: string;
  message: string;
  line?: number | null;
  column?: number | null;
  traceback?: string;
};

export type LabSnippet = {
  title: string;
  hint: string;
  code: string;
};

export type LabAdvice = {
  where: string;
  why: string;
  steps: string[];
  snippets: LabSnippet[];
  fixedCode?: string;
  provider?: string;
};

export const LAB_CONTRACT_SNIPPETS: LabSnippet[] = [
  {
    title: "Required imports",
    hint: "Only these libraries are allowed in the sandbox.",
    code: `from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.data import load_daily_prices
from backtest.engine import EngineConfig, PortfolioEngine
from backtest.metrics import compute_metrics`,
  },
  {
    title: "ASSETS list (whitelisted ETFs)",
    hint: "Module-level list. Tickers must be in the Quant Buffet whitelist.",
    code: `ASSETS = ["SPY", "QQQ", "TLT", "GLD", "BIL"]`,
  },
  {
    title: "make_on_day contract",
    hint: "Must return (on_day, ready). on_day calls engine.set_target_weights.",
    code: `def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    sma = prices[cols].rolling(200, min_periods=200).mean()
    state = {"last": None}

    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        if sma.loc[dt].isna().all():
            return
        key = (dt.year, dt.month)
        if state["last"] == key:
            return
        state["last"] = key
        long = [
            s for s in cols
            if pd.notna(prices.at[dt, s]) and pd.notna(sma.at[dt, s])
            and prices.at[dt, s] > sma.at[dt, s]
        ]
        weights = {} if not long else {s: 1.0 / len(long) for s in long}
        engine.set_target_weights(dt, weights)

    ready = sma.dropna(how="all").index.min() if sma.notna().any().any() else None
    return on_day, ready`,
  },
  {
    title: "Set target weights",
    hint: "Weights should sum to about 1.0. Empty dict = 100% cash.",
    code: `engine.set_target_weights(dt, {"SPY": 0.60, "BIL": 0.40})`,
  },
];

const MAKE_ON_DAY = LAB_CONTRACT_SNIPPETS[2].code;
const ASSETS_LINE = `ASSETS = ["SPY", "QQQ", "TLT", "GLD", "BIL"]`;

export function stripCodeFence(text: string): string {
  const t = (text || "").trim();
  const m = t.match(/^```(?:python)?\s*([\s\S]*?)\s*```$/i);
  return (m ? m[1] : t).trim();
}

function hasAssets(code: string): boolean {
  return /^\s*ASSETS\s*=/m.test(code);
}

function hasMakeOnDay(code: string): boolean {
  return /^\s*def\s+make_on_day\s*\(/m.test(code);
}

function insertAfterImports(code: string, block: string): string {
  const lines = code.replace(/\r\n/g, "\n").split("\n");
  let lastImport = -1;
  for (let i = 0; i < lines.length; i++) {
    const t = lines[i].trim();
    if (t.startsWith("import ") || t.startsWith("from ")) lastImport = i;
    else if (lastImport >= 0 && t === "") continue;
    else if (lastImport >= 0 && !t.startsWith("#") && t !== '"""' && t !== "'''") break;
  }
  const at = lastImport >= 0 ? lastImport + 1 : 0;
  lines.splice(at, 0, "", block, "");
  return lines.join("\n");
}

export function heuristicLabAdvice(error: LabRunError, code: string): LabAdvice {
  const msg = `${error.type || ""} ${error.message}`.toLowerCase();
  const line = error.line ?? null;
  const where = line ? `Line ${line} in the editor` : "In the strategy code";
  const steps: string[] = [];
  const snippets: LabSnippet[] = [];
  let fixedCode = "";

  if (msg.includes("syntax")) {
    steps.push(
      line
        ? `Open the editor around line ${line}. Look for a missing colon :, parenthesis, quote, or indent.`
        : "Scan the last line you edited for a missing colon, parenthesis, quote, or indent.",
    );
    steps.push("Python needs a colon after def / if / for / else, and consistent 4-space indents.");
    steps.push("Copy a known-good fragment below, paste over the broken lines, then Run backtest.");
    snippets.push({
      title: "Function header syntax",
      hint: "Colon after the signature. Next line must be indented 4 spaces.",
      code: `def make_on_day(prices: pd.DataFrame):
    cols = [c for c in ASSETS if c in prices.columns]
    return on_day, ready`,
    });
    snippets.push({
      title: "if / for syntax",
      hint: "Parentheses are optional; the colon is required.",
      code: `if sma.loc[dt].isna().all():
    return
for s in cols:
    print(s)`,
    });
  }

  if (msg.includes("import") || msg.includes("blocked") || msg.includes("not allowed")) {
    steps.push("Delete the blocked import (os, requests, yfinance, QuantConnect, etc.).");
    steps.push("Keep only Quant Buffet backtest.* plus numpy, pandas, math, typing.");
    snippets.push(LAB_CONTRACT_SNIPPETS[0]);
    const cleaned = code
      .replace(/\r\n/g, "\n")
      .split("\n")
      .filter((row) => {
        const t = row.trim();
        if (!/^(import|from)\s+/.test(t)) return true;
        const root = t
          .replace(/^from\s+/, "")
          .replace(/^import\s+/, "")
          .split(/[.\s]/)[0];
        return [
          "backtest",
          "numpy",
          "np",
          "pandas",
          "pd",
          "math",
          "json",
          "typing",
          "collections",
          "dataclasses",
          "functools",
          "itertools",
          "datetime",
          "re",
          "statistics",
          "decimal",
          "__future__",
        ].includes(root);
      })
      .join("\n");
    if (cleaned !== code.replace(/\r\n/g, "\n")) fixedCode = cleaned;
  }

  if (msg.includes("assets") || msg.includes("whitelist") || msg.includes("symbol")) {
    steps.push("Set a module-level ASSETS list using liquid ETFs from the whitelist.");
    steps.push("Common tickers: SPY, QQQ, IWM, TLT, IEF, GLD, BIL, EFA, EEM, BTC-USD, ETH-USD.");
    snippets.push({
      title: "Replace your ASSETS line",
      hint: "Paste at module level (not inside a function).",
      code: ASSETS_LINE,
    });
    if (!hasAssets(code)) {
      fixedCode = insertAfterImports(code, ASSETS_LINE);
    } else {
      fixedCode = code.replace(/^\s*ASSETS\s*=.*$/m, ASSETS_LINE);
    }
  }

  if (msg.includes("make_on_day") || msg.includes("contract")) {
    steps.push("Define def make_on_day(prices) that returns (on_day, ready).");
    steps.push("Inside on_day, call engine.set_target_weights(dt, weights).");
    snippets.push(LAB_CONTRACT_SNIPPETS[2]);
    snippets.push(LAB_CONTRACT_SNIPPETS[3]);
    if (!hasMakeOnDay(code)) {
      fixedCode = `${code.replace(/\s+$/, "")}\n\n${MAKE_ON_DAY}\n`;
    }
  }

  if (msg.includes("set_target_weights") || msg.includes("target_weights")) {
    steps.push("Call engine.set_target_weights(dt, weights) with a dict of ticker → weight.");
    snippets.push(LAB_CONTRACT_SNIPPETS[3]);
  }

  if (msg.includes("never ready") || msg.includes("lookback") || msg.includes("too short")) {
    steps.push("Shorten rolling windows (try 20–60 days) so the signal becomes ready sooner.");
    steps.push("Make sure ASSETS have history from the start date (2000-01-01).");
    snippets.push({
      title: "Shorter lookback",
      hint: "Paste near the top of make_on_day, then use LOOKBACK in rolling().",
      code: `LOOKBACK = 60
sma = prices[cols].rolling(LOOKBACK, min_periods=LOOKBACK).mean()`,
    });
  }

  if (msg.includes("nameerror") || msg.includes("is not defined")) {
    const m = error.message.match(/name ['"]([^'"]+)['"]/i);
    const name = m?.[1] || "that name";
    steps.push(`Define ${name} before you use it, or import it from an allowed module.`);
    if (name === "np" || name === "numpy") snippets.push({
      title: "Import numpy",
      hint: "Paste near the top of the file.",
      code: "import numpy as np",
    });
    if (name === "pd" || name === "pandas") snippets.push({
      title: "Import pandas",
      hint: "Paste near the top of the file.",
      code: "import pandas as pd",
    });
    if (name === "ASSETS") snippets.push({
      title: "Define ASSETS",
      hint: "Module-level list, above make_on_day.",
      code: ASSETS_LINE,
    });
    if (name === "PortfolioEngine" || name === "EngineConfig") {
      snippets.push({
        title: "Import the engine",
        hint: "Paste with the other imports.",
        code: "from backtest.engine import EngineConfig, PortfolioEngine",
      });
    }
  }

  if (msg.includes("indent")) {
    steps.push("Use 4 spaces per indent level. Do not mix tabs and spaces.");
    snippets.push({
      title: "Indented on_day body",
      hint: "Everything inside on_day must be indented one extra level.",
      code: `    def on_day(engine: PortfolioEngine, dt: pd.Timestamp) -> None:
        engine.set_target_weights(dt, {"SPY": 1.0})`,
    });
  }

  if (!steps.length) {
    steps.push("Read the error message above — it names the failing line or missing contract piece.");
    steps.push("Your file must define ASSETS = [...] and def make_on_day(prices) -> (on_day, ready).");
    steps.push("Copy a snippet below into the editor, then click Run backtest.");
  }

  if (!snippets.length) {
    snippets.push(...LAB_CONTRACT_SNIPPETS.slice(1, 4));
  }

  return {
    where,
    why: error.message,
    steps: steps.slice(0, 6),
    snippets: snippets.slice(0, 5),
    fixedCode: fixedCode.trim() ? fixedCode : undefined,
    provider: "heuristic",
  };
}

export function mergeLabAdvice(
  base: LabAdvice,
  llm: Partial<LabAdvice> & { fixes?: string[] },
  provider?: string,
): LabAdvice {
  const snippets = Array.isArray(llm.snippets) && llm.snippets.length
    ? llm.snippets
        .filter((s) => s && typeof s.code === "string" && s.code.trim())
        .map((s) => ({
          title: String(s.title || "Suggested syntax").slice(0, 80),
          hint: String(s.hint || "Paste this into the editor.").slice(0, 200),
          code: stripCodeFence(String(s.code)).slice(0, 4000),
        }))
        .slice(0, 5)
    : base.snippets;

  const steps = Array.isArray(llm.steps) && llm.steps.length
    ? llm.steps.map((s) => String(s).slice(0, 400)).slice(0, 6)
    : Array.isArray(llm.fixes)
      ? llm.fixes.map((s) => String(s).slice(0, 400)).slice(0, 6)
      : base.steps;

  const fixed = typeof llm.fixedCode === "string" ? stripCodeFence(llm.fixedCode) : "";

  return {
    where: (llm.where && String(llm.where)) || base.where,
    why: (llm.why && String(llm.why)) || base.why,
    steps,
    snippets: snippets.length ? snippets : base.snippets,
    fixedCode: fixed || base.fixedCode,
    provider: provider || llm.provider || base.provider,
  };
}
