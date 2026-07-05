import { NextResponse } from "next/server";

import { auth } from "@/auth";

export async function requireAdminResponse(): Promise<Response | null> {
  const session = await auth();
  if (!session?.user || session.user.role !== "ADMIN") {
    return NextResponse.json({ error: "FORBIDDEN" }, { status: 403 });
  }
  return null;
}
