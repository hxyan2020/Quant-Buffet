"use client";

import { useMemo, useState } from "react";

function fmtPct(n: number) {
  return `${(n * 100).toFixed(1)}%`;
}

export default function MetricsExplorer() {
  const [cagr, setCagr] = useState(0.12);
  const [vol, setVol] = useState(0.18);
  const [maxDd, setMaxDd] = useState(-0.22);
  const [rf, setRf] = useState(0.04);

  const sharpe = useMemo(() => {
    if (vol <= 0) return 0;
    return (cagr - rf) / vol;
  }, [cagr, vol, rf]);

  const calmar = useMemo(() => {
    if (maxDd >= 0) return 0;
    return cagr / Math.abs(maxDd);
  }, [cagr, maxDd]);

  const verdict =
    sharpe >= 1 ? "Strong risk-adjusted profile (research-grade curiosity)" : sharpe >= 0.5 ? "Moderate — dig into drawdowns" : "Weak — check overfitting or costs";

  return (
    <div className="qb-learn-visual qb-learn-metrics">
      <p className="qb-learn-metrics-intro">
        Drag the sliders to see how Sharpe and Calmar react. These are the same families of stats Quant Buffet reports
        after a lab run.
      </p>
      <div className="qb-learn-metrics-grid">
        <div className="qb-learn-metrics-sliders">
          <label className="qb-learn-slider">
            <span>CAGR {fmtPct(cagr)}</span>
            <input type="range" min={-0.1} max={0.35} step={0.01} value={cagr} onChange={(e) => setCagr(+e.target.value)} />
          </label>
          <label className="qb-learn-slider">
            <span>Volatility {fmtPct(vol)}</span>
            <input type="range" min={0.05} max={0.45} step={0.01} value={vol} onChange={(e) => setVol(+e.target.value)} />
          </label>
          <label className="qb-learn-slider">
            <span>Max drawdown {fmtPct(maxDd)}</span>
            <input type="range" min={-0.55} max={-0.05} step={0.01} value={maxDd} onChange={(e) => setMaxDd(+e.target.value)} />
          </label>
          <label className="qb-learn-slider">
            <span>Risk-free rate {fmtPct(rf)}</span>
            <input type="range" min={0} max={0.08} step={0.005} value={rf} onChange={(e) => setRf(+e.target.value)} />
          </label>
        </div>
        <div className="qb-learn-metrics-cards">
          <div className="qb-learn-metric-card">
            <div className="qb-learn-metric-label">Sharpe (approx.)</div>
            <div className="qb-learn-metric-value">{sharpe.toFixed(2)}</div>
            <div className="qb-learn-metric-hint">(CAGR − RF) / Vol</div>
          </div>
          <div className="qb-learn-metric-card">
            <div className="qb-learn-metric-label">Calmar (approx.)</div>
            <div className="qb-learn-metric-value">{calmar.toFixed(2)}</div>
            <div className="qb-learn-metric-hint">CAGR / |Max DD|</div>
          </div>
          <div className="qb-learn-metric-card qb-learn-metric-wide">
            <div className="qb-learn-metric-label">Interpretation</div>
            <p>{verdict}</p>
          </div>
        </div>
      </div>
      <table className="qb-learn-table qb-learn-table-compact">
        <thead>
          <tr>
            <th>Lab error</th>
            <th>Likely fix</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Signal never ready</td>
            <td>Shorten lookback or extend start date; check ASSETS history.</td>
          </tr>
          <tr>
            <td>Import blocked</td>
            <td>Only backtest.*, numpy, pandas — see API docs.</td>
          </tr>
          <tr>
            <td>Symbol not in whitelist</td>
            <td>Use ETFs from backtest.universes (SPY, TLT, GLD…).</td>
          </tr>
          <tr>
            <td>Equity curve too short</td>
            <td>Ensure on_day actually calls set_target_weights.</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
