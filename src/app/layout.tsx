import type { Metadata, Viewport } from "next";
import type { PropsWithChildren } from "react";
import { IBM_Plex_Mono, Inter } from "next/font/google";

import "@/app/globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--qb-sans",
});

const mono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-qb-mono",
  weight: ["400", "600"],
});

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
};

export const metadata: Metadata = {
  metadataBase: new URL(process.env.AUTH_URL ?? "https://www.quantbuffet.com"),
  title: {
    default: "Quant Buffet — Academic Quant Trading Strategies",
    template: "%s",
  },
  description:
    "Bilingual library of academic quantitative trading strategies with backtests and QuantConnect/LEAN Python code.",
  applicationName: "Quant Buffet",
  authors: [{ name: "Quant Buffet", url: "https://www.quantbuffet.com" }],
  creator: "Quant Buffet",
  category: "finance",
  openGraph: {
    type: "website",
    siteName: "Quant Buffet",
  },
  twitter: {
    card: "summary_large_image",
  },
};

export default function RootLayout({ children }: PropsWithChildren) {
  return (
    <html lang="en" suppressHydrationWarning className={`${inter.variable} ${mono.variable}`}>
      <body
        className={`${inter.className} ${mono.variable} min-h-screen bg-black font-sans antialiased text-white`}
      >
        {children}
      </body>
    </html>
  );
}
