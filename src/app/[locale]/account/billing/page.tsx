import { auth } from "@/auth";
import prisma from "@/lib/prisma";
import { getTranslations } from "next-intl/server";

type PageProps = { params: Promise<{ locale: string }> };

export default async function BillingHistoryPage({ params }: PageProps) {
  const { locale } = await params;
  const dictionary = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();

  const rows = await prisma.subscription.findMany({
    where: { userId: session!.user!.id },
    orderBy: { id: "desc" },
  });

  return (
    <div className="qb-card">
      <h2 className="qb-card-title">{dictionary("billing")}</h2>
      {rows.length === 0 ?
        <p className="qb-muted">{dictionary("billingEmpty")}</p>
      : (
        <div className="qb-table-wrap">
          <table className="qb-grid">
            <thead>
              <tr>
                <th>{dictionary("billingStatus")}</th>
                <th>{dictionary("billingTier")}</th>
                <th>Stripe</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.id}>
                  <td>{row.status}</td>
                  <td>{row.tier}</td>
                  <td style={{ fontSize: "0.75rem", color: "#8caacf", wordBreak: "break-all" }}>
                    {row.stripePaymentIntentId ?? row.stripeCheckoutSession ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
