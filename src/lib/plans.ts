/** One-time library unlock plans (USD cents). Longer terms get up to ~20% off monthly. */

export const PLAN_IDS = ["library-7d", "library-1m", "library-3m", "library-6m", "library-1y"] as const;

export type PlanId = (typeof PLAN_IDS)[number];

export type LibraryPlan = {
  id: PlanId;
  /** Access length */
  durationDays: number;
  /** Stripe unit_amount in USD cents */
  unitAmount: number;
  /** List price before discount (cents), for UI strikethrough when discounted */
  listAmount: number;
  /** Approximate % off vs pure monthly pro-rata at $99/mo */
  discountPercent: number;
  /** Highlight as best value */
  featured?: boolean;
};

/**
 * Baseline: $99 / 30 days.
 * 7d ≈ weekly trial (no volume discount).
 * 3m ~10% off, 6m ~15% off, 1y ~20% off.
 */
export const LIBRARY_PLANS: readonly LibraryPlan[] = [
  {
    id: "library-7d",
    durationDays: 7,
    unitAmount: 2900,
    listAmount: 2900,
    discountPercent: 0,
  },
  {
    id: "library-1m",
    durationDays: 30,
    unitAmount: 9900,
    listAmount: 9900,
    discountPercent: 0,
  },
  {
    id: "library-3m",
    durationDays: 90,
    unitAmount: 26700,
    listAmount: 29700,
    discountPercent: 10,
  },
  {
    id: "library-6m",
    durationDays: 180,
    unitAmount: 50500,
    listAmount: 59400,
    discountPercent: 15,
    featured: true,
  },
  {
    id: "library-1y",
    durationDays: 365,
    unitAmount: 94900,
    listAmount: 118800,
    discountPercent: 20,
  },
] as const;

export function isPlanId(value: unknown): value is PlanId {
  return typeof value === "string" && (PLAN_IDS as readonly string[]).includes(value);
}

export function getLibraryPlan(id: PlanId): LibraryPlan {
  const plan = LIBRARY_PLANS.find((p) => p.id === id);
  if (!plan) {
    throw new Error(`Unknown plan: ${id}`);
  }
  return plan;
}

export function formatUsdFromCents(cents: number): string {
  const dollars = cents / 100;
  return Number.isInteger(dollars) ? `$${dollars}` : `$${dollars.toFixed(2)}`;
}

/** Extend from an existing future end date, otherwise from now. */
export function computePlanPeriodEnd(durationDays: number, from: Date = new Date(), existingEnd?: Date | null) {
  const start =
    existingEnd && existingEnd.getTime() > from.getTime() ? new Date(existingEnd) : new Date(from);
  const end = new Date(start);
  end.setUTCDate(end.getUTCDate() + durationDays);
  return end;
}
