export type LearnBlock =
  | { kind: "p"; text: string }
  | { kind: "h2"; text: string }
  | { kind: "h3"; text: string }
  | { kind: "ul"; items: string[] }
  | { kind: "ol"; items: string[] }
  | { kind: "code"; lang?: string; code: string }
  | { kind: "note"; text: string }
  | { kind: "warn"; text: string }
  | { kind: "table"; headers: string[]; rows: string[][] }
  | { kind: "visual"; id: LearnVisualId }
  | { kind: "checklist"; title: string; items: string[] };

export type LearnVisualId =
  | "quant-journey"
  | "data-pipeline"
  | "asset-explorer"
  | "microstructure-stack"
  | "order-types"
  | "metrics-explorer"
  | "strategy-map";

export type LearnLesson = {
  slug: string;
  title: string;
  subtitle: string;
  order: number;
  duration: string;
  topics: string[];
  blocks: LearnBlock[];
};
