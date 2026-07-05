/** Heuristic: strategy HTML contains substantive Python / backtest code. */
export function detectPythonCode(html: string | null | undefined): boolean {
  if (!html?.trim()) return false;
  const sample = html.slice(0, 600_000);
  const lower = sample.toLowerCase();

  const patterns = [
    /language-python/i,
    /lang=["']python["']/i,
    /```python/i,
    /\bimport\s+pandas\b/i,
    /\bimport\s+numpy\b/i,
    /\bfrom\s+zipline\b/i,
    /\bimport\s+zipline\b/i,
    /\bbacktrader\b/i,
    /\bquantopian\b/i,
    /\bimport\s+backtrader\b/i,
    /full\s+python\s+code/i,
    /完整\s*python\s*代码/i,
    /python\s+implementation/i,
    /wp:code[^>]*python/i,
    /\bqcalgorithm\b/i,
    /\bquantconnect\b/i,
    /\bself\.set_\w+/i,
    /\bself\.add_equity\b/i,
    /\bself\.download\s*\(/i,
    /\bclass\s+\w*algorithm\w*/i,
    /<pre[^>]*>[\s\S]{30,}?\bimport\s+\w+/i,
    /<code[^>]*>[\s\S]{30,}?\bimport\s+\w+/i,
    /\bdef\s+\w+\s*\([^)]*\)\s*:/,
    /\bself\.\w+\s*[:=]/,
  ];

  return patterns.some((re) => re.test(sample) || re.test(lower));
}

/** Combined HTML used for detection and storage flags. */
export function strategyCodeBlob(
  contentHtml: string | null | undefined,
  pythonCodeHtml?: string | null,
): string {
  return [contentHtml ?? "", pythonCodeHtml ?? ""].filter(Boolean).join("\n");
}
