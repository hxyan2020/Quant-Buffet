"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";

import PlatformCodeExport from "@/components/PlatformCodeExport";
import {
  DrawdownChart,
  EquityLineChart,
  MetricsBarChart,
  MonthlyReturnBars,
  type CurvePoint,
} from "@/components/lab/LabCharts";
import {
  heuristicLabAdvice,
  LAB_CONTRACT_SNIPPETS,
  type LabAdvice,
  type LabSnippet,
} from "@/lib/lab-debug";

type DisplayMetrics = {
  annualisedReturn?: string | null;
  volatility?: string | null;
  sharpeRatio?: string | null;
  sortinoRatio?: string | null;
  maxDrawdown?: string | null;
  beta?: string | null;
  alpha?: string | null;
  winRate?: string | null;
};

type TradeFill = {
  date: string;
  symbol: string;
  side: string;
  shares: number;
  price: number;
  value: number;
  commission: number;
};

type RunError = {
  type?: string;
  message: string;
  line?: number | null;
  traceback?: string;
};

type Props = {
  locale: string;
  slug: string;
  title: string;
  initialCode: string;
  baselineMetrics: DisplayMetrics;
  baselineEquity?: CurvePoint[];
  baselineBenchmark?: CurvePoint[];
};

const METRIC_KEYS: { key: keyof DisplayMetrics; label: string }[] = [
  { key: "annualisedReturn", label: "CAGR" },
  { key: "sharpeRatio", label: "Sharpe" },
  { key: "maxDrawdown", label: "Max DD" },
  { key: "volatility", label: "Vol" },
  { key: "sortinoRatio", label: "Sortino" },
  { key: "beta", label: "Beta" },
  { key: "alpha", label: "Alpha" },
  { key: "winRate", label: "Up days" },
];

function SnippetCard({
  snippet,
  copied,
  onCopy,
  onInsert,
}: {
  snippet: LabSnippet;
  copied: boolean;
  onCopy: () => void;
  onInsert: () => void;
}) {
  return (
    <div className="qb-lab-snippet">
      <div className="qb-lab-snippet-head">
        <div>
          <strong>{snippet.title}</strong>
          {snippet.hint ? <div className="qb-lab-snippet-hint">{snippet.hint}</div> : null}
        </div>
        <div className="qb-lab-snippet-actions">
          <button type="button" className="qb-lab-btn qb-lab-btn-sm" onClick={onCopy}>
            {copied ? "Copied" : "Copy"}
          </button>
          <button type="button" className="qb-lab-btn qb-lab-btn-sm" onClick={onInsert}>
            Insert into editor
          </button>
        </div>
      </div>
      <pre className="qb-lab-snippet-code">
        <code>{snippet.code}</code>
      </pre>
    </div>
  );
}

function IdeEditor({
  code,
  errorLine,
  onChange,
  editorRef,
}: {
  code: string;
  errorLine?: number | null;
  onChange: (next: string) => void;
  editorRef: React.RefObject<HTMLTextAreaElement | null>;
}) {
  const gutterRef = useRef<HTMLDivElement | null>(null);
  const lines = useMemo(() => code.split("\n"), [code]);

  function syncScroll() {
    const el = editorRef.current;
    if (el && gutterRef.current) gutterRef.current.scrollTop = el.scrollTop;
  }

  return (
    <div className="qb-lab-ide">
      <div className="qb-lab-ide-gutter" ref={gutterRef} aria-hidden>
        {lines.map((_, i) => {
          const n = i + 1;
          const isErr = errorLine != null && n === errorLine;
          return (
            <div key={n} className={`qb-lab-ide-lineno${isErr ? " is-error" : ""}`}>
              {n}
            </div>
          );
        })}
      </div>
      <textarea
        ref={editorRef}
        className="qb-lab-editor qb-lab-ide-textarea"
        spellCheck={false}
        value={code}
        onChange={(e) => onChange(e.target.value)}
        onScroll={syncScroll}
        aria-label="Strategy Python IDE"
      />
    </div>
  );
}

