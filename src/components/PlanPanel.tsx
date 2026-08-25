"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { useTranslations } from "next-intl";

type Props = {
  locale: string;
  hasActivePlan: boolean;
  expiresAtIso: string | null;
  cancelAtPeriodEnd: boolean;
  tier: string | null;
  tierLabel: string | null;
  status: "none" | "active" | "canceling" | "expired";
  checkoutSessionId?: string | null;
  stripeFlash?: "success" | "canceled" | null;
};

export default function PlanPanel({
  locale,
  hasActivePlan,
  expiresAtIso,
  cancelAtPeriodEnd,
  tier,
  tierLabel,
  status,
  checkoutSessionId,
  stripeFlash,
}: Props) {
  const t = useTranslations("profile");
  const nav = useTranslations("nav");
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const expiresLabel =
    expiresAtIso ?
      new Date(expiresAtIso).toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : null;

  const confirmCheckout = useCallback(async () => {
    if (!checkoutSessionId) return;
    setConfirming(true);
    setError(null);
    try {
      const res = await fetch("/api/stripe/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId: checkoutSessionId }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(t("confirmFailed"));
        return;
      }
      setMessage(t("stripeSuccess"));
      router.refresh();
    } finally {
      setConfirming(false);
    }
  }, [checkoutSessionId, router, t]);

  useEffect(() => {
    if (stripeFlash === "success" && checkoutSessionId) {
      void confirmCheckout();
    } else if (stripeFlash === "success") {
      setMessage(t("stripeSuccess"));
      router.refresh();
    }
  }, [stripeFlash, checkoutSessionId, confirmCheckout, router, t]);

  async function cancelPlan() {
    if (!confirm(t("cancelConfirm"))) return;
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const res = await fetch("/api/account/cancel-plan", { method: "POST" });
      if (!res.ok) {
        setError(t("cancelFailed"));
        return;
      }
      setMessage(t("cancelScheduled", { date: expiresLabel ?? "" }));
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  async function resumePlan() {
    setBusy(true);
    setMessage(null);
    setError(null);
    try {
      const res = await fetch("/api/account/resume-plan", { method: "POST" });
      if (!res.ok) {
        setError(t("resumeFailed"));
        return;
      }
      setMessage(t("resumeSuccess"));
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  const statusLabel =
    status === "active" ? t("statusActive")
    : status === "canceling" ? t("statusCanceling")
    : status === "expired" ? t("statusExpired")
    : t("statusNone");

  if (!hasActivePlan) {
    return (
      <div className="qb-plan-panel">
        {stripeFlash === "canceled" ?
          <p className="qb-muted">{t("stripeCanceled")}</p>
        : null}
        {confirming ? <p className="qb-muted">{t("confirmingPayment")}</p> : null}
        {message ? <p className="qb-auth-success">{message}</p> : null}
        {error ? <p className="qb-auth-error">{error}</p> : null}
        <div className="qb-plan-status-row">
          <span className="qb-plan-badge is-muted">{statusLabel}</span>
        </div>
        <p className="qb-plan-status">{t("noPlan")}</p>
        <div className="qb-plan-actions">
          <Link className="qb-pill-primary qb-plan-cta" href={`/${locale}/pricing`}>
            {t("goPricing")}
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="qb-plan-panel">
      {confirming ? <p className="qb-muted">{t("confirmingPayment")}</p> : null}
      {message ? <p className="qb-auth-success">{message}</p> : null}
      {error ? <p className="qb-auth-error">{error}</p> : null}

      <div className="qb-plan-status-row">
        <span className={`qb-plan-badge ${cancelAtPeriodEnd ? "is-warn" : "is-ok"}`}>
          {statusLabel}
        </span>
      </div>

      <p className="qb-plan-status">
        {t("currentPlan")}: <strong>{tierLabel ?? tier ?? "full-library"}</strong>
      </p>
      {expiresLabel ?
        <p className="qb-muted">{t("accessUntil", { date: expiresLabel })}</p>
      : null}

      {cancelAtPeriodEnd ?
        <>
          <p className="qb-plan-warn">{t("cancelledReminder", { date: expiresLabel ?? "" })}</p>
          <div className="qb-plan-actions">
            <button
              type="button"
              className="qb-pill-primary qb-plan-cta"
              disabled={busy}
              onClick={() => void resumePlan()}
            >
              {t("resumePlan")}
            </button>
            <Link className="qb-secondary qb-plan-cta" href={`/${locale}/pricing`}>
              {t("renewPlan")}
            </Link>
          </div>
        </>
      : (
        <>
          <p className="qb-muted">{t("cancelHint", { date: expiresLabel ?? "" })}</p>
          <div className="qb-plan-actions">
            <Link className="qb-pill-primary qb-plan-cta" href={`/${locale}/pricing`}>
              {t("renewPlan")}
            </Link>
            <button
              type="button"
              className="qb-secondary qb-plan-cta"
              disabled={busy}
              onClick={() => void cancelPlan()}
            >
              {t("cancelPlan")}
            </button>
            <Link className="qb-accent-link" href={`/${locale}/account/payment`}>
              {t("payment")}
            </Link>
          </div>
        </>
      )}

      <p className="qb-muted qb-plan-foot">
        <Link className="qb-accent-link" href={`/${locale}/pricing`}>
          {nav("pricing")}
        </Link>
        {" · "}
        <Link className="qb-accent-link" href={`/${locale}/account/billing`}>
          {t("billing")}
        </Link>
      </p>
    </div>
  );
}
