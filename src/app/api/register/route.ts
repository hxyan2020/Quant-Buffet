import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";

import prisma from "@/lib/prisma";

const bodySchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
  name: z.string().trim().optional(),
});

export async function POST(request: Request) {
  try {
    const parsed = bodySchema.safeParse(await request.json());
    if (!parsed.success) {
      return NextResponse.json({ error: "INVALID_INPUT" }, { status: 400 });
    }
    const exists = await prisma.user.findUnique({
      where: { email: parsed.data.email.toLowerCase() },
      select: { id: true },
    });
    if (exists) {
      return NextResponse.json({ error: "EMAIL_EXISTS" }, { status: 409 });
    }

    await prisma.user.create({
      data: {
        email: parsed.data.email.toLowerCase(),
        passwordHash: await bcrypt.hash(parsed.data.password, 10),
        name: parsed.data.name,
        libraryUnlocked: false,
      },
    });

    return NextResponse.json({ ok: true });
  } catch (error) {
    console.error("[register]", error);
    return NextResponse.json({ error: "UNKNOWN" }, { status: 500 });
  }
}
