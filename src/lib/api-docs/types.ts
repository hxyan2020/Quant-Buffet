export type DocBlock =
  | { kind: "p"; text: string }
  | { kind: "h2"; text: string }
  | { kind: "h3"; text: string }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; items: string[] }
  | { kind: "code"; lang?: string; code: string }
  | { kind: "note"; text: string }
  | { kind: "warn"; text: string }
  | { kind: "table"; headers: string[]; rows: string[][] };

export type DocPage = {
  slug: string;
  title: string;
  description: string;
  order: number;
  blocks: DocBlock[];
};

export type DocLocale = "en" | "zh";
