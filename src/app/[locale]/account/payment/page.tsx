import { auth } from "@/auth";
import PaymentMethodsPanel from "@/components/PaymentMethodsPanel";
import { syncUserPlanAccess } from "@/lib/subscription";
import { stripeServer } from "@/lib/stripe";
import { getTranslations } from "next-intl/server";

type PageProps = { params: Promise<{ locale: string }> };

export default async function AccountPaymentPage({ params }: PageProps) {
  const { locale } = await params;
  const dictionary = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();
  const userId = session?.user?.id?.trim();
  if (!userId) {
    return (
      <div className="qb-card">
        <h2 className="qb-card-title">{dictionary("payment")}</h2>
        <p className="qb-muted">{dictionary("paymentPortalError")}</p>
      </div>
    );
  }

  const plan = await syncUserPlanAccess(userId);

  let paymentHint: string | null = null;
  if (plan.stripeCustomerId) {
    const stripe = stripeServer();
    if (stripe) {
      try {
        const methods = await stripe.paymentMethods.list({
          customer: plan.stripeCustomerId,
          type: "card",
          limit: 1,
        });
        const card = methods.data[0]?.card;
        if (card) {
          paymentHint = `${card.brand?.toUpperCase() ?? "Card"} •••• ${card.last4} (${card.exp_month}/${card.exp_year})`;
        }
      } catch {
        paymentHint = null;
      }
    }
  }

  return (
    <div className="qb-card">
      <h2 className="qb-card-title">{dictionary("payment")}</h2>
      <PaymentMethodsPanel
        locale={locale}
        hasCustomer={Boolean(plan.stripeCustomerId)}
        paymentHint={paymentHint}
      />
    </div>
  );
}
