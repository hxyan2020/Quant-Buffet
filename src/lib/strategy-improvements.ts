/** Per-strategy improvement bullets for the temp draft-preview lab (not production). */

export type ImprovementInput = {
  locale?: string;
  title: string;
  paperTitle?: string | null;
  template?: string | null;
  assets?: string[];
  params?: Record<string, unknown> | null;
  fidelity?: string | null;
  source?: "library" | "new100";
  assetClass?: string | null;
  region?: string | null;
  cagr?: number | null;
  sharpe?: number | null;
  maxDd?: number | null;
  vol?: number | null;
  trades?: number | null;
  siteCagr?: number | null;
  hasQc?: boolean;
};

const SECTORS = new Set(["XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY", "XLC", "XLRE"]);
const BONDS = new Set(["SHY", "IEI", "IEF", "TLT", "BND", "AGG", "TIP", "MBB", "BIL", "SHV"]);
const CREDIT = new Set(["LQD", "HYG"]);
const COMMS = new Set(["GLD", "SLV", "DBC", "GSG", "USO", "UNG", "DBA"]);
const CRYPTO = new Set(["BTC-USD", "ETH-USD"]);
const COUNTRY = new Set([
  "EFA", "EEM", "EWJ", "EWG", "EWU", "EWC", "EWA", "EWY", "EWT", "EWZ", "FXI", "ASHR", "VGK", "VWO", "VEA",
]);

export function parseMetricNumber(raw: string | number | null | undefined): number | null {
  if (raw == null || raw === "") return null;
  if (typeof raw === "number" && Number.isFinite(raw)) return raw;
  const t = String(raw).trim().replace(/,/g, "");
  const neg = t.startsWith("(") && t.endsWith(")");
  const core = t.replace(/[()%]/g, "");
  const n = Number(core);
  if (!Number.isFinite(n)) return null;
  const signed = neg ? -n : n;
  if (t.includes("%")) return signed / 100;
  return signed;
}

function pct(x: number | null | undefined, digits = 1): string {
  if (x == null || !Number.isFinite(x)) return "n/a";
  return `${(x * 100).toFixed(digits)}%`;
}

function num(x: number | null | undefined, digits = 2): string {
  if (x == null || !Number.isFinite(x)) return "n/a";
  return x.toFixed(digits);
}

function listAssets(assets: string[], max = 8): string {
  if (!assets.length) return "the current book";
  if (assets.length <= max) return assets.join(", ");
  return `${assets.slice(0, max).join(", ")} (+${assets.length - max})`;
}

function paramNum(params: Record<string, unknown> | null | undefined, key: string, fallback: number): number {
  const v = params?.[key];
  const n = typeof v === "number" ? v : Number(v);
  return Number.isFinite(n) ? n : fallback;
}

function paramStr(params: Record<string, unknown> | null | undefined, key: string, fallback: string): string {
  const v = params?.[key];
  return v == null || v === "" ? fallback : String(v);
}

type Book =
  | "crypto"
  | "sectors"
  | "bonds"
  | "credit"
  | "commodities"
  | "countries"
  | "spy_bil"
  | "qqq_bil"
  | "vol"
  | "reits"
  | "multi";

function classifyBook(assets: string[]): Book {
  const a = new Set(assets);
  if ([...a].some((s) => CRYPTO.has(s))) return "crypto";
  if ([...a].some((s) => s === "VIXY" || s === "SVXY")) return "vol";
  if ([...a].some((s) => s === "VNQ" || s === "IYR" || s === "RWX")) return "reits";
  const sectorN = [...a].filter((s) => SECTORS.has(s)).length;
  if (sectorN >= 6) return "sectors";
  const bondN = [...a].filter((s) => BONDS.has(s) || CREDIT.has(s)).length;
  if (bondN >= Math.max(2, assets.length - 1) && assets.length >= 2) {
    const treasN = [...a].filter((s) => BONDS.has(s)).length;
    return treasN >= 2 ? "bonds" : "credit";
  }
  const commN = [...a].filter((s) => COMMS.has(s)).length;
  if (commN >= 2 && commN >= assets.length - 1) return "commodities";
  const ctryN = [...a].filter((s) => COUNTRY.has(s)).length;
  if (ctryN >= 2) return "countries";
  if (a.size <= 2 && a.has("SPY") && (a.has("BIL") || a.has("SHY") || a.has("IEF"))) return "spy_bil";
  if (a.size <= 2 && a.has("QQQ") && (a.has("BIL") || a.has("SHY"))) return "qqq_bil";
  return "multi";
}

