"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

export type LabListRow = {
  source: "library" | "new100";
  slug: string;
  locale: string;
  title: string;
  template?: string | null;
  annualisedReturn?: string | null;
  sharpeRatio?: string | null;
  maxDrawdown?: string | null;
  href: string;
  assetClass?: string | null;
};

type Props = {
  rows: LabListRow[];
  libraryCount: number;
  new100Count: number;
};

/** Fully SSR-fed list — no client fetch (avoids tunnel / AbortSignal stalls). */
export default function LabStrategyList({ rows, libraryCount, new100Count }: Props) {
  const [q, setQ] = useState("");
  const [source, setSource] = useState<"all" | "library" | "new100">("all");
  const [locale, setLocale] = useState<"all" | "en" | "zh">("all");

  const filtered = useMemo(() => {
    const needle = q.trim().toLowerCase();
    return rows.filter((r) => {
      if (source !== "all" && r.source !== source) return false;
      if (locale !== "all" && r.locale !== locale) return false;
      if (!needle) return true;
      return (
        r.title.toLowerCase().includes(needle) ||
        r.slug.toLowerCase().includes(needle) ||
        (r.template || "").toLowerCase().includes(needle) ||
        (r.assetClass || "").toLowerCase().includes(needle)
      );
    });
  }, [rows, q, source, locale]);

  return (
    <div className="qb-lab-list">
      <div className="qb-lab-list-filters">
        <input
          className="qb-lab-list-search"
          placeholder="Search title, slug, template…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
          aria-label="Search strategies"
        />
        <select
          className="qb-lab-list-select"
          value={source}
          onChange={(e) => setSource(e.target.value as typeof source)}
          aria-label="Source filter"
        >
          <option value="all">All sources ({rows.length})</option>
          <option value="library">Library ({libraryCount})</option>
          <option value="new100">New drafts ({new100Count})</option>
        </select>
        <select
          className="qb-lab-list-select"
          value={locale}
          onChange={(e) => setLocale(e.target.value as typeof locale)}
          aria-label="Locale filter"
        >
          <option value="all">All locales</option>
          <option value="en">English</option>
          <option value="zh">中文</option>
        </select>
        <span className="qb-lab-list-count">
          Showing {filtered.length} / {rows.length}
        </span>
      </div>

      <div style={{ overflowX: "auto", marginTop: 12, maxHeight: "70vh", overflowY: "auto" }}>
        <table className="qb-table" style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead style={{ position: "sticky", top: 0, background: "var(--qb-surface, #0b0f12)" }}>
            <tr style={{ textAlign: "left", borderBottom: "1px solid rgba(159,179,207,0.35)" }}>
              <th style={{ padding: "8px 6px" }}>#</th>
              <th style={{ padding: "8px 6px" }}>Source</th>
              <th style={{ padding: "8px 6px" }}>Title</th>
              <th style={{ padding: "8px 6px" }}>CAGR</th>
              <th style={{ padding: "8px 6px" }}>Sharpe</th>
              <th style={{ padding: "8px 6px" }}>MaxDD</th>
              <th style={{ padding: "8px 6px" }}>Template</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((p, i) => (
              <tr
                key={`${p.source}:${p.locale}:${p.slug}`}
                style={{ borderBottom: "1px solid rgba(159,179,207,0.12)" }}
              >
                <td style={{ padding: "7px 6px", opacity: 0.65 }}>{i + 1}</td>
                <td style={{ padding: "7px 6px" }}>
                  <span className={p.source === "new100" ? "qb-lab-tag-new" : "qb-lab-tag-lib"}>
                    {p.source === "new100" ? "new" : "lib"}
                  </span>{" "}
                  <span style={{ opacity: 0.6 }}>{p.locale}</span>
                </td>
                <td style={{ padding: "7px 6px" }}>
                  <Link href={p.href}>{p.title}</Link>
                  <div style={{ fontSize: 11, opacity: 0.55, marginTop: 2 }}>{p.slug}</div>
                </td>
                <td style={{ padding: "7px 6px" }}>{p.annualisedReturn ?? "—"}</td>
                <td style={{ padding: "7px 6px" }}>{p.sharpeRatio ?? "—"}</td>
                <td style={{ padding: "7px 6px" }}>{p.maxDrawdown ?? "—"}</td>
                <td style={{ padding: "7px 6px" }}>{p.template ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
