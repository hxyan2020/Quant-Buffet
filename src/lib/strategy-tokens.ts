/** Strip HTML debris from imported spreadsheet / WordPress fields. */
export function sanitizeFilterToken(token: string): string {
  return token
    .replace(/<[^>]*>/g, "")
    .replace(/&nbsp;/gi, " ")
    .replace(/\s+/g, " ")
    .trim();
}

/** Singular/plural and alias → canonical display label for Market & Asset Class. */
const CANONICAL_LABELS: Record<string, string> = {
  bond: "Bond",
  bonds: "Bond",
  equity: "Equity",
  equities: "Equity",
  commodity: "Commodity",
  commodities: "Commodity",
  crypto: "Crypto",
  cryptos: "Crypto",
  currency: "Currency",
  currencies: "Currency",
  stock: "Stock",
  stocks: "Stocks",
  fund: "Funds",
  funds: "Funds",
  future: "Futures",
  futures: "Futures",
  reit: "REITs",
  reits: "REITs",
  etf: "ETFs",
  etfs: "ETFs",
  cfd: "CFDs",
  cfds: "CFDs",
};

function titleCaseWord(word: string): string {
  if (!word) return word;
  if (word.length <= 4 && word === word.toUpperCase()) return word;
  return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}

/** Stable key for matching filters (merges bond/bonds, Equity/equity, etc.). */
export function canonicalTokenKey(token: string): string {
  const clean = sanitizeFilterToken(token).toLowerCase();
  if (!clean) return "";
  if (CANONICAL_LABELS[clean]) return clean;
  if (clean.endsWith("s")) {
    const singular = clean.slice(0, -1);
    if (CANONICAL_LABELS[singular] || CANONICAL_LABELS[`${singular}s`]) {
      return singular in CANONICAL_LABELS ? singular : clean;
    }
  }
  return clean;
}

/** Human-readable label for UI and table cells. */
export function displayToken(token: string): string {
  const clean = sanitizeFilterToken(token);
  if (!clean) return "";
  const key = canonicalTokenKey(clean);
  if (CANONICAL_LABELS[key]) return CANONICAL_LABELS[key];
  if (CANONICAL_LABELS[clean.toLowerCase()]) return CANONICAL_LABELS[clean.toLowerCase()];
  return titleCaseWord(clean);
}

/** Split comma-separated library fields (EN commas, occasional Chinese顿号). */
export function splitFilterTokens(value: string | null | undefined): string[] {
  if (!value?.trim()) return [];
  return value
    .split(/[,，、]/)
    .map((part) => sanitizeFilterToken(part))
    .filter(Boolean);
}

export function normalizeTokenKey(token: string): string {
  return canonicalTokenKey(token);
}

export function tokenMatchesField(
  field: string | null | undefined,
  selected: string,
): boolean {
  if (!selected.trim()) return true;
  const needle = canonicalTokenKey(selected);
  return splitFilterTokens(field).some((token) => canonicalTokenKey(token) === needle);
}

/** Format multi-value field for table display (deduped, canonical labels). */
export function formatTokenList(value: string | null | undefined): string {
  const seen = new Set<string>();
  const labels: string[] = [];
  for (const raw of splitFilterTokens(value)) {
    const key = canonicalTokenKey(raw);
    if (!key || seen.has(key)) continue;
    seen.add(key);
    labels.push(displayToken(raw));
  }
  return labels.length ? labels.join(", ") : "—";
}

/** Distinct filter values; merges case/plural/HTML variants. */
export function collectDistinctTokens(rows: { value: string | null }[]): string[] {
  const byKey = new Map<string, string>();

  for (const row of rows) {
    for (const token of splitFilterTokens(row.value)) {
      const key = canonicalTokenKey(token);
      if (!key) continue;
      const label = displayToken(token);
      if (!byKey.has(key)) {
        byKey.set(key, label);
      }
    }
  }

  return [...byKey.values()].sort((a, b) =>
    a.localeCompare(b, undefined, { sensitivity: "base" }),
  );
}

/** Filter option value is the canonical key; label is display form. */
export function filterOptionValue(label: string): string {
  return canonicalTokenKey(label) || label;
}
