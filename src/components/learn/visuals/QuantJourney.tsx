"use client";

import { useState } from "react";

const STEPS = [
  {
    id: "research",
    label: "Research idea",
    detail: "Read a paper or hypothesis: e.g. \"assets with positive 12-month return tend to keep outperforming.\"",
  },
  {
    id: "data",
    label: "Load market data",
    detail: "Download daily adjusted closes for whitelisted ETFs (SPY, TLT, GLD…). Quant Buffet caches prices in backtest/data_cache/.",
  },
  {
    id: "signal",
    label: "Build signals",
    detail: "In make_on_day(prices), compute indicators (SMA, momentum rank, z-score) and decide target weights each day.",
  },
  {
    id: "engine",
    label: "Simulate fills",
    detail: "PortfolioEngine applies commission (5 bps) and slippage (2 bps), tracks cash and holdings.",
  },
  {
    id: "metrics",
    label: "Measure performance",
    detail: "compute_metrics reports CAGR, Sharpe, max drawdown, alpha vs SPY buy-and-hold.",
  },
  {
    id: "iterate",
    label: "Debug & iterate",
    detail: "Use the lab AI debugger, API docs, and this course. Refine — never treat backtests as guarantees.",
  },
];

export default function QuantJourney() {
  const [active, setActive] = useState(0);

  return (
    <div className="qb-learn-visual qb-learn-journey">
      <div className="qb-learn-journey-track" role="tablist" aria-label="Quant trading workflow">
        {STEPS.map((step, i) => (
          <button
            key={step.id}
            type="button"
            role="tab"
            aria-selected={active === i}
            className={`qb-learn-journey-step${active === i ? " is-active" : ""}${i < active ? " is-done" : ""}`}
            onClick={() => setActive(i)}
          >
            <span className="qb-learn-journey-num">{i + 1}</span>
            <span className="qb-learn-journey-label">{step.label}</span>
          </button>
        ))}
      </div>
      <div className="qb-learn-journey-panel" role="tabpanel">
        <h4 className="qb-learn-visual-title">{STEPS[active].label}</h4>
        <p>{STEPS[active].detail}</p>
      </div>
    </div>
  );
}
