"use client";

import { useState } from "react";

export default function CheckoutButton({
  locale,
  label,
  disabledReason,
}: {
  locale: "en" | "zh";
  label: string;
  disabledReason?: string;
}) {
  const [loading, setLoading] = useState(false);
  const disabled = !!disabledReason || loading;

  async function checkout() {
    setLoading(true);
    try {
      const response = await fetch("/api/stripe/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ locale }),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(
          typeof data?.error === "string" ? data.error : `checkout:${response.status}`,
        );
      }
      if (typeof data.url !== "string") {
        throw new Error("checkout:url");
      }
      window.location.href = data.url;
    } catch (error) {
      const code = typeof error === "object" && error && "message" in error ? String(error.message) : "unknown";
      if (code.includes("STRIPE_NOT_CONFIGURED")) {
        alert("Set STRIPE_SECRET_KEY plus STRIPE_WEBHOOK_SECRET locally and restart npm run dev.");
      } else if (code === "UNAUTHORIZED") {
        alert("Please log in before checking out.");
      } else {
        alert("Stripe checkout failed. Review server logs.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-3">
      <button type="button" onClick={() => checkout()} disabled={disabled} className="qb-pill-primary px-12 text-[16px]">
        {loading ? "Redirecting..." : label}
      </button>
      {disabledReason ? <p className="text-xs text-yellow-400">{disabledReason}</p> : null}
    </div>
  );
}
