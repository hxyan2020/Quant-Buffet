"use client";

/** Shared chart helpers for the Quant Buffet onsite backtest IDE. */

export type CurvePoint = { date: string; equity: number };

export function toIndexed(series: CurvePoint[]): { date: string; v: number }[] {
  if (!series.length) return [];
  const e0 = series[0].equity || 1;
  return series.map((p) => ({ date: p.date, v: (p.equity / e0) * 100 }));
}

export function drawdownSeries(equity: CurvePoint[]): { date: string; dd: number }[] {
  let peak = -Infinity;
  return equity.map((p) => {
    peak = Math.max(peak, p.equity);
    const dd = peak > 0 ? (p.equity / peak - 1) * 100 : 0;
    return { date: p.date, dd };
  });
}

/** Approx calendar-month returns from downsampled equity curve. */
export function monthlyReturns(equity: CurvePoint[]): { label: string; ret: number }[] {
  if (equity.length < 2) return [];
  const byMonth = new Map<string, { first: number; last: number }>();
  for (const p of equity) {
    const key = p.date.slice(0, 7);
    const cur = byMonth.get(key);
    if (!cur) byMonth.set(key, { first: p.equity, last: p.equity });
    else cur.last = p.equity;
  }
  const keys = [...byMonth.keys()].sort();
  // Sample last ~24 months for readability
  const slice = keys.slice(-24);
  return slice.map((k) => {
    const { first, last } = byMonth.get(k)!;
    return { label: k, ret: first > 0 ? (last / first - 1) * 100 : 0 };
  });
}

export function parseMetricPct(raw: string | null | undefined): number | null {
  if (!raw || /^n\/a$/i.test(raw)) return null;
  const m = raw.replace(/,/g, "").match(/-?\d+(?:\.\d+)?/);
  if (!m) return null;
  const n = Number(m[0]);
  if (raw.includes("%")) return n;
  // Sharpe / beta often unitless
  return n;
}

type Pad = { t: number; r: number; b: number; l: number };

export function EquityLineChart({
  equity,
  benchmark,
  height = 240,
}: {
  equity: CurvePoint[];
  benchmark?: CurvePoint[];
  height?: number;
}) {
  if (!equity.length) return null;
  const width = 720;
  const pad: Pad = { t: 16, r: 16, b: 32, l: 48 };
  const series = toIndexed(equity);
  const bench = toIndexed(benchmark || []);
  const allVals = [...series.map((s) => s.v), ...bench.map((s) => s.v)];
  const minV = Math.min(...allVals) * 0.98;
  const maxV = Math.max(...allVals) * 1.02;
  const x = (i: number, n: number) =>
    pad.l + (i / Math.max(n - 1, 1)) * (width - pad.l - pad.r);
  const y = (v: number) =>
    pad.t + ((maxV - v) / Math.max(maxV - minV, 1e-9)) * (height - pad.t - pad.b);
  const path = (pts: { v: number }[]) =>
    pts
      .map((p, i) => `${i === 0 ? "M" : "L"}${x(i, pts.length).toFixed(1)},${y(p.v).toFixed(1)}`)
      .join(" ");
  const area =
    series.length > 1
      ? `${path(series)} L${x(series.length - 1, series.length).toFixed(1)},${(height - pad.b).toFixed(1)} L${x(0, series.length).toFixed(1)},${(height - pad.b).toFixed(1)} Z`
      : "";

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      role="img"
      aria-label="Equity curve indexed to 100"
      className="qb-lab-chart"
    >
      <defs>
        <linearGradient id="qbEqFill" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--qb-accent)" stopOpacity="0.28" />
          <stop offset="100%" stopColor="var(--qb-accent)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0.25, 0.5, 0.75].map((f) => {
        const gv = minV + (maxV - minV) * f;
        return (
          <line
            key={f}
            x1={pad.l}
            x2={width - pad.r}
            y1={y(gv)}
            y2={y(gv)}
            stroke="currentColor"
            strokeOpacity={0.08}
          />
        );
      })}
      <line
        x1={pad.l}
        x2={width - pad.r}
        y1={y(100)}
        y2={y(100)}
        stroke="currentColor"
        strokeOpacity={0.25}
        strokeDasharray="4 4"
      />
      {area ? <path d={area} fill="url(#qbEqFill)" /> : null}
      {bench.length > 1 ? (
        <path d={path(bench)} fill="none" stroke="#8caacf" strokeWidth={1.5} strokeDasharray="5 4" />
      ) : null}
      <path d={path(series)} fill="none" stroke="var(--qb-accent)" strokeWidth={2.25} />
      <text x={pad.l} y={height - 10} fontSize={11} fill="currentColor" opacity={0.55}>
        {series[0]?.date?.slice(0, 7)}
      </text>
      <text
        x={width - pad.r}
        y={height - 10}
        fontSize={11}
        fill="currentColor"
        opacity={0.55}
        textAnchor="end"
      >
        {series[series.length - 1]?.date?.slice(0, 7)}
      </text>
      <text x={6} y={y(maxV) + 4} fontSize={10} fill="currentColor" opacity={0.55}>
        {maxV.toFixed(0)}
      </text>
      <text x={6} y={y(minV)} fontSize={10} fill="currentColor" opacity={0.55}>
        {minV.toFixed(0)}
      </text>
    </svg>
  );
}

