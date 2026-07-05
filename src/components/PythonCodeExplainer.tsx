"use client";

import { useCallback, useMemo, useState } from "react";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/github-dark.min.css";

import { extractPythonPlainText } from "@/lib/format-python";
import { PYTHON_TIPS_ALL } from "@/lib/python-tooltips";

hljs.registerLanguage("python", python);

type Props = {
  codeHtml: string;
  locale: string;
};

type ActiveTip = { text: string; className: string; label: string };

function highlightSegment(text: string): string {
  if (!text) return "";
  return hljs.highlight(text, { language: "python" }).value;
}

export default function PythonCodeExplainer({ codeHtml, locale }: Props) {
  const [active, setActive] = useState<ActiveTip | null>(null);
  const isZh = locale === "zh";

  const code = useMemo(() => extractPythonPlainText(codeHtml), [codeHtml]);

  const segments = useMemo(() => {
    if (!code.trim()) return [];
    type Seg = { text: string; tip?: ActiveTip; html?: string };
    const tips = PYTHON_TIPS_ALL.map((t) => ({
      ...t,
      text: isZh ? t.zh : t.en,
      label: t.syntax,
    }));

    const matches: { index: number; len: number; tip: ActiveTip }[] = [];
    for (const tip of tips) {
      const re = new RegExp(
        tip.pattern.source,
        tip.pattern.flags.includes("g") ? tip.pattern.flags : `${tip.pattern.flags}g`,
      );
      let m: RegExpExecArray | null;
      while ((m = re.exec(code)) !== null) {
        matches.push({
          index: m.index,
          len: m[0].length,
          tip: { text: tip.text, className: tip.className, label: tip.syntax },
        });
      }
    }
    matches.sort((a, b) => a.index - b.index);

    const out: Seg[] = [];
    let cursor = 0;
    for (const hit of matches) {
      if (hit.index < cursor) continue;
      if (hit.index > cursor) {
        const plain = code.slice(cursor, hit.index);
        out.push({ text: plain, html: highlightSegment(plain) });
      }
      out.push({
        text: code.slice(hit.index, hit.index + hit.len),
        tip: hit.tip,
      });
      cursor = hit.index + hit.len;
    }
    if (cursor < code.length) {
      const plain = code.slice(cursor);
      out.push({ text: plain, html: highlightSegment(plain) });
    }
    return out;
  }, [code, isZh]);

  const showTip = useCallback((tip: ActiveTip | undefined) => {
    setActive(tip ?? null);
  }, []);

  if (!code.trim()) {
    return null;
  }

  return (
    <div className="qb-python-explainer">
      <pre className="qb-python-pretty qb-python-interactive qb-python-highlight-wrap">
        <code className="language-python hljs">
          {segments.map((seg, i) =>
            seg.tip ?
              <mark
                key={i}
                className={`qb-py-mark ${seg.tip.className}`}
                onMouseEnter={() => showTip(seg.tip)}
                onMouseLeave={() => showTip(undefined)}
                onClick={() =>
                  setActive((prev) =>
                    prev?.label === seg.tip?.label ? null : (seg.tip ?? null),
                  )
                }
              >
                {seg.text}
              </mark>
            : <span key={i} dangerouslySetInnerHTML={{ __html: seg.html ?? "" }} />,
          )}
        </code>
      </pre>
      {active ?
        <div className="qb-python-tooltip" role="tooltip">
          <p className="qb-python-tooltip-label">{active.label}</p>
          <p>{active.text}</p>
          <p className="qb-python-tooltip-hint">
            {isZh ? "点击或悬停查看说明（手机可点击）" : "Hover (desktop) or tap (mobile) highlighted syntax"}
          </p>
        </div>
      : null}
    </div>
  );
}
