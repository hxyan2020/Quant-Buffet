"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useMemo, useTransition } from "react";

import LibraryCollectButton from "@/components/LibraryCollectButton";
import { strategyHref } from "@/lib/slug";
import { formatTokenList } from "@/lib/strategy-tokens";

export type StrategyRow = {
  id: string;
  slug: string;
  title: string;
  annualisedReturn: string | null;
  sharpeRatio: string | null;
  region: string | null;
  market: string | null;
  assetClass: string | null;
  frequency: string | null;
  isPaywalled: boolean;
};

type Labels = {
  colNo: string;
  colName: string;
  colAnn: string;
  colSharpe: string;
  colRegion: string;
  colMarket: string;
  colAsset: string;
  colFreq: string;
  colPlan: string;
  colCollect: string;
  colLink: string;
  planPaid: string;
  planFree: string;
  collect: string;
  collected: string;
  open: string;
  searchPlaceholder: string;
  showing: string;
  prev: string;
  next: string;
  filterSearch: string;
  filterMarket: string;
  filterRegion: string;
  filterAsset: string;
  filterPlan: string;
  filterCollection: string;
  filterAll: string;
  filterCollected: string;
  filterNotCollected: string;
  apply: string;
  clear: string;
};

type FilterOptions = {
  markets: string[];
  regions: string[];
  assetClasses: string[];
};

type Props = {
  locale: string;
  rows: StrategyRow[];
  total: number;
  page: number;
  totalPages: number;
  pageSize: number;
  isLoggedIn: boolean;
  collectedIds: string[];
  initialQuery: string;
  initialMarket: string;
  initialRegion: string;
  initialAssetClass: string;
  initialPlan: string;
  initialCollection: string;
  filterOptions: FilterOptions;
  labels: Labels;
};

