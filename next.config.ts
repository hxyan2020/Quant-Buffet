import createNextIntlPlugin from "next-intl/plugin";

import type { NextConfig } from "next";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  output: "standalone",
  // Exact hosts needed — wildcards alone are unreliable for Cloudflare quick tunnels.
  allowedDevOrigins: [
    "suse-murray-benchmark-gallery.trycloudflare.com",
    "euro-dial-somerset-screen.trycloudflare.com",
    "pts-usd-diego-jobs.trycloudflare.com",
    "restoration-catering-transmission-screenshots.trycloudflare.com",
    "mile-amy-heater-carol.trycloudflare.com",
    "successful-deadline-servers-marked.trycloudflare.com",
    "bibliographic-restructuring-halifax-selling.trycloudflare.com",
    "shaky-ravens-hear.loca.lt",
    "*.trycloudflare.com",
    "*.loca.lt",
    "localhost",
    "127.0.0.1",
  ],
  experimental: {
    serverActions: {
      bodySizeLimit: "2mb",
    },
  },
};

export default withNextIntl(nextConfig);
