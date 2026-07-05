"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import PythonCodePreview from "@/components/PythonCodePreview";
import { naOr } from "@/lib/sanitize-text";

import {
  backtestMetricsToJson,
  parseBacktestMetricsJson,
} from "@/lib/parse-strategy-content";

type LocaleOption = "en" | "zh";

type SerializedStrategy = {
  id: string;
  slug: string;
  locale: string;
  title: string;
  teaser?: string | null;
  summary?: string | null;
  contentHtml: string;
  annualisedReturn?: string | null;
  sharpeRatio?: string | null;
  volatility?: string | null;
  beta?: string | null;
  sortinoRatio?: string | null;
  maxDrawdown?: string | null;
  winRate?: string | null;
  backtestMetrics?: string | null;
  region?: string | null;
  market?: string | null;
  assetClass?: string | null;
  frequency?: string | null;
  paperTitle?: string | null;
  paperAuthors?: string | null;
  paperInstitute?: string | null;
  academicLink?: string | null;
  economicRationale?: string | null;
  pythonCodeHtml?: string | null;
  metaTitle?: string | null;
  metaDescription?: string | null;
  sortOrder?: number | null;
  published: boolean;
  isPaywalled: boolean;
};

export type ManageStrategyProps = {
  basePath: string;
  mode: "create" | "edit";
  strategyId?: string;
  strategyTitle?: string;
};

type FormShape = ReturnType<typeof buildFormState>;

function metricsFromSeed(seed?: SerializedStrategy) {
  const parsed = parseBacktestMetricsJson(seed?.backtestMetrics ?? "{}");
  return {
    annualisedReturn: parsed.annualisedReturn ?? seed?.annualisedReturn ?? "",
    volatility: parsed.volatility ?? seed?.volatility ?? "",
    beta: parsed.beta ?? seed?.beta ?? "",
    sharpeRatio: parsed.sharpeRatio ?? seed?.sharpeRatio ?? "",
    sortinoRatio: parsed.sortinoRatio ?? seed?.sortinoRatio ?? "",
    maxDrawdown: parsed.maxDrawdown ?? seed?.maxDrawdown ?? "",
    winRate: parsed.winRate ?? seed?.winRate ?? "",
  };
}

function buildFormState(seed?: SerializedStrategy) {
  const metrics = metricsFromSeed(seed);
  if (!seed) {
    return {
      slug: "",
      locale: "en" as LocaleOption,
      title: "",
      teaser: "",
      summary: "",
      contentHtml: "",
      economicRationale: "",
      pythonCodeHtml: "",
      ...metrics,
      region: "",
      market: "",
      assetClass: "",
      frequency: "",
      paperTitle: "",
      paperAuthors: "",
      paperInstitute: "N/A",
      academicLink: "",
      metaTitle: "",
      metaDescription: "",
      sortOrder: "0",
      published: true,
      isPaywalled: true,
    };
  }

  return {
    slug: seed.slug,
    locale: (seed.locale === "zh" ? "zh" : "en") as LocaleOption,
    title: seed.title,
    teaser: naOr(seed.teaser),
    summary: naOr(seed.summary),
    contentHtml: seed.contentHtml,
    economicRationale: naOr(seed.economicRationale),
    pythonCodeHtml: seed.pythonCodeHtml ?? "",
    ...metrics,
    region: seed.region ?? "",
    market: seed.market ?? "",
    assetClass: seed.assetClass ?? "",
    frequency: seed.frequency ?? "",
    paperTitle: naOr(seed.paperTitle),
    paperAuthors: naOr(seed.paperAuthors),
    paperInstitute: naOr(seed.paperInstitute),
    academicLink: seed.academicLink ?? "",
    metaTitle: seed.metaTitle ?? "",
    metaDescription: seed.metaDescription ?? "",
    sortOrder: String(seed.sortOrder ?? 0),
    published: seed.published,
    isPaywalled: seed.isPaywalled,
  };
}

function nullable(text: string) {
  const trimmed = text.trim();
  return trimmed.length === 0 || trimmed.toUpperCase() === "N/A" ? null : trimmed;
}

function fieldOrNa(text: string) {
  const t = text.trim();
  return t.length === 0 ? "N/A" : t;
}

