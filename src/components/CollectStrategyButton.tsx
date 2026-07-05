"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { useTranslations } from "next-intl";

import CollectionToast from "./CollectionToast";

type Props = {
  strategyId: string;
  locale: string;
  initialCollected: boolean;
  isLoggedIn: boolean;
  loginHref: string;
};

export default function CollectStrategyButton({
  strategyId,
  locale,
  initialCollected,
  isLoggedIn,
  loginHref,
}: Props) {
  const t = useTranslations("strategy");
  const router = useRouter();
  const [collected, setCollected] = useState(initialCollected);
  const [pending, startTransition] = useTransition();
  const [toastOpen, setToastOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isLoggedIn) {
    return (
      <Link className="qb-collect-btn qb-collect-btn-outline" href={loginHref}>
        {t("collectLogin")}
      </Link>
    );
  }

  async function toggle() {
    setError(null);
    startTransition(async () => {
      const res = await fetch("/api/collections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategyId,
          action: collected ? "uncollect" : "collect",
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setError(t("collectError"));
        return;
      }
      const nowCollected = Boolean(data.collected);
      setCollected(nowCollected);
      if (nowCollected) setToastOpen(true);
      router.refresh();
    });
  }

  return (
    <>
      <button
        type="button"
        className={collected ? "qb-collect-btn qb-collect-btn-active" : "qb-collect-btn"}
        disabled={pending}
        onClick={() => void toggle()}
        aria-pressed={collected}
      >
        {collected ? t("collected") : t("collect")}
      </button>
      {error ? <p className="qb-auth-error">{error}</p> : null}
      <CollectionToast locale={locale} open={toastOpen} onClose={() => setToastOpen(false)} />
    </>
  );
}
