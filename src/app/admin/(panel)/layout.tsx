import type { PropsWithChildren } from "react";
import Link from "next/link";
import { redirect } from "next/navigation";

import { auth } from "@/auth";
import BrandLogo from "@/components/BrandLogo";

export default async function AdminPanelLayout({ children }: PropsWithChildren) {
  const session = await auth();

  if (!session?.user) {
    redirect("/admin/login");
  }

  if (session.user.role !== "ADMIN") {
    redirect("/admin/login?error=forbidden");
  }

  return (
    <div className="qb-admin-shell">
      <header className="qb-admin-topbar">
        <div className="qb-admin-topbar-inner">
          <Link href="/admin/strategies" className="qb-admin-brand">
            <BrandLogo size={32} />
            <span>Quant Buffet Admin</span>
          </Link>
          <nav className="qb-admin-topnav">
            <Link href="/admin/strategies">Strategies</Link>
            <Link href="/admin/tooltips">Python tooltips</Link>
            <Link href="/en/strategy-library" target="_blank" rel="noopener noreferrer">
              View site
            </Link>
            <Link href="/api/auth/signout?callbackUrl=/admin/login">Sign out</Link>
          </nav>
        </div>
      </header>
      <main className="qb-admin-main">{children}</main>
    </div>
  );
}
