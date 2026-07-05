"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { useTranslations } from "next-intl";

import FlagIcon from "@/components/FlagIcon";

const locales = ["en", "zh"] as const;

type AppLocale = (typeof locales)[number];

export default function LocaleSwitcher({ locale }: { locale: string }) {
  const labels = useTranslations("locale");
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  const activeLocale: AppLocale = locale.startsWith("zh") ? "zh" : "en";
  const others = locales.filter((code) => code !== activeLocale);

  useEffect(() => {
    const onDoc = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const switchTo = (targetLocale: AppLocale) => {
    const segments = pathname.split("/").filter(Boolean);
    if (segments[0]) {
      segments[0] = targetLocale;
    } else {
      segments.unshift(targetLocale);
    }
    router.push("/" + segments.join("/"));
    setOpen(false);
  };

  const activeLabel = labels(activeLocale);

  return (
    <div className="qb-locale-wrap" ref={rootRef}>
      <button
        type="button"
        className="qb-locale-btn"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={activeLabel}
        onClick={() => setOpen((value) => !value)}
      >
        <FlagIcon locale={activeLocale} size={22} />
        <span className="qb-locale-label">{activeLabel}</span>
      </button>
      {open ?
        <div className="qb-locale-menu" role="listbox">
          {others.map((code) => (
              <button
                key={code}
                type="button"
                className="qb-locale-menu-item"
                role="option"
                onClick={() => switchTo(code)}
              >
                <FlagIcon locale={code} size={22} />
                <span>{labels(code)}</span>
              </button>
            ))}
        </div>
      : null}
    </div>
  );
}