function blobOf(input: ImprovementInput): string {
  return `${input.title} ${input.paperTitle || ""} ${input.assetClass || ""}`.toLowerCase();
}

function has(blob: string, ...keys: string[]): boolean {
  return keys.some((k) => blob.includes(k));
}

function mismatchNote(input: ImprovementInput, book: Book, zh: boolean): string | null {
  const blob = blobOf(input);
  const assets = listAssets(input.assets || []);
  const paper = input.paperTitle || input.title;

  if (book === "spy_bil" && has(blob, "crypto", "bitcoin", "ethereum", "加密")) {
    return zh
      ? `标题是「${paper}」，但回测资产是 ${assets}。这是美股/现金择时，不是加密策略。把 ASSETS 改成 BTC-USD、ETH-USD，并加 BIL 作为绝对动量失败时的避风港。`
      : `The title is “${paper}”, but the book is ${assets}. That is an equity/cash timer, not a crypto strategy. Set ASSETS to BTC-USD and ETH-USD, and keep BIL as the absolute-momentum crash sleeve.`;
  }
  if (book === "spy_bil" && has(blob, "option", "straddle", "intraday", "期权", "日内")) {
    return zh
      ? `论文讲期权/日内，回测却是 ${assets} 上的日频规则。用 QQQ 或 SPY 的日线只能做粗代理：下一步加 20 日实现波动上限，并禁止在开盘跳空日调仓。`
      : `The paper is about options/intraday microstructure, but the run is a daily rule on ${assets}. Keep the ETF proxy, but cap 20-day realized vol and skip rebalances on gap days so the timer is not a stand-in for an options book.`;
  }
  if (book === "spy_bil" && has(blob, "china", "chinese", "a-share", "中国", "a股")) {
    return zh
      ? `论文针对中国/A股，资产却是 ${assets}。换成 FXI、ASHR、EWH，并用当地交易日历做月度再平衡。`
      : `The paper targets China/A-shares, but the book is ${assets}. Switch ASSETS to FXI, ASHR, and EWH, and rebalance on the China ETF calendar rather than SPY.`;
  }
  if (book === "spy_bil" && has(blob, "bond", "treasury", "credit", "fixed income", "债")) {
    return zh
      ? `论文是债券/信用，回测却在 ${assets}。把风险资产换成 IEF 或 LQD，现金仍用 BIL，才能测利率风险而不是股票风险。`
      : `The paper is a bond/credit idea running on ${assets}. Replace the risky leg with IEF or LQD and keep BIL as cash so the timer measures rate risk, not equity risk.`;
  }
  if (book === "bonds" && has(blob, "crypto", "bitcoin", "加密")) {
    return zh
      ? `「${paper}」被映射到债券 ETF ${assets}，所以高夏普来自短债，不是加密。应改用 BTC-USD/ETH-USD。`
      : `“${paper}” was mapped onto bond ETFs ${assets}, so the high Sharpe is T-bill-like, not crypto. Rebuild ASSETS as BTC-USD / ETH-USD.`;
  }
  if (book === "crypto" && has(blob, "intraday", "high-frequency", "high frequency", "分钟", "高频")) {
    return zh
      ? `论文是日内/高频，回测却是 BTC/ETH 的日线月度再平衡。至少把 LOOKBACK 降到 20 日，并在日线信号触发时交易，而不是等月初。`
      : `The paper is intraday/high-frequency, but this run is monthly on daily BTC/ETH bars. Drop LOOKBACK to ~20 days and trade when the daily signal flips, not only on month-start.`;
  }
  if (
    (input.fidelity || "").includes("proxy") ||
    input.fidelity === "no_qc_theme_proxy" ||
    input.fidelity === "signal_unavailable_etf_proxy"
  ) {
    return zh
      ? `保真度是 ${input.fidelity}：这是「${paper}」的流动性 ETF 代理，不是原文信号。下一步用论文里的因子/情绪/期权变量，映射到最接近的 ${assets} 权重。`
      : `Fidelity is ${input.fidelity}: this is a liquid ETF proxy for “${paper}”, not the paper’s signal. Map the actual factor/sentiment/options variable onto weights over ${assets}.`;
  }
  return null;
}

