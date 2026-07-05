import CountryFlag from "@/components/CountryFlag";
import type { PaperAffiliation } from "@/lib/fetch-paper-meta";

export function parseAffiliationsJson(raw: string | null | undefined): PaperAffiliation[] {
  if (!raw?.trim()) return [];
  try {
    const parsed = JSON.parse(raw) as PaperAffiliation[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export default function InstituteList({
  affiliationsJson,
  fallbackText,
  label,
}: {
  affiliationsJson: string;
  fallbackText: string;
  label: string;
}) {
  const rows = parseAffiliationsJson(affiliationsJson);
  const text = fallbackText?.trim();

  if (rows.length === 0) {
    return (
      <p>
        <span className="qb-paper-meta-label">{label}</span>
        {text && text !== "N/A" ? text : "N/A"}
      </p>
    );
  }

  return (
    <div>
      <span className="qb-paper-meta-label">{label}</span>
      <ul className="qb-institute-list">
        {rows.map((row, i) => (
          <li key={`${row.institute}-${i}`} className="qb-institute-item">
            <CountryFlag code={row.countryCode} size={18} />
            <span>{row.institute}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
