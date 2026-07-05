/** Extract and pretty-print Python from WordPress HTML code blocks. */

function decodeEntities(text: string): string {
  return text
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/g, "&")
    .replace(/&lt;/g, "<")
    .replace(/&gt;/g, ">")
    .replace(/&quot;/g, '"')
    .replace(/&#039;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
}

function extractRawCode(html: string): string {
  const pre = html.match(/<pre[^>]*>([\s\S]*?)<\/pre>/i);
  if (pre?.[1]) return decodeEntities(pre[1].replace(/<[^>]+>/g, ""));
  const code = html.match(/<code[^>]*>([\s\S]*?)<\/code>/i);
  if (code?.[1]) return decodeEntities(code[1].replace(/<[^>]+>/g, ""));
  if (html.includes("```")) {
    const fence = html.match(/```(?:python)?\s*([\s\S]*?)```/i);
    if (fence?.[1]) return fence[1].trim();
  }
  return decodeEntities(html.replace(/<[^>]+>/g, "\n"));
}

/** Normalize indentation and line endings for display. */
function normalizePythonLines(source: string): string {
  const lines = source.replace(/\r\n/g, "\n").split("\n");
  const nonEmpty = lines.filter((l) => l.trim().length > 0);
  if (nonEmpty.length === 0) return source.trim();

  const indents = nonEmpty.map((l) => l.match(/^(\s*)/)?.[1]?.length ?? 0);
  const minIndent = Math.min(...indents.filter((n) => n > 0), Infinity);
  const trimBy = Number.isFinite(minIndent) && minIndent > 0 ? minIndent : 0;

  return lines
    .map((line) => (trimBy > 0 && line.startsWith(" ".repeat(trimBy)) ? line.slice(trimBy) : line))
    .join("\n")
    .trim();
}

/** HTML snippet for strategy article / admin (escaped, monospace pre). */
export function formatPythonCodeHtml(rawHtmlOrCode: string | null | undefined): string {
  if (!rawHtmlOrCode?.trim()) return "";

  const raw = extractRawCode(rawHtmlOrCode);
  const pretty = normalizePythonLines(raw);
  if (!pretty) return "";

  const escaped = pretty
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return `<pre class="qb-python-pretty"><code class="language-python">${escaped}</code></pre>`;
}

export function extractPythonPlainText(rawHtmlOrCode: string | null | undefined): string {
  if (!rawHtmlOrCode?.trim()) return "";
  return normalizePythonLines(extractRawCode(rawHtmlOrCode));
}