function templateBullets(input: ImprovementInput, book: Book, zh: boolean): string[] {
  const assets = input.assets || [];
  const bookStr = listAssets(assets);
  const p = input.params || {};
  const lookback = paramNum(p, "lookback", input.template === "momentum_rotation" ? 126 : 252);
  const sma = paramNum(p, "sma_days", 200);
  const topN = paramNum(p, "top_n", 1);
  const targetVol = paramNum(p, "target_vol", 0.1);
  const volLb = paramNum(p, "vol_lookback", 63);
  const entryZ = paramNum(p, "entry_z", -1);
  const rebalance = paramStr(p, "rebalance", "monthly");
  const t = input.template || "";
  const out: string[] = [];

  if (t === "sma_trend") {
    out.push(
      zh
        ? `现在是 ${bookStr} 上 ${sma} 日均线、${rebalance} 再平衡：价格高于均线才等权持有，否则现金。把均线改成 10 个月均线（约 210 日），并要求 12 个月收益为正才离开现金，减少 2022 年那种均线附近来回打脸。`
        : `This run holds ${bookStr} equal-weight only when price > the ${sma}-day SMA, cash otherwise, ${rebalance}. Switch to a 10-month SMA (~210 days) and require 12-month return > 0 before leaving cash so 2022-style whipsaws around the moving average are skipped.`,
    );
    if (book === "spy_bil") {
      out.push(
        zh
          ? `SPY/BIL 的 200 日规则是崩盘过滤器，不是选股。若论文是质量/低波动，把 SPY 换成 QUAL 或 SPLV，BIL 仍作避险。`
          : `A 200-day rule on SPY/BIL is a crash filter, not stock selection. If the paper is quality or low-vol, replace SPY with QUAL or SPLV and keep BIL as the defensive sleeve.`,
      );
    }
    if (book === "sectors") {
      out.push(
        zh
          ? `11 个行业 ETF 各自对 ${sma} 日均线做多，等于行业趋势跟随。改成只持有均线之上且 6 个月收益最高的 3 个行业（XLK/XLE 等），避免把所有疲弱板块一齐买入。`
          : `Each of the 11 sector ETFs is long vs its own ${sma}-day SMA, which is sector trend-following. Hold only the top 3 sectors that are both above the SMA and have the best 6-month return so weak groups (e.g. XLE vs XLK) are not bought together.`,
      );
    }
    if (book === "crypto") {
      out.push(
        zh
          ? `BTC/ETH 的 ${sma} 日均线在 2018、2022 年仍会吃到深回撤。均线之上再加 63 日波动目标（例如 25%），或单币权重上限 40%。`
          : `A ${sma}-day SMA on BTC/ETH still rode the 2018 and 2022 crypto winters. Overlay a 63-day vol target (e.g. 25%) or cap each coin at 40% of equity.`,
      );
    }
  }

  if (t === "abs_momentum") {
    out.push(
      zh
        ? `绝对动量：${bookStr} 里 ${lookback} 日收益为正才等权持有（${rebalance}）。这会在趋势中满仓。加一条 3 个月动量确认，或当 63 日波动超过 30% 时把权重减半。`
        : `Absolute momentum: equal-weight names in ${bookStr} with positive ${lookback}-day return, ${rebalance}. That stays fully invested in a trend. Add a 3-month confirmation, or cut weights in half when 63-day vol exceeds 30%.`,
    );
    if (book === "crypto") {
      out.push(
        zh
          ? `BTC 与 ETH 的 ${lookback} 日动量会在赢家上拿到 −80% 级回撤。失败时切到 BIL，而不是空仓后再追涨；单币仓位封顶 50%。`
          : `${lookback}-day momentum on BTC and ETH will sit 100% in the winner through −80% drawdowns. When both 12-month returns are negative, hold BIL instead of cash-then-chase, and cap any single coin at 50%.`,
      );
    }
    if (book === "spy_bil" || book === "qqq_bil") {
      out.push(
        zh
          ? `两资产绝对动量几乎等于「股票涨就持有、否则 BIL」。若论文是横截面因子，应对一组因子 ETF（VLUE、QUAL、MTUM）分别做 ${lookback} 日过滤，而不是只打 ${assets[0] || "SPY"}。`
          : `Two-asset absolute momentum is just “hold the equity ETF when it is up, else BIL”. If the paper is cross-sectional, apply the ${lookback}-day filter to a factor sleeve (VLUE, QUAL, MTUM) rather than only ${assets[0] || "SPY"}.`,
      );
    }
  }

  if (t === "dual_momentum") {
    out.push(
      zh
        ? `双动量：在 ${bookStr} 里选 ${lookback} 日收益最高的风险资产，若其为负则持有 BIL（${rebalance}）。若只有一个风险腿，这就是绝对动量。加入第二风险腿（例如 EFA 或 TLT）才能发挥相对动量。`
        : `Dual momentum picks the best ${lookback}-day risky name in ${bookStr} and holds BIL if that return is negative (${rebalance}). With one risky leg this is only absolute momentum. Add a second risky sleeve (EFA or TLT) so relative momentum can actually switch.`,
    );
  }

  if (t === "momentum_rotation") {
    out.push(
      zh
        ? `轮动：按 ${lookback} 日收益对 ${bookStr} 排序，等权持有前 ${topN} 名（${rebalance}）。${lookback} 日对「1 个月动量」偏长——若标题是月度动量，把 LOOKBACK 改成 21，并加 12 个月趋势过滤避免接飞刀。`
        : `Rotation ranks ${bookStr} on ${lookback}-day return and holds the top ${topN} equal-weight (${rebalance}). ${lookback} days is long for a “1-month momentum” title — set LOOKBACK=21 and keep a 12-month trend filter so you do not catch falling knives.`,
    );
    if (book === "bonds") {
      out.push(
        zh
          ? `债券轮动在 SHY/IEF/TLT/LQD/HYG 上会在加息年同时踩中长久期和信用。对 TLT 与 HYG 加 60 日波动惩罚，或强制组合久期不超过 IEF。`
          : `Bond rotation across SHY/IEF/TLT/LQD/HYG can hold long duration and credit together in hiking cycles. Penalize TLT and HYG by 60-day vol, or cap portfolio duration at IEF.`,
      );
    }
    if (book === "commodities") {
      out.push(
        zh
          ? `商品动量在 UNG/USO 上极吵。从轮动里去掉 UNG，或对单品种权重设 25% 上限，并要求 12 个月收益为正。`
          : `Commodity momentum is dominated by UNG/USO noise. Drop UNG from the rotation, or cap any one name at 25% and require 12-month return > 0.`,
      );
    }
    if (book === "sectors") {
      out.push(
        zh
          ? `行业轮动 top-${topN} 在 ${lookback} 日窗口上会长期偏 XLK。加入 20 日反转惩罚或波动标准化收益，避免科技单边。`
          : `Sector rotation top-${topN} on a ${lookback}-day window will concentrate in XLK for years. Rank on return / 20-day vol, or add a 1-month reversal skip so mega-cap tech does not become the whole book.`,
      );
    }
  }

  if (t === "mean_reversion") {
    out.push(
      zh
        ? `均值回归对 ${bookStr} 用 ${lookback} 日 z 值，低于 ${entryZ} 开仓、回到 0 平仓，而且每天都 set_target_weights。这会产生数千笔碎单和手续费。只在开平仓日交易，持有期不要每日再平衡。`
        : `Mean reversion on ${bookStr} uses a ${lookback}-day z-score (enter ≤ ${entryZ}, exit at 0) and calls set_target_weights every day. That creates thousands of dust fills and cost drag. Trade only on entry/exit days; do not daily-rebalance while a name is held.`,
    );
    if (book === "credit" || book === "bonds") {
      out.push(
        zh
          ? `做多 LQD/HYG 的短线 z 值不是「做空公司债对冲尾部」。要对冲信用尾部：在 HYG 的 20 日 z 过高时做空 HYG、做多 IEF/BIL，并设硬止损。`
          : `Long-only z-scores on LQD/HYG are not a short-credit tail hedge. To match a shorting-credit paper: short HYG and long IEF/BIL when HYG’s 20-day z is stretched, with a hard stop.`,
      );
    }
    if (book === "crypto") {
      out.push(
        zh
          ? `BTC/ETH 日线 z 值均值回归在趋势年会连续止损。加一个 200 日均线过滤器：只有价格低于均线才允许做多超卖。`
          : `Daily z-score reversion on BTC/ETH gets run over in trend years. Add a 200-day SMA filter: only fade oversold prints when price is already below the SMA.`,
      );
    }
  }

  if (t === "vol_target") {
    out.push(
      zh
        ? `波动目标：把 ${bookStr} 的仓位缩放到年化 ${pct(targetVol, 0)}，用 ${volLb} 日实现波动、${rebalance} 再平衡。Moreira–Muir 是对因子超额收益做缩放，不是对 SPY 价格。对 SPY 相对 BIL 的超额收益做 ${volLb} 日波动缩放，现金放 BIL。`
        : `Vol targeting scales ${bookStr} toward ${pct(targetVol, 0)} annualized using ${volLb}-day realized vol, ${rebalance}. Moreira–Muir scale factor excess returns, not the SPY price level. Apply the ${volLb}-day scaler to SPY excess vs BIL and park residual cash in BIL.`,
    );
    if (targetVol <= 0.12 && book === "spy_bil") {
      out.push(
        zh
          ? `10% 波动目标会长期低配美股，所以 CAGR 被压到债券附近。对市场组合试 15–20% 目标，或只在 VIX 代理（可用 SPY 20 日波动）高位时降仓。`
          : `A 10% vol target structurally underweights US equities, so CAGR looks bond-like. Try 15–20% for a market sleeve, or de-risk only when 20-day SPY vol is in the top quartile.`,
      );
    }
  }

  if (t === "risk_parity") {
    out.push(
      zh
        ? `风险平价按 ${volLb} 日波动的倒数配置 ${bookStr}。债券波动低会占很大权重。对 TLT/IEF 设 40% 上限，或用 3 年协方差做真正的风险预算，而不是波动倒数。`
        : `Risk parity inverse-vol weights ${bookStr} on a ${volLb}-day window. Low-vol bonds then dominate. Cap TLT/IEF at 40%, or use a 3-year covariance risk-budget instead of 1/vol.`,
    );
  }

  if (t === "equal_weight") {
    out.push(
      zh
        ? `等权月度再平衡 ${bookStr} 没有择时。若论文有动量/质量信号，用该信号做 ±10% 倾斜，而不是改成全有全无。`
        : `Equal-weight monthly rebalance of ${bookStr} has no timing. If the paper has a momentum or quality signal, tilt ±10% around equal weight rather than going all-in/all-out.`,
    );
    if (book === "commodities") {
      out.push(
        zh
          ? `等权商品会把 UNG/USO 的回撤平均进组合。改为波动倒数加权，或剔除 UNG。`
          : `Equal-weight commodities lets UNG/USO drawdowns dominate. Inverse-vol weight the book, or drop UNG.`,
      );
    }
  }

  if (t === "dual_ma") {
    const fast = paramNum(p, "fast", 50);
    const slow = paramNum(p, "slow", 200);
    out.push(
      zh
        ? `双均线 ${fast}/${slow} 作用在 ${bookStr}。金叉死叉在震荡市反复。加 12 个月收益过滤，或把再平衡从日频改成周频。`
        : `Dual MA ${fast}/${slow} on ${bookStr} whipsaws in ranges. Add a 12-month return filter, or rebalance weekly instead of daily.`,
    );
  }

  return out;
}

