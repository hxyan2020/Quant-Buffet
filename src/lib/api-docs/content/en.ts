import type { DocPage } from "../types";
import {
  ENGINE_USAGE,
  IMPORTS,
  LOAD_PRICES,
  MEAN_REVERSION,
  METRICS_USAGE,
  MINIMAL_STRATEGY,
  TEMPLATE_SMA,
} from "../shared-code";

export const EN_DOC_PAGES: DocPage[] = [
  {
    slug: "overview",
    title: "Overview",
    description: "What the Quant Buffet backtest API is and how lab strategies are structured.",
    order: 1,
    blocks: [
      {
        kind: "p",
        text: "Quant Buffet strategies run inside a **Python sandbox** that uses the in-house `backtest.*` package. You write daily-rebalance logic; the engine simulates fills, tracks equity, and computes performance metrics.",
      },
      { kind: "h2", text: "What you write" },
      {
        kind: "ul",
        items: [
          "**Module-level `ASSETS`** — list of ETF/crypto tickers (max 15, whitelist only).",
          "**`make_on_day(prices)`** — builds signals from a price panel and returns `(on_day, ready)`.",
          "**`on_day(engine, dt)`** — called each trading day; call `engine.set_target_weights()` to rebalance.",
          "**`ready`** — first date when signals are valid (usually after your longest lookback).",
        ],
      },
      { kind: "h2", text: "Execution flow" },
      {
        kind: "ol",
        items: [
          "Sandbox validates imports and AST (no file I/O, no network from your code).",
          "`load_daily_prices(ASSETS, start=…)` downloads or reads cached OHLCV.",
          "`make_on_day(prices)` returns your daily callback and warmup date.",
          "`PortfolioEngine.run(on_day, start=ready)` walks the calendar and records trades.",
          "`compute_metrics(equity, …)` produces CAGR, Sharpe, drawdown, etc.",
        ],
      },
      { kind: "h2", text: "Minimal working strategy" },
      {
        kind: "note",
        text: "Every lab strategy follows this skeleton. Monthly rebalance SMA trend on four ETFs — copy and adapt.",
      },
      { kind: "code", lang: "python", code: MINIMAL_STRATEGY },
      { kind: "h2", text: "Documentation map" },
      {
        kind: "ul",
        items: [
          "**Lab contract** — required functions, return types, common mistakes.",
          "**Data API** — `load_daily_prices`, caching, panel shape.",
          "**Engine API** — `PortfolioEngine`, `EngineConfig`, `set_target_weights`.",
          "**Metrics API** — `compute_metrics` output fields.",
          "**Sandbox rules** — allowed imports, size limits, blocked builtins.",
          "**Universes** — ETF whitelist and named books.",
          "**Templates** — pre-built `make_*` factories in `backtest.templates`.",
          "**Examples** — momentum, mean reversion, and template-based patterns.",
        ],
      },
    ],
  },
  {
    slug: "lab-contract",
    title: "Lab contract",
    description: "Required symbols, function signatures, and the make_on_day → on_day pattern.",
    order: 2,
    blocks: [
      {
        kind: "p",
        text: "The sandbox loader (`backtest/sandbox_runner.py`) expects a **fixed contract**. Strategies that omit or rename these pieces fail with `ContractError` before any prices load.",
      },
      { kind: "h2", text: "ASSETS (required)" },
      {
        kind: "p",
        text: "Define at **module scope** (not inside a function):",
      },
      { kind: "code", lang: "python", code: 'ASSETS = ["SPY", "QQQ", "TLT", "GLD", "BIL"]' },
      {
        kind: "ul",
        items: [
          "Each ticker must be in the **Quant Buffet whitelist** (see Universes page).",
          "Maximum **15 symbols** per strategy.",
          "Crypto proxies `BTC-USD` and `ETH-USD` are allowed via yfinance.",
          "Order does not matter; missing history is forward-filled per column.",
        ],
      },
      { kind: "h2", text: "make_on_day(prices)" },
      {
        kind: "p",
        text: "Signature and return value:",
      },
      {
        kind: "code",
        lang: "python",
        code: `def make_on_day(prices: pd.DataFrame):
    # prices: rows = trading dates, columns = ASSETS tickers (float close)
    ...
    return on_day, ready`,
      },
      {
        kind: "table",
        headers: ["Return", "Type", "Description"],
        rows: [
          ["`on_day`", "`Callable[[PortfolioEngine, pd.Timestamp], None]`", "Invoked once per date in the backtest window."],
          ["`ready`", "`pd.Timestamp | None`", "First date when signals exist. Backtest starts here via `engine.run(..., start=ready)`."],
        ],
      },
      {
        kind: "warn",
        text: "If `ready` is `None` or never becomes valid, the sandbox raises: *Signal never ready — check lookbacks / ASSETS history.*",
      },
      { kind: "h2", text: "on_day(engine, dt)" },
      {
        kind: "ul",
        items: [
          "Receive the live **`PortfolioEngine`** instance and the current **`pd.Timestamp`**.",
          "Compute target portfolio weights and pass them to **`engine.set_target_weights(dt, weights)`**.",
          "Weights are **long-only**; sum must be **≤ 1.0** (remainder stays in cash).",
          "Use a **state dict** closed over by `on_day` to throttle rebalance frequency (e.g. monthly).",
          "Guard early dates with `if indicator.loc[dt].isna().all(): return`.",
        ],
      },
      { kind: "h2", text: "Recommended imports" },
      { kind: "code", lang: "python", code: IMPORTS },
      { kind: "h2", text: "Anti-patterns" },
      {
        kind: "ul",
        items: [
          "Putting `ASSETS` inside `make_on_day` — the loader reads module-level `ASSETS` only.",
          "Returning weights from `make_on_day` instead of an `on_day` callback.",
          "Calling `set_target_weights` every day with identical weights — the engine skips no-ops, but churny float noise still slows runs.",
          "Using tickers outside the whitelist (e.g. single stocks) — blocked at load time.",
          "Importing `os`, `sys`, `subprocess`, or third-party packages — blocked by AST validation.",
        ],
      },
    ],
  },
  {
    slug: "data-api",
    title: "Data API",
    description: "load_daily_prices and price panel conventions.",
    order: 3,
    blocks: [
      {
        kind: "p",
        text: "Market data lives in **`backtest.data`**. The lab uses **adjusted daily closes** from Yahoo Finance, cached under `backtest/data_cache/` for repeat runs.",
      },
      { kind: "h2", text: "load_daily_prices" },
      { kind: "code", lang: "python", code: LOAD_PRICES },
      {
        kind: "table",
        headers: ["Parameter", "Default", "Description"],
        rows: [
          ["`symbols`", "—", "List of ticker strings, e.g. `[\"SPY\", \"TLT\"]`."],
          ["`start`", "`\"2000-01-01\"`", "Inclusive start date (ISO string)."],
          ["`end`", "`None`", "Optional exclusive end; `None` means latest available."],
          ["`use_cache`", "`True`", "Read/write CSV cache files keyed by symbol and date range."],
          ["`strict`", "`False`", "If `True`, raise on first symbol failure instead of skipping."],
        ],
      },
      { kind: "h2", text: "Return value" },
      {
        kind: "ul",
        items: [
          "**`pd.DataFrame`** indexed by **`DatetimeIndex`** (timezone-naive).",
          "One **float column per symbol** that loaded successfully.",
          "Missing days within a series are **forward-filled**; pre-IPO history stays NaN until first print.",
          "Failed symbols are omitted unless `strict=True`. Partial failures attach `prices.attrs[\"load_errors\"]` when some symbols fail.",
        ],
      },
      { kind: "h2", text: "load_price_panel (optional)" },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.data import load_price_panel

prices, missing = load_price_panel(["SPY", "XYZ"], start="2010-01-01")
# missing: list of symbols with no data`,
      },
      {
        kind: "note",
        text: "In the lab sandbox you normally do not call `load_daily_prices` yourself — the runner loads `ASSETS` for you. Use this API when running scripts locally or in batch backtests.",
      },
      { kind: "h2", text: "Working with the panel" },
      {
        kind: "ul",
        items: [
          "Filter columns: `cols = [c for c in ASSETS if c in prices.columns]`.",
          "Rolling windows: `prices[cols].rolling(20, min_periods=20).mean()`.",
          "Cross-sectional ranks: `rets.rank(axis=1, ascending=False)`.",
          "Align to engine dates: `series.reindex(engine_index).ffill()`.",
        ],
      },
    ],
  },
  {
    slug: "engine-api",
    title: "Engine API",
    description: "PortfolioEngine, EngineConfig, trades, and BacktestResult.",
    order: 4,
    blocks: [
      {
        kind: "p",
        text: "**`backtest.engine`** implements a **daily, long-only** simulator with cash, commission, and slippage. Strategies interact almost exclusively through **`set_target_weights`**.",
      },
      { kind: "h2", text: "EngineConfig" },
      {
        kind: "code",
        lang: "python",
        code: `@dataclass
class EngineConfig:
    initial_cash: float = 100_000.0
    commission_bps: float = 5.0   # basis points on notional per fill
    slippage_bps: float = 2.0     # basis points price impact per side`,
      },
      {
        kind: "p",
        text: "The lab sandbox uses **`initial_cash=100_000`**, **`commission_bps=5`**, **`slippage_bps=2`** by default.",
      },
      { kind: "h2", text: "PortfolioEngine" },
      { kind: "code", lang: "python", code: ENGINE_USAGE },
      { kind: "h2", text: "set_target_weights(dt, weights)" },
      {
        kind: "ul",
        items: [
          "`weights`: `dict[str, float]` mapping symbol → target **fraction of equity** (0–1).",
          "Symbols not in the dict are treated as **0%**.",
          "If weights sum to **> 1**, they are **normalized** to sum to 1.",
          "Rebalance is **skipped** when targets are unchanged (within 1e-6) — avoids dust trades on mean-reversion strategies.",
          "Sells execute before buys to free cash; buys may scale down if cash is insufficient.",
        ],
      },
      { kind: "h2", text: "BacktestResult" },
      {
        kind: "table",
        headers: ["Field", "Type", "Description"],
        rows: [
          ["`equity`", "`pd.Series`", "Total portfolio value over time."],
          ["`holdings`", "`pd.DataFrame`", "Share counts per symbol by date."],
          ["`trades`", "`list[Trade]`", "Every fill with side, shares, price, commission."],
          ["`cash`", "`pd.Series`", "Cash balance over time."],
          ["`benchmark`", "`pd.Series | None`", "Optional benchmark series (set by caller)."],
          ["`meta`", "`dict`", "Extra metadata bag."],
        ],
      },
      { kind: "h2", text: "Trade" },
      {
        kind: "code",
        lang: "python",
        code: `@dataclass
class Trade:
    date: str       # "YYYY-MM-DD"
    symbol: str
    side: str       # "buy" | "sell"
    shares: float
    price: float    # after slippage
    value: float    # notional
    commission: float`,
      },
    ],
  },
  {
    slug: "metrics-api",
    title: "Metrics API",
    description: "compute_metrics fields and benchmark-relative stats.",
    order: 5,
    blocks: [
      {
        kind: "p",
        text: "**`backtest.metrics.compute_metrics`** turns an equity curve into the statistics shown in the lab UI (CAGR, Sharpe, drawdown, etc.).",
      },
      { kind: "h2", text: "Usage" },
      { kind: "code", lang: "python", code: METRICS_USAGE },
      { kind: "h2", text: "Core output fields" },
      {
        kind: "table",
        headers: ["Key", "Description"],
        rows: [
          ["`start`, `end`", "First and last equity dates (strings)."],
          ["`years`", "Calendar years spanned."],
          ["`start_equity`, `end_equity`", "Dollar values at start/end."],
          ["`total_return`", "End/start − 1 (not annualised)."],
          ["`cagr`", "Compound annual growth rate."],
          ["`volatility`", "Annualised standard deviation of daily returns."],
          ["`sharpe`", "Excess return / volatility (annualised, `risk_free` subtracted)."],
          ["`sortino`", "Return / downside deviation."],
          ["`max_drawdown`", "Worst peak-to-trough (negative fraction)."],
          ["`calmar`", "CAGR / |max_drawdown|."],
          ["`daily_win_rate`", "Fraction of positive return days."],
          ["`trades`", "Trade count passed through from the engine."],
        ],
      },
      { kind: "h2", text: "Benchmark fields (when benchmark provided)" },
      {
        kind: "ul",
        items: [
          "`benchmark_total_return`, `benchmark_cagr`",
          "`alpha` — annualised Jensen's alpha vs benchmark daily returns",
          "`beta` — covariance / variance vs benchmark",
        ],
      },
      {
        kind: "note",
        text: "The lab builds a buy-and-hold benchmark from **SPY** when available, otherwise the first asset in `ASSETS`. Display strings (percent formatting) are applied server-side in `displayMetrics`.",
      },
    ],
  },
  {
    slug: "sandbox-rules",
    title: "Sandbox rules",
    description: "Allowed imports, builtins, limits, and error types.",
    order: 6,
    blocks: [
      {
        kind: "p",
        text: "Draft-preview and batch lab runs execute your code in **`backtest/sandbox_runner.py`**. Source is parsed with **`ast`**, stripped of bootstrap boilerplate, then **`exec`'d** with a restricted namespace.",
      },
      { kind: "h2", text: "Allowed import roots" },
      {
        kind: "ul",
        items: [
          "`backtest.*` — data, engine, metrics, templates, universes",
          "`numpy` / `np`, `pandas` / `pd`",
          "`math`, `json`, `typing`, `collections`, `dataclasses`",
          "`functools`, `itertools`, `datetime`, `re`, `statistics`, `decimal`",
          "`__future__`",
        ],
      },
      { kind: "h2", text: "Blocked" },
      {
        kind: "ul",
        items: [
          "Standard library modules outside the allow-list (`os`, `sys`, `pathlib`, `subprocess`, …).",
          "Third-party packages (`requests`, `sklearn`, `matplotlib`, …).",
          "Calls to `eval`, `exec`, `compile`, `open`, `input`, `breakpoint`.",
          "`async` / `await` syntax.",
          "Source files larger than **80 KB**.",
        ],
      },
      {
        kind: "note",
        text: "Generated strategy files may include a `sys.path` bootstrap; `backtest/lab_sanitize.py` removes it before validation. Do not rely on that in hand-written lab code.",
      },
      { kind: "h2", text: "Safe builtins" },
      {
        kind: "p",
        text: "A subset of Python builtins is injected: `abs`, `min`, `max`, `sum`, `len`, `range`, `enumerate`, `zip`, `map`, `filter`, `sorted`, container types, `round`, `print`, `isinstance`, `hasattr`, `type`, and common exceptions.",
      },
      { kind: "h2", text: "Runtime limits" },
      {
        kind: "table",
        headers: ["Limit", "Value"],
        rows: [
          ["Max symbols in `ASSETS`", "15"],
          ["Min price history", "30 rows after load"],
          ["Min equity curve length", "20 points after run"],
          ["Equity chart points returned", "90 (downsampled)"],
          ["Default backtest start (payload)", "2000-01-01 or lab UI date"],
        ],
      },
      { kind: "h2", text: "Common error types" },
      {
        kind: "table",
        headers: ["Type", "Typical cause"],
        rows: [
          ["`SyntaxError`", "Invalid Python; line number returned when available."],
          ["`ContractError`", "Missing `make_on_day` or wrong return shape."],
          ["`ValueError`", "Bad import, whitelist symbol, empty ASSETS, signal never ready."],
          ["`ImportError`", "Blocked module at runtime."],
          ["`RuntimeError`", "No price data loaded for any symbol."],
        ],
      },
    ],
  },
  {
    slug: "universes",
    title: "Universes & whitelist",
    description: "Named ETF books and the WHITELIST used by the sandbox.",
    order: 7,
    blocks: [
      {
        kind: "p",
        text: "**`backtest.universes`** defines liquid ETF **proxies** for equities, sectors, countries, bonds, commodities, and crypto. Only symbols in **`WHITELIST`** (plus `BTC-USD` / `ETH-USD`) can appear in `ASSETS`.",
      },
      { kind: "h2", text: "Named books" },
      {
        kind: "table",
        headers: ["Constant", "Typical use"],
        rows: [
          ["`US_EQUITY`", "SPY, QQQ, IWM"],
          ["`US_SECTORS_FULL`", "XLB … XLRE sector ETFs"],
          ["`GLOBAL_EQUITY`", "SPY, EFA, EEM, VGK, EWJ, FXI"],
          ["`COUNTRY_DM` / `COUNTRY_EM`", "Single-country ETFs"],
          ["`BONDS` / `CREDIT`", "Treasury and credit duration ladder"],
          ["`COMMODITIES`", "GLD, SLV, DBC, USO, …"],
          ["`REAL_ESTATE`", "VNQ, IYR, RWX"],
          ["`MULTI_ASSET`", "Cross-asset balanced mix"],
          ["`RISK_ON_OFF`", "SPY, QQQ, TLT, IEF, GLD, BIL"],
          ["`VOL_PROXY`", "SPY, BIL, VIXY, SVXY"],
          ["`CRYPTO_PROXY`", "BTC-USD, ETH-USD"],
        ],
      },
      { kind: "h2", text: "Using a book in ASSETS" },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.universes import US_SECTORS_FULL, BONDS

ASSETS = list(US_SECTORS_FULL) + ["TLT", "GLD", "BIL"]
# Still subject to max 15 symbols — slice or subset as needed`,
      },
      { kind: "h2", text: "WHITELIST" },
      {
        kind: "p",
        text: "`WHITELIST` is the union of all named books plus additional liquid ETFs (VTI, VOO, DIA, ACWI, …). Single stocks and illiquid tickers are **not** supported in the lab.",
      },
      {
        kind: "warn",
        text: "Some symbols in `FX_PROXY` (UUP, FXE, …) may fail to load depending on Yahoo availability. Prefer `FX_SAFE` or explicit ETFs you have verified in the cache.",
      },
    ],
  },
  {
    slug: "templates",
    title: "Templates",
    description: "Pre-built make_* factories in backtest.templates.",
    order: 8,
    blocks: [
      {
        kind: "p",
        text: "**`backtest.templates`** provides reusable **`make_*`** functions that return `(on_day, ready)` — the same contract as your own `make_on_day` body. Import and delegate instead of rewriting common patterns.",
      },
      { kind: "h2", text: "Pattern" },
      { kind: "code", lang: "python", code: TEMPLATE_SMA },
      { kind: "h2", text: "Available factories" },
      {
        kind: "table",
        headers: ["Function", "Idea", "Key params"],
        rows: [
          ["`make_sma_trend`", "Long assets above SMA", "`sma_days` (default 200)"],
          ["`make_dual_ma`", "Fast MA > slow MA", "`fast`, `slow`"],
          ["`make_abs_momentum`", "Rank by trailing return, top N", "`lookback`, `top_n`, `cash_symbol`"],
          ["`make_dual_momentum`", "Absolute + relative momentum filter", "`lookback`, `top_n`"],
          ["`make_momentum_rotation`", "Monthly rotate into winners", "`lookback`, `top_n`"],
          ["`make_equal_weight`", "Static equal weight rebalance", "`rebalance` cadence in params"],
          ["`make_mean_reversion`", "Buy recent losers (z-score)", "`lookback`, `entry_z`"],
          ["`make_vol_target`", "Scale exposure to vol target", "`lookback`, `target_vol`"],
          ["`make_risk_parity`", "Inverse-vol weights", "`lookback`"],
        ],
      },
      {
        kind: "note",
        text: "Templates rebalance on **month boundaries** or **daily** depending on the factory — read the source in `backtest/templates.py` when tuning turnover.",
      },
      { kind: "h2", text: "Custom params" },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.templates import make_abs_momentum

ASSETS = ["SPY", "EFA", "EEM", "TLT", "GLD", "BIL"]

def make_on_day(prices: pd.DataFrame):
    return make_abs_momentum(
        prices,
        ASSETS,
        {"lookback": 126, "top_n": 3, "cash_symbol": "BIL"},
    )`,
      },
    ],
  },
  {
    slug: "examples",
    title: "Examples",
    description: "Copy-paste strategy patterns for the lab.",
    order: 9,
    blocks: [
      { kind: "h2", text: "1. SMA trend (from scratch)" },
      { kind: "code", lang: "python", code: MINIMAL_STRATEGY },
      { kind: "h2", text: "2. Template-based SMA trend" },
      { kind: "code", lang: "python", code: TEMPLATE_SMA },
      { kind: "h2", text: "3. Cross-sectional mean reversion" },
      { kind: "code", lang: "python", code: MEAN_REVERSION },
      { kind: "h2", text: "4. Local script (full pipeline)" },
      {
        kind: "code",
        lang: "python",
        code: `${IMPORTS}

ASSETS = ["SPY", "TLT"]

def make_on_day(prices: pd.DataFrame):
    ...

if __name__ == "__main__":
    prices = load_daily_prices(ASSETS, start="2010-01-01")
    on_day, ready = make_on_day(prices)
    engine = PortfolioEngine(prices, EngineConfig())
    result = engine.run(on_day, start=ready)
    print(compute_metrics(result.equity, trades_count=len(result.trades)))`,
      },
      {
        kind: "note",
        text: "Run local scripts from the repo root so `backtest` resolves: `python -m backtest.sandbox_runner` or your strategy file with `PYTHONPATH=.`",
      },
    ],
  },
];

export function getEnDocPage(slug: string): DocPage | undefined {
  return EN_DOC_PAGES.find((p) => p.slug === slug);
}

export function getEnDocSlugs(): string[] {
  return EN_DOC_PAGES.map((p) => p.slug);
}
