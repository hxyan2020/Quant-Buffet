import type { PropsWithChildren } from "react";

import "@/app/globals.css";

export const metadata = {
  title: "Quant Buffet Admin",
  robots: { index: false, follow: false },
};

export default function AdminRootLayout({ children }: PropsWithChildren) {
  return (
    <div className="qb-admin-root min-h-screen bg-[#030508] text-[#e8f0fa]">{children}</div>
  );
}