export function DrawdownChart({ equity, height = 140 }: { equity: CurvePoint[]; height?: number }) {
  const dd = drawdownSeries(equity);
  if (dd.length < 2) return null;
  const width = 720;
  const pad: Pad = { t: 12, r: 16, b: 28, l: 48 };
  const minV = Math.min(...dd.map((d) => d.dd), -1);
  const maxV = 0;
  const x = (i: number) => pad.l + (i / Math.max(dd.length - 1, 1)) * (width - pad.l - pad.r);
  const y = (v: number) =>
    pad.t + ((maxV - v) / Math.max(maxV - minV, 1e-9)) * (height - pad.t - pad.b);
  const line = dd
    .map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.dd).toFixed(1)}`)
    .join(" ");
  const area = `${line} L${x(dd.length - 1).toFixed(1)},${y(0).toFixed(1)} L${x(0).toFixed(1)},${y(0).toFixed(1)} Z`;
  const worst = Math.min(...dd.map((d) => d.dd));

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      role="img"
      aria-label="Drawdown chart"
      className="qb-lab-chart"
    >
      <path d={area} fill="rgba(251, 113, 133, 0.22)" />
      <path d={line} fill="none" stroke="#fb7185" strokeWidth={1.75} />
      <text x={pad.l} y={height - 8} fontSize={11} fill="currentColor" opacity={0.55}>
        Worst {worst.toFixed(1)}%
      </text>
      <text x={6} y={y(worst) + 4} fontSize={10} fill="#fb7185" opacity={0.8}>
        {worst.toFixed(0)}%
      </text>
    </svg>
  );
}

export function MetricsBarChart({
  metrics,
  baseline,
  height = 180,
}: {
  metrics: Record<string, string | null | undefined>;
  baseline: Record<string, string | null | undefined>;
  height?: number;
}) {
  const rows = [
    { key: "annualisedReturn", label: "CAGR" },
    { key: "sharpeRatio", label: "Sharpe" },
    { key: "sortinoRatio", label: "Sortino" },
    { key: "volatility", label: "Vol" },
    { key: "maxDrawdown", label: "|DD|" },
    { key: "winRate", label: "Up%" },
  ]
    .map((r) => {
      let cur = parseMetricPct(metrics[r.key]);
      let base = parseMetricPct(baseline[r.key]);
      if (r.key === "maxDrawdown") {
        if (cur != null) cur = Math.abs(cur);
        if (base != null) base = Math.abs(base);
      }
      return { ...r, cur, base };
    })
    .filter((r) => r.cur != null);

  if (!rows.length) return null;

  const width = 720;
  const pad: Pad = { t: 16, r: 16, b: 36, l: 40 };
  const groupW = (width - pad.l - pad.r) / rows.length;
  const maxAbs = Math.max(
    ...rows.flatMap((r) => [Math.abs(r.cur || 0), Math.abs(r.base || 0)]),
    1,
  );
  const barH = (v: number) => (Math.abs(v) / maxAbs) * (height - pad.t - pad.b - 8);
  const zeroY = height - pad.b;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      role="img"
      aria-label="Metrics comparison bar chart"
      className="qb-lab-chart"
    >
      <line
        x1={pad.l}
        x2={width - pad.r}
        y1={zeroY}
        y2={zeroY}
        stroke="currentColor"
        strokeOpacity={0.2}
      />
      {rows.map((r, i) => {
        const cx = pad.l + i * groupW + groupW / 2;
        const curH = barH(r.cur || 0);
        const baseH = r.base != null ? barH(r.base) : 0;
        return (
          <g key={r.key}>
            {r.base != null ? (
              <rect
                x={cx - 14}
                y={zeroY - baseH}
                width={12}
                height={baseH}
                fill="#8caacf"
                opacity={0.55}
                rx={2}
              />
            ) : null}
            <rect
              x={cx + (r.base != null ? 2 : -6)}
              y={zeroY - curH}
              width={12}
              height={curH}
              fill="var(--qb-accent)"
              rx={2}
            />
            <text
              x={cx}
              y={height - 10}
              fontSize={10}
              fill="currentColor"
              opacity={0.7}
              textAnchor="middle"
            >
              {r.label}
            </text>
          </g>
        );
      })}
      <text x={pad.l} y={14} fontSize={10} fill="#8caacf">
        Grey = baseline · Accent = live run
      </text>
    </svg>
  );
}

export function MonthlyReturnBars({
  equity,
  height = 160,
}: {
  equity: CurvePoint[];
  height?: number;
}) {
  const rows = monthlyReturns(equity);
  if (rows.length < 2) return null;
  const width = 720;
  const pad: Pad = { t: 16, r: 12, b: 36, l: 40 };
  const midY = pad.t + (height - pad.t - pad.b) / 2;
  const maxAbs = Math.max(...rows.map((r) => Math.abs(r.ret)), 1);
  const barW = Math.max(4, (width - pad.l - pad.r) / rows.length - 2);
  const scale = (height - pad.t - pad.b) / 2 / maxAbs;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      width="100%"
      height={height}
      role="img"
      aria-label="Monthly return bars"
      className="qb-lab-chart"
    >
      <line
        x1={pad.l}
        x2={width - pad.r}
        y1={midY}
        y2={midY}
        stroke="currentColor"
        strokeOpacity={0.25}
      />
      {rows.map((r, i) => {
        const x = pad.l + i * ((width - pad.l - pad.r) / rows.length) + 1;
        const h = Math.abs(r.ret) * scale;
        const y = r.ret >= 0 ? midY - h : midY;
        return (
          <rect
            key={r.label}
            x={x}
            y={y}
            width={barW}
            height={Math.max(h, 1)}
            fill={r.ret >= 0 ? "#34d399" : "#fb7185"}
            opacity={0.85}
            rx={1}
          >
            <title>
              {r.label}: {r.ret.toFixed(2)}%
            </title>
          </rect>
        );
      })}
      <text x={pad.l} y={height - 10} fontSize={10} fill="currentColor" opacity={0.55}>
        {rows[0]?.label}
      </text>
      <text
        x={width - pad.r}
        y={height - 10}
        fontSize={10}
        fill="currentColor"
        opacity={0.55}
        textAnchor="end"
      >
        {rows[rows.length - 1]?.label} · last {rows.length} months
      </text>
    </svg>
  );
}
