import { NextResponse } from "next/server";
import { z } from "zod";

import { auth } from "@/auth";
import {
  collectStrategy,
  listCollectedStrategies,
  uncollectStrategy,
} from "@/lib/collections";

const postSchema = z.object({
  strategyId: z.string().min(1),
  action: z.enum(["collect", "uncollect"]),
});

export async function GET(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
  }

  const strategies = await listCollectedStrategies(session.user.id);
  return NextResponse.json({ strategies });
}

export async function POST(request: Request) {
  const session = await auth();
  if (!session?.user?.id) {
    return NextResponse.json({ error: "UNAUTHORIZED" }, { status: 401 });
  }

  const parsed = postSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "BAD_REQUEST" }, { status: 400 });
  }

  const { strategyId, action } = parsed.data;
  const userId = session.user.id;

  if (action === "collect") {
    const result = await collectStrategy(userId, strategyId);
    if (!result.ok) {
      return NextResponse.json({ error: result.error }, { status: 404 });
    }
    return NextResponse.json({ collected: true });
  }

  await uncollectStrategy(userId, strategyId);
  return NextResponse.json({ collected: false });
}