function metricBullets(input: ImprovementInput, book: Book, zh: boolean): string[] {
  const out: string[] = [];
  const { cagr, sharpe, maxDd, vol, trades, siteCagr, template } = input;
  const assets = listAssets(input.assets || []);

  if (maxDd != null && maxDd <= -0.5) {
    out.push(
      zh
        ? `最大回撤 ${pct(maxDd)}（${assets}）。在 ${template || "该规则"} 上加 63 日波动目标或 12 个月绝对动量：回撤过半说明趋势规则在熊市没有减到足够轻。`
        : `Max drawdown is ${pct(maxDd)} on ${assets}. Overlay a 63-day vol target or 12-month absolute-momentum cut: a >50% hole means the ${template || "rule"} did not de-risk enough in the bear leg.`,
    );
  } else if (maxDd != null && maxDd <= -0.25 && (sharpe == null || sharpe < 0.7)) {
    out.push(
      zh
        ? `回撤 ${pct(maxDd)}、夏普 ${num(sharpe)}。对 ${assets} 用「新高后才加仓」或把再平衡推迟到月中波动回落，避免在回撤中点加仓。`
        : `Drawdown ${pct(maxDd)} with Sharpe ${num(sharpe)} on ${assets}. Only add risk on a 20-day high, or delay the monthly rebalance until 20-day vol has fallen, so you are not averaging in mid-drawdown.`,
    );
  }

  if (sharpe != null && sharpe < 0.25) {
    out.push(
      zh
        ? `夏普 ${num(sharpe)}、CAGR ${pct(cagr)} 说明这条 ${template || "规则"} 在 ${assets} 上几乎没有风险调整后的边。先关掉每日再平衡，再试更长 lookback；若仍差，说明该论文信号无法用这些 ETF 表达。`
        : `Sharpe ${num(sharpe)} and CAGR ${pct(cagr)} mean this ${template || "rule"} has almost no risk-adjusted edge on ${assets}. Turn off daily rebalancing first, then lengthen lookback; if it stays weak, the paper’s signal is not expressible with these ETFs.`,
    );
  }

  if (cagr != null && cagr > 0.35 && book === "crypto") {
    out.push(
      zh
        ? `CAGR ${pct(cagr)} 主要来自 2015 年后 BTC/ETH 本身，不是精细 alpha。用 2018–2022 样本外窗口重跑，并以 20% 波动目标缩放，才能看出规则有没有独立价值。`
        : `CAGR ${pct(cagr)} is mostly the 2015–onward BTC/ETH asset, not fine-grained alpha. Re-run 2018–2022 out of sample and scale to a 20% vol target to see whether the rule adds anything beyond holding crypto.`,
    );
  }

  if (vol != null && vol > 0.35) {
    out.push(
      zh
        ? `实现波动 ${pct(vol)} 对 ${assets} 过高。在 make_on_day 里把目标权重乘以 min(1, 0.15/σ)，σ 用 20 日波动。`
        : `Realized vol ${pct(vol)} is too high for a productized sleeve on ${assets}. Multiply target weights by min(1, 0.15 / σ) using 20-day σ inside make_on_day.`,
    );
  }

  if (trades != null && trades > 2000) {
    out.push(
      zh
        ? `成交 ${trades} 笔，对日频账户不现实。把再平衡改成信号变化时才交易，或改 monthly，否则 5bp+2bp 会吃掉均值回归的边。`
        : `${trades} fills is not a tradable daily book. Rebalance only when the signal set changes, or switch to monthly — 5 bp + 2 bp will erase a mean-reversion edge.`,
    );
  }

  if (siteCagr != null && cagr != null && Math.abs(siteCagr - cagr) > 0.1) {
    out.push(
      zh
        ? `站点原 CAGR ${pct(siteCagr)}，本引擎 ${pct(cagr)}，差 ${pct(Math.abs(siteCagr - cagr))}。不要把本页数字当成原文结果；要对齐，必须复现论文宇宙与信号，而不是 ${assets} 代理。`
        : `Published site CAGR ${pct(siteCagr)} vs this engine ${pct(cagr)} (${pct(Math.abs(siteCagr - cagr))} gap). Do not treat this page as the original study — replicate the paper’s universe and signal, not the ${assets} proxy.`,
    );
  }

  return out;
}

