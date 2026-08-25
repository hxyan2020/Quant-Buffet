"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import LegalModal, { type LegalPanel } from "@/components/LegalModal";

type Props = {
  locale: string;
  termsLabel: string;
  contactLabel: string;
  termsTitle: string;
  termsBody: string;
  contactTitle: string;
  contactBody: string;
  contactTelegram: string;
  contactEmail: string;
};

export default function SiteFooterClient({
  locale,
  termsLabel,
  contactLabel,
  termsTitle,
  termsBody,
  contactTitle,
  contactBody,
  contactTelegram,
  contactEmail,
}: Props) {
  const searchParams = useSearchParams();
  const pathname = usePathname();
  const router = useRouter();
  const [panel, setPanel] = useState<LegalPanel>(null);

  const openPanel = useCallback((next: LegalPanel) => setPanel(next), []);
  const closePanel = useCallback(() => {
    setPanel(null);
    const legal = searchParams.get("legal");
    if (legal) {
      const url = new URL(window.location.href);
      url.searchParams.delete("legal");
      router.replace(url.pathname + url.search);
    }
  }, [router, searchParams]);

  useEffect(() => {
    const legal = searchParams.get("legal");
    if (legal === "terms" || legal === "contact") {
      setPanel(legal);
    }
  }, [searchParams]);

  // Prefer dedicated SEO pages; keep modal for deep-links (?legal=).
  const onTermsPage = pathname?.includes("/terms");
  const onContactPage = pathname?.includes("/contact");

  return (
    <>
      <footer className="qb-footer-float-bar" aria-label="Legal">
        <Link
          href={`/${locale}/terms`}
          className="qb-footer-pill"
          onClick={(e) => {
            if (!onTermsPage && e.metaKey !== true && e.ctrlKey !== true) {
              e.preventDefault();
              openPanel("terms");
            }
          }}
        >
          {termsLabel}
        </Link>
        <Link
          href={`/${locale}/contact`}
          className="qb-footer-pill"
          onClick={(e) => {
            if (!onContactPage && e.metaKey !== true && e.ctrlKey !== true) {
              e.preventDefault();
              openPanel("contact");
            }
          }}
        >
          {contactLabel}
        </Link>
      </footer>

      <LegalModal
        panel={panel}
        onClose={closePanel}
        termsTitle={termsTitle}
        termsBody={termsBody}
        contactTitle={contactTitle}
        contactBody={contactBody}
        contactTelegram={contactTelegram}
        contactEmail={contactEmail}
      />
    </>
  );
}
