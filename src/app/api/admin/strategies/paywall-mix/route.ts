import { NextResponse } from "next/server";

import { requireAdminResponse } from "@/lib/authz";
import { applyFreeLibraryShare } from "@/lib/paywall";

export async function POST() {
  const guard = await requireAdminResponse();
  if (guard) return guard;

  const result = await applyFreeLibraryShare();
  return NextResponse.json({ ok: true, ...result });
}
