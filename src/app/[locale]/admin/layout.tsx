import type { PropsWithChildren } from "react";

/** Legacy locale-prefixed admin URLs redirect in each page; no public site chrome. */
export default function LegacyAdminLayout({ children }: PropsWithChildren) {
  return children;
}
