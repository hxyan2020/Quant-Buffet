"use client";

import Link from "next/link";

import AuthModal, { useAuthModal } from "@/components/AuthModal";
import BrandLogo from "@/components/BrandLogo";
import LocaleSwitcher from "@/components/LocaleSwitcher";
import ProfileMenu from "@/components/ProfileMenu";

type NavLink = { href: string; label: string };

type Props = {
  locale: string;
  brandName: string;
  brandTagline: string;
  navLinks: NavLink[];
  profileLabels: {
    profile: string;
    collected: string;
    plan: string;
    billing: string;
    account: string;
    login: string;
    logout: string;
    admin: string;
  };
  isLoggedIn: boolean;
  isAdmin: boolean;
  googleEnabled: boolean;
  handwritingClass: string;
};

export default function SiteHeaderShell({
  locale,
  brandName,
  brandTagline,
  navLinks,
  profileLabels,
  isLoggedIn,
  isAdmin,
  googleEnabled,
  handwritingClass,
}: Props) {
  const base = `/${locale}`;
  const auth = useAuthModal();

  return (
    <>
      <header className="qb-header">
        <div className="qb-header-float">
          <div className="qb-header-pill">
            <div className="qb-brand">
              <BrandLogo size={36} className="qb-brand-logo" />
              <div className="qb-brand-text">
                <Link href={base} className="qb-brand-name">
                  {brandName}
                </Link>
                <span className={`qb-brand-tagline ${handwritingClass}`}>{brandTagline}</span>
              </div>
            </div>

            <nav className="qb-nav-desktop" aria-label="Main">
              {navLinks.map((item) => (
                <Link key={item.href} className="qb-nav-link" href={item.href}>
                  {item.label}
                </Link>
              ))}
            </nav>

            <div className="qb-header-actions">
              <LocaleSwitcher locale={locale} />
              <ProfileMenu
                locale={locale}
                labels={profileLabels}
                isLoggedIn={isLoggedIn}
                isAdmin={isAdmin}
                onLoginClick={auth.openLogin}
              />
            </div>
          </div>
        </div>

        <nav className="qb-nav-mobile" aria-label="Main mobile">
          {navLinks.map((item) => (
            <Link key={item.href} className="qb-nav-link" href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
      </header>

      {/* Outside header so pointer-events:none on .qb-header does not block clicks */}
      <AuthModal
        locale={locale}
        googleEnabled={googleEnabled}
        open={auth.open}
        onClose={auth.close}
      />
    </>
  );
}
