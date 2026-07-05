"use client";

import { useCallback, useEffect } from "react";

export type LegalPanel = "terms" | "contact" | null;

type Props = {
  panel: LegalPanel;
  onClose: () => void;
  termsTitle: string;
  termsBody: string;
  contactTitle: string;
  contactBody: string;
  contactTelegram: string;
  contactEmail: string;
};

export default function LegalModal({
  panel,
  onClose,
  termsTitle,
  termsBody,
  contactTitle,
  contactBody,
  contactTelegram,
  contactEmail,
}: Props) {
  const close = useCallback(() => onClose(), [onClose]);

  useEffect(() => {
    if (!panel) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") close();
    };
    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKey);
    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKey);
    };
  }, [panel, close]);

  if (!panel) return null;

  const title = panel === "terms" ? termsTitle : contactTitle;

  return (
    <div className="qb-legal-backdrop" role="presentation" onClick={close}>
      <div
        className="qb-legal-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="legal-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        <button type="button" className="qb-legal-close" onClick={close} aria-label="Close">
          ×
        </button>
        <h2 id="legal-modal-title" className="qb-legal-modal-title">
          {title}
        </h2>
        <div className="qb-legal-modal-body">
          {panel === "terms" ?
            termsBody.split("\n\n").map((paragraph) => <p key={paragraph.slice(0, 32)}>{paragraph}</p>)
          : (
            <>
              {contactBody.split("\n\n").map((paragraph) => (
                <p key={paragraph.slice(0, 32)}>{paragraph}</p>
              ))}
              <ul className="qb-contact-emoji-list">
                <li>
                  <span aria-hidden>💬</span>
                  <span>
                    <strong>Telegram</strong>
                    <br />
                    <a href="https://t.me/+6588023346" target="_blank" rel="noopener noreferrer">
                      {contactTelegram}
                    </a>
                  </span>
                </li>
                <li>
                  <span aria-hidden>✉️</span>
                  <span>
                    <strong>Email</strong>
                    <br />
                    <a href={`mailto:${contactEmail}`}>{contactEmail}</a>
                  </span>
                </li>
                <li>
                  <span aria-hidden>📚</span>
                  <span>
                    <strong>Strategy library</strong>
                    <br />
                    Browse 800+ quant ideas backed by academic research.
                  </span>
                </li>
              </ul>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
