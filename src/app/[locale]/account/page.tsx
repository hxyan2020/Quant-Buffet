import { redirect } from "next/navigation";

import AccountManagementPanel from "@/components/AccountManagementPanel";
import { auth } from "@/auth";
import { getAccountLoginInfo } from "@/lib/account-info";
import { getTranslations } from "next-intl/server";

type PageProps = { params: Promise<{ locale: string }> };

export default async function AccountManagementPage({ params }: PageProps) {
  const { locale } = await params;
  const dictionary = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();
  const userId = session?.user?.id?.trim();

  if (!userId) {
    redirect(`/${locale}?auth=login&next=/${locale}/account`);
  }

  const loginInfo = await getAccountLoginInfo(userId);
  if (!loginInfo) {
    redirect(`/${locale}?auth=login&next=/${locale}/account`);
  }

  return (
    <div className="qb-card">
      <h2 className="qb-card-title">{dictionary("account")}</h2>
      <p className="qb-muted qb-account-mgmt-hint">{dictionary("accountHint")}</p>
      <AccountManagementPanel
        locale={locale}
        email={loginInfo.email}
        hasPassword={loginInfo.hasPassword}
        socialLogins={loginInfo.socialLogins}
      />
    </div>
  );
}
