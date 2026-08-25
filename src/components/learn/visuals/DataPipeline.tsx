"use client";

const ROWS = [
  { source: "Exchange / vendor", raw: "Tick-by-tick trades, quotes", qb: "Not used in lab" },
  { source: "Yahoo Finance (yfinance)", raw: "Daily OHLCV", qb: "Downloaded via load_daily_prices" },
  { source: "Quant Buffet cache", raw: "CSV per symbol + date range", qb: "backtest/data_cache/*.csv" },
  { source: "Your strategy", raw: "pd.DataFrame panel", qb: "Columns = ASSETS, index = dates" },
  { source: "Indicators", raw: "Rolling SMA, returns, z-scores", qb: "Computed inside make_on_day" },
];

export default function DataPipeline() {
  return (
    <div className="qb-learn-visual qb-learn-pipeline">
      <svg viewBox="0 0 720 200" className="qb-learn-pipeline-svg" aria-hidden>
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L6,3 L0,6 Z" fill="rgba(56,189,248,0.8)" />
          </marker>
        </defs>
        {[
          { x: 20, label: "Vendor" },
          { x: 160, label: "yfinance" },
          { x: 300, label: "Cache" },
          { x: 440, label: "prices DF" },
          { x: 580, label: "Signals" },
        ].map((node, i, arr) => (
          <g key={node.label}>
            <rect
              x={node.x}
              y="40"
              width="110"
              height="48"
              rx="8"
              fill="rgba(56,189,248,0.12)"
              stroke="rgba(56,189,248,0.45)"
            />
            <text x={node.x + 55} y="68" textAnchor="middle" fill="#e2f0ff" fontSize="13" fontFamily="monospace">
              {node.label}
            </text>
            {i < arr.length - 1 ? (
              <line
                x1={node.x + 110}
                y1="64"
                x2={arr[i + 1].x}
                y2="64"
                stroke="rgba(56,189,248,0.5)"
                strokeWidth="2"
                markerEnd="url(#arrow)"
              />
            ) : null}
          </g>
        ))}
        <text x="360" y="130" textAnchor="middle" fill="#8caacf" fontSize="12">
          Daily adjusted close panel — one row per trading day
        </text>
      </svg>
      <table className="qb-learn-table">
        <thead>
          <tr>
            <th>Layer</th>
            <th>What you get</th>
            <th>In Quant Buffet</th>
          </tr>
        </thead>
        <tbody>
          {ROWS.map((r) => (
            <tr key={r.source}>
              <td>{r.source}</td>
              <td>{r.raw}</td>
              <td>{r.qb}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
