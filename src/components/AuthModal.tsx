"use client";

import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import InteractiveLogin from "@/app/[locale]/login/InteractiveLogin";

type Props = {
  locale: string;
  googleEnabled: boolean;
  open?: boolean;
  onClose?: () => void;
};

export default function AuthModal({ locale, googleEnabled, open: controlledOpen, onClose }: Props) {
  const searchParams = useSearchParams();
  const authQuery = searchParams.get("auth");
  const next = searchParams.get("next") ?? undefined;

  const [internalOpen, setInternalOpen] = useState(false);
  const isOpen =
    Boolean(controlledOpen) ||
    internalOpen ||
    authQuery === "login" ||
    authQuery === "register";

  const close = useCallback(() => {
    setInternalOpen(false);
    onClose?.();
    if (authQuery) {
      const url = new URL(window.location.href);
      url.searchParams.delete("auth");
      url.searchParams.delete("next");
      window.history.replaceState({}, "", url.pathname + url.search);
    }
  }, [authQuery, onClose]);

  useEffect(() => {
    if (!isOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [isOpen, close]);

  if (!isOpen) return null;

  return (
    <div className="qb-auth-backdrop" role="presentation" onClick={close}>
      <div
        className="qb-auth-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="auth-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <button type="button" className="qb-auth-close" onClick={close} aria-label="Close">
          ×
        </button>
        <InteractiveLogin
          locale={locale}
          next={next}
          googleEnabled={googleEnabled}
          onSuccess={close}
        />
      </div>
    </div>
  );
}

export function useAuthModal() {
  const [open, setOpen] = useState(false);
  return {
    open,
    openLogin: () => setOpen(true),
    close: () => setOpen(false),
  };
}
