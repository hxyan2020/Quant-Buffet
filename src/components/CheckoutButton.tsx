"use client";

import { useState } from "react";

import type { PlanId } from "@/lib/plans";

export default function CheckoutButton({
  locale,
  planId,
  label,
  disabledReason,
}: {
  locale: "en" | "zh";
  planId: PlanId;
  label: string;
  disabledReason?: string;
}) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const disabled = !!disabledReason || loading;

  async function checkout() {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ locale, planId }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const code = typeof data?.error === "string" ? data.error : `checkout:${response.status}`;
        if (code === "UNAUTHORIZED") {
          setError(locale === "zh" ? "请先登录再付款。" : "Please log in before checking out.");
        } else if (code.includes("STRIPE_NOT_CONFIGURED")) {
          setError(
            locale === "zh" ?
              "支付尚未配置，请联系管理员。"
            : "Payments are not configured yet. Please contact support.",
          );
        } else {
          setError(locale === "zh" ? "无法打开 Stripe 结账，请稍后重试。" : "Could not start Stripe checkout. Try again.");
        }
        return;
      }
      if (typeof data.url !== "string") {
        setError(locale === "zh" ? "结账链接无效。" : "Invalid checkout link.");
        return;
      }
      window.location.href = data.url;
    } catch {
      setError(locale === "zh" ? "网络错误，请稍后重试。" : "Network error. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="qb-checkout-wrap">
      <button
        type="button"
        onClick={() => void checkout()}
        disabled={disabled}
        className="qb-pill-primary qb-pricing-pay"
      >
        {loading ?
          locale === "zh" ?
            "正在跳转…"
          : "Redirecting…"
        : label}
      </button>
      {disabledReason ? <p className="qb-pricing-login-warn">{disabledReason}</p> : null}
      {error ? <p className="qb-auth-error">{error}</p> : null}
    </div>
  );
}
