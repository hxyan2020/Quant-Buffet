import { auth } from "@/auth";
import prisma from "@/lib/prisma";
import { getLibraryPlan, isPlanId, formatUsdFromCents } from "@/lib/plans";
import { getTranslations } from "next-intl/server";

type PageProps = { params: Promise<{ locale: string }> };

function planLabel(tier: string, locale: string) {
  if (!isPlanId(tier)) return tier;
  const days = getLibraryPlan(tier).durationDays;
  if (locale === "zh") {
    if (days === 7) return "7 天";
    if (days === 30) return "1 个月";
    if (days === 90) return "3 个月";
    if (days === 180) return "6 个月";
    if (days === 365) return "1 年";
  }
  if (days === 7) return "7 days";
  if (days === 30) return "1 month";
  if (days === 90) return "3 months";
  if (days === 180) return "6 months";
  if (days === 365) return "1 year";
  return tier;
}

export default async function BillingHistoryPage({ params }: PageProps) {
  const { locale } = await params;
  const dictionary = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();

  const rows = await prisma.subscription.findMany({
    where: { userId: session!.user!.id },
    orderBy: { createdAt: "desc" },
  });

  const dateFmt = new Intl.DateTimeFormat(locale === "zh" ? "zh-CN" : "en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });

  return (
    <div className="qb-card">
      <h2 className="qb-card-title">{dictionary("billing")}</h2>
      <p className="qb-muted">{dictionary("billingHint")}</p>
      {rows.length === 0 ?
        <p className="qb-muted">{dictionary("billingEmpty")}</p>
      : (
        <div className="qb-table-wrap">
          <table className="qb-grid">
            <thead>
              <tr>
                <th>{dictionary("billingDate")}</th>
                <th>{dictionary("billingStatus")}</th>
                <th>{dictionary("billingTier")}</th>
                <th>{dictionary("billingAmount")}</th>
                <th>{dictionary("billingAccessUntil")}</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const amount =
                  isPlanId(row.tier) ? formatUsdFromCents(getLibraryPlan(row.tier).unitAmount) : "—";
                return (
                  <tr key={row.id}>
                    <td>{dateFmt.format(row.createdAt)}</td>
                    <td>
                      <span className={`qb-plan-badge ${row.status === "active" ? "is-ok" : "is-muted"}`}>
                        {row.status}
                        {row.cancelAtPeriodEnd ? ` · ${dictionary("statusCanceling")}` : ""}
                      </span>
                    </td>
                    <td>{planLabel(row.tier, locale)}</td>
                    <td>{amount}</td>
                    <td>{row.currentPeriodEnd ? dateFmt.format(row.currentPeriodEnd) : "—"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
