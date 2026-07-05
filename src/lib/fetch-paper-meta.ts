/**
 * Resolve paper metadata via OpenAlex / CrossRef (SSRN blocks direct HTML scrape).
 */

import { decodeEntities, sanitizePlainText } from "@/lib/sanitize-text";

export type PaperAffiliation = {
  institute: string;
  countryCode: string;
};

export type PaperMetaFromUrl = {
  paperTitle: string | null;
  paperAuthors: string | null;
  paperInstitute: string | null;
  paperAffiliations: PaperAffiliation[];
};

const INVALID_TITLE =
  /^(abstract|&lt;abstract&gt;|<abstract>|\[click to open PDF\]|n\/a)$/i;

function cleanTitle(raw: string | null | undefined): string | null {
  if (!raw?.trim()) return null;
  let t = decodeEntities(raw)
    .replace(/\s*[-|–—]\s*SSRN.*$/i, "")
    .replace(/\s*\|\s*Semantic Scholar.*$/i, "")
    .trim();
  if (t.length < 8 || INVALID_TITLE.test(t)) return null;
  if (/^(I{1,3}|IV|V)\.\s/i.test(t)) return null;
  return t.slice(0, 500);
}

function extractDoiCandidates(url: string): string[] {
  const out: string[] = [];
  const direct = url.match(/10\.\d{4,9}\/[^\s"']+/i);
  if (direct) out.push(direct[0].replace(/[.,;]+$/, ""));

  const ssrn = url.match(/ssrn\.com\/abstract=(\d+)/i) ?? url.match(/abstract_id=(\d+)/i);
  if (ssrn?.[1]) out.push(`10.2139/ssrn.${ssrn[1]}`);

  return [...new Set(out)];
}

type OpenAlexInstitution = {
  display_name?: string;
  country_code?: string;
};

type OpenAlexAuthorship = {
  author?: { display_name?: string };
  institutions?: OpenAlexInstitution[];
  raw_affiliation_strings?: string[];
};

async function fetchOpenAlex(doi: string): Promise<PaperMetaFromUrl | null> {
  const id = encodeURIComponent(`https://doi.org/${doi}`);
  const res = await fetch(`https://api.openalex.org/works/${id}`, {
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(15_000),
  });
  if (!res.ok) return null;

  const data = (await res.json()) as {
    title?: string;
    authorships?: OpenAlexAuthorship[];
  };

  const title = cleanTitle(data.title);
  const authors: string[] = [];
  const affiliationMap = new Map<string, PaperAffiliation>();

  for (const row of data.authorships ?? []) {
    const name = row.author?.display_name?.trim();
    if (name) authors.push(name);

    for (const inst of row.institutions ?? []) {
      const institute = inst.display_name?.trim();
      const countryCode = inst.country_code?.trim().toUpperCase() ?? "XX";
      if (!institute) continue;
      const prev = [...affiliationMap.entries()].find(([k]) => k.startsWith(`${institute}|`));
      if (prev) {
        if (prev[1].countryCode === "XX" && countryCode !== "XX") {
          affiliationMap.delete(prev[0]);
          affiliationMap.set(`${institute}|${countryCode}`, { institute, countryCode });
        }
      } else {
        affiliationMap.set(`${institute}|${countryCode}`, { institute, countryCode });
      }
    }

    for (const raw of row.raw_affiliation_strings ?? []) {
      const institute = raw.trim();
      if (!institute || affiliationMap.has(`${institute}|XX`)) continue;
      const existing = [...affiliationMap.values()].find((a) => a.institute === institute);
      if (!existing) {
        affiliationMap.set(`${institute}|XX`, { institute, countryCode: "XX" });
      }
    }
  }

  const paperAffiliations = [...affiliationMap.values()];
  const paperInstitute =
    paperAffiliations.length > 0
      ? paperAffiliations.map((a) => a.institute).join("; ")
      : null;

  return {
    paperTitle: title,
    paperAuthors: authors.length ? authors.join("; ") : null,
    paperInstitute,
    paperAffiliations,
  };
}

async function fetchCrossRef(doi: string): Promise<PaperMetaFromUrl | null> {
  const res = await fetch(`https://api.crossref.org/works/${encodeURIComponent(doi)}`, {
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(12_000),
  });
  if (!res.ok) return null;

  const data = (await res.json()) as {
    message?: { title?: string[]; author?: { given?: string; family?: string }[] };
  };
  const msg = data.message;
  if (!msg) return null;

  const title = cleanTitle(msg.title?.[0]);
  const authors = (msg.author ?? [])
    .map((a) => `${a.given ?? ""} ${a.family ?? ""}`.trim())
    .filter(Boolean);

  return {
    paperTitle: title,
    paperAuthors: authors.length ? authors.join("; ") : null,
    paperInstitute: null,
    paperAffiliations: [],
  };
}

const cache = new Map<string, PaperMetaFromUrl | null>();

export async function fetchPaperMetaFromUrl(
  url: string | null | undefined,
): Promise<PaperMetaFromUrl | null> {
  const href = url?.trim();
  if (!href || !/^https?:\/\//i.test(href)) return null;

  if (cache.has(href)) return cache.get(href) ?? null;

  const dois = extractDoiCandidates(href);
  for (const doi of dois) {
    const openAlex = await fetchOpenAlex(doi);
    if (openAlex?.paperTitle) {
      cache.set(href, openAlex);
      return openAlex;
    }
    const crossRef = await fetchCrossRef(doi);
    if (crossRef?.paperTitle) {
      cache.set(href, crossRef);
      return crossRef;
    }
  }

  cache.set(href, null);
  return null;
}

export function mergePaperMeta(
  fromWp: {
    paperTitle: string | null;
    paperAuthors: string | null;
    paperInstitute: string | null;
    academicLink: string | null;
  },
  fromUrl: PaperMetaFromUrl | null,
): {
  paperTitle: string;
  paperAuthors: string;
  paperInstitute: string;
  paperAffiliationsJson: string;
  academicLink: string | null;
} {
  const wpTitle = fromWp.paperTitle?.trim() ?? "";
  const badTitle =
    !wpTitle ||
    wpTitle === "N/A" ||
    INVALID_TITLE.test(wpTitle) ||
    /^&lt;|abstract/i.test(wpTitle) ||
    wpTitle.length < 10;

  const title = badTitle
    ? fromUrl?.paperTitle || ""
    : wpTitle && wpTitle !== "N/A"
      ? wpTitle
      : fromUrl?.paperTitle || "";

  const wpAuthorsBad =
    !fromWp.paperAuthors?.trim() || fromWp.paperAuthors === "N/A" || fromWp.paperAuthors.length < 3;
  const authors = wpAuthorsBad
    ? fromUrl?.paperAuthors || ""
    : fromWp.paperAuthors || fromUrl?.paperAuthors || "";

  const affiliations =
    fromUrl?.paperAffiliations?.length
      ? fromUrl.paperAffiliations
      : parseInstituteString(fromWp.paperInstitute);

  const institute =
    affiliations.length > 0
      ? affiliations.map((a) => a.institute).join("; ")
      : fromWp.paperInstitute && fromWp.paperInstitute !== "N/A"
        ? fromWp.paperInstitute
        : fromUrl?.paperInstitute || "";

  return {
    paperTitle: title ? sanitizePlainText(title) : "N/A",
    paperAuthors: authors ? sanitizePlainText(authors) : "N/A",
    paperInstitute: institute ? sanitizePlainText(institute) : "N/A",
    paperAffiliationsJson: JSON.stringify(affiliations),
    academicLink: fromWp.academicLink,
  };
}

function parseInstituteString(raw: string | null | undefined): PaperAffiliation[] {
  if (!raw?.trim() || raw === "N/A") return [];
  return raw.split(/[;；]/).map((s) => ({
    institute: s.trim(),
    countryCode: guessCountryFromText(s),
  }));
}

function guessCountryFromText(text: string): string {
  const rules: [RegExp, string][] = [
    [/france|montpellier/i, "FR"],
    [/poland|pozna/i, "PL"],
    [/australia|monash|melbourne/i, "AU"],
    [/dubai|uae|emirates/i, "AE"],
    [/china|zhejiang|hangzhou|beijing|shanghai/i, "CN"],
    [/united states|usa|nber|mit|stanford|harvard/i, "US"],
    [/united kingdom|london|oxford|cambridge/i, "GB"],
    [/germany|frankfurt/i, "DE"],
    [/netherlands|rotterdam|amsterdam/i, "NL"],
    [/singapore/i, "SG"],
    [/hong kong/i, "HK"],
    [/japan|tokyo/i, "JP"],
  ];
  for (const [re, code] of rules) {
    if (re.test(text)) return code;
  }
  return "XX";
}
