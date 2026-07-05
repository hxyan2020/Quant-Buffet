/** Clean plain text extracted from WordPress HTML. */

const SECTION_TAIL =
  /\s*(?:(?:I{1,3}|IV|V|VI{0,3})\.\s*)?(?:SOURCE\s+PAPER|BACKTEST\s+PERFORMANCE|ECONOMIC\s+RATIONALE|STRATEGY\s+IN\s+A\s+NUTSHELL|FULL\s+PYTHON\s+CODE|来源论文|回测|经济逻辑|策略概要)\s*\.?\s*$/i;

const BROKEN_TAG_TAIL = /\s*<(?:strong|em|b|i|a|p|span|div)(?:\s[^>]*)?$/i;
const BROKEN_TAG_ANY = /<(?:strong|em|b|i)(?:\s[^>]*)?$/gi;
const ROMAN_ONLY = /^\s*(?:I{1,3}|IV|V|VI{0,3})\.\s*$/i;

export function decodeEntities(text: string): string {
  return text
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
}

export function stripHtmlToText(html: string): string {
  return decodeEntities(
    html
      .replace(/<br\s*\/?>/gi, "\n")
      .replace(/<\/p>/gi, "\n")
      .replace(/<\/h[1-6]>/gi, "\n")
      .replace(/<[^>]+>/g, ""),
  );
}

export function sanitizePlainText(htmlOrText: string): string {
  let t = stripHtmlToText(htmlOrText);
  t = t.replace(BROKEN_TAG_ANY, "");
  t = t.replace(BROKEN_TAG_TAIL, "");
  t = t.replace(/```[\s\S]*?```/g, "");
  t = t.replace(/`[^`]+`/g, "");
  t = t.replace(SECTION_TAIL, "");
  t = t.replace(/\s*(?:I{1,3}|IV|V|VI{0,3})\.\s*$/gi, "");
  t = t
    .split("\n")
    .map((line) => line.trim())
    .filter((line) => line.length > 0 && !ROMAN_ONLY.test(line))
    .join("\n\n");
  t = t.replace(/\n{3,}/g, "\n\n").trim();
  return t;
}

export function naOr(value: string | null | undefined): string {
  const v = value?.trim() ?? "";
  if (!v || v.toLowerCase() === "n/a") return "N/A";
  return v;
}

/** True when a section should render (not empty, not N/A, not placeholder-only). */
export function hasMeaningfulContent(value: string | null | undefined): boolean {
  const v = naOr(value);
  if (v === "N/A") return false;
  if (/^[?？\s.—\-–·•|/\\]+$/u.test(v)) return false;
  return true;
}

export function emptyToNa(value: string | null | undefined): string {
  const v = sanitizePlainText(value ?? "");
  return v.length > 0 ? v : "N/A";
}