export default function StrategyBacktestLab({
  locale,
  slug,
  title,
  initialCode,
  baselineMetrics,
  baselineEquity = [],
  baselineBenchmark = [],
}: Props) {
  const editorRef = useRef<HTMLTextAreaElement | null>(null);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const [code, setCode] = useState(initialCode);
  const [busy, setBusy] = useState(false);
  const [aiBusy, setAiBusy] = useState(false);
  const [status, setStatus] = useState<string>("Ready — edit code, then Run backtest.");
  const [error, setError] = useState<RunError | null>(null);
  const [advice, setAdvice] = useState<LabAdvice | null>(null);
  const [copiedKey, setCopiedKey] = useState<string>("");
  const [metrics, setMetrics] = useState<DisplayMetrics>(baselineMetrics);
  const [equity, setEquity] = useState<CurvePoint[]>(baselineEquity);
  const [benchmark, setBenchmark] = useState<CurvePoint[]>(baselineBenchmark);
  const [meta, setMeta] = useState<{
    start?: string;
    end?: string;
    trades?: number;
    assets?: string[];
    tradesNote?: string | null;
  }>({});
  const [fills, setFills] = useState<TradeFill[]>([]);
  const [runToken, setRunToken] = useState(0);

  const lineCount = useMemo(() => code.split("\n").length, [code]);

  useEffect(() => {
    if (runToken > 0 && resultsRef.current) {
      resultsRef.current.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [runToken]);

  async function copyText(key: string, text: string) {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey((cur) => (cur === key ? "" : cur)), 1600);
    } catch {
      setStatus("Could not copy — select the snippet and copy manually.");
    }
  }

  function insertSnippet(snippet: string) {
    const el = editorRef.current;
    const block = snippet.endsWith("\n") ? snippet : `${snippet}\n`;
    if (!el) {
      setCode((c) => `${c.replace(/\s+$/, "")}\n\n${block}`);
      setStatus("Inserted snippet at the end of the editor.");
      return;
    }
    const start = el.selectionStart ?? code.length;
    const end = el.selectionEnd ?? start;
    const next = code.slice(0, start) + block + code.slice(end);
    setCode(next);
    setStatus("Inserted snippet at the cursor — edit if needed, then Run backtest.");
    requestAnimationFrame(() => {
      el.focus();
      const pos = start + block.length;
      el.setSelectionRange(pos, pos);
    });
  }

  async function askAiFix(err: RunError | null, source: string) {
    setAiBusy(true);
    setStatus(err ? "AI debugger reading the error…" : "Asking AI for Quant Buffet syntax…");
    try {
      const res = await fetch("/api/draft-preview/fix-code", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug, locale, code: source, error: err || undefined }),
      });
      const data = await res.json();
      if (!res.ok) {
        setAdvice(
          heuristicLabAdvice(err || { message: "AI helper unavailable." }, source),
        );
        setStatus("AI helper unavailable; showing copy-paste syntax tips.");
        return;
      }
      setAdvice({
        where: data.where,
        why: data.why,
        steps: data.steps || data.fixes || [],
        snippets: Array.isArray(data.snippets) ? data.snippets : [],
        fixedCode: data.fixedCode,
        provider: data.provider,
      });
      setStatus(
        data.provider === "heuristic"
          ? "Debugger ready (rule-based tips + copy-paste syntax)."
          : `AI debugger ready (${data.provider || "model"}). Copy a snippet or apply the full fix.`,
      );
    } catch {
      setAdvice(
        heuristicLabAdvice(err || { message: "Network error talking to AI." }, source),
      );
      setStatus("AI request failed; showing copy-paste syntax tips.");
    } finally {
      setAiBusy(false);
    }
  }

  async function runBacktest() {
    setBusy(true);
    setError(null);
    setAdvice(null);
    setStatus("Running Quant Buffet sandbox…");
    try {
      const res = await fetch("/api/draft-preview/backtest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ slug, code, start: "2000-01-01" }),
      });
      const data = await res.json();
      if (!res.ok) {
        const err: RunError = { message: data.error || `HTTP ${res.status}` };
        setError(err);
        setAdvice(heuristicLabAdvice(err, code));
        setStatus("Backtest request failed.");
        void askAiFix(err, code);
        return;
      }
      if (!data.ok) {
        const err = (data.error || { message: "Unknown error" }) as RunError;
        setError(err);
        setAdvice(heuristicLabAdvice(err, code));
        setStatus(
          err.line
            ? `Error at line ${err.line}: ${err.type || "Error"} — AI debugger started.`
            : `Error: ${err.type || "Error"} — AI debugger started.`,
        );
        void askAiFix(err, code);
        return;
      }
      setMetrics(data.displayMetrics || {});
      setEquity(data.equity || []);
      setBenchmark(data.benchmark || []);
      setMeta({
        start: data.start,
        end: data.end,
        trades: data.trades,
        assets: data.assets,
        tradesNote: data.trades_sample_note || null,
      });
      setFills(Array.isArray(data.trades_sample) ? data.trades_sample : []);
      setRunToken((t) => t + 1);
      setStatus(
        `OK · ${data.start} → ${data.end} · ${data.trades} trades · ${(data.assets || []).join(", ")}`,
      );
    } catch (e) {
      const err: RunError = { message: e instanceof Error ? e.message : "Network error" };
      setError(err);
      setAdvice(heuristicLabAdvice(err, code));
      setStatus("Backtest failed to reach the server.");
      void askAiFix(err, code);
    } finally {
      setBusy(false);
    }
  }

  function applyFixedCode() {
    if (advice?.fixedCode?.trim()) {
      setCode(advice.fixedCode.trim() + "\n");
      setStatus("Applied suggested code — run the backtest again.");
      setError(null);
    }
  }

  function resetCode() {
    setCode(initialCode);
    setMetrics(baselineMetrics);
    setEquity(baselineEquity);
    setBenchmark(baselineBenchmark);
    setError(null);
    setAdvice(null);
    setMeta({});
    setFills([]);
    setStatus("Reset to original draft code / baseline results.");
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      if (!busy) void runBacktest();
    }
  }

  return (
    <section className="qb-lab" id="backtest-lab" onKeyDown={onKeyDown}>
      <div className="qb-lab-header">
        <div className="qb-lab-header-row">
          <h2 className="qb-strategy-section-title">Onsite backtest IDE</h2>
          <span className="qb-lab-ide-badge">Temp lab · all strategies</span>
        </div>
        <p className="qb-lab-sub">
          Edit and run Quant Buffet Python for <strong>{title}</strong> in the browser. Results
          update live with equity, drawdown, and metrics charts. Allowed:{" "}
          <code>backtest.data</code>, <code>backtest.engine</code>, <code>backtest.metrics</code>,{" "}
          <code>numpy</code>, <code>pandas</code>. Define <code>ASSETS</code> and{" "}
          <code>make_on_day(prices)</code>. Shortcut: <kbd>Ctrl</kbd>+<kbd>Enter</kbd>.{" "}
          <Link href={`/${locale}/docs`} className="qb-lab-docs-link">
            API docs →
          </Link>
        </p>
      </div>

      <div className="qb-lab-toolbar">
        <button type="button" className="qb-pill-primary" disabled={busy} onClick={() => void runBacktest()}>
          {busy ? "Running…" : "Run backtest"}
        </button>
        <button type="button" className="qb-lab-btn" disabled={busy} onClick={resetCode}>
          Reset code
        </button>
        <button
          type="button"
          className="qb-lab-btn"
          disabled={aiBusy || busy}
          onClick={() => void askAiFix(error, code)}
        >
          {aiBusy ? "AI thinking…" : error ? "Ask AI again" : "Ask AI for syntax"}
        </button>
        <span className="qb-lab-status">{status}</span>
      </div>

      <div className="qb-lab-grid">
        <div className="qb-lab-editor-wrap">
          <div className="qb-lab-editor-meta">
            IDE · {lineCount} lines
            {error?.line ? (
              <span className="qb-lab-err-line"> · error near line {error.line}</span>
            ) : null}
          </div>
          <IdeEditor
            code={code}
            errorLine={error?.line}
            onChange={setCode}
            editorRef={editorRef}
          />
          <details className="qb-lab-cheatsheet">
            <summary>Quant Buffet syntax cheat sheet (copy / insert)</summary>
            <p className="qb-lab-snippet-hint">
              Paste these fragments into the editor. The sandbox rejects QuantConnect, os, and
              network libraries.
            </p>
            {LAB_CONTRACT_SNIPPETS.map((s, i) => (
              <SnippetCard
                key={`cheat-${i}`}
                snippet={s}
                copied={copiedKey === `cheat-${i}`}
                onCopy={() => void copyText(`cheat-${i}`, s.code)}
                onInsert={() => insertSnippet(s.code)}
              />
            ))}
          </details>
        </div>

        <div className="qb-lab-results" ref={resultsRef}>
          <h3 className="qb-lab-h3">Live backtest performance</h3>
          <div className="qb-lab-metrics">
            {METRIC_KEYS.map(({ key, label }) => {
              const v = metrics[key];
              if (!v || /^n\/a$/i.test(v)) return null;
              return (
                <div key={key} className="qb-lab-metric">
                  <div className="qb-lab-metric-label">{label}</div>
                  <div className="qb-lab-metric-value">{v}</div>
                  {baselineMetrics[key] && baselineMetrics[key] !== v ? (
                    <div className="qb-lab-metric-base">baseline {baselineMetrics[key]}</div>
                  ) : null}
                </div>
              );
            })}
          </div>

          {meta.start ? (
            <p className="qb-lab-meta">
              Window {meta.start} → {meta.end}
              {meta.trades != null ? ` · ${meta.trades} fills` : ""}
              {meta.assets?.length ? ` · ${meta.assets.join(", ")}` : ""}
            </p>
          ) : equity.length ? (
            <p className="qb-lab-meta">Showing saved draft baseline until you re-run.</p>
          ) : (
            <p className="qb-lab-meta">Run the backtest to populate charts.</p>
          )}

          {equity.length ? (
            <div className="qb-lab-viz-stack">
              <div className="qb-lab-viz">
                <div className="qb-lab-viz-title">Equity curve (indexed = 100)</div>
                <p className="qb-lab-chart-cap">
                  Accent = strategy · dashed grey = buy-and-hold benchmark
                </p>
                <EquityLineChart equity={equity} benchmark={benchmark} />
              </div>
              <div className="qb-lab-viz">
                <div className="qb-lab-viz-title">Drawdown</div>
                <DrawdownChart equity={equity} />
              </div>
              <div className="qb-lab-viz">
                <div className="qb-lab-viz-title">Metrics bar chart</div>
                <MetricsBarChart
                  metrics={metrics as Record<string, string | null | undefined>}
                  baseline={baselineMetrics as Record<string, string | null | undefined>}
                />
              </div>
              <div className="qb-lab-viz">
                <div className="qb-lab-viz-title">Monthly returns</div>
                <MonthlyReturnBars equity={equity} />
              </div>
            </div>
          ) : null}

          {fills.length ? (
            <div className="qb-lab-fills">
              <h3 className="qb-lab-h3">Trade fills</h3>
              <p className="qb-lab-meta">
                {meta.tradesNote || `Showing ${fills.length} sample fills`}
              </p>
              <div className="qb-lab-fills-wrap">
                <table className="qb-lab-fills-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Symbol</th>
                      <th>Side</th>
                      <th>Shares</th>
                      <th>Price</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fills.map((t, i) => (
                      <tr key={`${t.date}-${t.symbol}-${i}`}>
                        <td>{t.date}</td>
                        <td>{t.symbol}</td>
                        <td className={t.side === "buy" ? "qb-lab-side-buy" : "qb-lab-side-sell"}>
                          {t.side}
                        </td>
                        <td>{t.shares}</td>
                        <td>{t.price}</td>
                        <td>{t.value}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : null}

          {error ? (
            <div className="qb-lab-error" role="alert">
              <strong>
                {error.type || "Error"}
                {error.line ? ` · line ${error.line}` : ""}
              </strong>
              <p>{error.message}</p>
              {error.traceback ? (
                <pre className="qb-lab-traceback">{error.traceback}</pre>
              ) : null}
            </div>
          ) : null}

          {advice ? (
            <div className="qb-lab-advice">
              <h3 className="qb-lab-h3">
                Debugger
                {advice.provider ? (
                  <span className="qb-lab-advice-provider"> · {advice.provider}</span>
                ) : null}
                {aiBusy ? <span className="qb-lab-advice-provider"> · updating…</span> : null}
              </h3>
              {advice.where ? <p>{advice.where}</p> : null}
              {advice.why ? <p>{advice.why}</p> : null}
              {advice.steps?.length ? (
                <ol className="qb-lab-steps">
                  {advice.steps.map((step) => (
                    <li key={step.slice(0, 48)}>{step}</li>
                  ))}
                </ol>
              ) : null}
              {advice.snippets?.map((s, i) => (
                <SnippetCard
                  key={`adv-${i}`}
                  snippet={s}
                  copied={copiedKey === `adv-${i}`}
                  onCopy={() => void copyText(`adv-${i}`, s.code)}
                  onInsert={() => insertSnippet(s.code)}
                />
              ))}
              {advice.fixedCode?.trim() ? (
                <div className="qb-lab-snippet-actions qb-lab-fullfix">
                  <button type="button" className="qb-lab-btn" onClick={applyFixedCode}>
                    Replace editor with full suggested file
                  </button>
                  <button
                    type="button"
                    className="qb-lab-btn"
                    onClick={() => void copyText("full", advice.fixedCode || "")}
                  >
                    {copiedKey === "full" ? "Copied full file" : "Copy full suggested file"}
                  </button>
                </div>
              ) : null}
            </div>
          ) : aiBusy ? (
            <p className="qb-lab-meta">AI debugger is writing fix steps…</p>
          ) : null}
        </div>
      </div>

      <PlatformCodeExport
        locale={locale}
        title={title}
        liveCode={code}
        labPythonSource={initialCode}
      />
    </section>
  );
}
