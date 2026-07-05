import prisma from "@/lib/prisma";

import type { SocialLoginInfo } from "@/components/AccountManagementPanel";

export async function getAccountLoginInfo(userId: string) {
  const user = await prisma.user.findUnique({
    where: { id: userId },
    select: {
      email: true,
      name: true,
      passwordHash: true,
      accounts: {
        select: { provider: true, providerAccountId: true },
      },
    },
  });

  if (!user) {
    return null;
  }

  const socialLogins: SocialLoginInfo[] = [];
  for (const account of user.accounts) {
    if (account.provider !== "google" && account.provider !== "wechat") {
      continue;
    }
    const displayName =
      user.name?.trim() ||
      user.email ||
      account.providerAccountId ||
      account.provider;
    socialLogins.push({
      provider: account.provider,
      displayName,
    });
  }

  return {
    email: user.email,
    hasPassword: Boolean(user.passwordHash),
    socialLogins,
  };
}
