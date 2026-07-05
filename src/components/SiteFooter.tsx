import { Suspense } from "react";
import { getTranslations } from "next-intl/server";

import SiteFooterClient from "@/components/SiteFooterClient";

export default async function SiteFooter({ locale }: { locale: string }) {
  const footer = await getTranslations({ locale, namespace: "footer" });
  const legal = await getTranslations({ locale, namespace: "legal" });

  return (
    <Suspense fallback={null}>
      <SiteFooterClient
        termsLabel={footer("terms")}
        contactLabel={footer("contact")}
        termsTitle={legal("termsTitle")}
        termsBody={legal("termsBody")}
        contactTitle={legal("contactTitle")}
        contactBody={legal("contactBody")}
        contactTelegram="+65 88023346"
        contactEmail="hola@quantbuffet.com"
      />
    </Suspense>
  );
}
