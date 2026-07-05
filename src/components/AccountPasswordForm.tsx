"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";

type Props = {
  onClose?: () => void;
};

export default function AccountPasswordForm({ onClose }: Props) {
  const t = useTranslations("profile");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    setError(null);

    if (newPassword.length < 8) {
      setError(t("passwordTooShort"));
      return;
    }
    if (newPassword !== confirmPassword) {
      setError(t("passwordMismatch"));
      return;
    }

    setBusy(true);
    try {
      const res = await fetch("/api/account/password", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ currentPassword, newPassword }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (data.error === "WRONG_PASSWORD") setError(t("passwordWrong"));
        else if (data.error === "NO_PASSWORD") setError(t("passwordOAuthOnly"));
        else setError(t("passwordFailed"));
        return;
      }
      setMessage(t("passwordUpdated"));
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="qb-account-password-form" onSubmit={(e) => void submit(e)}>
      <div className="qb-account-password-head">
        <h3 className="qb-card-subtitle">{t("resetPasswordTitle")}</h3>
        {onClose ?
          <button type="button" className="qb-account-form-close" onClick={onClose}>
            {t("resetPasswordClose")}
          </button>
        : null}
      </div>
      <p className="qb-muted">{t("resetPasswordHint")}</p>
      <label className="qb-auth-label">
        <span>{t("currentPassword")}</span>
        <input
          className="qb-auth-input"
          type="password"
          autoComplete="current-password"
          value={currentPassword}
          onChange={(e) => setCurrentPassword(e.target.value)}
        />
      </label>
      <label className="qb-auth-label">
        <span>{t("newPassword")}</span>
        <input
          className="qb-auth-input"
          type="password"
          autoComplete="new-password"
          value={newPassword}
          onChange={(e) => setNewPassword(e.target.value)}
        />
      </label>
      <label className="qb-auth-label">
        <span>{t("confirmPassword")}</span>
        <input
          className="qb-auth-input"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
        />
      </label>
      {error ? <p className="qb-auth-error">{error}</p> : null}
      {message ? <p className="qb-auth-success">{message}</p> : null}
      <button type="submit" className="qb-pill-primary" disabled={busy}>
        {t("updatePassword")}
      </button>
    </form>
  );
}
