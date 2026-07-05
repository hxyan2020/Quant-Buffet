/** Month options (YYYY-MM) for admin date-range dropdowns. */

export function buildMonthSelectOptions(startYear = 2015): { value: string; label: string }[] {
  const options: { value: string; label: string }[] = [{ value: "", label: "Any" }];
  const now = new Date();
  const end = new Date(now.getFullYear(), now.getMonth(), 1);

  for (let y = end.getFullYear(); y >= startYear; y--) {
    const monthStart = y === end.getFullYear() ? end.getMonth() : 11;
    for (let m = monthStart; m >= 0; m--) {
      const value = `${y}-${String(m + 1).padStart(2, "0")}`;
      const label = new Date(y, m, 1).toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
      });
      options.push({ value, label });
    }
  }
  return options;
}

/** Convert YYYY-MM from dropdown to ISO date bounds for Prisma filters. */
export function monthToRangeStart(ym: string): string | undefined {
  if (!ym.trim()) return undefined;
  return `${ym}-01`;
}

export function monthToRangeEnd(ym: string): string | undefined {
  if (!ym.trim()) return undefined;
  const [y, m] = ym.split("-").map(Number);
  if (!y || !m) return undefined;
  const last = new Date(y, m, 0).getDate();
  return `${ym}-${String(last).padStart(2, "0")}`;
}
