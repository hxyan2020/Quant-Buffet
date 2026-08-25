import type { Metadata } from "next";
import type { PropsWithChildren } from "react";
import { redirect } from "next/navigation";

import { auth } from "@/auth";
import AccountNav from "@/components/AccountNav";
import { pageMetadata } from "@/lib/seo";
import { getTranslations } from "next-intl/server";

type Props = PropsWithChildren<{ params: Promise<{ locale: string }> }>;

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale } = await params;
  const seo = await getTranslations({ locale, namespace: "seo" });
  return pageMetadata({
    locale,
    path: "/account",
    title: seo("accountTitle"),
    description: seo("accountDescription"),
    noIndex: true,
  });
}

export default async function AccountLayout({ children, params }: Props) {
  const { locale } = await params;
  const profile = await getTranslations({ locale, namespace: "profile" });
  const session = await auth();

  if (!session?.user?.id) {
    redirect(`/${locale}?auth=login&next=/${locale}/account/plan`);
  }

  const base = `/${locale}/account`;
  const tabs = [
    { href: `${base}/collected`, label: profile("collected") },
    { href: `${base}/plan`, label: profile("plan") },
    { href: `${base}/payment`, label: profile("payment") },
    { href: `${base}/billing`, label: profile("billing") },
    { href: base, label: profile("account") },
  ];

  return (
    <div className="qb-page">
      <header className="qb-page-header">
        <p className="qb-page-eyebrow">Quant Buffet</p>
        <h1 className="qb-page-title">{profile("title")}</h1>
      </header>
      <AccountNav tabs={tabs} />
      <div className="qb-account-body">{children}</div>
    </div>
  );
}
