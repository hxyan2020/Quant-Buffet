import { type NextRequest, NextResponse } from "next/server";
import createIntlMiddleware from "next-intl/middleware";
import { routing } from "@/i18n/routing";

const intlMiddleware = createIntlMiddleware({
  locales: [...routing.locales],
  defaultLocale: routing.defaultLocale,
  localePrefix: "always",
  localeDetection: false,
});

function pickLocale(request: NextRequest): "en" | "zh" {
  const pref = request.cookies.get("LOCALE_PREF")?.value;
  if (pref === "en" || pref === "zh") return pref;

  const countryRaw =
    request.headers.get("cf-ipcountry") ??
    request.headers.get("CF-Ipcountry") ??
    request.headers.get("x-vercel-ip-country") ??
    "";
  const country = countryRaw.toUpperCase();
  const chineseRegions = ["CN", "TW", "HK", "MO"];
  if (country && chineseRegions.includes(country)) {
    return "zh";
  }

  const accept = request.headers.get("accept-language")?.toLowerCase() ?? "";
  if (accept.includes("zh")) {
    return "zh";
  }
  return "en";
}

export default function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/admin")) {
    return NextResponse.next();
  }

  if (pathname === "/") {
    const locale = pickLocale(request);
    const redirectUrl = request.nextUrl.clone();
    redirectUrl.pathname = `/${locale}`;
    const response = NextResponse.redirect(redirectUrl);
    response.cookies.set("LOCALE_PREF", locale, {
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
      sameSite: "lax",
    });
    return response;
  }

  const response = intlMiddleware(request);
  const [, maybeLocale] = pathname.split("/");
  if (
    maybeLocale &&
    routing.locales.includes(maybeLocale as "en" | "zh") &&
    response instanceof NextResponse
  ) {
    response.cookies.set("LOCALE_PREF", maybeLocale, {
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
      sameSite: "lax",
    });
  }

  return response;
}

export const config = {
  matcher: [
    "/",
    "/((?!api|_next|_vercel|favicon.ico|robots.txt|sitemap.xml|.*\\.).*)",
  ],
};
