"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

import AccountActions from "./AccountActions";
import AccountPasswordForm from "./AccountPasswordForm";

export type SocialLoginInfo = {
  provider: "google" | "wechat";
  displayName: string;
};

type Props = {
  locale: string;
  email: string;
  hasPassword: boolean;
  socialLogins: SocialLoginInfo[];
};

export default function AccountManagementPanel({
  locale,
  email,
  hasPassword,
  socialLogins,
}: Props) {
  const t = useTranslations("profile");
  const [resetOpen, setResetOpen] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);

  const providerLabel = (provider: SocialLoginInfo["provider"]) => {
    if (provider === "google") return t("loginProviderGoogle");
    return t("loginProviderWechat");
  };

  return (
    <div className="qb-account-mgmt">
      <div className="qb-account-info">
        {socialLogins.length > 0 ?
          socialLogins.map((login) => (
            <div key={login.provider} className="qb-account-info-row">
              <span className="qb-account-info-label">{providerLabel(login.provider)}</span>
              <span className="qb-account-info-value">{login.displayName}</span>
            </div>
          ))
        : null}

        {hasPassword ?
          <>
            <div className="qb-account-info-row">
              <span className="qb-account-info-label">{t("accountEmail")}</span>
              <span className="qb-account-info-value">{email}</span>
            </div>
            <div className="qb-account-info-row">
              <span className="qb-account-info-label">{t("accountPassword")}</span>
              <div className="qb-account-secret">
                <span className="qb-account-secret-value">
                  {passwordVisible ? t("passwordNotRetrievable") : "••••••••"}
                </span>
                <button
                  type="button"
                  className="qb-account-unhide"
                  onClick={() => setPasswordVisible((v) => !v)}
                >
                  {passwordVisible ? t("hidePassword") : t("unhidePassword")}
                </button>
              </div>
            </div>
          </>
        : socialLogins.length === 0 ?
          <div className="qb-account-info-row">
            <span className="qb-account-info-label">{t("accountEmail")}</span>
            <span className="qb-account-info-value">{email}</span>
          </div>
        : null}
      </div>

      {hasPassword ?
        <>
          {!resetOpen ?
            <button
              type="button"
              className="qb-pill-primary qb-account-reset-trigger"
              onClick={() => setResetOpen(true)}
            >
              {t("resetPasswordTitle")}
            </button>
          : null}
          {resetOpen ?
            <AccountPasswordForm onClose={() => setResetOpen(false)} />
          : null}
        </>
      : (
        <p className="qb-muted qb-account-oauth-note">{t("passwordOAuthOnly")}</p>
      )}

      <AccountActions locale={locale} />
    </div>
  );
}
