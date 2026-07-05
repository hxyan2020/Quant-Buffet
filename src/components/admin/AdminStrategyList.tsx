"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState, useTransition } from "react";

import {
  buildMonthSelectOptions,
  monthToRangeEnd,
  monthToRangeStart,
} from "@/lib/admin-date-options";

type StrategyRow = {
  id: string;
  locale: string;
  title: string;
  slug: string;
  region: string | null;
  market: string | null;
  assetClass: string | null;
  isPaywalled: boolean;
  published: boolean;
  hasPythonCode: boolean;
  createdAt: string;
  updatedAt: string;
};

type FilterOptions = {
  regions: string[];
  markets: string[];
  assetClasses: string[];
};

function formatDt(iso: string) {
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Map stored ISO date param back to YYYY-MM for month dropdowns. */
function isoToMonthParam(iso: string | null): string {
  if (!iso?.trim()) return "";
  const m = iso.match(/^(\d{4}-\d{2})/);
  return m?.[1] ?? "";
}

export default function AdminStrategyList() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [pending, startTransition] = useTransition();
  const [rows, setRows] = useState<StrategyRow[]>([]);
  const [filterOptions, setFilterOptions] = useState<FilterOptions>({
    regions: [],
    markets: [],
    assetClasses: [],
  });
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const monthOptions = useMemo(() => buildMonthSelectOptions(), []);
  const queryString = searchParams.toString();

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`/api/admin/strategies?${queryString}`);
      const data = await res.json();
      if (!res.ok) throw new Error(data?.error ?? "load_failed");
      setRows(data.strategies ?? []);
      setTotal(data.total ?? 0);
      setFilterOptions(data.filterOptions ?? { regions: [], markets: [], assetClasses: [] });
    } catch {
      setRows([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [queryString]);

  useEffect(() => {
    void load();
  }, [load]);

  const pushFilters = (form: HTMLFormElement) => {
    const data = new FormData(form);
    const params = new URLSearchParams();
    for (const [key, value] of data.entries()) {
      const v = value.toString().trim();
      if (!v) continue;
      if (key === "createdMin" || key === "updatedMin") {
        const start = monthToRangeStart(v);
        if (start) params.set(key, start);
      } else if (key === "createdMax" || key === "updatedMax") {
        const end = monthToRangeEnd(v);
        if (end) params.set(key, end);
      } else {
        params.set(key, v);
      }
    }
    startTransition(() => {
      router.push(`/admin/strategies?${params.toString()}`);
    });
  };

  async function togglePaywall(id: string, next: boolean) {
    const res = await fetch(`/api/admin/strategies/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ isPaywalled: next }),
    });
    if (res.ok) {
      setRows((prev) =>
        prev.map((row) => (row.id === id ? { ...row, isPaywalled: next } : row)),
      );
    }
  }

  const sp = searchParams;

  return (
    <div className="qb-admin-page">
      <div className="qb-admin-page-head">
        <div>
          <h1 className="qb-admin-page-title">Strategy CMS</h1>
          <p className="qb-admin-page-sub">{total} strategies (filtered)</p>
        </div>
        <Link href="/admin/strategies/new" className="qb-admin-btn-primary">
          + Create strategy
        </Link>
      </div>

      <form
        className="qb-admin-filters"
        onSubmit={(e) => {
          e.preventDefault();
          pushFilters(e.currentTarget);
        }}
      >
        <div className="qb-admin-filter-field qb-admin-filter-grow">
          <label htmlFor="adm-q">Search name</label>
          <input
            id="adm-q"
            name="q"
            type="search"
            className="qb-admin-input"
            defaultValue={sp.get("q") ?? ""}
            placeholder="Strategy title or slug…"
          />
        </div>
        <div className="qb-admin-filter-field">
          <label htmlFor="adm-lang">Language</label>
          <select id="adm-lang" name="locale" className="qb-admin-input" defaultValue={sp.get("locale") ?? ""}>
            <option value="">All</option>
            <option value="en">EN</option>
            <option value="zh">CN</option>
          </select>
        </div>
        <div className="qb-admin-filter-field">
          <label htmlFor="adm-python">Python code</label>
          <select id="adm-python" name="python" className="qb-admin-input" defaultValue={sp.get("python") ?? ""}>
            <option value="">All</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
        <div className="qb-admin-filter-field">
          <label htmlFor="adm-paywall">Paywall</label>
          <select id="adm-paywall" name="paywall" className="qb-admin-input" defaultValue={sp.get("paywall") ?? ""}>
            <option value="">All</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
        <div className="qb-admin-filter-field">
          <label htmlFor="adm-pub">Published</label>
          <select id="adm-pub" name="published" className="qb-admin-input" defaultValue={sp.get("published") ?? ""}>
            <option value="">All</option>
            <option value="yes">Yes</option>
            <option value="no">No</option>
          </select>
        </div>
        <div className="qb-admin-filter-field">
          <label htmlFor="adm-asset">Asset class</label>
          <select id="adm-asset" name="assetClass" className="qb-admin-input" defaultValue={sp.get("assetClass") ?? ""}>
            <option value="">All</option>
            {filterOptions.assetClasses.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
        <div className="qb-admin-filter-field">
          <label htmlFor="adm-region">Region</label>
          <select id="adm-region" name="region" className="qb-admin-input" defaultValue={sp.get("region") ?? ""}>
            <option value="">All</option>
            {filterOptions.regions.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
        <div className="qb-admin-filter-field">
          <label htmlFor="adm-market">Market</label>
          <select id="adm-market" name="market" className="qb-admin-input" defaultValue={sp.get("market") ?? ""}>
            <option value="">All</option>
            {filterOptions.markets.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </div>
        <div className="qb-admin-filters-dates">
          <div className="qb-admin-filter-field">
            <label htmlFor="adm-cmin">Created from</label>
            <select
              id="adm-cmin"
              name="createdMin"
              className="qb-admin-input"
              defaultValue={isoToMonthParam(sp.get("createdMin"))}
            >
              {monthOptions.map((o) => (
                <option key={`cmin-${o.value || "any"}`} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="qb-admin-filter-field">
            <label htmlFor="adm-cmax">Created to</label>
            <select
              id="adm-cmax"
              name="createdMax"
              className="qb-admin-input"
              defaultValue={isoToMonthParam(sp.get("createdMax"))}
            >
              {monthOptions.map((o) => (
                <option key={`cmax-${o.value || "any"}`} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="qb-admin-filter-field">
            <label htmlFor="adm-umin">Updated from</label>
            <select
              id="adm-umin"
              name="updatedMin"
              className="qb-admin-input"
              defaultValue={isoToMonthParam(sp.get("updatedMin"))}
            >
              {monthOptions.map((o) => (
                <option key={`umin-${o.value || "any"}`} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
          <div className="qb-admin-filter-field">
            <label htmlFor="adm-umax">Updated to</label>
            <select
              id="adm-umax"
              name="updatedMax"
              className="qb-admin-input"
              defaultValue={isoToMonthParam(sp.get("updatedMax"))}
            >
              {monthOptions.map((o) => (
                <option key={`umax-${o.value || "any"}`} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <p className="qb-admin-filter-hint">
          Date filters use Created/Updated timestamps. If a filter returns no rows, set all date fields to
          &nbsp;<strong>Any</strong> and click Clear.
        </p>

        <div className="qb-admin-filter-actions qb-admin-filter-actions-bottom">
          <button type="submit" className="qb-admin-btn-primary" disabled={pending}>
            Apply
          </button>
          <button
            type="button"
            className="qb-admin-btn-secondary"
            disabled={pending}
            onClick={() => router.push("/admin/strategies")}
          >
            Clear
          </button>
        </div>
      </form>

      <div className="qb-admin-table-wrap">
        {loading ?
          <p className="qb-admin-muted">Loading…</p>
        : (
          <table className="qb-admin-table">
            <thead>
              <tr>
                <th>Lang</th>
                <th>Title</th>
                <th>Paywall</th>
                <th>Published</th>
                <th>Python</th>
                <th>Created</th>
                <th>Updated</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ?
                <tr>
                  <td colSpan={8} className="qb-admin-empty">
                    No strategies match these filters.
                  </td>
                </tr>
              : rows.map((row) => (
                  <tr key={row.id}>
                    <td>{row.locale === "zh" ? "CN" : "EN"}</td>
                    <td className="qb-admin-title-cell">
                      <span className="qb-admin-title-text">{row.title}</span>
                      <span className="qb-admin-slug">{row.slug}</span>
                    </td>
                    <td>
                      <select
                        className="qb-admin-toggle-select"
                        value={row.isPaywalled ? "yes" : "no"}
                        onChange={(e) =>
                          void togglePaywall(row.id, e.target.value === "yes")
                        }
                      >
                        <option value="yes">Yes</option>
                        <option value="no">No</option>
                      </select>
                    </td>
                    <td>{row.published ? "Yes" : "No"}</td>
                    <td>{row.hasPythonCode ? "Yes" : "No"}</td>
                    <td className="qb-admin-dt">{formatDt(row.createdAt)}</td>
                    <td className="qb-admin-dt">{formatDt(row.updatedAt)}</td>
                    <td>
                      <Link href={`/admin/strategies/${row.id}`} className="qb-admin-link">
                        Edit
                      </Link>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
