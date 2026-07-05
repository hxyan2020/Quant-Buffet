/** Small flag by ISO 3166-1 alpha-2 country code. */
export default function CountryFlag({
  code,
  size = 16,
}: {
  code: string;
  size?: number;
}) {
  const c = (code || "XX").toUpperCase().slice(0, 2);
  const label = c === "XX" ? "?" : c;

  if (c === "CN") {
    return (
      <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-label="China" className="qb-flag-svg">
        <rect width="30" height="20" fill="#de2910" />
        <polygon points="6,4 7.2,7.5 10.9,7.5 7.9,9.6 9,13 6,10.8 3,13 4.1,9.6 1.1,7.5 4.8,7.5" fill="#ffde00" />
      </svg>
    );
  }
  if (c === "US") {
    return (
      <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-label="USA" className="qb-flag-svg">
        <rect width="30" height="20" fill="#b22234" />
        <rect width="12" height="10.77" fill="#3c3b6e" />
      </svg>
    );
  }
  if (c === "FR") {
    return (
      <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-label="France" className="qb-flag-svg">
        <rect width="10" height="20" fill="#0055a4" />
        <rect x="10" width="10" height="20" fill="#fff" />
        <rect x="20" width="10" height="20" fill="#ef4135" />
      </svg>
    );
  }
  if (c === "PL") {
    return (
      <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-label="Poland" className="qb-flag-svg">
        <rect width="30" height="10" fill="#fff" />
        <rect y="10" width="30" height="10" fill="#dc143c" />
      </svg>
    );
  }
  if (c === "AU") {
    return (
      <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-label="Australia" className="qb-flag-svg">
        <rect width="30" height="20" fill="#012169" />
        <rect width="15" height="10" fill="#012169" />
      </svg>
    );
  }
  if (c === "AE") {
    return (
      <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-label="UAE" className="qb-flag-svg">
        <rect width="30" height="20" fill="#00732f" />
        <rect width="8" height="20" fill="#ff0000" />
      </svg>
    );
  }
  if (c === "GB") {
    return (
      <svg width={size} height={size * 0.67} viewBox="0 0 30 20" aria-label="UK" className="qb-flag-svg">
        <rect width="30" height="20" fill="#012169" />
      </svg>
    );
  }

  return (
    <span className="qb-flag-fallback" title={label}>
      {label}
    </span>
  );
}
