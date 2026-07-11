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
  title: "Quant Buffet",
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
