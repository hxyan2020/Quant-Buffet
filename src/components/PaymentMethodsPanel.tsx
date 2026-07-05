"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

type Props = {
  locale: string;
  hasCustomer: boolean;
  paymentHint: string | null;
};

export default function PaymentMethodsPanel({ locale, hasCustomer, paymentHint }: Props) {
  const t = useTranslations("profile");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function openPortal() {
    setBusy(true);
    setError(null);
    try {
      const res = await fetch("/api/account/billing-portal", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ locale }),
      });
      const data = await res.json();
      if (!res.ok || !data.url) {
        setError(t("paymentPortalError"));
        return;
      }
      window.location.href = data.url;
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="qb-payment-panel">
      <p className="qb-muted">{t("paymentHint")}</p>
      {paymentHint ?
        <p className="qb-payment-current">
          <span className="qb-paper-meta-label">{t("paymentCurrent")}</span>
          {paymentHint}
        </p>
      : (
        <p className="qb-muted">{t("paymentNone")}</p>
      )}
      {hasCustomer ?
        <button type="button" className="qb-pill-primary" disabled={busy} onClick={() => void openPortal()}>
          {t("managePayment")}
        </button>
      : (
        <p className="qb-muted">{t("paymentAfterCheckout")}</p>
      )}
      {error ? <p className="qb-auth-error">{error}</p> : null}
    </div>
  );
}
