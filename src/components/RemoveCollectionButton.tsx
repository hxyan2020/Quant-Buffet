"use client";

import { useRouter } from "next/navigation";
import { useTransition } from "react";
import { useTranslations } from "next-intl";

type Props = {
  strategyId: string;
};

export default function RemoveCollectionButton({ strategyId }: Props) {
  const t = useTranslations("profile");
  const router = useRouter();
  const [pending, startTransition] = useTransition();

  return (
    <button
      type="button"
      className="qb-secondary qb-remove-collect"
      disabled={pending}
      onClick={() => {
        startTransition(async () => {
          await fetch("/api/collections", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ strategyId, action: "uncollect" }),
          });
          router.refresh();
        });
      }}
    >
      {t("removeCollected")}
    </button>
  );
}
