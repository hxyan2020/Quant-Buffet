import { getRequestConfig } from "next-intl/server";
import { routing } from "./routing";

export default getRequestConfig(async ({ requestLocale }) => {
  let locale = await requestLocale;
  if (!locale || !routing.locales.includes(locale as "en" | "zh")) {
    locale = routing.defaultLocale;
  }

  const messages =
    locale === "zh"
      ? (await import("../../messages/zh.json")).default
      : (await import("../../messages/en.json")).default;

  return {
    locale,
    messages,
  };
});
