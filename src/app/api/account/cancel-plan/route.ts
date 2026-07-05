import { NextResponse } from "next/server";

import { auth } from "@/auth";
import { cancelUserPlan } from "@/lib/subscription";

export async function POST() {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
  }

  const result = await cancelUserPlan(session.user.id);
  if (!result.ok) {
    return NextResponse.json({ error: result.error }, { status: 400 });
  }

  return NextResponse.json({ ok: true, state: result.state });
}
