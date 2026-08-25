import type { LearnLesson } from "../types";

export const ZH_LESSONS: LearnLesson[] = [
  {
    slug: "intro",
    title: "从零到系统化交易者",
    subtitle: "什么是量化交易、Quant Buffet 如何教学，以及写代码前需要的心态。",
    order: 1,
    duration: "12 分钟",
    topics: ["心态", "工作流", "实验室概览"],
    blocks: [
      {
        kind: "p",
        text: "**量化交易者**用规则、数据和代码——而非直觉——决定买卖。你不需要金融学位，但需要好奇心、基础 Python，以及把每次回测当作**研究**而非盈利承诺的耐心。",
      },
      { kind: "visual", id: "quant-journey" },
      { kind: "h2", text: "什么是「量化」？" },
      {
        kind: "table",
        headers: ["主观交易", "量化 / 系统化交易"],
        rows: [
          ["凭新闻和图表主观判断", "用代码编码规则（若 X 则买 Y）"],
          ["决策难以复现", "相同输入 → 相同信号"],
          ["粗略估计风险", "Sharpe、回撤等统计"],
          ["单一市场叙事", "在库中测试 800+ 学术想法"],
        ],
      },
      {
        kind: "warn",
        text: "Quant Buffet 仅供教育研究。历史回测忽略税费、容量与制度变化。实盘与合规由您自行负责。",
      },
      {
        kind: "checklist",
        title: "进入第 2 课前 — 您应理解",
        items: [
          "量化 = **规则 + 数据 + 模拟**。",
          "实验室策略使用 **日频 ETF 价格** 与 **仅做多** 权重。",
          "第 2–7 课将学习数据、基础设施、订单、指标与经典模式。",
        ],
      },
    ],
  },
  {
    slug: "market-data",
    title: "市场数据基础",
    subtitle: "价格、K 线、调整后收盘价，以及策略每天消费的数据面板。",
    order: 2,
    duration: "18 分钟",
    topics: ["OHLCV", "复权", "面板"],
    blocks: [
      {
        kind: "p",
        text: "每个策略都从 **市场数据** 开始。Quant Buffet 实验室通过 `load_daily_prices()` 加载 **日频调整后收盘价**，并缓存在 `backtest/data_cache/`。",
      },
      { kind: "visual", id: "data-pipeline" },
      { kind: "h2", text: "核心词汇" },
      {
        kind: "table",
        headers: ["术语", "含义", "实验室示例"],
        rows: [
          ["代码 symbol", "标的标识", "`SPY`, `TLT`, `BTC-USD`"],
          ["OHLCV", "开高低收量", "每个交易日一行"],
          ["调整后收盘", "分红拆股修正后的收盘价", "`load_daily_prices` 默认"],
          ["面板 panel", "日期 × 标的表格", "`make_on_day` 中的 `prices`"],
          ["回看 lookback", "指标所需历史长度", "200 日 SMA 需 200 行"],
        ],
      },
      { kind: "h3", text: "常见数据陷阱" },
      {
        kind: "ul",
        items: [
          "**存活偏差** — 只测今天仍存在的标的。",
          "**前视偏差** — 信号中使用了未来信息。",
          "**公司行动** — 长回测应使用复权价。",
          "**IPO 前历史** — `ready` 须在数据存在之后开始。",
        ],
      },
    ],
  },
  {
    slug: "asset-classes",
    title: "资产类别与 ETF 代理",
    subtitle: "股票、债券、商品、外汇、加密货币 — Quant Buffet 如何在回测中表示它们。",
    order: 3,
    duration: "15 分钟",
    topics: ["ETF", "风险", "资产池"],
    blocks: [
      {
        kind: "p",
        text: "**资产类别**是行为相似的投资大类。Quant Buffet 使用 `backtest.universes` 中的 **ETF 代理** — 流动性好、易模拟、可与 800+ 库内策略对比。",
      },
      { kind: "visual", id: "asset-explorer" },
      { kind: "h2", text: "为何用 ETF 而非个股？" },
      {
        kind: "ul",
        items: [
          "**流动性** — SPY 日成交量巨大，滑点模型更 realistic。",
          "**分散** — 一只 ETF 覆盖数百成分。",
          "**一致性** — 白名单内统一 Yahoo 数据源。",
          "**教学聚焦** — 学策略逻辑，而非单票噪声。",
        ],
      },
      {
        kind: "code",
        lang: "python",
        code: `from backtest.universes import US_SECTORS_FULL, BONDS

ASSETS = ["XLK", "XLF", "XLE", "TLT", "GLD", "BIL"]  # 实验室最多 15 个`,
      },
    ],
  },
  {
    slug: "microstructure",
    title: "微观结构与交易基础设施",
    subtitle: "交易所、券商、价差，以及研究模拟与实盘的差异。",
    order: 4,
    duration: "16 分钟",
    topics: ["场所", "券商", "成本"],
    blocks: [
      {
        kind: "p",
        text: "**市场微观结构**研究订单如何变成成交。你不必自建交易所，但必须清楚 **模拟结束、真实基础设施开始** 的位置。",
      },
      { kind: "visual", id: "microstructure-stack" },
      { kind: "h2", text: "研究栈 vs 实盘栈" },
      {
        kind: "table",
        headers: ["层级", "回测实验室", "实盘"],
        rows: [
          ["信号时间", "日收盘", "日内或日频 — 自选"],
          ["成交价", "收盘 + 2 bps 滑点", "券商买卖价"],
          ["佣金", "5 bps / 笔", "券商费率"],
          ["资金", "虚拟 10 万美元", "真实现金与保证金"],
        ],
      },
    ],
  },
  {
    slug: "order-types",
    title: "订单类型与执行",
    subtitle: "市价、限价、止损 — 以及 PortfolioEngine 如何模拟成交。",
    order: 5,
    duration: "14 分钟",
    topics: ["订单", "滑点", "调仓"],
    blocks: [
      {
        kind: "p",
        text: "**订单**是给券商的指令。系统化交易中，你通常在代码里用 **`set_target_weights`** 表达意图，由基础设施转化为实际订单。",
      },
      { kind: "visual", id: "order-types" },
      {
        kind: "code",
        lang: "python",
        code: `def on_day(engine, dt):
    engine.set_target_weights(dt, {"SPY": 0.6, "TLT": 0.4})`,
      },
      {
        kind: "ul",
        items: [
          "以 **日收盘价** 为参考价调仓。",
          "**滑点** 2 bps：买贵卖贱。",
          "**佣金** 5 bps 按成交额计。",
          "先卖后买；连续相同权重会 **跳过** 调仓。",
        ],
      },
    ],
  },
  {
    slug: "metrics-debug",
    title: "绩效指标与调试",
    subtitle: "Sharpe、回撤、CAGR — 以及实验室常见错误的修复方法。",
    order: 6,
    duration: "20 分钟",
    topics: ["Sharpe", "回撤", "调试"],
    blocks: [
      {
        kind: "p",
        text: "没有 **指标** 的回测只是一张图。Quant Buffet 报告风险调整统计，并在代码出错时提供 **AI 调试器**。",
      },
      { kind: "visual", id: "metrics-explorer" },
      { kind: "h2", text: "指标词汇" },
      {
        kind: "table",
        headers: ["指标", "含义", "审慎看待"],
        rows: [
          ["CAGR", "复合年化收益", "单段牛市可能夸大"],
          ["Volatility", "波动率", "低波可能隐藏杠杆"],
          ["Sharpe", "单位风险收益", "样本太短则失真"],
          ["Max drawdown", "最大回撤", "实盘能否扛住？"],
        ],
      },
      {
        kind: "ol",
        items: [
          "阅读实验室 **错误信息与行号**。",
          "对照 **语法速查** 检查 `ASSETS` 与 `make_on_day`。",
          "点击 **Ask AI** 获取逐步修复。",
          "查阅 **API 文档** 与白名单标的。",
        ],
      },
    ],
  },
  {
    slug: "classic-strategies",
    title: "库中的经典策略",
    subtitle: "动量、趋势、均值回归、风险平价 — 1,700+ 策略背后的模式。",
    order: 7,
    duration: "22 分钟",
    topics: ["动量", "均值回归", "模板"],
    blocks: [
      {
        kind: "p",
        text: "大多数量化想法属于 **少数几大家族**。Quant Buffet 用 **`backtest.templates`** 与自定义代码实现。识别家族即可快速阅读任意文章。",
      },
      { kind: "visual", id: "strategy-map" },
      {
        kind: "table",
        headers: ["模板", "经济逻辑", "库内占比"],
        rows: [
          ["`dual_momentum`", "选最强标的，趋势弱则现金", "~35%"],
          ["`abs_momentum`", "等权持有近期赢家", "~19%"],
          ["`sma_trend`", "价格在均线上方才持有", "~13%"],
          ["`mean_reversion`", "买入超卖 z-score", "~6%"],
        ],
      },
      {
        kind: "checklist",
        title: "课程完成 — 您现在能够",
        items: [
          "说明 **日频数据** 如何进入 **`make_on_day`**。",
          "列举 **资产类别** 并从 universes 选 ETF。",
          "描述 **券商 / 交易所 / 平台** 与成本模型。",
          "对比 **订单类型** 与 Quant Buffet 的权重执行。",
          "解读 **Sharpe 与回撤** 并修复常见错误。",
          "在库中识别 **动量、趋势、均值回归** 模板。",
        ],
      },
      {
        kind: "warn",
        text: "完成课程意味着能负责任地学习 — 不代表任何策略可直接实盘。请模拟盘、小资金起步。",
      },
    ],
  },
];

export function getZhLesson(slug: string): LearnLesson | undefined {
  return ZH_LESSONS.find((l) => l.slug === slug);
}
