"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useTranslations } from "next-intl";

type Props = {
  locale: string;
  hasActivePlan: boolean;
  expiresAtIso: string | null;
  cancelAtPeriodEnd: boolean;
  tier: string | null;
};

export default function PlanPanel({
  locale,
  hasActivePlan,
  expiresAtIso,
  cancelAtPeriodEnd,
  tier,
}: Props) {
  const t = useTranslations("profile");
  const nav = useTranslations("nav");
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const expiresLabel =
    expiresAtIso ?
      new Date(expiresAtIso).toLocaleDateString(locale === "zh" ? "zh-CN" : "en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : null;

  async function cancelPlan() {
    if (!confirm(t("cancelConfirm"))) return;
    setBusy(true);
    setMessage(null);
    try {
      const res = await fetch("/api/account/cancel-plan", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setMessage(t("cancelFailed"));
        return;
      }
      setMessage(
        cancelAtPeriodEnd ? t("alreadyCancelled") : t("cancelScheduled", { date: expiresLabel ?? "" }),
      );
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  if (!hasActivePlan) {
    return (
      <div className="qb-plan-panel">
        <p className="qb-plan-status">{t("noPlan")}</p>
        <Link className="qb-pill-primary qb-plan-cta" href={`/${locale}/pricing`}>
          {t("goPricing")}
        </Link>
      </div>
    );
  }

  return (
    <div className="qb-plan-panel">
      <p className="qb-plan-status">
        {t("currentPlan")}: <strong>{tier ?? "full-library"}</strong>
      </p>
      {expiresLabel ?
        <p className="qb-muted">{t("accessUntil", { date: expiresLabel })}</p>
      : null}
      {cancelAtPeriodEnd ?
        <p className="qb-plan-warn">{t("cancelledReminder", { date: expiresLabel ?? "" })}</p>
      : (
        <>
          <p className="qb-muted">{t("cancelHint", { date: expiresLabel ?? "" })}</p>
          <button
            type="button"
            className="qb-secondary qb-plan-cta"
            disabled={busy}
            onClick={() => void cancelPlan()}
          >
            {t("cancelPlan")}
          </button>
        </>
      )}
      {message ? <p className="qb-auth-success">{message}</p> : null}
      <p className="qb-muted" style={{ marginTop: "1rem" }}>
        <Link className="qb-accent-link" href={`/${locale}/pricing`}>
          {nav("pricing")}
        </Link>
      </p>
    </div>
  );
}
