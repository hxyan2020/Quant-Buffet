import { Dancing_Script } from "next/font/google";
import { getTranslations } from "next-intl/server";

import { auth } from "@/auth";
import SiteHeaderShell from "@/components/SiteHeaderShell";

const handwriting = Dancing_Script({
  weight: ["400", "700"],
  subsets: ["latin"],
});

type Props = { locale: string };

export async function SiteHeader({ locale }: Props) {
  const nav = await getTranslations("nav");
  const brand = await getTranslations("brand");
  const profile = await getTranslations("profile");
  const base = `/${locale}`;
  const session = await auth();

  const navLinks = [
    { href: base, label: nav("home") },
    { href: `${base}/strategy-library`, label: nav("library") },
    { href: `${base}/pricing`, label: nav("pricing") },
  ];

  const googleEnabled = Boolean(
    process.env.AUTH_GOOGLE_ID?.trim() && process.env.AUTH_GOOGLE_SECRET?.trim(),
  );

  return (
    <SiteHeaderShell
      locale={locale}
      brandName={brand("name")}
      brandTagline={brand("tagline")}
      navLinks={navLinks}
      profileLabels={{
        profile: profile("title"),
        collected: profile("collected"),
        plan: profile("plan"),
        billing: profile("billing"),
        account: nav("account"),
        login: profile("login"),
        logout: profile("logout"),
        admin: nav("admin"),
      }}
      isLoggedIn={Boolean(session?.user)}
      isAdmin={session?.user?.role === "ADMIN"}
      googleEnabled={googleEnabled}
      handwritingClass={handwriting.className}
    />
  );
}
