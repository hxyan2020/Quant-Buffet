"use client";

import Link from "next/link";
import { useTranslations } from "next-intl";

type Props = {
  locale: string;
  open: boolean;
  onClose: () => void;
};

export default function CollectionToast({ locale, open, onClose }: Props) {
  const t = useTranslations("strategy");

  if (!open) return null;

  return (
    <div className="qb-toast-backdrop" role="presentation" onClick={onClose}>
      <div
        className="qb-toast-card"
        role="alertdialog"
        aria-live="polite"
        onClick={(e) => e.stopPropagation()}
      >
        <p className="qb-toast-title">{t("collectSuccessTitle")}</p>
        <p className="qb-toast-body">{t("collectSuccessBody")}</p>
        <div className="qb-toast-actions">
          <Link className="qb-pill-primary" href={`/${locale}/account/collected`} onClick={onClose}>
            {t("collectSuccessCta")}
          </Link>
          <button type="button" className="qb-secondary" onClick={onClose}>
            {t("collectSuccessClose")}
          </button>
        </div>
      </div>
    </div>
  );
}
