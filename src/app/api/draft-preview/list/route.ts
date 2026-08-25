import { NextResponse } from "next/server";

import { draftPreviewEnabled, loadLabListResponseJson } from "@/lib/draft-preview";

export const runtime = "nodejs";

/** Full lab strategy list for temp preview (not production). */
export async function GET() {
  if (!draftPreviewEnabled()) {
    return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
  }
  return new NextResponse(loadLabListResponseJson(), {
    status: 200,
    headers: {
      "Content-Type": "application/json; charset=utf-8",
      "Cache-Control": "no-store",
    },
  });
}
