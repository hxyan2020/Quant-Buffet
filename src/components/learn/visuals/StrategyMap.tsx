"use client";

import { useState } from "react";

const FAMILIES = [
  {
    id: "momentum",
    name: "Momentum",
    share: "62%",
    templates: ["abs_momentum", "dual_momentum", "momentum_rotation"],
    idea: "Winners keep winning over 3–12 month horizons. Library favorite: dual_momentum (623 strategies).",
    pitfall: "Crash risk when trends reverse sharply (2009, 2020).",
  },
  {
    id: "trend",
    name: "Trend following",
    share: "13%",
    templates: ["sma_trend", "dual_ma"],
    idea: "Stay long when price is above moving average. Simple, robust, but whipsaws in ranges.",
    pitfall: "Long flat periods when markets chop sideways.",
  },
  {
    id: "meanrev",
    name: "Mean reversion",
    share: "6%",
    templates: ["mean_reversion"],
    idea: "Buy oversold, sell normalized — z-scores on returns or spreads.",
    pitfall: "Fighting strong trends; needs risk controls.",
  },
  {
    id: "allocation",
    name: "Allocation / risk",
    share: "12%",
    templates: ["equal_weight", "risk_parity", "vol_target"],
    idea: "Balance risk contributions or target portfolio volatility.",
    pitfall: "Assumes historical vol predicts future vol.",
  },
  {
    id: "pairs",
    name: "Pairs / stat arb",
    share: "Library theme",
    templates: ["Custom code"],
    idea: "Trade spread between correlated assets when it diverges.",
    pitfall: "Relationships break; capacity limits in live trading.",
  },
  {
    id: "carry",
    name: "Carry / factor",
    share: "Library theme",
    templates: ["multi-asset books"],
    idea: "Earn roll yield (FX/bonds) or factor premia (value, low-vol).",
    pitfall: "Tail events — carry strategies bleed until they gap.",
  },
];

export default function StrategyMap() {
  const [active, setActive] = useState(FAMILIES[0].id);
  const f = FAMILIES.find((x) => x.id === active) ?? FAMILIES[0];

  return (
    <div className="qb-learn-visual qb-learn-strategies">
      <div className="qb-learn-strat-bars">
        {FAMILIES.filter((x) => x.share.includes("%")).map((fam) => {
          const pct = parseInt(fam.share, 10) || 8;
          return (
            <button
              key={fam.id}
              type="button"
              className={`qb-learn-strat-bar${active === fam.id ? " is-active" : ""}`}
              style={{ flex: pct }}
              onClick={() => setActive(fam.id)}
              title={fam.name}
            >
              <span>{fam.name}</span>
              <span className="qb-learn-strat-pct">{fam.share}</span>
            </button>
          );
        })}
      </div>
      <div className="qb-learn-strat-themes">
        {FAMILIES.filter((x) => !x.share.includes("%")).map((fam) => (
          <button
            key={fam.id}
            type="button"
            className={`qb-learn-strat-chip${active === fam.id ? " is-active" : ""}`}
            onClick={() => setActive(fam.id)}
          >
            {fam.name}
          </button>
        ))}
      </div>
      <div className="qb-learn-strat-detail">
        <h4 className="qb-learn-visual-title">{f.name}</h4>
        <p>{f.idea}</p>
        <p>
          <strong>Quant Buffet templates:</strong>{" "}
          {f.templates.map((t) => (
            <code key={t} className="qb-learn-ticker">
              {t}
            </code>
          ))}
        </p>
        <p className="qb-learn-strat-pitfall">
          <strong>Watch out:</strong> {f.pitfall}
        </p>
      </div>
    </div>
  );
}
