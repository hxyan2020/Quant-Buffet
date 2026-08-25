import type { MetadataRoute } from "next";

import { SITE_URL } from "@/lib/seo";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: "/",
        disallow: ["/admin", "/api/", "/*/account", "/*/admin"],
      },
      {
        userAgent: "GPTBot",
        allow: ["/", "/en/", "/zh/", "/sitemap.xml"],
        disallow: ["/admin", "/api/", "/*/account"],
      },
    ],
    sitemap: `${SITE_URL}/sitemap.xml`,
    host: SITE_URL,
  };
}
