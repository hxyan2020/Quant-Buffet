"use client";

import { useEffect } from "react";

/** Keep <html lang> aligned with the active locale for SEO/a11y. */
export default function LocaleHtmlLang({ locale }: { locale: string }) {
  useEffect(() => {
    document.documentElement.lang = locale === "zh" ? "zh-CN" : "en";
  }, [locale]);
  return null;
}
