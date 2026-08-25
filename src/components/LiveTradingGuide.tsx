import type { LiveTradingGuide } from "@/lib/live-trading-guide";

export default function LiveTradingGuidePanel({
  locale,
  guide,
}: {
  locale: string;
  guide: LiveTradingGuide;
}) {
  const zh = locale === "zh";
  return (
    <section className="qb-live" id="live-trading">
      <h2 className="qb-strategy-section-title">
        {zh ? "如何接到实盘交易" : "How to connect this backtest to live trading"}
      </h2>
      <p className="qb-live-summary">{guide.summary}</p>

      <div className="qb-live-meta">
        <div>
          <div className="qb-live-k">{zh ? "推荐场所" : "Venue"}</div>
          <div className="qb-live-v">{guide.venueName}</div>
        </div>
        <div>
          <div className="qb-live-k">{zh ? "账户类型" : "Account"}</div>
          <div className="qb-live-v">{guide.accountType}</div>
        </div>
        <div>
          <div className="qb-live-k">{zh ? "交易品种" : "Products"}</div>
          <div className="qb-live-v">{guide.products}</div>
        </div>
      </div>

      <ol className="qb-live-steps">
        {guide.steps.map((step) => (
          <li key={step.title}>
            <strong>{step.title}</strong>
            <p>{step.body}</p>
            {step.href ? (
              <p>
                <a className="qb-accent-link" href={step.href} target="_blank" rel="noopener noreferrer">
                  {step.hrefLabel || step.href}
                </a>
              </p>
            ) : null}
          </li>
        ))}
      </ol>

      {guide.firstOrders.length ? (
        <>
          <h3 className="qb-live-h3">{zh ? "第一批订单（对本策略）" : "First orders for this strategy"}</h3>
          <ul className="qb-live-orders">
            {guide.firstOrders.map((row) => (
              <li key={row}>{row}</li>
            ))}
          </ul>
        </>
      ) : null}

      <div className="qb-live-warn">
        {guide.warnings.map((w) => (
          <p key={w}>{w}</p>
        ))}
      </div>
    </section>
  );
}