export default function StrategyLibraryTable({
  locale,
  rows,
  total,
  page,
  totalPages,
  pageSize,
  isLoggedIn,
  collectedIds,
  initialQuery,
  initialMarket,
  initialRegion,
  initialAssetClass,
  initialPlan,
  initialCollection,
  filterOptions,
  labels,
}: Props) {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const [pending, startTransition] = useTransition();
  const collectedSet = useMemo(() => new Set(collectedIds), [collectedIds]);

  const pushParams = useCallback(
    (next: {
      page: number;
      q: string;
      market: string;
      region: string;
      assetClass: string;
      plan: string;
      collection: string;
    }) => {
      const params = new URLSearchParams(searchParams.toString());
      params.set("page", String(next.page));
      if (next.q.trim()) params.set("q", next.q.trim());
      else params.delete("q");
      if (next.market) params.set("market", next.market);
      else params.delete("market");
      if (next.region) params.set("region", next.region);
      else params.delete("region");
      if (next.assetClass) params.set("assetClass", next.assetClass);
      else params.delete("assetClass");
      if (next.plan === "paid" || next.plan === "free") params.set("plan", next.plan);
      else params.delete("plan");
      if (next.collection === "collected" || next.collection === "not_collected") {
        params.set("collection", next.collection);
      } else params.delete("collection");
      startTransition(() => {
        router.push(`${pathname}?${params.toString()}`);
      });
    },
    [pathname, router, searchParams],
  );

  const startNo = (page - 1) * pageSize + 1;

  return (
    <div>
      <form
        className="qb-search-row"
        onSubmit={(event) => {
          event.preventDefault();
          const form = event.currentTarget;
          const data = new FormData(form);
          pushParams({
            page: 1,
            q: data.get("q")?.toString() ?? "",
            market: data.get("market")?.toString() ?? "",
            region: data.get("region")?.toString() ?? "",
            assetClass: data.get("assetClass")?.toString() ?? "",
            plan: data.get("plan")?.toString() ?? "",
            collection: data.get("collection")?.toString() ?? "",
          });
        }}
      >
        <div className="qb-filter-field qb-filter-field-grow">
          <label className="qb-filter-label" htmlFor="library-search">
            {labels.filterSearch}
          </label>
          <input
            id="library-search"
            name="q"
            type="search"
            defaultValue={initialQuery}
            placeholder={labels.searchPlaceholder}
            className="qb-input"
          />
        </div>
        <div className="qb-filter-field">
          <label className="qb-filter-label" htmlFor="library-collection">
            {labels.filterCollection}
          </label>
          <select id="library-collection" name="collection" className="qb-select" defaultValue={initialCollection}>
            <option value="">{labels.filterAll}</option>
            <option value="collected">{labels.filterCollected}</option>
            <option value="not_collected">{labels.filterNotCollected}</option>
          </select>
        </div>
        <div className="qb-filter-field">
          <label className="qb-filter-label" htmlFor="library-plan">
            {labels.filterPlan}
          </label>
          <select id="library-plan" name="plan" className="qb-select" defaultValue={initialPlan}>
            <option value="">{labels.filterAll}</option>
            <option value="free">{labels.planFree}</option>
            <option value="paid">{labels.planPaid}</option>
          </select>
        </div>
        <div className="qb-filter-field">
          <label className="qb-filter-label" htmlFor="library-asset">
            {labels.filterAsset}
          </label>
          <select id="library-asset" name="assetClass" className="qb-select" defaultValue={initialAssetClass}>
            <option value="">{labels.filterAll}</option>
            {filterOptions.assetClasses.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div className="qb-filter-field">
          <label className="qb-filter-label" htmlFor="library-region">
            {labels.filterRegion}
          </label>
          <select id="library-region" name="region" className="qb-select" defaultValue={initialRegion}>
            <option value="">{labels.filterAll}</option>
            {filterOptions.regions.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div className="qb-filter-field">
          <label className="qb-filter-label" htmlFor="library-market">
            {labels.filterMarket}
          </label>
          <select id="library-market" name="market" className="qb-select" defaultValue={initialMarket}>
            <option value="">{labels.filterAll}</option>
            {filterOptions.markets.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </div>
        <div className="qb-search-actions">
          <button type="submit" className="qb-pill-primary" disabled={pending}>
            {labels.apply}
          </button>
          <button
            type="button"
            className="qb-secondary"
            disabled={pending}
            onClick={() =>
              pushParams({
                page: 1,
                q: "",
                market: "",
                region: "",
                assetClass: "",
                plan: "",
                collection: "",
              })
            }
          >
            {labels.clear}
          </button>
        </div>
      </form>

      <p className="qb-muted" style={{ fontSize: "0.75rem", letterSpacing: "0.2em", textTransform: "uppercase" }}>
        {labels.showing}
      </p>

      <div className="qb-table-wrap" style={{ marginTop: "1rem" }}>
        <table className="qb-grid qb-library-grid">
          <thead>
            <tr>
              <th>{labels.colNo}</th>
              <th>{labels.colName}</th>
              <th>{labels.colAnn}</th>
              <th>{labels.colSharpe}</th>
              <th>{labels.colRegion}</th>
              <th>{labels.colMarket}</th>
              <th>{labels.colAsset}</th>
              <th>{labels.colFreq}</th>
              <th>{labels.colPlan}</th>
              <th>{labels.colCollect}</th>
              <th>{labels.colLink}</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 ?
              <tr>
                <td colSpan={11} style={{ padding: "3rem", textAlign: "center", color: "#8ca0b8" }}>
                  No strategies match your search.
                </td>
              </tr>
            : rows.map((strategy, index) => (
                <tr key={strategy.id}>
                  <td style={{ color: "#8ca0b8", whiteSpace: "nowrap" }}>{startNo + index}</td>
                  <td className="qb-strategy-title-cell">{strategy.title}</td>
                  <td style={{ whiteSpace: "nowrap" }}>{strategy.annualisedReturn ?? "—"}</td>
                  <td style={{ whiteSpace: "nowrap" }}>{strategy.sharpeRatio ?? "—"}</td>
                  <td>{formatTokenList(strategy.region)}</td>
                  <td>{formatTokenList(strategy.market)}</td>
                  <td>{formatTokenList(strategy.assetClass)}</td>
                  <td style={{ whiteSpace: "nowrap" }}>{strategy.frequency ?? "—"}</td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <span className={strategy.isPaywalled ? "qb-badge-paid" : "qb-badge-free"}>
                      {strategy.isPaywalled ? labels.planPaid : labels.planFree}
                    </span>
                  </td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <LibraryCollectButton
                      strategyId={strategy.id}
                      locale={locale}
                      initialCollected={collectedSet.has(strategy.id)}
                      isLoggedIn={isLoggedIn}
                    />
                  </td>
                  <td style={{ whiteSpace: "nowrap" }}>
                    <Link className="qb-accent-link" href={strategyHref(locale, strategy.slug)}>
                      {labels.open}
                    </Link>
                  </td>
                </tr>
              ))
            }
          </tbody>
        </table>
      </div>

      <div className="qb-pagination">
        <button
          type="button"
          className="qb-secondary"
          disabled={page <= 1 || pending}
          onClick={() =>
            pushParams({
              page: page - 1,
              q: initialQuery,
              market: initialMarket,
              region: initialRegion,
              assetClass: initialAssetClass,
              plan: initialPlan,
              collection: initialCollection,
            })
          }
        >
          {labels.prev}
        </button>
        <span style={{ fontFamily: "var(--font-qb-mono, monospace)", fontSize: "0.875rem", color: "#8caacf" }}>
          {page} / {totalPages}
        </span>
        <button
          type="button"
          className="qb-secondary"
          disabled={page >= totalPages || pending}
          onClick={() =>
            pushParams({
              page: page + 1,
              q: initialQuery,
              market: initialMarket,
              region: initialRegion,
              assetClass: initialAssetClass,
              plan: initialPlan,
              collection: initialCollection,
            })
          }
        >
          {labels.next}
        </button>
      </div>
    </div>
  );
}
