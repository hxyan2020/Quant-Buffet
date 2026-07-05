/* eslint-disable no-console */

import bcrypt from "bcryptjs";

import { PrismaClient } from "@prisma/client";

const prismaClient = new PrismaClient();

async function main() {
  const adminEmail =
    process.env.ADMIN_EMAIL?.trim()?.toLowerCase() ?? "admin@local.dev";
  const adminPassword =
    process.env.ADMIN_PASSWORD?.trim() ??
    Math.random().toString(36).slice(2, 11);

  const passwordHash = await bcrypt.hash(adminPassword, 10);

  await prismaClient.user.upsert({
    where: { email: adminEmail },
    update: {},
    create: {
      email: adminEmail,
      name: "Local Admin",
      role: "ADMIN",
      passwordHash,
      libraryUnlocked: true,
    },
  });

  await prismaClient.strategy.upsert({
    where: {
      slug_locale: {
        slug: "enhanced-reverse-beta-equities",
        locale: "en",
      },
    },
    update: {},
    create: {
      slug: "enhanced-reverse-beta-equities",
      locale: "en",
      title: "Enhanced reversal beta tilt on US equities",
      annualisedReturn: "≈13.4%",
      sharpeRatio: "1.12",
      region: "United States",
      market: "US equities",
      frequency: "Monthly rebalance",
      summary:
        "Mean-reverting beta overlay inspired by behavioural finance anomalies with explicit transaction cost haircut.",
      isPaywalled: true,
      paperTitle:
        "Reversal, momentum, and the risk-free rate: an integrated framework",
      paperAuthors: "Academic working paper (representative citation)",
      academicLink:
        "https://www.google.com/search?q=reversal+momentum+risk-free+integrated+framework",
      contentHtml: `
<section>
  <h2>Investment thesis</h2>
  <p>
    Stocks that lagged sharply in the prior month—but screen cheap on fundamentals—recover as macro beta mean-reverts and crowding fades.
    The strategy layers a reversal sleeve on liquid large caps while beta-hedging with sector ETFs intramonth only when realised variance spikes.
  </p>
</section>

<section>
  <h2>Signal specification</h2>
  <ol>
    <li>Universe = US Top 700 by liquidity, excludes REIT / ADRs with penny spreads.</li>
    <li>Score = −1 × z-score(monthly excess return) × z-score(book-to-market).</li>
    <li>Neutralise dollar &amp; sectors using regression weights capped at ±3% net.</li>
    <li>Transaction cost haircut of 35bps round trip before ranking.</li>
  </ol>
</section>

<section>
  <h2>Risk checklist</h2>
  <ul>
    <li>Correlation spikes alongside macro shocks tighten crowding assumptions.</li>
    <li>Turnover guardrails throttle if cumulative costs exceed modeled alpha decay.</li>
  </ul>
</section>`,
      sortOrder: 1,
      published: true,
    },
  });

  await prismaClient.strategy.upsert({
    where: {
      slug_locale: {
        slug: "enhanced-reverse-beta-equities",
        locale: "zh",
      },
    },
    update: {},
    create: {
      slug: "enhanced-reverse-beta-equities",
      locale: "zh",
      title: "增强型反转Beta在美国股市的运用",
      annualisedReturn: "≈13.4%",
      sharpeRatio: "1.12",
      region: "美国",
      market: "股票",
      frequency: "月频调仓",
      summary:
        "结合月度反转与企业估值溢价的复合型 Alpha，显式计提较高的换手成本以保护样本外可信度。",
      isPaywalled: true,
      paperTitle: "反转、动量与无风险利率：整合框架示例",
      paperAuthors: "学术工作论文示例",
      academicLink:
        "https://www.google.com/search?q=reversal+momentum+risk-free+integrated+framework",
      contentHtml: `
<section>
  <h2>策略逻辑</h2>
  <p>
    当大型蓝筹在一月内因拥挤交易被过度抛售且估值安全边际抬升后，市场情绪修复往往触发短期反转，
    本策略在上述股票池中叠加价值因子滤网，并使用行业ETF仅在波动率上冲时做一次 beta 回补。
  </p>
</section>

<section>
  <h2>打分细节</h2>
  <ol>
    <li>股票池 = 美国流动性排名前 700 的普通股。</li>
    <li>综合得分 = −1 × （上月超额收益标准化） × （账面市值比标准化）。</li>
    <li>行业与美元的暴露通过回归剔除，单笔净暴露 capped at ±3%。</li>
    <li>在排序前先扣除双边 35bp 交易成本假设。</li>
  </ol>
</section>

<section>
  <h2>风险提醒</h2>
  <ul>
    <li>宏观冲击可能与因子拥挤共振，压低样本外夏普。</li>
    <li>若估计成本持续高于隐含 alpha，将自动缩放换手。</li>
  </ul>
</section>`,
      sortOrder: 2,
      published: true,
    },
  });

  console.log(`Seeded admin ${adminEmail} / password: ${adminPassword}`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prismaClient.$disconnect();
  });
