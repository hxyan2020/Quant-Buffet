import { auth } from "@/auth";
import PlanPanel from "@/components/PlanPanel";
import { syncUserPlanAccess } from "@/lib/subscription";
import { getTranslations } from "next-intl/server";

type PageProps = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ stripe?: string; session_id?: string }>;
};

export default async function AccountPlanPage({ params, searchParams }: PageProps) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const dictionary = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();
  const userId = session?.user?.id?.trim() ?? "";
  const plan = await syncUserPlanAccess(userId, locale);

  const stripeFlash =
    query.stripe === "success" ? "success"
    : query.stripe === "canceled" ? "canceled"
    : null;

  return (
    <div className="qb-card">
      <h2 className="qb-card-title">{dictionary("plan")}</h2>
      <PlanPanel
        locale={locale}
        hasActivePlan={plan.hasActivePlan}
        expiresAtIso={plan.expiresAt?.toISOString() ?? null}
        cancelAtPeriodEnd={plan.cancelAtPeriodEnd}
        tier={plan.tier}
        tierLabel={plan.tierLabel}
        status={plan.status}
        checkoutSessionId={query.session_id ?? null}
        stripeFlash={stripeFlash}
      />
    </div>
  );
}
