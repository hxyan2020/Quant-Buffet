import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";

import { auth } from "@/auth";
import prisma from "@/lib/prisma";

const bodySchema = z.object({
  currentPassword: z.string().min(1),
  newPassword: z.string().min(8),
});

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
  }

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
  }

  const user = await prisma.user.findUnique({
    where: { id: session.user.id },
    select: { passwordHash: true },
  });

  if (!user?.passwordHash) {
    return NextResponse.json({ error: "NO_PASSWORD" }, { status: 400 });
  }

  const valid = await bcrypt.compare(parsed.data.currentPassword, user.passwordHash);
  if (!valid) {
    return NextResponse.json({ error: "WRONG_PASSWORD" }, { status: 403 });
  }

  await prisma.user.update({
    where: { id: session.user.id },
    data: { passwordHash: await bcrypt.hash(parsed.data.newPassword, 10) },
  });

  return NextResponse.json({ ok: true });
}
