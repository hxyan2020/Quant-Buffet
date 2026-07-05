import { auth } from "@/auth";
import CheckoutButton from "@/components/CheckoutButton";
import { getTranslations } from "next-intl/server";

type PageProps = { params: Promise<{ locale: string }> };

export default async function Pricing({ params }: PageProps) {
  const { locale } = await params;
  const billingLocale = locale === "zh" ? "zh" : "en";
  const dictionary = await getTranslations({ locale, namespace: "pricing" });
  const session = await auth();

  return (
    <div className="qb-pricing-page">
      <div className="qb-pricing-card">
        <p className="qb-pricing-eyebrow">{dictionary("title")}</p>
        <h1 className="qb-pricing-price">{dictionary("price")}</h1>
        <p className="qb-pricing-lead">{dictionary("once")}</p>
        <p className="qb-pricing-valid">{dictionary("validPeriod")}</p>
        <p className="qb-pricing-hint">{dictionary("signedInHint")}</p>

        <div className="qb-pricing-cta">
          <CheckoutButton
            locale={billingLocale}
            label={dictionary("cta")}
            disabledReason={
              session ? undefined :
                billingLocale === "zh"
                  ? "请先登录，确保 Stripe 收据与账号绑定。"
                : "Log in so Stripe can associate the payment with your account."
            }
          />
        </div>

        <p className="qb-pricing-footnote">{dictionary("footnote")}</p>
      </div>
    </div>
  );
}
