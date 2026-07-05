import prisma from "@/lib/prisma";
import type { QuantRole } from "@/types/quant-role";

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
  const active = await prisma.subscription.findFirst({
    where: { userId, status: "active" },
  });

  if (active) {
    await prisma.user.update({
      where: { id: userId },
      data: {
        libraryUnlocked: true,
      },
    });
    return true;
  }

  return false;
}
