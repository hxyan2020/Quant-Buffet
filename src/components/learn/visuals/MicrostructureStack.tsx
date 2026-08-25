"use client";

import { useState } from "react";

const LAYERS = [
  {
    id: "venue",
    title: "Trading venue",
    items: ["NYSE / NASDAQ", "CME futures", "Crypto exchanges (24/7)"],
    note: "Where orders meet liquidity. Quant Buffet lab does not connect to venues — it simulates.",
  },
  {
    id: "broker",
    title: "Broker / custodian",
    items: ["Interactive Brokers", "Coinbase Advanced", "Paper vs live accounts"],
    note: "Routes your orders, holds cash and positions, reports fills.",
  },
  {
    id: "platform",
    title: "Quant platform",
    items: ["Quant Buffet backtest lab", "QuantConnect / LEAN (library code)", "Python + pandas locally"],
    note: "Research layer: signals, backtests, and strategy articles.",
  },
  {
    id: "data",
    title: "Market data feed",
    items: ["Yahoo daily (lab)", "Vendor tick data (institutional)", "Corporate actions / splits"],
    note: "Quality and latency define what strategies are feasible.",
  },
];

export default function MicrostructureStack() {
  const [open, setOpen] = useState("platform");

  return (
    <div className="qb-learn-visual qb-learn-stack">
      <div className="qb-learn-stack-diagram">
        {LAYERS.map((layer, i) => (
          <button
            key={layer.id}
            type="button"
            className={`qb-learn-stack-layer${open === layer.id ? " is-open" : ""}`}
            style={{ zIndex: LAYERS.length - i }}
            onClick={() => setOpen(layer.id)}
          >
            <span className="qb-learn-stack-index">{LAYERS.length - i}</span>
            <span>{layer.title}</span>
          </button>
        ))}
      </div>
      <div className="qb-learn-stack-detail">
        <h4 className="qb-learn-visual-title">{LAYERS.find((l) => l.id === open)?.title}</h4>
        <ul>
          {(LAYERS.find((l) => l.id === open)?.items ?? []).map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
        <p className="qb-learn-stack-note">{LAYERS.find((l) => l.id === open)?.note}</p>
      </div>
      <table className="qb-learn-table qb-learn-table-compact">
        <thead>
          <tr>
            <th>Concept</th>
            <th>Plain English</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Bid–ask spread</td>
            <td>Gap between best buy and sell price — hidden cost when you trade.</td>
          </tr>
          <tr>
            <td>Slippage</td>
            <td>Fill price worse than expected; Quant Buffet models 2 bps per side.</td>
          </tr>
          <tr>
            <td>Latency</td>
            <td>Delay from signal to fill; matters for HFT, less for monthly ETF rotation.</td>
          </tr>
          <tr>
            <td>Partial fill</td>
            <td>Order only partly executed — engine scales buys if cash is insufficient.</td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
