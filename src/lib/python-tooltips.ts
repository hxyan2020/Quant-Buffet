export type { PythonTip } from "@/lib/python-tooltips-data";
export {
  PYTHON_TIPS,
  PYTHON_TIPS_ALL,
  PYTHON_TIP_COUNT,
  getPythonTooltipCatalog,
} from "@/lib/python-tooltips-data";

import { PYTHON_TIPS_ALL } from "@/lib/python-tooltips-data";

export function buildTooltipLexicon(locale: string): Record<string, { text: string; className: string }> {
  const lex: Record<string, { text: string; className: string }> = {};
  for (const tip of PYTHON_TIPS_ALL) {
    lex[tip.pattern.source] = {
      text: locale === "zh" ? tip.zh : tip.en,
      className: tip.className,
    };
  }
  return lex;
}
