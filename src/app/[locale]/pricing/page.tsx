import { auth } from "@/auth";
import CheckoutButton from "@/components/CheckoutButton";
import JsonLd from "@/components/JsonLd";
import { LIBRARY_PLANS, formatUsdFromCents } from "@/lib/plans";
import { breadcrumbJsonLd, pageMetadata } from "@/lib/seo";
import { getTranslations } from "next-intl/server";
import type { Metadata } from "next";

type PageProps = {
  params: Promise<{ locale: string }>;
  searchParams: Promise<{ stripe?: string }>;
};

export async function generateMetadata({ params }: PageProps): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "/pricing",
    title: seo("pricingTitle"),
    description: seo("pricingDescription"),
    keywords: seo("pricingKeywords").split(",").map((k) => k.trim()),
  });
}

export default async function Pricing({ params, searchParams }: PageProps) {
  const [{ locale }, query] = await Promise.all([params, searchParams]);
  const billingLocale = locale === "zh" ? "zh" : "en";
  const dictionary = await getTranslations({ locale, namespace: "pricing" });
  const profile = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();
  const loginHint =
    session ? undefined
    : billingLocale === "zh"
      ? "请先登录，确保 Stripe 收据与账号绑定。"
    : "Log in so Stripe can associate the payment with your account.";

  return (
    <div className="qb-pricing-page">
      <JsonLd
        data={breadcrumbJsonLd(
          [
            { name: locale === "zh" ? "首页" : "Home", path: "" },
            { name: dictionary("title"), path: "/pricing" },
          ],
          locale,
        )}
      />
      <header className="qb-pricing-header">
        <p className="qb-pricing-eyebrow">{dictionary("title")}</p>
        <h1 className="qb-pricing-heading">{dictionary("heading")}</h1>
        <p className="qb-pricing-sub">{dictionary("subtitle")}</p>
        {session ?
          <p className="qb-pricing-hint">{dictionary("signedInHint")}</p>
        : null}
        {query.stripe === "canceled" ?
          <p className="qb-pricing-hint">{profile("stripeCanceled")}</p>
        : null}
      </header>

      <div className="qb-pricing-grid">
        {LIBRARY_PLANS.map((plan) => {
          const key = plan.id;
          const showList = plan.listAmount > plan.unitAmount;
          return (
            <article
              key={plan.id}
              className={plan.featured ? "qb-pricing-card is-featured" : "qb-pricing-card"}
            >
              {plan.featured ?
                <span className="qb-pricing-badge">{dictionary("bestValue")}</span>
              : null}
              <p className="qb-pricing-plan-name">{dictionary(`plans.${key}.name`)}</p>
              <div className="qb-pricing-price-row">
                <h2 className="qb-pricing-price">{formatUsdFromCents(plan.unitAmount)}</h2>
                {showList ?
                  <span className="qb-pricing-list-price">{formatUsdFromCents(plan.listAmount)}</span>
                : null}
              </div>
              {plan.discountPercent > 0 ?
                <p className="qb-pricing-save">{dictionary("savePercent", { percent: plan.discountPercent })}</p>
              : <p className="qb-pricing-save is-muted">{dictionary(`plans.${key}.rateNote`)}</p>}
              <p className="qb-pricing-valid">{dictionary(`plans.${key}.duration`)}</p>
              <p className="qb-pricing-lead">{dictionary(`plans.${key}.covers`)}</p>
              <p className="qb-pricing-audience">{dictionary(`plans.${key}.suitable`)}</p>
              <ul className="qb-pricing-bullets">
                <li>{dictionary(`plans.${key}.bullet1`)}</li>
                <li>{dictionary(`plans.${key}.bullet2`)}</li>
                <li>{dictionary(`plans.${key}.bullet3`)}</li>
              </ul>
              <div className="qb-pricing-cta">
                <CheckoutButton
                  locale={billingLocale}
                  planId={plan.id}
                  label={dictionary("cta")}
                  disabledReason={loginHint}
                />
              </div>
            </article>
          );
        })}
      </div>

      <p className="qb-pricing-footnote">{dictionary("footnote")}</p>
    </div>
  );
}
