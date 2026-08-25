/** Extract and rewrite WordPress paper screenshots for strategy articles. */

export type PaperImage = {
  src: string;
  alt: string;
};

const IMG_TAG_RE = /<img\b[^>]*>/gi;
const ATTR_RE = (name: string) => new RegExp(`\\b${name}\\s*=\\s*("([^"]*)"|'([^']*)'|([^\\s>]+))`, "i");

const BANNER_NAME_RE = /qb-banner|banner[-_]?\d|site[-_]?logo|favicon/i;
const PAPER_SECTION_RE = /SOURCE\s+PAPER|来源\s*论文|学术论文/i;
const NEXT_SECTION_RE = /BACKTEST\s+PERFORMANCE|回测\s*表现|回测\s*绩效|(?:FULL\s+)?PYTHON\s+CODE|完整\s*python|Python\s*代码/i;

function attr(tag: string, name: string): string {
  const m = tag.match(ATTR_RE(name));
  if (!m) return "";
  return (m[2] ?? m[3] ?? m[4] ?? "").trim();
}

/** Map legacy WP / staging upload URLs onto the public WordPress.com file CDN. */
export function rewriteWordPressMediaUrl(raw: string): string | null {
  const src = (raw || "").trim();
  if (!src || src.startsWith("data:")) return null;

  let url: URL;
  try {
    url = new URL(src, "https://quantbuffet.com");
  } catch {
    return null;
  }

  const path = decodeURIComponent(url.pathname);
  const upload = path.match(/\/(?:wp-content\/)?uploads\/(\d{4}\/\d{2}\/.+)$/i);
  if (upload?.[1]) {
    return `https://quantbuffet.files.wordpress.com/${upload[1].replace(/\/+/g, "/")}`;
  }

  const files = path.match(/\/(\d{4}\/\d{2}\/.+)$/);
  if (/\.files\.wordpress\.com$/i.test(url.hostname) && files?.[1]) {
    return `https://quantbuffet.files.wordpress.com/${files[1].replace(/\/+/g, "/")}`;
  }

  return null;
}

export function isDecorativeBannerUrl(src: string): boolean {
  try {
    const path = decodeURIComponent(new URL(src, "https://quantbuffet.com").pathname);
    return BANNER_NAME_RE.test(path);
  } catch {
    return BANNER_NAME_RE.test(src);
  }
}

function paperSectionHtml(html: string): string {
  const start = html.search(PAPER_SECTION_RE);
  if (start < 0) return "";
  const tail = html.slice(start);
  const next = tail.search(NEXT_SECTION_RE);
  // next matches SOURCE PAPER itself at 0 sometimes — search after a small offset
  const afterHeader = tail.slice(Math.min(80, tail.length));
  const next2 = afterHeader.search(NEXT_SECTION_RE);
  if (next2 >= 0) return tail.slice(0, 80 + next2);
  if (next > 40) return tail.slice(0, next);
  return tail.slice(0, 12_000);
}

function collectImages(html: string): PaperImage[] {
  const out: PaperImage[] = [];
  const seen = new Set<string>();
  for (const tag of html.match(IMG_TAG_RE) ?? []) {
    const rawSrc = attr(tag, "src") || attr(tag, "data-src") || attr(tag, "data-lazy-src");
    const rewritten = rewriteWordPressMediaUrl(rawSrc);
    if (!rewritten || isDecorativeBannerUrl(rewritten) || seen.has(rewritten)) continue;
    seen.add(rewritten);
    const alt = attr(tag, "alt") || "Screenshot from the original paper";
    out.push({ src: rewritten, alt });
  }
  return out;
}

/**
 * Prefer images under SOURCE PAPER; fall back to other non-banner body images.
 * Skips qb-banner decorative headers.
 */
export function extractPaperImages(contentHtml: string): PaperImage[] {
  const html = contentHtml ?? "";
  if (!html.trim()) return [];

  const fromPaper = collectImages(paperSectionHtml(html));
  if (fromPaper.length > 0) return fromPaper;

  // Fall back: all non-banner images in the post body.
  return collectImages(html);
}

export function paperImagesToJson(images: PaperImage[]): string {
  return JSON.stringify(images);
}

export function parsePaperImagesJson(raw: string | null | undefined): PaperImage[] {
  if (!raw?.trim()) return [];
  try {
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed
      .map((row) => {
        if (!row || typeof row !== "object") return null;
        const src = typeof (row as PaperImage).src === "string" ? (row as PaperImage).src.trim() : "";
        if (!src) return null;
        const alt =
          typeof (row as PaperImage).alt === "string" && (row as PaperImage).alt.trim()
            ? (row as PaperImage).alt.trim()
            : "Screenshot from the original paper";
        return { src, alt } satisfies PaperImage;
      })
      .filter((x): x is PaperImage => Boolean(x));
  } catch {
    return [];
  }
}