function labNextStep(input: ImprovementInput, zh: boolean): string {
  const t = input.template || "rule";
  const a0 = (input.assets || [])[0] || "SPY";
  const a1 = (input.assets || [])[1] || "BIL";
  if (t === "sma_trend") {
    return zh
      ? `在编辑器里把 SMA_DAYS 从 ${paramNum(input.params, "sma_days", 200)} 改成 150 和 250 各跑一次，比较 ${a0}/${a1} 的最大回撤，而不是只看 CAGR。`
      : `In the lab editor, rerun SMA_DAYS at 150 and 250 (instead of ${paramNum(input.params, "sma_days", 200)}) and compare max drawdown on ${a0}/${a1}, not only CAGR.`;
  }
  if (t === "momentum_rotation") {
    return zh
      ? `把 LOOKBACK 改成 21、TOP_N 改成 ${Math.min(3, Math.max(1, (input.assets || []).length - 1))} 再跑，看 ${listAssets(input.assets || [])} 的换手是否下降、回撤是否变浅。`
      : `Set LOOKBACK=21 and TOP_N=${Math.min(3, Math.max(1, (input.assets || []).length - 1))}, rerun, and check whether turnover and drawdown improve on ${listAssets(input.assets || [])}.`;
  }
  if (t === "mean_reversion") {
    return zh
      ? `把 on_day 改成仅在 held 状态翻转时调用 set_target_weights，重跑后核对成交笔数是否从数千降到数百。`
      : `Change on_day so set_target_weights runs only when a name’s held flag flips, then confirm fill count drops from thousands to hundreds.`;
  }
  if (t === "vol_target") {
    return zh
      ? `把 TARGET_VOL 改成 0.15 和 0.20，看 SPY 腿是否仍跑输买入持有；若 CAGR 上升而回撤不变差，说明 0.10 目标过紧。`
      : `Rerun TARGET_VOL at 0.15 and 0.20. If CAGR rises without a worse max DD, the 0.10 target is too tight for this sleeve.`;
  }
  if (t === "dual_momentum" || t === "abs_momentum") {
    return zh
      ? `在 ASSETS 中加入 ${a0 === "SPY" ? "EFA" : "BIL"}，把 LOOKBACK 设为 126 再跑，检查相对动量会不会减少对单一赢家的依赖。`
      : `Add ${a0 === "SPY" ? "EFA" : "BIL"} to ASSETS, set LOOKBACK=126, and check whether relative momentum reduces single-name concentration.`;
  }
  return zh
    ? `在实验室把 ${a1} 权重上限设为 40%，重跑后对比目前的回撤 ${pct(input.maxDd)}。`
    : `Cap ${a1} at 40% of equity in the lab and compare max drawdown with the current ${pct(input.maxDd)}.`;
}

