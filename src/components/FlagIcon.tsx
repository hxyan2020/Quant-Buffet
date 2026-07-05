type LocaleCode = "en" | "zh";

/** SVG flags (emoji flags render as "US"/"CN" on many Windows fonts). */
export default function FlagIcon({ locale, size = 20 }: { locale: LocaleCode; size?: number }) {
  if (locale === "zh") {
    return (
      <svg
        width={size}
        height={size * 0.67}
        viewBox="0 0 30 20"
        aria-hidden
        className="qb-flag-svg"
      >
        <rect width="30" height="20" fill="#de2910" />
        <polygon
          points="6,4 7.2,7.5 10.9,7.5 7.9,9.6 9,13 6,10.8 3,13 4.1,9.6 1.1,7.5 4.8,7.5"
          fill="#ffde00"
        />
        <polygon
          points="12,2 12.6,3.8 14.5,3.8 13,5 13.5,6.8 12,5.6 10.5,6.8 11,5 9.5,3.8 11.4,3.8"
          fill="#ffde00"
        />
        <polygon
          points="14,6 14.6,7.8 16.5,7.8 15,9 15.5,10.8 14,9.6 12.5,10.8 13,9 11.5,7.8 13.4,7.8"
          fill="#ffde00"
        />
        <polygon
          points="13,11 13.6,12.8 15.5,12.8 14,14 14.5,15.8 13,14.6 11.5,15.8 12,14 10.5,12.8 12.4,12.8"
          fill="#ffde00"
        />
        <polygon
          points="9,12 9.6,13.8 11.5,13.8 10,15 10.5,16.8 9,15.6 7.5,16.8 8,15 6.5,13.8 8.4,13.8"
          fill="#ffde00"
        />
      </svg>
    );
  }

  return (
    <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-hidden className="qb-flag-svg">
      <rect width="30" height="20" fill="#b22234" />
      <rect y="1.54" width="30" height="1.54" fill="#fff" />
      <rect y="4.62" width="30" height="1.54" fill="#fff" />
      <rect y="7.69" width="30" height="1.54" fill="#fff" />
      <rect y="10.77" width="30" height="1.54" fill="#fff" />
      <rect y="13.85" width="30" height="1.54" fill="#fff" />
      <rect y="16.92" width="30" height="1.54" fill="#fff" />
      <rect width="12" height="10.77" fill="#3c3b6e" />
    </svg>
  );
}
