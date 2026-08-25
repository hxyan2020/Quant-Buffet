"use client";

import { useState, type CSSProperties } from "react";

const CLASSES = [
  {
    id: "equity",
    name: "Equities",
    emoji: "EQ",
    color: "#38bdf8",
    desc: "Ownership in companies. Quant Buffet uses liquid ETF proxies (SPY, QQQ, sector XLE/XLK…).",
    examples: ["SPY", "QQQ", "IWM", "XLK", "EFA"],
    risk: "High growth potential; drawdowns can be sharp.",
  },
  {
    id: "bonds",
    name: "Bonds / Rates",
    emoji: "BD",
    color: "#a78bfa",
    desc: "Government and corporate debt. Duration ETFs (SHY, IEF, TLT) proxy interest-rate exposure.",
    examples: ["TLT", "IEF", "SHY", "LQD", "HYG"],
    risk: "Lower vol than stocks; sensitive to rates and credit spreads.",
  },
  {
    id: "commodities",
    name: "Commodities",
    emoji: "CM",
    color: "#fbbf24",
    desc: "Physical goods and inflation hedges via GLD, DBC, USO.",
    examples: ["GLD", "SLV", "DBC", "USO", "DBA"],
    risk: "Can diversify stocks; roll costs matter in futures.",
  },
  {
    id: "realestate",
    name: "Real estate",
    emoji: "RE",
    color: "#34d399",
    desc: "Property exposure through REIT ETFs like VNQ.",
    examples: ["VNQ", "IYR", "RWX"],
    risk: "Equity-like but driven by rates and occupancy cycles.",
  },
  {
    id: "fx",
    name: "FX / Dollar",
    emoji: "FX",
    color: "#fb7185",
    desc: "Currency moves. Lab uses dollar-sensitive mixes (EFA, GLD) when pure FX ETFs fail to load.",
    examples: ["EFA", "EWJ", "GLD", "TLT"],
    risk: "Carry and macro shocks; data quality varies by pair.",
  },
  {
    id: "crypto",
    name: "Crypto",
    emoji: "CR",
    color: "#f472b6",
    desc: "BTC-USD and ETH-USD via yfinance — high vol momentum playground in the library.",
    examples: ["BTC-USD", "ETH-USD"],
    risk: "Extreme volatility; 24/7 markets differ from ETF sessions.",
  },
];

export default function AssetClassExplorer() {
  const [selected, setSelected] = useState(CLASSES[0].id);
  const active = CLASSES.find((c) => c.id === selected) ?? CLASSES[0];

  return (
    <div className="qb-learn-visual qb-learn-assets">
      <div className="qb-learn-asset-grid">
        {CLASSES.map((c) => (
          <button
            key={c.id}
            type="button"
            className={`qb-learn-asset-chip${selected === c.id ? " is-active" : ""}`}
            style={{ "--chip-accent": c.color } as CSSProperties}
            onClick={() => setSelected(c.id)}
          >
            <span className="qb-learn-asset-badge">{c.emoji}</span>
            {c.name}
          </button>
        ))}
      </div>
      <div className="qb-learn-asset-panel">
        <h4 className="qb-learn-visual-title">{active.name}</h4>
        <p>{active.desc}</p>
        <p className="qb-learn-asset-examples">
          <strong>Lab tickers:</strong>{" "}
          {active.examples.map((t) => (
            <code key={t} className="qb-learn-ticker">
              {t}
            </code>
          ))}
        </p>
        <p className="qb-learn-asset-risk">
          <strong>Risk note:</strong> {active.risk}
        </p>
      </div>
    </div>
  );
}
