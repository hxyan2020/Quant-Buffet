import type { LearnLesson } from "../types";

export const EN_LESSONS: LearnLesson[] = [
  {
    slug: "intro",
    title: "From zero to systematic trader",
    subtitle: "What quantitative trading is, how Quant Buffet teaches it, and the mindset you need before touching code.",
    order: 1,
    duration: "12 min",
    topics: ["Mindset", "Workflow", "Lab overview"],
    blocks: [
      {
        kind: "p",
        text: "A **quantitative trader** uses rules, data, and code — not gut feel — to decide when to buy and sell. You do not need a finance degree to start. You need curiosity, basic Python literacy, and patience to treat every backtest as **research**, not a profit promise.",
      },
      { kind: "visual", id: "quant-journey" },
      { kind: "h2", text: "What makes trading \"quant\"?" },
      {
        kind: "table",
        headers: ["Discretionary trader", "Quant / systematic trader"],
        rows: [
          ["Reads news and charts subjectively", "Encodes rules in code (if X, then buy Y)"],
          ["Hard to reproduce decisions", "Same inputs → same signals every time"],
          ["Back-of-napkin risk guess", "Sharpe, drawdown, and scenario stats"],
          ["One market story", "Tests 800+ academic ideas in a library"],
        ],
      },
      { kind: "h2", text: "How Quant Buffet helps beginners" },
      {
        kind: "ul",
        items: [
          "**Strategy Library** — peer-reviewed ideas with economic rationale and Python.",
          "**Backtest lab** (draft preview) — edit code, run in-browser, see equity curves.",
          "**API docs** — reference for `ASSETS`, `make_on_day`, engine, and metrics.",
          "**This course** — concepts before code, mapped to what the platform actually runs.",
        ],
      },
      {
        kind: "warn",
        text: "Quant Buffet is educational research. Past backtests ignore taxes, capacity, and regime change. You are responsible for live trading and compliance.",
      },
      {
        kind: "checklist",
        title: "Before Lesson 2 — you should understand",
        items: [
          "Quants express ideas as **rules + data + simulation**.",
          "Quant Buffet lab strategies use **daily ETF prices** and **long-only** weights.",
          "Your goal in Lesson 2–7 is to read data, infrastructure, orders, metrics, and classic patterns.",
        ],
      },
    ],
  },
  {
    slug: "market-data",
    title: "Market data fundamentals",
    subtitle: "Prices, bars, adjusted data, and the panels your strategies consume every day.",
    order: 2,
    duration: "18 min",
    topics: ["OHLCV", "Adjusted close", "Panels"],
    blocks: [
      {
        kind: "p",
        text: "Every strategy starts with **market data** — a time series of prices. Quant Buffet's lab uses **daily adjusted close** for liquid ETFs, loaded through `load_daily_prices()` and cached on disk.",
      },
      { kind: "visual", id: "data-pipeline" },
      { kind: "h2", text: "Core vocabulary" },
      {
        kind: "table",
        headers: ["Term", "Meaning", "Example in lab"],
        rows: [
          ["Ticker / symbol", "Instrument code", "`SPY`, `TLT`, `BTC-USD`"],
          ["OHLCV bar", "Open, High, Low, Close, Volume for one period", "One row per trading day"],
          ["Adjusted close", "Close corrected for splits & dividends", "Default in `load_daily_prices`"],
          ["Panel", "Table: dates × symbols", "`prices` DataFrame in `make_on_day`"],
          ["Lookback", "History window for an indicator", "200-day SMA needs 200 rows"],
        ],
      },
      { kind: "h2", text: "Reading a price panel" },
      {
        kind: "code",
        lang: "python",
        code: `# Inside make_on_day — prices is already loaded for your ASSETS
cols = [c for c in ASSETS if c in prices.columns]
close = prices[cols]
daily_return = close.pct_change()
sma_200 = close.rolling(200, min_periods=200).mean()`,
      },
      { kind: "h3", text: "Common data pitfalls" },
      {
        kind: "ul",
        items: [
          "**Survivorship bias** — testing only assets that exist today ignores delisted names.",
          "**Look-ahead bias** — using future data in today's signal (e.g. full-sample mean).",
          "**Corporate actions** — always prefer adjusted prices for long backtests.",
          "**Missing IPO history** — forward-fill does not invent pre-IPO prices; `ready` must start after data exists.",
        ],
      },
      {
        kind: "note",
        text: "The library's 1,700+ strategies often map academic papers to **ETF proxies** when original assets (single stocks, futures) are not in the lab whitelist.",
      },
    ],
  },
  {
    slug: "asset-classes",
    title: "Asset classes & ETF proxies",
    subtitle: "Equities, bonds, commodities, FX, and crypto — how Quant Buffet represents each in backtests.",
    order: 3,
    duration: "15 min",
    topics: ["ETFs", "Risk", "Universes"],
    blocks: [
      {
        kind: "p",
        text: "An **asset class** is a category of investments with similar behaviour. Real portfolios mix them for diversification. In Quant Buffet you trade **ETF proxies** from `backtest.universes` — liquid, cheap to simulate, and comparable across 800+ library strategies.",
      },
      { kind: "visual", id: "asset-explorer" },
      { kind: "h2", text: "Why ETFs instead of single stocks?" },
      {
        kind: "ul",
        items: [
          "**Liquidity** — SPY trades millions of shares; slippage models are realistic.",
          "**Diversification** — one ticker exposes you to hundreds of names.",
          "**Consistency** — same data source (Yahoo) for the whole whitelist.",
          "**Teaching focus** — you learn the *strategy logic*, not ticker-specific noise.",
        ],
      },
      { kind: "h2", text: "Named books in code" },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.universes import US_SECTORS_FULL, BONDS, MULTI_ASSET

# Example: sector rotation + safety assets (max 15 symbols in lab)
ASSETS = ["XLK", "XLF", "XLE", "XLV", "TLT", "GLD", "BIL"]`,
      },
      {
        kind: "table",
        headers: ["Book constant", "Typical strategy use"],
        rows: [
          ["`RISK_ON_OFF`", "Switch between SPY/QQQ and TLT/GLD/BIL"],
          ["`US_SECTORS_FULL`", "Industry momentum & rotation"],
          ["`GLOBAL_EQUITY`", "Cross-country equity momentum"],
          ["`COMMODITIES`", "Inflation / crisis hedges"],
          ["`CRYPTO_PROXY`", "BTC/ETH momentum papers"],
        ],
      },
    ],
  },
  {
    slug: "microstructure",
    title: "Microstructure & trading infrastructure",
    subtitle: "Exchanges, brokers, spreads, and how research simulation differs from live trading.",
    order: 4,
    duration: "16 min",
    topics: ["Venues", "Brokers", "Costs"],
    blocks: [
      {
        kind: "p",
        text: "**Market microstructure** is the mechanics of how orders become trades — queues, spreads, and latency. You do not need to build a exchange to learn quant trading, but you **must** know where simulation ends and real infrastructure begins.",
      },
      { kind: "visual", id: "microstructure-stack" },
      { kind: "h2", text: "Research stack vs live stack" },
      {
        kind: "table",
        headers: ["Layer", "Backtest lab", "Live trading"],
        rows: [
          ["Signal time", "Daily close", "Intraday or daily — your choice"],
          ["Execution price", "Close + 2 bps slippage model", "Bid/ask at broker"],
          ["Commission", "5 bps per fill", "Broker fee schedule"],
          ["Capital", "Virtual $100,000", "Real cash & margin"],
          ["Failure mode", "Python exception", "Rejected order, partial fill, outage"],
        ],
      },
      { kind: "h2", text: "Infrastructure checklist for live trading" },
      {
        kind: "ol",
        items: [
          "**Broker account** — e.g. Interactive Brokers for ETFs, crypto exchange for BTC.",
          "**Market data subscription** — free delayed vs paid real-time.",
          "**Order routing** — desktop, API, or platform like QuantConnect.",
          "**Risk limits** — max position size, max daily loss, kill switch.",
          "**Logging & reconciliation** — compare fills to what your model expected.",
        ],
      },
      {
        kind: "note",
        text: "Quant Buffet's live-trading guide (draft preview) maps ETF strategies to IBKR and crypto ideas to Coinbase/Kraken — always verify fees and regulations in your jurisdiction.",
      },
    ],
  },
  {
    slug: "order-types",
    title: "Order types & execution",
    subtitle: "Market, limit, and stop orders — and how the PortfolioEngine simulates fills.",
    order: 5,
    duration: "14 min",
    topics: ["Orders", "Slippage", "Rebalance"],
    blocks: [
      {
        kind: "p",
        text: "An **order** is an instruction to your broker. Beginners hear jargon — market, limit, stop — but in systematic trading you usually encode intent in **`set_target_weights`** and let infrastructure translate to orders.",
      },
      { kind: "visual", id: "order-types" },
      { kind: "h2", text: "How Quant Buffet executes in code" },
      {
        kind: "code",
        lang: "python",
        code: `def on_day(engine, dt):
    # Target 60% SPY, 40% TLT — engine sells/buys to match
    engine.set_target_weights(dt, {"SPY": 0.6, "TLT": 0.4})`,
      },
      {
        kind: "ul",
        items: [
          "Rebalance uses the **daily close** as the reference price.",
          "**Slippage** (2 bps) makes buys slightly more expensive, sells slightly cheaper.",
          "**Commission** (5 bps) charged on notional each fill.",
          "Sells happen **before** buys so cash is available.",
          "Identical weights on consecutive days are **skipped** to reduce churn.",
        ],
      },
      { kind: "h2", text: "Long-only weight math" },
      {
        kind: "table",
        headers: ["Weights", "Interpretation"],
        rows: [
          ["`{\"SPY\": 1.0}`", "100% in SPY, 0% cash"],
          ["`{\"SPY\": 0.5, \"TLT\": 0.5}`", "Fully invested, equal split"],
          ["`{\"SPY\": 0.6, \"TLT\": 0.3}`", "90% invested, 10% cash"],
          ["`{}` or all zeros", "Move to cash (if engine had positions)"],
        ],
      },
    ],
  },
  {
    slug: "metrics-debug",
    title: "Performance metrics & debugging",
    subtitle: "Sharpe, drawdown, CAGR — and fixing the errors you will see in the lab.",
    order: 6,
    duration: "20 min",
    topics: ["Sharpe", "Drawdown", "Debug"],
    blocks: [
      {
        kind: "p",
        text: "A backtest without **metrics** is just a chart. Quant Buffet reports risk-adjusted statistics so you can compare strategies — and provides an **AI debugger** when code breaks.",
      },
      { kind: "visual", id: "metrics-explorer" },
      { kind: "h2", text: "Metrics glossary" },
      {
        kind: "table",
        headers: ["Metric", "What it tells you", "Healthy scepticism"],
        rows: [
          ["CAGR", "Average yearly growth if path repeated", "One great decade can inflate it"],
          ["Volatility", "How bumpy the ride is", "Low vol can mean hidden leverage"],
          ["Sharpe", "Return per unit of risk", "Meaningless if only 2 years of data"],
          ["Max drawdown", "Worst peak-to-trough loss", "Can you hold through it live?"],
          ["Alpha / Beta", "Excess return vs SPY; market sensitivity", "Proxy benchmark ≠ your live book"],
          ["Win rate", "% of positive days", "High win rate can still lose money"],
        ],
      },
      { kind: "h2", text: "Debugging workflow" },
      {
        kind: "ol",
        items: [
          "Read the **error message** and line number in the lab panel.",
          "Open the **syntax cheat sheet** — compare to required `ASSETS` + `make_on_day`.",
          "Click **Ask AI for syntax** — step-by-step fixes with copy-paste snippets.",
          "Consult **API docs** for imports, whitelist symbols, and template examples.",
          "Re-run with a **shorter ASSETS list** and later `start` date to isolate data issues.",
        ],
      },
      {
        kind: "code",
        lang: "python",
        code: `# After a local or lab run
metrics = compute_metrics(result.equity, benchmark=spy_bh, trades_count=len(result.trades))
print(metrics["sharpe"], metrics["max_drawdown"])`,
      },
    ],
  },
  {
    slug: "classic-strategies",
    title: "Classic strategies in the library",
    subtitle: "Momentum, trend, mean reversion, risk parity — the patterns behind 1,700+ Quant Buffet strategies.",
    order: 7,
    duration: "22 min",
    topics: ["Momentum", "Mean reversion", "Templates"],
    blocks: [
      {
        kind: "p",
        text: "Most published quant ideas fall into a **small set of families**. Quant Buffet encodes them as **`backtest.templates`** and as custom code in the strategy library. Recognizing the family helps you read any article faster.",
      },
      { kind: "visual", id: "strategy-map" },
      { kind: "h2", text: "Template cheat sheet" },
      {
        kind: "table",
        headers: ["Template", "Economic story", "Library share"],
        rows: [
          ["`dual_momentum`", "Pick best asset, but go to cash if trend weak", "~35% of catalog"],
          ["`abs_momentum`", "Own recent winners equally", "~19%"],
          ["`momentum_rotation`", "Rotate into top-N performers monthly", "~14%"],
          ["`sma_trend`", "Only hold assets above long average", "~13%"],
          ["`equal_weight`", "Diversify naively, rebalance", "~11%"],
          ["`mean_reversion`", "Buy oversold z-scores", "~6%"],
          ["`vol_target` / `risk_parity`", "Scale or balance by volatility", "Rare but important"],
        ],
      },
      { kind: "h2", text: "Your first hands-on path" },
      {
        kind: "ol",
        items: [
          "Finish **Lesson 1–6** checklists.",
          "Open **API docs → Examples** and paste the minimal SMA strategy into the lab.",
          "Browse **Strategy Library** filtered by momentum or mean reversion.",
          "Change `ASSETS` to a `MULTI_ASSET` book and re-run — watch Sharpe vs drawdown.",
          "Read the **academic paper** linked on the strategy page — compare proxy to original.",
        ],
      },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.templates import make_dual_momentum

ASSETS = ["SPY", "EFA", "EEM", "TLT", "GLD", "BIL"]

def make_on_day(prices):
    return make_dual_momentum(prices, ASSETS, {"lookback": 252, "top_n": 1})`,
      },
      {
        kind: "checklist",
        title: "Course complete — you can now",
        items: [
          "Explain how **daily data** flows into **`make_on_day`**.",
          "Name major **asset classes** and pick ETF proxies from universes.",
          "Describe **broker / venue / platform** layers and cost models.",
          "Contrast **order types** with Quant Buffet's weight-based execution.",
          "Interpret **Sharpe & drawdown** and fix common lab errors.",
          "Identify **momentum, trend, mean reversion, and risk** templates in the library.",
        ],
      },
      {
        kind: "warn",
        text: "Graduation means you can learn responsibly — not that any strategy is ready for live capital. Paper trade, start small, and keep studying.",
      },
    ],
  },
];

export function getEnLesson(slug: string): LearnLesson | undefined {
  return EN_LESSONS.find((l) => l.slug === slug);
}
