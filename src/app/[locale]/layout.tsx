import type { PropsWithChildren } from "react";
import "@/app/globals.css";
import { NextIntlClientProvider } from "next-intl";
import { getMessages, setRequestLocale } from "next-intl/server";
import { notFound } from "next/navigation";

import { ClientSessionProvider } from "@/components/ClientSessionProvider";
import SiteFooter from "@/components/SiteFooter";
import { SiteHeader } from "@/components/SiteHeader";
import { routing } from "@/i18n/routing";

type LocaleLayoutProps = PropsWithChildren<{
  params: Promise<{ locale: string }>;
}>;

export default async function LocaleLayout({ children, params }: LocaleLayoutProps) {
  const { locale } = await params;
  const supported = routing.locales.includes(locale as (typeof routing.locales)[number]);
  if (!supported) {
    notFound();
  }

  setRequestLocale(locale);
  const messages = await getMessages();

  return (
    <NextIntlClientProvider locale={locale} messages={messages}>
      <ClientSessionProvider>
        <div className="qb-site">
          <SiteHeader locale={locale} />
          <main className="qb-main">{children}</main>
          <SiteFooter locale={locale} />
        </div>
      </ClientSessionProvider>
    </NextIntlClientProvider>
  );
}

export function generateStaticParams() {
  return routing.locales.map((entry) => ({ locale: entry }));
}
