/** Strategy-specific live-trading checklist for the temp draft-preview lab. */

export type LiveStep = {
  title: string;
  body: string;
  href?: string;
  hrefLabel?: string;
};

export type LiveTradingGuide = {
  venueName: string;
  accountType: string;
  products: string;
  summary: string;
  steps: LiveStep[];
  firstOrders: string[];
  warnings: string[];
};

const CRYPTO = new Set(["BTC-USD", "ETH-USD"]);

function listAssets(assets: string[], max = 10): string {
  if (!assets.length) return "the backtest universe";
  if (assets.length <= max) return assets.join(", ");
  return `${assets.slice(0, max).join(", ")} (+${assets.length - max})`;
}

function spotCrypto(sym: string): string {
  if (sym === "BTC-USD") return "BTC";
  if (sym === "ETH-USD") return "ETH";
  return sym.replace("-USD", "");
}

export function buildLiveTradingGuide(opts: {
  locale?: string;
  title: string;
  assets?: string[];
  template?: string | null;
  region?: string | null;
}): LiveTradingGuide {
  const zh = opts.locale === "zh";
  const assets = (opts.assets || []).filter(Boolean);
  const crypto = assets.filter((s) => CRYPTO.has(s));
  const etfs = assets.filter((s) => !CRYPTO.has(s));
  const mixed = crypto.length > 0 && etfs.length > 0;
  const cryptoOnly = crypto.length > 0 && etfs.length === 0;
  const book = listAssets(assets);
  const title = opts.title;
  const rebalance =
    opts.template === "mean_reversion" ? (zh ? "按信号日" : "on signal days") : zh ? "每月" : "monthly";

  if (cryptoOnly) {
    const coins = crypto.map(spotCrypto).join(", ");
    return {
      venueName: zh ? "HashKey Exchange（香港持牌）或 Coinbase / Kraken" : "Coinbase or Kraken (HashKey if you are in Hong Kong)",
      accountType: zh ? "现货交易账户（个人）" : "Individual spot account",
      products: zh ? `现货 ${coins}（对应回测 ${book}）` : `Spot ${coins} (backtest symbols ${book})`,
      summary: zh
        ? `「${title}」回测买卖的是 ${book}。实盘对应 BTC/ETH 现货，不是美股 ETF。用持牌加密交易所开现货账户，先入金法币或稳定币，再按策略权重买入 ${coins}。`
        : `“${title}” backtests ${book}. Live, that is BTC/ETH spot, not a US ETF. Open a spot account at a licensed crypto exchange, fund it, then buy ${coins} in the strategy weights.`,
      steps: [
        {
          title: zh ? "1. 选交易所并确认你所在地可开户" : "1. Pick an exchange that onboards your country",
          body: zh
            ? "香港：HashKey Exchange（证监会持牌）。美国/多数国家：Coinbase 或 Kraken。中国内地居民通常无法合法使用境外加密交易所，请先核对自己的法规，不要用 VPN 规避。"
            : "Hong Kong: HashKey Exchange (SFC-licensed). US and many other countries: Coinbase or Kraken. If your country bans retail crypto, do not open an offshore account to get around that.",
          href: zh ? "https://www.hashkey.com/" : "https://www.coinbase.com/",
          hrefLabel: zh ? "HashKey 官网" : "Coinbase",
        },
        {
          title: zh ? "2. 注册个人现货账户" : "2. Register a personal spot account",
          body: zh
            ? "用邮箱注册 → 验证手机 → 设置 2FA（推荐验证器 App，不要只用短信）。账户类型选个人/现货，不要开合约或杠杆，除非你明确要做永续，本回测是现货多头。"
            : "Sign up with email → verify phone → turn on 2FA (authenticator app, not SMS-only). Choose an individual spot account. This backtest is long-only spot, not perps or margin.",
          href: "https://www.kraken.com/sign-up",
          hrefLabel: "Kraken sign-up",
        },
        {
          title: zh ? "3. 完成 KYC" : "3. Complete identity verification (KYC)",
          body: zh
            ? "准备护照或身份证、住址证明（3 个月内账单）、自拍核验。通过后才能法币入金和提币。保存交易所给的充值地址白名单。"
            : "Passport or national ID, a proof of address dated within 3 months, and a selfie check. Fiat deposits and withdrawals stay locked until KYC clears. Save withdrawal-address allowlists.",
        },
        {
          title: zh ? "4. 入金（充值）" : "4. Top up the balance",
          body: zh
            ? "优先银行转账/FPS 入 HKD 或 USD（手续费低于信用卡）。也可充值 USDC 再换成 BTC/ETH。先小额测试一笔到账，再转入计划本金。不要把全部资金留在交易所长期托管。"
            : "Bank transfer / FPS into USD or HKD is usually cheaper than cards. You can also deposit USDC and convert to BTC/ETH. Send a small test deposit first. Do not leave all capital on the exchange long term.",
        },
        {
          title: zh ? "5. 买入策略资产" : "5. Buy the strategy assets",
          body: zh
            ? `在现货市场买入 ${coins}。市价单适合小额；大额用限价。按回测权重分配（两币等权则各约 50%）。现金腿若回测用 BIL，在交易所就留法币/USDC，不要硬买一个债券 ETF。`
            : `Buy spot ${coins}. Use market orders for small size, limits for larger clips. Match backtest weights (equal-weight two coins ≈ 50/50). If the backtest cash sleeve is BIL, hold fiat or USDC on the exchange — do not invent a bond ETF there.`,
        },
        {
          title: zh ? "6. 按回测节奏再平衡" : "6. Rebalance on the same cadence as the backtest",
          body: zh
            ? `本策略模板是 ${opts.template || "规则"}，再平衡按 ${rebalance}。在日历上设提醒，按最新权重买卖 ${coins}，不要盘中频繁刷单。`
            : `This template (${opts.template || "rule"}) rebalances ${rebalance}. Put a calendar reminder, trade ${coins} back to target weights, and avoid intraday churn.`,
        },
      ],
      firstOrders: crypto.map((s) =>
        zh ? `现货买入 ${spotCrypto(s)}（对应 ${s}）` : `Spot buy ${spotCrypto(s)} (backtest ${s})`,
      ),
      warnings: [
        zh
          ? "加密波动极大；回测里 −80% 回撤在实盘同样可能发生。"
          : "Crypto drawdowns of −80% in the backtest can happen live.",
        zh
          ? "Quant Buffet 不托管资金、不接交易所 API 下单；本页只是操作说明。"
          : "Quant Buffet does not custody funds or place exchange orders. This is an operations checklist only.",
      ],
    };
  }

  if (mixed) {
    const coins = crypto.map(spotCrypto).join(", ");
    const etfStr = listAssets(etfs);
    return {
      venueName: zh ? "Interactive Brokers（ETF）+ 持牌加密交易所（现货）" : "Interactive Brokers (ETFs) + a licensed crypto exchange (spot)",
      accountType: zh ? "IBKR 现金账户 + 加密现货账户" : "IBKR cash account + crypto spot account",
      products: zh ? `ETF ${etfStr}；现货 ${coins}` : `ETFs ${etfStr}; spot ${coins}`,
      summary: zh
        ? `「${title}」同时用了交易所交易基金 ${etfStr} 和加密 ${book.includes("BTC") ? coins : book}。实盘需要两个账户：IBKR 买 ETF，HashKey/Coinbase/Kraken 买 ${coins}。按回测权重拆分本金，不要在单一账户里用 CFD 冒充另一边。`
        : `“${title}” mixes ETFs (${etfStr}) and crypto. Live you need two accounts: IBKR for the ETFs and Coinbase/Kraken/HashKey for ${coins}. Split capital by backtest weights; do not fake the crypto leg with a CFD.`,
      steps: [
        {
          title: zh ? "1. 开 Interactive Brokers 账户买 ETF" : "1. Open Interactive Brokers for the ETF sleeve",
          body: zh
            ? `注册个人现金账户（本回测只做多，不必开保证金）。税务居住地填真实国家，非美国税务居民要填 W-8BEN 才能交易美股 ETF（${etfStr}）。`
            : `Open an individual cash account (this backtest is long-only, so margin is optional). Non-US tax residents complete Form W-8BEN to trade US ETFs (${etfStr}).`,
          href: "https://www.interactivebrokers.com/en/trading/open-account.php",
          hrefLabel: "IBKR open account",
        },
        {
          title: zh ? "2. IBKR 入金" : "2. Fund IBKR",
          body: zh
            ? "银行电汇 USD 最稳。香港可用本地银行转 USD。先汇一笔小额确认到账，再汇本金。到账后在账户里确认有 USD 购买力。"
            : "USD wire is the usual path. Send a small test wire first. Confirm USD buying power before you size the ETF sleeve.",
        },
        {
          title: zh ? "3. 另开加密现货账户" : "3. Open a separate crypto spot account",
          body: zh
            ? `香港用 HashKey；其他地区用 Coinbase 或 Kraken。完成 KYC 与 2FA。不要用 IBKR 的加密 CFD 去替代 ${coins} 现货，除非你清楚合约条款。`
            : `HashKey in Hong Kong; Coinbase or Kraken elsewhere. Finish KYC and 2FA. Do not substitute crypto CFDs at IBKR for spot ${coins} unless you understand the product.`,
          href: "https://www.coinbase.com/",
          hrefLabel: "Coinbase",
        },
        {
          title: zh ? "4. 加密账户入金" : "4. Top up the crypto account",
          body: zh
            ? "银行入金法币或转入 USDC，先小额测试。按回测里加密资产的权重把这部分本金换成 BTC/ETH。"
            : "Fiat bank transfer or USDC, test size first. Convert this sleeve to BTC/ETH using the backtest crypto weights.",
        },
        {
          title: zh ? "5. 两边按同一日历再平衡" : "5. Rebalance both sleeves on the same calendar",
          body: zh
            ? `模板 ${opts.template || "规则"} 为 ${rebalance} 再平衡。同一天在 IBKR 调 ETF、在交易所调 ${coins}，使总组合接近回测权重。`
            : `${opts.template || "This rule"} rebalances ${rebalance}. On that day, trade ETFs at IBKR and ${coins} at the exchange so the combined book matches target weights.`,
        },
      ],
      firstOrders: [
        ...etfs.slice(0, 6).map((s) => (zh ? `IBKR 买入 ${s}（SMART/USD）` : `IBKR buy ${s} (SMART / USD)`)),
        ...crypto.map((s) => (zh ? `现货买入 ${spotCrypto(s)}` : `Spot buy ${spotCrypto(s)}`)),
      ],
      warnings: [
        zh
          ? "两个账户的资金和税务要分开记账；汇率和入金费不会出现在回测里。"
          : "Two accounts means extra FX and deposit fees that the backtest does not include.",
        zh
          ? "Quant Buffet 不代客下单、不连接你的券商。"
          : "Quant Buffet does not place orders or connect to your broker.",
      ],
    };
  }

  // ETF / futures-proxy ETFs via IBKR
  const needsUs = etfs.some((s) => !["ASHR", "FXI", "EWH"].includes(s));
  const volNote = etfs.some((s) => s === "VIXY" || s === "SVXY");
  const bondNote = etfs.some((s) => ["TLT", "IEF", "SHY", "BIL", "LQD", "HYG", "BND", "TIP"].includes(s));
  const sectorNote = etfs.some((s) => s.startsWith("XL"));

  return {
    venueName: "Interactive Brokers",
    accountType: zh ? "个人现金账户（美股权限）" : "Individual cash account with US stock permission",
    products: zh ? `美股上市 ETF：${book}` : `US-listed ETFs: ${book}`,
    summary: zh
      ? `「${title}」回测交易 ${book}。这些是纽约上市的 ETF，不是加密货币。用 Interactive Brokers（或同等可交易美股 ETF 的券商）开个人账户，电汇入金 USD，再按权重买入上述代码。`
      : `“${title}” trades ${book}. Those are US-listed ETFs, not crypto. Open an Interactive Brokers account (or another broker that offers these US ETFs), wire USD, then buy the tickers at the backtest weights.`,
    steps: [
      {
        title: zh ? "1. 注册 Interactive Brokers" : "1. Register at Interactive Brokers",
        body: zh
          ? "打开 IBKR 开户页 → 个人账户 → 账户基数选现金账户（Cash）。本回测只做多、不卖空，现金账户足够，也可稍后升级保证金。填写居住国家与税务信息，必须与银行账户一致。"
          : "Go to IBKR’s open-account page → Individual → Cash base currency USD. This backtest is long-only, so a cash account is enough (you can add margin later). Residence and tax country must match the bank you will wire from.",
        href: "https://www.interactivebrokers.com/en/trading/open-account.php",
        hrefLabel: "IBKR open account",
      },
      {
        title: zh ? "2. 提交身份与税务文件" : "2. Submit ID and tax forms",
        body: zh
          ? `护照或身份证、住址证明。非美国税务居民在线签署 W-8BEN，才能交易美股 ETF${needsUs ? "（本策略需要美股权限）" : ""}。美国人填 W-9。审核通常 1–3 个工作日。`
          : `Passport or national ID plus proof of address. Non-US tax residents sign Form W-8BEN to trade US ETFs${needsUs ? " (this strategy needs the US stock permission)" : ""}. US persons file W-9. Review is often 1–3 business days.`,
      },
      {
        title: zh ? "3. 开通美股交易权限" : "3. Enable US stock trading",
        body: zh
          ? `在 Client Portal → 设置 → 交易权限中打开「美国股票」。${bondNote ? "债券 ETF（如 TLT、BIL、LQD）走股票权限即可，不必开债券期货。" : ""}${sectorNote ? "行业 ETF（XLK 等）同样是美股。" : ""}${volNote ? "VIXY/SVXY 是波动 ETN，衰减很快，只建议用极小仓位。" : ""}`
          : `In Client Portal → Settings → Trading permissions, enable United States stocks. ${bondNote ? "Bond ETFs (TLT, BIL, LQD) use the stock permission — you do not need futures. " : ""}${sectorNote ? "Sector SPDRs (XLK, …) are ordinary US equities. " : ""}${volNote ? "VIXY/SVXY are volatility ETNs that decay; keep size tiny. " : ""}`,
      },
      {
        title: zh ? "4. 入金（Top up）" : "4. Top up the account",
        body: zh
          ? "Client Portal → 转账 → 入金：选银行电汇 USD。复制 IBKR 给你的收款银行、账户名、备注（必须含你的 IBKR 账号）。先汇 100–500 USD 测试，到账后再汇计划本金。香港/新加坡常用本地银行 USD 电汇；信用卡入金费用高，不建议。"
          : "Client Portal → Transfer & Pay → Deposit → bank wire in USD. Copy IBKR’s beneficiary bank, account name, and the memo (must include your IBKR account number). Wire $100–500 as a test, then the rest. Cards are expensive; use a bank wire.",
        href: "https://www.interactivebrokers.com/en/support/fund-your-account.php",
        hrefLabel: "IBKR funding help",
      },
      {
        title: zh ? "5. 可选：先开模拟账户" : "5. Optional: paper-trade first",
        body: zh
          ? `同一登录下可开 IBKR Paper Account，用虚拟资金按 ${book} 下单，确认代码、时区（美东）和月度再平衡流程，再转真实账户。`
          : `Open an IBKR Paper Account under the same login, trade ${book} with virtual cash, and confirm tickers, US/Eastern session, and the ${rebalance} rebalance before using real money.`,
      },
      {
        title: zh ? "6. 买入本策略代码并再平衡" : "6. Buy this strategy’s tickers and rebalance",
        body: zh
          ? `在 TWS 或 Client Portal 用 SMART/USD 买入：${book}。按回测权重下单（等权则每只约 ${assets.length ? (100 / assets.length).toFixed(0) : "—"}%）。之后按 ${rebalance} 调回目标权重。本引擎假设 5bp 佣金 + 2bp 滑点，IBKR 美股 ETF 佣金通常更低，但仍会有买卖价差。`
          : `In TWS or Client Portal, buy ${book} via SMART/USD at the backtest weights (equal weight ≈ ${assets.length ? (100 / assets.length).toFixed(0) : "—"}% each). Rebalance ${rebalance}. The lab assumes 5 bp commission + 2 bp slip; IBKR ETF commissions are often lower, but spreads still apply.`,
      },
    ],
    firstOrders: etfs.slice(0, 8).map((s) =>
      zh ? `买入 ${s} · SMART · USD` : `Buy ${s} · SMART · USD`,
    ),
    warnings: [
      zh
        ? "回测不是收益承诺；实盘有停牌、溢价/折价、分红税和入金延迟。"
        : "The backtest is not a return promise. Live trading adds halts, ETF premium/discount, dividend tax, and deposit delays.",
      zh
        ? "Quant Buffet 是教育研究库，不提供投资建议，也不连接你的券商账户。"
        : "Quant Buffet is an educational research library. This is not investment advice and we do not connect to your broker.",
    ],
  };
}
