"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

type Tab = { href: string; label: string };

export default function AccountNav({ tabs }: { tabs: Tab[] }) {
  const pathname = usePathname();

  return (
    <nav className="qb-account-nav" aria-label="Account">
      {tabs.map((tab) => {
        const active =
          pathname === tab.href ||
          (tab.href.endsWith("/account") && pathname === tab.href);
        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={active ? "qb-account-nav-link is-active" : "qb-account-nav-link"}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
