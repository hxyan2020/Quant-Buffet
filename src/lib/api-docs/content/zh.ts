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

export const ZH_DOC_PAGES: DocPage[] = [
  {
    slug: "overview",
    title: "概览",
    description: "Quant Buffet 回测 API 是什么，以及实验室策略的基本结构。",
    order: 1,
    blocks: [
      {
        kind: "p",
        text: "Quant Buffet 策略在 **Python 沙箱** 中运行，使用内置的 `backtest.*` 包。你编写每日调仓逻辑；引擎模拟成交、跟踪权益曲线并计算绩效指标。",
      },
      { kind: "h2", text: "你需要编写的内容" },
      {
        kind: "ul",
        items: [
          "**模块级 `ASSETS`** — ETF/加密货币代码列表（最多 15 个，仅限白名单）。",
          "**`make_on_day(prices)`** — 从价格面板构建信号，返回 `(on_day, ready)`。",
          "**`on_day(engine, dt)`** — 每个交易日调用；通过 `engine.set_target_weights()` 调仓。",
          "**`ready`** — 信号首次有效的日期（通常在最长回看窗口之后）。",
        ],
      },
      { kind: "h2", text: "执行流程" },
      {
        kind: "ol",
        items: [
          "沙箱验证 import 与 AST（你的代码不能进行文件 I/O 或网络访问）。",
          "`load_daily_prices(ASSETS, start=…)` 下载或读取缓存的 OHLCV。",
          "`make_on_day(prices)` 返回每日回调函数与预热日期。",
          "`PortfolioEngine.run(on_day, start=ready)` 遍历日历并记录交易。",
          "`compute_metrics(equity, …)` 产出 CAGR、Sharpe、回撤等。",
        ],
      },
      { kind: "h2", text: "最小可运行策略" },
      {
        kind: "note",
        text: "每个实验室策略都遵循此骨架。四 ETF 月度 SMA 趋势 — 可直接复制并修改。",
      },
      { kind: "code", lang: "python", code: MINIMAL_STRATEGY },
      { kind: "h2", text: "文档目录" },
      {
        kind: "ul",
        items: [
          "**Lab contract** — 必需函数、返回类型、常见错误。",
          "**Data API** — `load_daily_prices`、缓存、面板结构。",
          "**Engine API** — `PortfolioEngine`、`EngineConfig`、`set_target_weights`。",
          "**Metrics API** — `compute_metrics` 输出字段。",
          "**Sandbox rules** — 允许的 import、大小限制、禁用的 builtins。",
          "**Universes** — ETF 白名单与命名资产池。",
          "**Templates** — `backtest.templates` 中的预置 `make_*` 工厂。",
          "**Examples** — 动量、均值回归与模板示例。",
        ],
      },
    ],
  },
  {
    slug: "lab-contract",
    title: "实验室合约",
    description: "必需符号、函数签名，以及 make_on_day → on_day 模式。",
    order: 2,
    blocks: [
      {
        kind: "p",
        text: "沙箱加载器（`backtest/sandbox_runner.py`）要求 **固定合约**。缺少或改名的部分会在加载价格前以 `ContractError` 失败。",
      },
      { kind: "h2", text: "ASSETS（必需）" },
      { kind: "p", text: "在 **模块作用域** 定义（不要放在函数内部）：" },
      { kind: "code", lang: "python", code: 'ASSETS = ["SPY", "QQQ", "TLT", "GLD", "BIL"]' },
      {
        kind: "ul",
        items: [
          "每个代码必须在 **Quant Buffet 白名单** 中（见 Universes 页）。",
          "每个策略最多 **15 个** 代码。",
          "加密货币代理 `BTC-USD`、`ETH-USD` 可通过 yfinance 使用。",
          "顺序无关；缺失历史按列前向填充。",
        ],
      },
      { kind: "h2", text: "make_on_day(prices)" },
      { kind: "p", text: "签名与返回值：" },
      {
        kind: "code",
        lang: "python",
        code: `def make_on_day(prices: pd.DataFrame):
    # prices: 行 = 交易日, 列 = ASSETS 代码 (收盘价 float)
    ...
    return on_day, ready`,
      },
      {
        kind: "table",
        headers: ["返回值", "类型", "说明"],
        rows: [
          ["`on_day`", "`Callable[[PortfolioEngine, pd.Timestamp], None]`", "回测窗口内每个日期调用一次。"],
          ["`ready`", "`pd.Timestamp | None`", "信号首次存在的日期。通过 `engine.run(..., start=ready)` 从此开始。"],
        ],
      },
      {
        kind: "warn",
        text: "若 `ready` 为 `None` 或始终无效，沙箱报错：*Signal never ready — check lookbacks / ASSETS history.*",
      },
      { kind: "h2", text: "on_day(engine, dt)" },
      {
        kind: "ul",
        items: [
          "接收 **`PortfolioEngine`** 实例与当前 **`pd.Timestamp`**。",
          "计算目标权重并调用 **`engine.set_target_weights(dt, weights)`**。",
          "权重为 **仅做多**；总和须 **≤ 1.0**（剩余为现金）。",
          "用 **`on_day` 闭包内的 state dict** 控制调仓频率（如按月）。",
          "早期日期用 `if indicator.loc[dt].isna().all(): return` 跳过。",
        ],
      },
      { kind: "h2", text: "推荐 import" },
      { kind: "code", lang: "python", code: IMPORTS },
      { kind: "h2", text: "反模式" },
      {
        kind: "ul",
        items: [
          "把 `ASSETS` 放在 `make_on_day` 内部 — 加载器只读模块级 `ASSETS`。",
          "从 `make_on_day` 返回权重而非 `on_day` 回调。",
          "每天以相同权重调用 `set_target_weights` — 引擎会跳过无变化调仓，但浮点噪声仍可能拖慢运行。",
          "使用白名单外代码（如个股）— 加载时会被拒绝。",
          "import `os`、`sys`、`subprocess` 或第三方包 — AST 验证会拦截。",
        ],
      },
    ],
  },
  {
    slug: "data-api",
    title: "数据 API",
    description: "load_daily_prices 与价格面板约定。",
    order: 3,
    blocks: [
      {
        kind: "p",
        text: "行情数据在 **`backtest.data`**。实验室使用 Yahoo Finance 的 **调整后日收盘价**，缓存在 `backtest/data_cache/` 以便重复运行。",
      },
      { kind: "h2", text: "load_daily_prices" },
      { kind: "code", lang: "python", code: LOAD_PRICES },
      {
        kind: "table",
        headers: ["参数", "默认", "说明"],
        rows: [
          ["`symbols`", "—", "代码列表，如 `[\"SPY\", \"TLT\"]`。"],
          ["`start`", "`\"2000-01-01\"`", "起始日期（含）。"],
          ["`end`", "`None`", "可选结束；`None` 表示最新。"],
          ["`use_cache`", "`True`", "按代码与日期范围读写 CSV 缓存。"],
          ["`strict`", "`False`", "`True` 时首个失败即抛错。"],
        ],
      },
      { kind: "h2", text: "返回值" },
      {
        kind: "ul",
        items: [
          "**`pd.DataFrame`**，索引为 **`DatetimeIndex`**（无时区）。",
          "每个成功加载的代码一列 **float**。",
          "序列内缺失日 **前向填充**；IPO 前历史保持 NaN。",
          "除非 `strict=True`，失败代码会被跳过；部分失败时 `prices.attrs[\"load_errors\"]` 记录错误。",
        ],
      },
      { kind: "h2", text: "load_price_panel（可选）" },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.data import load_price_panel

prices, missing = load_price_panel(["SPY", "XYZ"], start="2010-01-01")
# missing: 无数据的代码列表`,
      },
      {
        kind: "note",
        text: "实验室沙箱通常 **不需要** 你自己调用 `load_daily_prices` — 运行器会根据 `ASSETS` 加载。本地脚本或批量回测时使用此 API。",
      },
    ],
  },
  {
    slug: "engine-api",
    title: "引擎 API",
    description: "PortfolioEngine、EngineConfig、成交与 BacktestResult。",
    order: 4,
    blocks: [
      {
        kind: "p",
        text: "**`backtest.engine`** 实现 **日频、仅做多** 模拟器，含现金、佣金与滑点。策略主要通过 **`set_target_weights`** 交互。",
      },
      { kind: "h2", text: "EngineConfig" },
      {
        kind: "code",
        lang: "python",
        code: `@dataclass
class EngineConfig:
    initial_cash: float = 100_000.0
    commission_bps: float = 5.0
    slippage_bps: float = 2.0`,
      },
      { kind: "p", text: "实验室默认：**`initial_cash=100_000`**、**`commission_bps=5`**、**`slippage_bps=2`**。" },
      { kind: "h2", text: "PortfolioEngine" },
      { kind: "code", lang: "python", code: ENGINE_USAGE },
      { kind: "h2", text: "set_target_weights(dt, weights)" },
      {
        kind: "ul",
        items: [
          "`weights`：`dict[str, float]`，符号 → 目标 **权益占比**（0–1）。",
          "未出现在 dict 中的符号视为 **0%**。",
          "若权重和 **> 1**，会 **归一化** 为 1。",
          "目标不变时 **跳过调仓**（1e-6 容差）— 避免均值回归策略的粉尘交易。",
          "先卖后买释放现金；现金不足时买单可能缩量。",
        ],
      },
      { kind: "h2", text: "BacktestResult" },
      {
        kind: "table",
        headers: ["字段", "类型", "说明"],
        rows: [
          ["`equity`", "`pd.Series`", "组合总价值序列。"],
          ["`holdings`", "`pd.DataFrame`", "各日持仓股数。"],
          ["`trades`", "`list[Trade]`", "每笔成交含方向、股数、价格、佣金。"],
          ["`cash`", "`pd.Series`", "现金余额序列。"],
        ],
      },
    ],
  },
  {
    slug: "metrics-api",
    title: "指标 API",
    description: "compute_metrics 字段与相对基准统计。",
    order: 5,
    blocks: [
      { kind: "p", text: "**`backtest.metrics.compute_metrics`** 将权益曲线转为实验室 UI 中的统计（CAGR、Sharpe、回撤等）。" },
      { kind: "h2", text: "用法" },
      { kind: "code", lang: "python", code: METRICS_USAGE },
      { kind: "h2", text: "主要输出字段" },
      {
        kind: "table",
        headers: ["键", "说明"],
        rows: [
          ["`cagr`", "复合年化收益率。"],
          ["`volatility`", "日收益年化标准差。"],
          ["`sharpe`", "超额收益 / 波动率。"],
          ["`sortino`", "收益 / 下行波动。"],
          ["`max_drawdown`", "最大回撤（负分数）。"],
          ["`calmar`", "CAGR / |max_drawdown|。"],
          ["`daily_win_rate`", "正收益日占比。"],
          ["`trades`", "成交笔数。"],
        ],
      },
      {
        kind: "note",
        text: "实验室以 **SPY** 买入持有为基准（若无则用 `ASSETS` 第一项）。百分比展示由服务端 `displayMetrics` 格式化。",
      },
    ],
  },
  {
    slug: "sandbox-rules",
    title: "沙箱规则",
    description: "允许的 import、builtins、限制与错误类型。",
    order: 6,
    blocks: [
      {
        kind: "p",
        text: "草稿预览与批量实验室在 **`backtest/sandbox_runner.py`** 中执行代码。源码经 **`ast`** 解析、清理引导代码后，在受限命名空间中 **`exec`**。",
      },
      { kind: "h2", text: "允许的 import 根模块" },
      {
        kind: "ul",
        items: [
          "`backtest.*`",
          "`numpy` / `np`、`pandas` / `pd`",
          "`math`、`json`、`typing`、`collections`、`dataclasses`",
          "`functools`、`itertools`、`datetime`、`re`、`statistics`、`decimal`",
        ],
      },
      { kind: "h2", text: "禁止" },
      {
        kind: "ul",
        items: [
          "允许列表外的标准库（`os`、`sys`、`subprocess` 等）。",
          "第三方包（`requests`、`sklearn` 等）。",
          "调用 `eval`、`exec`、`open` 等。",
          "`async` / `await` 语法。",
          "源码超过 **80 KB**。",
        ],
      },
      { kind: "h2", text: "运行时限制" },
      {
        kind: "table",
        headers: ["限制", "值"],
        rows: [
          ["`ASSETS` 最多代码数", "15"],
          ["最少价格行数", "30"],
          ["最少权益曲线长度", "20"],
          ["图表返回点数", "90（降采样）"],
        ],
      },
    ],
  },
  {
    slug: "universes",
    title: "资产池与白名单",
    description: "命名 ETF 池与沙箱 WHITELIST。",
    order: 7,
    blocks: [
      {
        kind: "p",
        text: "**`backtest.universes`** 定义股票、行业、国家、债券、商品与加密货币的 ETF **代理**。仅 **`WHITELIST`**（及 `BTC-USD` / `ETH-USD`）中的代码可用于 `ASSETS`。",
      },
      { kind: "h2", text: "命名资产池" },
      {
        kind: "table",
        headers: ["常量", "用途"],
        rows: [
          ["`US_EQUITY`", "SPY, QQQ, IWM"],
          ["`US_SECTORS_FULL`", "行业 ETF"],
          ["`GLOBAL_EQUITY`", "全球股票"],
          ["`BONDS` / `CREDIT`", "利率与信用"],
          ["`COMMODITIES`", "商品"],
          ["`RISK_ON_OFF`", "风险偏好切换"],
          ["`CRYPTO_PROXY`", "BTC-USD, ETH-USD"],
        ],
      },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.universes import US_SECTORS_FULL

ASSETS = list(US_SECTORS_FULL)[:15]`,
      },
    ],
  },
  {
    slug: "templates",
    title: "模板",
    description: "backtest.templates 中的预置 make_* 工厂。",
    order: 8,
    blocks: [
      {
        kind: "p",
        text: "**`backtest.templates`** 提供可复用的 **`make_*`** 函数，返回 `(on_day, ready)` — 与 `make_on_day` 合约相同。",
      },
      { kind: "h2", text: "用法模式" },
      { kind: "code", lang: "python", code: TEMPLATE_SMA },
      {
        kind: "table",
        headers: ["函数", "思路", "主要参数"],
        rows: [
          ["`make_sma_trend`", "价格在 SMA 上方做多", "`sma_days`"],
          ["`make_dual_ma`", "快线在慢线上方", "`fast`, `slow`"],
          ["`make_abs_momentum`", "按 trailing return 排名", "`lookback`, `top_n`"],
          ["`make_dual_momentum`", "绝对 + 相对动量过滤", "`lookback`, `top_n`"],
          ["`make_momentum_rotation`", "月度轮动赢家", "`lookback`, `top_n`"],
          ["`make_mean_reversion`", "买入近期弱势", "`lookback`, `entry_z`"],
          ["`make_vol_target`", "波动率目标缩放", "`lookback`, `target_vol`"],
          ["`make_risk_parity`", "逆波动率加权", "`lookback`"],
        ],
      },
    ],
  },
  {
    slug: "examples",
    title: "示例",
    description: "可在实验室直接使用的策略模式。",
    order: 9,
    blocks: [
      { kind: "h2", text: "1. 从零编写 SMA 趋势" },
      { kind: "code", lang: "python", code: MINIMAL_STRATEGY },
      { kind: "h2", text: "2. 模板 SMA 趋势" },
      { kind: "code", lang: "python", code: TEMPLATE_SMA },
      { kind: "h2", text: "3. 横截面均值回归" },
      { kind: "code", lang: "python", code: MEAN_REVERSION },
    ],
  },
];

export function getZhDocPage(slug: string): DocPage | undefined {
  return ZH_DOC_PAGES.find((p) => p.slug === slug);
}

export function getZhDocSlugs(): string[] {
  return ZH_DOC_PAGES.map((p) => p.slug);
}