function uniq(items: string[]): string[] {
  const seen = new Set<string>();
  const out: string[] = [];
  for (const s of items) {
    const k = s.slice(0, 80);
    if (!s.trim() || seen.has(k)) continue;
    seen.add(k);
    out.push(s);
  }
  return out;
}

export function buildStrategyImprovements(input: ImprovementInput): string[] {
  const zh = input.locale === "zh";
  const assets = input.assets || [];
  const book = classifyBook(assets);
  const bullets: string[] = [];

  const mis = mismatchNote(input, book, zh);
  if (mis) bullets.push(mis);

  bullets.push(...templateBullets(input, book, zh));
  bullets.push(...metricBullets(input, book, zh));
  bullets.push(labNextStep(input, zh));

  if (input.source === "new100") {
    bullets.push(
      zh
        ? `这是新抓取草稿，尚未上线。先在实验室改 ASSETS/参数并保存曲线，再考虑是否值得写成正式 Quant Buffet 帖。`
        : `This is an unpublished scraped draft. Change ASSETS/parameters in the lab and keep the curve before promoting it to a Quant Buffet post.`,
    );
  }

  const cleaned = uniq(bullets).slice(0, 6);
  if (cleaned.length >= 3) return cleaned;

  cleaned.push(
    zh
      ? `针对「${input.title}」，下一步应用 ${listAssets(assets)} 的论文原始信号替换当前 ${input.template || "模板"} 代理。`
      : `For “${input.title}”, replace the ${input.template || "template"} proxy with the paper’s actual signal on ${listAssets(assets)}.`,
  );
  return uniq(cleaned).slice(0, 6);
}
