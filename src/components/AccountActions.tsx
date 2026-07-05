"use client";

import { signOut } from "next-auth/react";
import { useTranslations } from "next-intl";

export default function AccountActions({ locale }: { locale: string }) {
  const nav = useTranslations("nav");

  return (
    <div className="qb-account-actions flex flex-wrap gap-4">
      <button type="button" className="qb-secondary" onClick={() => signOut({ callbackUrl: `/${locale}` })}>
        {nav("logout")}
      </button>
    </div>
  );
}
