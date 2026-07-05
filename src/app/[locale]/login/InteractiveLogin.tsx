"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { signIn } from "next-auth/react";
import { useTranslations } from "next-intl";

type Props = {
  locale: string;
  next?: string;
  googleEnabled: boolean;
  onSuccess?: () => void;
};

export default function InteractiveLogin({ locale, next, googleEnabled, onSuccess }: Props) {
  const router = useRouter();
  const authText = useTranslations("auth");
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const successPath =
    typeof next === "string" && next.startsWith(`/${locale}`) ? next
    : typeof next === "string" && next.startsWith("/") ? next
      : `/${locale}/account/plan`;

  const googleButtonDisabled = useMemo(() => !googleEnabled || busy, [googleEnabled, busy]);

  const handleCredentials = async (event?: React.FormEvent) => {
    event?.preventDefault();
    setError(null);

    const trimmedEmail = email.trim().toLowerCase();
    if (!trimmedEmail || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(trimmedEmail)) {
      setError(authText("errorInvalidEmail"));
      return;
    }
    if (password.length < 8) {
      setError(authText("errorPasswordShort"));
      return;
    }

    setBusy(true);
    try {
      if (mode === "register") {
        const resp = await fetch("/api/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: trimmedEmail,
            password,
            ...(fullName.trim() ? { name: fullName.trim() } : {}),
          }),
        });
        const json = await resp.json().catch(() => ({}));
        if (!resp.ok && json?.error === "EMAIL_EXISTS") {
          setError(authText("errorEmailExists"));
          return;
        }
        if (!resp.ok) {
          setError(authText("errorRegisterFailed"));
          return;
        }
      }

      const result = await signIn("credentials", {
        redirect: false,
        email: trimmedEmail,
        password,
      });

      if (!result?.ok) {
        setError(authText("errorLoginFailed"));
        return;
      }

      onSuccess?.();
      router.replace(successPath);
      router.refresh();
    } catch {
      setError(authText("errorNetwork"));
    } finally {
      setBusy(false);
    }
  };

  return (
    <form className="qb-auth-form" onSubmit={(e) => void handleCredentials(e)}>
      <h2 id="auth-modal-title" className="qb-auth-heading">
        {mode === "login" ? authText("title") : authText("registerTitle")}
      </h2>

      <div className="qb-auth-tabs" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={mode === "login"}
          className={mode === "login" ? "qb-auth-tab is-active" : "qb-auth-tab"}
          onClick={() => {
            setMode("login");
            setError(null);
          }}
        >
          {authText("title")}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={mode === "register"}
          className={mode === "register" ? "qb-auth-tab is-active" : "qb-auth-tab"}
          onClick={() => {
            setMode("register");
            setError(null);
          }}
        >
          {authText("registerTitle")}
        </button>
      </div>

      <div className="qb-auth-oauth">
        <button
          type="button"
          disabled={googleButtonDisabled}
          onClick={() => signIn("google", { callbackUrl: successPath })}
          className="qb-auth-oauth-btn"
        >
          {authText("google")}
        </button>
        <button type="button" disabled className="qb-auth-oauth-btn is-disabled">
          {authText("wechat")}
        </button>
      </div>

      <div className="qb-auth-divider">
        <span>{authText("credentials")}</span>
      </div>

      <div className="qb-auth-fields">
        {mode === "register" ?
          <label className="qb-auth-label">
            <span>{authText("displayName")}</span>
            <input
              className="qb-auth-input"
              autoComplete="name"
              value={fullName}
              onChange={(evt) => setFullName(evt.target.value)}
            />
          </label>
        : null}

        <label className="qb-auth-label">
          <span>{authText("email")}</span>
          <input
            className="qb-auth-input"
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(evt) => setEmail(evt.target.value)}
          />
        </label>

        <label className="qb-auth-label">
          <span>{authText("password")}</span>
          <input
            className="qb-auth-input"
            type="password"
            required
            minLength={8}
            autoComplete={mode === "register" ? "new-password" : "current-password"}
            value={password}
            onChange={(evt) => setPassword(evt.target.value)}
          />
        </label>
      </div>

      {error ? <p className="qb-auth-error">{error}</p> : null}

      <button type="submit" disabled={busy} className="qb-auth-submit">
        {busy ?
          mode === "login" ?
            authText("submittingLogin")
          : authText("submittingRegister")
        : mode === "login" ?
          authText("submitLogin")
        : authText("submitRegister")}
      </button>

      <p className="qb-auth-footnote">
        <Link prefetch href={`/${locale}/pricing`}>
          {authText("pricingLink")}
        </Link>
      </p>
    </form>
  );
}
