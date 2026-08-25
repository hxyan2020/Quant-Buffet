import prisma from "@/lib/prisma";
import type { QuantRole } from "@/types/quant-role";
import { syncUserPlanAccess } from "@/lib/subscription";

type LightweightUser = {
  id: string;
  role?: QuantRole | string;
  libraryUnlocked?: boolean | null;
};

export function viewerCanSeeFullArticle(
  viewer: LightweightUser | null | undefined,
  options: {
    articlePaywalled: boolean;
  },
) {
  if (!options.articlePaywalled) return true;

  if (!viewer) return false;
  if (viewer.role === "ADMIN") return true;
  if (viewer.libraryUnlocked) return true;

  return false;
}

export async function refreshSubscriberFlag(userId: string) {
  const state = await syncUserPlanAccess(userId);
  return state.hasActivePlan;
}

/** Prefer this over JWT flag alone when gating paid content. */
export async function userHasLibraryAccess(userId: string, locale = "en") {
  if (!userId) return false;
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: { role: true },
  });
  if (user?.role === "ADMIN") return true;
  const state = await syncUserPlanAccess(userId, locale);
  return state.hasActivePlan;
}
