"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { getSession, signIn, signOut } from "next-auth/react";

export default function AdminLoginForm() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await signIn("credentials", {
        redirect: false,
        email,
        password,
      });

      if (!result?.ok) {
        setError("Invalid email or password.");
        return;
      }

      const session = await getSession();
      if (session?.user?.role !== "ADMIN") {
        await signOut({ redirect: false });
        setError("This account does not have admin access.");
        return;
      }

      router.replace("/admin/strategies");
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="qb-admin-login-form" onSubmit={(e) => void handleSubmit(e)}>
      <label className="qb-admin-label">
        Email
        <input
          className="qb-admin-input"
          type="email"
          autoComplete="username"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </label>
      <label className="qb-admin-label">
        Password
        <input
          className="qb-admin-input"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </label>
      {error ?
        <p className="qb-admin-error" role="alert">
          {error}
        </p>
      : null}
      <button type="submit" className="qb-admin-btn-primary" disabled={busy}>
        {busy ? "Signing in…" : "Sign in to admin"}
      </button>
    </form>
  );
}
