"use client";

import Link from "next/link";
import { signOut } from "next-auth/react";
import { useEffect, useRef, useState } from "react";

type Labels = {
  profile: string;
  collected: string;
  plan: string;
  billing: string;
  account: string;
  login: string;
  logout: string;
  admin: string;
};

type Props = {
  locale: string;
  labels: Labels;
  isLoggedIn: boolean;
  isAdmin: boolean;
  onLoginClick: () => void;
};

export default function ProfileMenu({
  locale,
  labels,
  isLoggedIn,
  isAdmin,
  onLoginClick,
}: Props) {
  const base = `/${locale}`;
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const onDoc = (event: MouseEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const items = isLoggedIn
    ? [
        { href: `${base}/account/collected`, label: labels.collected },
        { href: `${base}/account/plan`, label: labels.plan },
        { href: `${base}/account/billing`, label: labels.billing },
        { href: `${base}/account`, label: labels.account },
        ...(isAdmin ? [{ href: "/admin/strategies", label: labels.admin }] : []),
      ]
    : [];

  return (
    <div className="qb-profile-wrap" ref={rootRef}>
      <button
        type="button"
        className="qb-profile-btn"
        aria-expanded={open}
        aria-haspopup="menu"
        onClick={() => setOpen((value) => !value)}
      >
        {labels.profile}
      </button>
      {open ?
        <div className="qb-profile-menu" role="menu">
          {items.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="qb-profile-menu-item"
              role="menuitem"
              onClick={() => setOpen(false)}
            >
              {item.label}
            </Link>
          ))}
          {isLoggedIn ?
            <button
              type="button"
              className="qb-profile-menu-item qb-profile-menu-item-btn"
              role="menuitem"
              onClick={() => {
                setOpen(false);
                void signOut({ callbackUrl: base });
              }}
            >
              {labels.logout}
            </button>
          : (
            <button
              type="button"
              className="qb-profile-menu-item qb-profile-menu-item-btn"
              role="menuitem"
              onClick={() => {
                setOpen(false);
                onLoginClick();
              }}
            >
              {labels.login}
            </button>
          )}
        </div>
      : null}
    </div>
  );
}
