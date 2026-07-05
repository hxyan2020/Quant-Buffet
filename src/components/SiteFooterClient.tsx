"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import LegalModal, { type LegalPanel } from "@/components/LegalModal";

type Props = {
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

  return (
    <>
      <footer className="qb-footer-float-bar" aria-label="Legal">
        <button type="button" className="qb-footer-pill" onClick={() => openPanel("terms")}>
          {termsLabel}
        </button>
        <button type="button" className="qb-footer-pill" onClick={() => openPanel("contact")}>
          {contactLabel}
        </button>
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
