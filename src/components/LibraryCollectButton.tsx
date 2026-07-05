"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";
import { useTranslations } from "next-intl";

import CollectionToast from "./CollectionToast";

type Props = {
  strategyId: string;
  locale: string;
  initialCollected: boolean;
  isLoggedIn: boolean;
};

export default function LibraryCollectButton({
  strategyId,
  locale,
  initialCollected,
  isLoggedIn,
}: Props) {
  const t = useTranslations("library");
  const router = useRouter();
  const [collected, setCollected] = useState(initialCollected);
  const [pending, startTransition] = useTransition();
  const [toastOpen, setToastOpen] = useState(false);

  if (!isLoggedIn) {
    return <span className="qb-muted">—</span>;
  }

  function toggle() {
    startTransition(async () => {
      const res = await fetch("/api/collections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          strategyId,
          action: collected ? "uncollect" : "collect",
        }),
      });
      if (!res.ok) return;
      const data = await res.json();
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
        className={collected ? "qb-collect-link is-active" : "qb-collect-link"}
        disabled={pending}
        onClick={() => toggle()}
      >
        {collected ? t("collected") : t("collect")}
      </button>
      <CollectionToast locale={locale} open={toastOpen} onClose={() => setToastOpen(false)} />
    </>
  );
}
