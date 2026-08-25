"use client";

import { useState } from "react";

type OrderType = "market" | "limit" | "stop" | "stop_limit";

const ORDERS: Record<
  OrderType,
  { name: string; definition: string; pro: string; con: string; qb: string }
> = {
  market: {
    name: "Market",
    definition: "Execute now at the best available price.",
    pro: "Certainty of fill (if liquidity exists).",
    con: "Price uncertainty — you pay the spread + slippage.",
    qb: "PortfolioEngine rebalances at the daily close with slippage applied — similar to a market-on-close intent.",
  },
  limit: {
    name: "Limit",
    definition: "Only fill at your price or better.",
    pro: "Price control.",
    con: "May never fill if the market moves away.",
    qb: "Not modeled explicitly — daily backtest assumes you trade at the close.",
  },
  stop: {
    name: "Stop (stop-market)",
    definition: "Becomes a market order once a trigger price is touched.",
    pro: "Automates exit when trend breaks.",
    con: "Gap risk — trigger can fill far below stop in a crash.",
    qb: "Implement via signal logic (e.g. exit when price crosses below SMA), not a broker order object.",
  },
  stop_limit: {
    name: "Stop-limit",
    definition: "Stop triggers a limit order instead of a market order.",
    pro: "Caps worst fill after trigger.",
    con: "May not exit at all in fast markets.",
    qb: "Same as stop — encode rules in on_day(), not order types.",
  },
};

export default function OrderTypeGuide() {
  const [type, setType] = useState<OrderType>("market");
  const o = ORDERS[type];

  return (
    <div className="qb-learn-visual qb-learn-orders">
      <div className="qb-learn-order-tabs" role="tablist">
        {(Object.keys(ORDERS) as OrderType[]).map((key) => (
          <button
            key={key}
            type="button"
            role="tab"
            aria-selected={type === key}
            className={`qb-learn-order-tab${type === key ? " is-active" : ""}`}
            onClick={() => setType(key)}
          >
            {ORDERS[key].name}
          </button>
        ))}
      </div>
      <div className="qb-learn-order-panel" role="tabpanel">
        <p>
          <strong>Definition:</strong> {o.definition}
        </p>
        <div className="qb-learn-order-cols">
          <div>
            <strong>Pros</strong>
            <p>{o.pro}</p>
          </div>
          <div>
            <strong>Cons</strong>
            <p>{o.con}</p>
          </div>
        </div>
        <p className="qb-learn-order-qb">
          <strong>Quant Buffet:</strong> {o.qb}
        </p>
      </div>
      <svg viewBox="0 0 400 120" className="qb-learn-order-svg" aria-label="Simplified fill diagram">
        <text x="200" y="20" textAnchor="middle" fill="#8caacf" fontSize="11">
          Daily bar (lab assumption)
        </text>
        <line x1="40" y1="90" x2="360" y2="90" stroke="rgba(255,255,255,0.2)" />
        <rect x="80" y="50" width="8" height="40" fill="#38bdf8" opacity="0.5" />
        <line x1="84" y1="45" x2="84" y2="95" stroke="#38bdf8" strokeWidth="2" />
        <line x1="70" y1="45" x2="98" y2="45" stroke="#38bdf8" strokeWidth="2" />
        <line x1="70" y1="95" x2="98" y2="95" stroke="#38bdf8" strokeWidth="2" />
        <text x="110" y="72" fill="#e2f0ff" fontSize="12">
          Close price → engine fill + slippage
        </text>
      </svg>
    </div>
  );
}
