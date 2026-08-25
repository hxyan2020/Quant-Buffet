import { findLabEntry, loadLabPythonSource } from "@/lib/draft-preview";
import { extractPythonPlainText } from "@/lib/format-python";
import { toLabPythonSource } from "@/lib/draft-preview";

/**
 * Resolve Quant Buffet–native Python for platform export on strategy pages.
 * Prefers generated lab .py files; falls back to HTML/plain code.
 */
export function resolveStrategyLabSource(opts: {
  slug: string;
  locale: string;
  pythonCodeHtml?: string | null;
}): string {
  const html = opts.pythonCodeHtml || "";
  const entry =
    findLabEntry(opts.locale, opts.slug) ||
    findLabEntry("en", opts.slug) ||
    findLabEntry("zh", opts.slug);

  if (entry) {
    return loadLabPythonSource(entry, html);
  }

  const plain = extractPythonPlainText(html);
  if (!plain.trim()) return "";
  return toLabPythonSource(opts.slug, plain);
}
