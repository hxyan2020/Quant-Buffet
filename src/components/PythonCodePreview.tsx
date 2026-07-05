"use client";

import { useEffect, useRef } from "react";
import hljs from "highlight.js/lib/core";
import python from "highlight.js/lib/languages/python";
import "highlight.js/styles/github-dark.min.css";

hljs.registerLanguage("python", python);

type Props = {
  codeHtml: string;
};

export default function PythonCodePreview({ codeHtml }: Props) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!ref.current) return;
    ref.current.querySelectorAll("pre code").forEach((block) => {
      hljs.highlightElement(block as HTMLElement);
    });
  }, [codeHtml]);

  if (!codeHtml.trim()) return null;

  return (
    <div
      ref={ref}
      className="qb-python-highlight-wrap strategy-python-block"
      dangerouslySetInnerHTML={{ __html: codeHtml }}
    />
  );
}
