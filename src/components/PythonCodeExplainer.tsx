"use client";

import { useCallback, useMemo, useState } from "react";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/github-dark.min.css";
import { useTranslations } from "next-intl";

import { extractPythonPlainText, stripPythonAnnotations } from "@/lib/format-python";
import { PYTHON_TIPS_ALL } from "@/lib/python-tooltips";

hljs.registerLanguage("python", python);

type Props = {
  codeHtml: string;
  locale: string;
};

type ActiveTip = { text: string; className: string; label: string };
type Seg = { text: string; tip?: ActiveTip; html?: string };
type CodeMode = "annotated" | "clean";

function highlightSegment(text: string): string {
  if (!text) return "";
  return hljs.highlight(text, { language: "python" }).value;
}

function buildSegments(code: string, isZh: boolean): Seg[] {
  if (!code.trim()) return [];

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
}

/** Split whole-file segments into per-line segment lists (preserves tip marks). */
function segmentsByLine(segments: Seg[]): Seg[][] {
  const lines: Seg[][] = [[]];
  for (const seg of segments) {
    const parts = seg.text.split("\n");
    parts.forEach((part, partIndex) => {
      if (partIndex > 0) lines.push([]);
      if (part.length === 0) return;
      lines[lines.length - 1].push(
        seg.tip ? { text: part, tip: seg.tip } : { text: part, html: highlightSegment(part) },
      );
    });
  }
  return lines;
}

export default function PythonCodeExplainer({ codeHtml, locale }: Props) {
  const dictionary = useTranslations("strategy");
  const [active, setActive] = useState<ActiveTip | null>(null);
  const [mode, setMode] = useState<CodeMode>("annotated");
  const [copied, setCopied] = useState(false);
  const isZh = locale === "zh";

  const annotated = useMemo(() => extractPythonPlainText(codeHtml), [codeHtml]);
  const clean = useMemo(() => stripPythonAnnotations(annotated), [annotated]);
  const displayCode = mode === "clean" ? clean : annotated;
  const isClean = mode === "clean";

  const lineSegments = useMemo((): Seg[][] => {
    if (isClean) {
      // Plain syntax highlight only — no tip marks.
      return displayCode.split("\n").map((line) =>
        line.length > 0 ? [{ text: line, html: highlightSegment(line) }] : [],
      );
    }
    return segmentsByLine(buildSegments(displayCode, isZh));
  }, [displayCode, isZh, isClean]);

  const showTip = useCallback((tip: ActiveTip | undefined) => {
    setActive(tip ?? null);
  }, []);

  const setCodeMode = useCallback((next: CodeMode) => {
    setMode(next);
    if (next === "clean") setActive(null);
  }, []);

  const copyCode = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(displayCode);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1800);
    } catch {
      setCopied(false);
    }
  }, [displayCode]);

  if (!annotated.trim()) {
    return null;
  }

  return (
    <div className="qb-python-explainer">
      <div className="qb-python-toolbar">
        <div className="qb-python-mode-toggle" role="group" aria-label={dictionary("codeModeLabel")}>
          <button
            type="button"
            className={mode === "annotated" ? "is-active" : undefined}
            aria-pressed={mode === "annotated"}
            onClick={() => setCodeMode("annotated")}
          >
            {dictionary("codeAnnotated")}
          </button>
          <button
            type="button"
            className={mode === "clean" ? "is-active" : undefined}
            aria-pressed={mode === "clean"}
            onClick={() => setCodeMode("clean")}
          >
            {dictionary("codeClean")}
          </button>
        </div>
        <button type="button" className="qb-python-copy" onClick={copyCode}>
          {copied ? dictionary("codeCopied") : dictionary("codeCopy")}
        </button>
      </div>

      <pre
        className={`qb-python-pretty qb-python-highlight-wrap qb-python-with-lines${
          isClean ? "" : " qb-python-interactive"
        }`}
      >
        <code className="language-python hljs qb-python-lines">
          {lineSegments.map((segs, lineIndex) => (
            <span className="qb-python-line" key={lineIndex}>
              <span className="qb-python-lineno" aria-hidden>
                {lineIndex + 1}
              </span>
              <span className="qb-python-line-code">
                {segs.map((seg, i) =>
                  !isClean && seg.tip ?
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
                  : <span key={i} dangerouslySetInnerHTML={{ __html: seg.html ?? highlightSegment(seg.text) }} />,
                )}
                {"\n"}
              </span>
            </span>
          ))}
        </code>
      </pre>

      {!isClean && active ?
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