export default function ManageStrategyPanel({
  basePath,
  mode,
  strategyId,
  strategyTitle,
}: ManageStrategyProps) {
  const router = useRouter();
  const [strategy, setStrategy] = useState<SerializedStrategy | null>(null);
  const [form, setForm] = useState<FormShape>(() => buildFormState());
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(mode === "edit");

  useEffect(() => {
    if (mode !== "edit" || !strategyId) return;

    let cancelled = false;
    setLoading(true);
    setStatus(null);

    void (async () => {
      try {
        const res = await fetch(`/api/admin/strategies/${strategyId}`);
        const json = await res.json();
        if (!res.ok) throw new Error(json?.error ?? "load_failed");
        if (cancelled) return;
        const row = json.strategy as SerializedStrategy;
        setStrategy(row);
        setForm(buildFormState(row));
      } catch (error) {
        console.error("[ManageStrategy.load]", error);
        if (!cancelled) setStatus("Failed to load strategy — try refreshing.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [mode, strategyId]);

  const headline =
    mode === "create" ? "New strategy" : `Edit • ${strategy?.title ?? strategyTitle ?? "…"}`;

  async function saveStrategy() {
    setBusy(true);
    setStatus(null);
    try {
      const backtestMetrics = backtestMetricsToJson({
        annualisedReturn: form.annualisedReturn || undefined,
        volatility: form.volatility || undefined,
        beta: form.beta || undefined,
        sharpeRatio: form.sharpeRatio || undefined,
        sortinoRatio: form.sortinoRatio || undefined,
        maxDrawdown: form.maxDrawdown || undefined,
        winRate: form.winRate || undefined,
      });

      const payload = {
        slug: form.slug.trim(),
        title: form.title.trim(),
        teaser: fieldOrNa(form.teaser),
        summary: fieldOrNa(form.summary),
        contentHtml: form.contentHtml,
        backtestMetrics,
        annualisedReturn: nullable(form.annualisedReturn ?? ""),
        sharpeRatio: nullable(form.sharpeRatio ?? ""),
        volatility: nullable(form.volatility ?? ""),
        beta: nullable(form.beta ?? ""),
        sortinoRatio: nullable(form.sortinoRatio ?? ""),
        maxDrawdown: nullable(form.maxDrawdown ?? ""),
        winRate: nullable(form.winRate ?? ""),
        region: nullable(form.region ?? ""),
        market: nullable(form.market ?? ""),
        assetClass: nullable(form.assetClass ?? ""),
        frequency: nullable(form.frequency ?? ""),
        paperTitle: fieldOrNa(form.paperTitle),
        paperAuthors: fieldOrNa(form.paperAuthors),
        paperInstitute: fieldOrNa(form.paperInstitute),
        academicLink: nullable(form.academicLink ?? ""),
        economicRationale: fieldOrNa(form.economicRationale),
        pythonCodeHtml: form.pythonCodeHtml,
        metaTitle: nullable(form.metaTitle ?? ""),
        metaDescription: nullable(form.metaDescription ?? ""),
        sortOrder: Number(form.sortOrder) || 0,
        published: form.published,
        isPaywalled: form.isPaywalled,
      };

      if (mode === "create") {
        const response = await fetch("/api/admin/strategies", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...payload, locale: form.locale }),
        });
        const json = await response.json();
        if (!response.ok) throw new Error(json?.error ?? "create_failed");
        const id = typeof json.strategy?.id === "string" ? json.strategy.id : null;
        if (id) router.replace(`${basePath}/strategies/${id}`);
        router.refresh();
        setStatus("Created ✅");
      } else if (strategy) {
        const response = await fetch(`/api/admin/strategies/${strategy.id}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const json = await response.json().catch(() => null);
        if (!response.ok) throw new Error(json?.error ?? "update_failed");
        router.refresh();
        setStatus("Saved ✅");
      }
    } catch (error) {
      console.error("[ManageStrategy]", error);
      setStatus("Save failed — inspect console/logs.");
    } finally {
      setBusy(false);
    }
  }

  async function destroyStrategy() {
    if (!strategy) return;
    if (!confirm("Remove this strategy permanently?")) return;
    const response = await fetch(`/api/admin/strategies/${strategy.id}`, { method: "DELETE" });
    if (response.ok) {
      router.replace(`${basePath}/strategies`);
      router.refresh();
    } else {
      setStatus("Delete blocked.");
    }
  }

  if (loading) {
    return (
      <div className="qb-admin-loading-panel">
        <p className="qb-admin-muted">Loading strategy…</p>
        <Link className="qb-admin-link" href={`${basePath}/strategies`}>
          ← Strategies
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-8 rounded-[32px] border border-white/10 bg-[#080c14]/95 p-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.45em] text-[#5ddcff]">
            {mode === "create" ? form.locale.toUpperCase() : strategy?.locale ?? ""}
          </p>
          <h1 className="text-3xl font-semibold text-white">{headline}</h1>
        </div>
        <Link className="text-sm text-[#55e0ff]" href={`${basePath}/strategies`}>
          ← Strategies
        </Link>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <LabeledInput label="Slug" value={form.slug} disabled={busy} monospace onChange={(slug) => setForm({ ...form, slug })} />
        <label className="space-y-2 text-[11px] uppercase tracking-[0.35em] text-white">
          Locale
          <select
            className="qb-input bg-black text-sm font-mono"
            value={form.locale}
            disabled={busy || mode === "edit"}
            onChange={(evt) => setForm({ ...form, locale: evt.target.value as LocaleOption })}
          >
            <option value="en">English</option>
            <option value="zh">中文</option>
          </select>
        </label>
      </div>

      <AdminSection title="Title & content">
        <LabeledInput label="Title" value={form.title} disabled={busy} onChange={(title) => setForm({ ...form, title })} />
        <LabeledTextArea label="Teaser" value={form.teaser} rows={4} disabled={busy} onChange={(teaser) => setForm({ ...form, teaser })} />
        <LabeledTextArea label="Summary (strategy in a nutshell)" value={form.summary} rows={8} disabled={busy} onChange={(summary) => setForm({ ...form, summary })} />
        <LabeledTextArea label="Economic rationale" value={form.economicRationale} rows={8} disabled={busy} onChange={(economicRationale) => setForm({ ...form, economicRationale })} />
      </AdminSection>

      <AdminSection title="Backtest performance">
        <div className="grid gap-6 md:grid-cols-2">
          <LabeledInput label="Annualised return" value={form.annualisedReturn} disabled={busy} onChange={(annualisedReturn) => setForm({ ...form, annualisedReturn })} />
          <LabeledInput label="Volatility" value={form.volatility} disabled={busy} onChange={(volatility) => setForm({ ...form, volatility })} />
          <LabeledInput label="Beta" value={form.beta} disabled={busy} onChange={(beta) => setForm({ ...form, beta })} />
          <LabeledInput label="Sharpe ratio" value={form.sharpeRatio} disabled={busy} onChange={(sharpeRatio) => setForm({ ...form, sharpeRatio })} />
          <LabeledInput label="Sortino ratio" value={form.sortinoRatio} disabled={busy} onChange={(sortinoRatio) => setForm({ ...form, sortinoRatio })} />
          <LabeledInput label="Maximum drawdown" value={form.maxDrawdown} disabled={busy} onChange={(maxDrawdown) => setForm({ ...form, maxDrawdown })} />
          <LabeledInput label="Win rate" value={form.winRate} disabled={busy} onChange={(winRate) => setForm({ ...form, winRate })} />
        </div>
      </AdminSection>

      <AdminSection title="Classification">
      <div className="grid gap-6 md:grid-cols-2">
        <LabeledInput label="Region" value={form.region} disabled={busy} onChange={(region) => setForm({ ...form, region })} />
        <LabeledInput label="Market" value={form.market} disabled={busy} onChange={(market) => setForm({ ...form, market })} />
        <LabeledInput label="Asset class" value={form.assetClass} disabled={busy} onChange={(assetClass) => setForm({ ...form, assetClass })} />
        <LabeledInput label="Frequency" value={form.frequency} disabled={busy} onChange={(frequency) => setForm({ ...form, frequency })} />
        <LabeledInput label="Sort order" value={form.sortOrder} disabled={busy} monospace onChange={(sortOrder) => setForm({ ...form, sortOrder })} />
      </div>
      </AdminSection>

      <AdminSection title="Source paper">
      <div className="grid gap-6 md:grid-cols-2">
        <LabeledInput label="Paper title" value={form.paperTitle} disabled={busy} onChange={(paperTitle) => setForm({ ...form, paperTitle })} />
        <LabeledInput label="Paper authors" value={form.paperAuthors} disabled={busy} onChange={(paperAuthors) => setForm({ ...form, paperAuthors })} />
        <div className="md:col-span-2">
          <LabeledInput label="Institute / affiliation" value={form.paperInstitute} disabled={busy} onChange={(paperInstitute) => setForm({ ...form, paperInstitute })} />
        </div>
        <div className="md:col-span-2">
          <LabeledInput label="Paper link" value={form.academicLink} disabled={busy} monospace onChange={(academicLink) => setForm({ ...form, academicLink })} />
        </div>
      </div>
      </AdminSection>

      <AdminSection title="Python code">
        <LabeledTextArea label="Source" monospace value={form.pythonCodeHtml} rows={12} disabled={busy} onChange={(pythonCodeHtml) => setForm({ ...form, pythonCodeHtml })} />
        {form.pythonCodeHtml.trim() ?
          <PythonCodePreview codeHtml={form.pythonCodeHtml} />
        : <p className="qb-na">N/A</p>}
      </AdminSection>

      <AdminSection title="Additional HTML (admin only)" tone="amber">
        <LabeledTextArea label="Markup" monospace value={form.contentHtml} rows={6} disabled={busy} onChange={(contentHtml) => setForm({ ...form, contentHtml })} />
      </AdminSection>

      <AdminSection title="SEO">
        <LabeledInput label="SEO title" value={form.metaTitle} disabled={busy} onChange={(metaTitle) => setForm({ ...form, metaTitle })} />
        <LabeledTextArea label="SEO meta description" value={form.metaDescription} rows={3} disabled={busy} onChange={(metaDescription) => setForm({ ...form, metaDescription })} />
      </AdminSection>

      <div className="flex flex-wrap gap-6 text-sm">
        <label className="flex items-center gap-2 text-[#dbe7fb]">
          <input type="checkbox" checked={form.published} disabled={busy} onChange={(evt) => setForm({ ...form, published: evt.target.checked })} />
          Published / visible on site
        </label>
        <label className="flex items-center gap-2 text-[#dbe7fb]">
          <input type="checkbox" checked={form.isPaywalled} disabled={busy} onChange={(evt) => setForm({ ...form, isPaywalled: evt.target.checked })} />
          Paywall enabled for non-subscribers
        </label>
      </div>

      <div className="flex flex-wrap gap-4">
        <button type="button" disabled={busy} className="qb-pill-primary" onClick={() => void saveStrategy()}>
          {mode === "create" ? "Create strategy" : "Save changes"}
        </button>
        {mode === "edit" ?
          <button type="button" disabled={busy} className="qb-secondary px-8 text-[13px] text-red-200" onClick={() => destroyStrategy()}>
            Delete permanently
          </button>
        : null}
      </div>

      {status ? <p className="text-[13px] text-yellow-200">{status}</p> : null}
    </div>
  );
}

function AdminSection({
  title,
  children,
  tone = "accent",
}: {
  title: string;
  children: React.ReactNode;
  tone?: "accent" | "amber";
}) {
  const color = tone === "amber" ? "text-amber-200" : "text-[var(--qb-accent)]";
  const border = tone === "amber" ? "border-amber-500/30 bg-[#12100a]/40" : "border-[#55e0ff]/25 bg-[#0a1218]/50";
  return (
    <div className={`space-y-4 rounded-2xl border p-6 ${border}`}>
      <p className={`text-[11px] font-bold uppercase tracking-[0.35em] ${color}`}>{title}</p>
      {children}
    </div>
  );
}

function LabeledInput(props: {
  label: string;
  value: string;
  disabled: boolean;
  monospace?: boolean;
  onChange(value: string): void;
}) {
  return (
    <label className="space-y-2 text-[11px] uppercase tracking-[0.35em] text-white">
      {props.label}
      <input
        value={props.value}
        disabled={props.disabled}
        onChange={(evt) => props.onChange(evt.target.value)}
        className={`qb-input text-sm text-white ${props.monospace ? "font-mono" : ""}`}
      />
    </label>
  );
}

function LabeledTextArea(props: {
  label: string;
  value: string;
  rows: number;
  disabled: boolean;
  monospace?: boolean;
  onChange(value: string): void;
}) {
  return (
    <label className="space-y-2 text-[11px] uppercase tracking-[0.35em] text-white">
      {props.label}
      <textarea
        value={props.value}
        rows={props.rows}
        disabled={props.disabled}
        onChange={(evt) => props.onChange(evt.target.value)}
        className={`qb-input text-sm leading-relaxed text-white ${props.monospace ? "font-mono" : ""}`}
      />
    </label>
  );
}
