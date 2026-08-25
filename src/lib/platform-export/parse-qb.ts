/** Parse Quant Buffet lab Python into a portable strategy sketch. */

export type QbPattern =
  | "sma_trend"
  | "dual_ma"
  | "abs_momentum"
  | "dual_momentum"
  | "momentum_rotation"
  | "mean_reversion"
  | "equal_weight"
  | "vol_target"
  | "risk_parity"
  | "custom";

export type QbStrategySketch = {
  assets: string[];
  pattern: QbPattern;
  params: Record<string, number | string | boolean>;
  source: string;
  titleHint: string;
};

const ASSETS_RE = /ASSETS\s*=\s*\[([\s\S]*?)\]/;

function parseStringList(inner: string): string[] {
  const out: string[] = [];
  const re = /['"]([^'"]+)['"]/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(inner))) {
    const s = m[1].trim();
    if (s && !out.includes(s)) out.push(s);
  }
  return out;
}

function numConst(source: string, name: string, fallback: number): number {
  const m = source.match(new RegExp(`(?:^|\\n)\\s*${name}\\s*=\\s*(-?\\d+(?:\\.\\d+)?)`, "m"));
  return m ? Number(m[1]) : fallback;
}

function strConst(source: string, name: string, fallback: string): string {
  const m = source.match(new RegExp(`(?:^|\\n)\\s*${name}\\s*=\\s*['"]([^'"]+)['"]`, "m"));
  return m?.[1] ?? fallback;
}

export function detectQbPattern(source: string): { pattern: QbPattern; params: Record<string, number | string | boolean> } {
  const s = source;
  if (/ENTRY_Z|entry_z|make_mean_reversion/.test(s) || (/z\s*=/.test(s) && /rolling/.test(s) && /ENTRY/.test(s))) {
    return {
      pattern: "mean_reversion",
      params: {
        lookback: numConst(s, "LOOKBACK", 20),
        entry_z: numConst(s, "ENTRY_Z", -1),
        exit_z: numConst(s, "EXIT_Z", 0),
      },
    };
  }
  if (/make_dual_momentum|dual_momentum|CASH_SYMBOL|cash_symbol/.test(s) && /LOOKBACK|lookback/.test(s)) {
    return {
      pattern: "dual_momentum",
      params: {
        lookback: numConst(s, "LOOKBACK", 252),
        top_n: numConst(s, "TOP_N", 1),
        cash_symbol: strConst(s, "CASH", strConst(s, "CASH_SYMBOL", "BIL")),
      },
    };
  }
  if (/TOP_N|make_momentum_rotation|momentum_rotation/.test(s) && /LOOKBACK|lookback|pct_change/.test(s)) {
    return {
      pattern: "momentum_rotation",
      params: {
        lookback: numConst(s, "LOOKBACK", 126),
        top_n: numConst(s, "TOP_N", 1),
        invert: /INVERT\s*=\s*True/.test(s),
      },
    };
  }
  if (/make_risk_parity|risk_parity|inverse.?vol/i.test(s)) {
    return { pattern: "risk_parity", params: { lookback: numConst(s, "LOOKBACK", 63) } };
  }
  if (/make_vol_target|VOL_TARGET|target_vol|TARGET_VOL/.test(s)) {
    return {
      pattern: "vol_target",
      params: {
        lookback: numConst(s, "LOOKBACK", 63),
        target_vol: numConst(s, "TARGET_VOL", 0.1),
      },
    };
  }
  if (/FAST\s*=|make_dual_ma|dual_ma/.test(s) && /SLOW\s*=/.test(s)) {
    return {
      pattern: "dual_ma",
      params: { fast: numConst(s, "FAST", 50), slow: numConst(s, "SLOW", 200) },
    };
  }
  if (/SMA_DAYS|make_sma_trend|sma_trend/.test(s) || (/rolling\s*\(\s*200/.test(s) && /set_target_weights/.test(s))) {
    return { pattern: "sma_trend", params: { sma_days: numConst(s, "SMA_DAYS", 200) } };
  }
  if (/make_abs_momentum|abs_momentum/.test(s) || (/pct_change\s*\(\s*LOOKBACK/.test(s) && /> 0/.test(s))) {
    return { pattern: "abs_momentum", params: { lookback: numConst(s, "LOOKBACK", 252) } };
  }
  if (/make_equal_weight|equal_weight|1\.0\s*\/\s*len\(cols\)/.test(s)) {
    return { pattern: "equal_weight", params: {} };
  }
  if (/set_target_weights|make_on_day/.test(s)) {
    return { pattern: "custom", params: {} };
  }
  return { pattern: "custom", params: {} };
}

/** Extract tickers from QuantConnect-style or free-form Python. */
export function extractTickersFallback(source: string): string[] {
  const assets = ASSETS_RE.exec(source);
  if (assets?.[1]) {
    const list = parseStringList(assets[1]);
    if (list.length) return list;
  }
  const tickers = new Set<string>();
  const patterns = [
    /AddEquity\s*\(\s*["']([A-Z][A-Z0-9.\-]{0,11})["']/g,
    /symbol\s*=\s*["']([A-Z][A-Z0-9.\-]{0,11})["']/gi,
    /["']([A-Z]{2,5})["']\s*,/g,
  ];
  for (const re of patterns) {
    let m: RegExpExecArray | null;
    while ((m = re.exec(source))) {
      const t = m[1].toUpperCase();
      if (t.length >= 2 && t.length <= 12) tickers.add(t);
    }
  }
  const preferred = ["SPY", "QQQ", "TLT", "GLD", "BIL", "EFA", "EEM", "IWM"];
  const found = [...tickers];
  if (found.length) return found.slice(0, 15);
  return preferred.slice(0, 5);
}

export function parseQbStrategy(source: string, titleHint = "Quant Buffet strategy"): QbStrategySketch {
  const cleaned = source.replace(/\r\n/g, "\n").trim();
  const assetsMatch = ASSETS_RE.exec(cleaned);
  const assets = assetsMatch?.[1] ? parseStringList(assetsMatch[1]) : extractTickersFallback(cleaned);
  const { pattern, params } = detectQbPattern(cleaned);
  return {
    assets: assets.length ? assets : ["SPY", "TLT", "GLD", "BIL"],
    pattern,
    params,
    source: cleaned,
    titleHint,
  };
}

export function patternLabel(pattern: QbPattern): string {
  const map: Record<QbPattern, string> = {
    sma_trend: "SMA trend",
    dual_ma: "Dual moving average",
    abs_momentum: "Absolute momentum",
    dual_momentum: "Dual momentum",
    momentum_rotation: "Momentum rotation",
    mean_reversion: "Mean reversion",
    equal_weight: "Equal weight",
    vol_target: "Volatility targeting",
    risk_parity: "Risk parity",
    custom: "Custom / hybrid",
  };
  return map[pattern];
}
