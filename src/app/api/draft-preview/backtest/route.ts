import { spawn } from "child_process";
import fs from "fs";
import path from "path";

import { NextResponse } from "next/server";
import { z } from "zod";

import { draftPreviewEnabled, findDraftPost, labStrategyExists, loadLabIndex, toLabPythonSource } from "@/lib/draft-preview";

export const runtime = "nodejs";
export const maxDuration = 120;

const bodySchema = z.object({
  slug: z.string().min(1).max(120),
  code: z.string().min(20).max(80_000),
  start: z.string().optional(),
});

function pythonBin(): string {
  return process.env.PYTHON_PATH || process.env.PYTHON || "python";
}

function runSandbox(code: string, start: string): Promise<{
  ok: boolean;
  raw: string;
  timedOut?: boolean;
  exitCode: number | null;
}> {
  const runner = path.join(process.cwd(), "backtest", "sandbox_runner.py");
  if (!fs.existsSync(runner)) {
    return Promise.resolve({
      ok: false,
      raw: JSON.stringify({
        ok: false,
        error: { type: "ServerError", message: "sandbox_runner.py missing" },
      }),
      exitCode: 1,
    });
  }

  return new Promise((resolve) => {
    const child = spawn(pythonBin(), [runner], {
      cwd: process.cwd(),
      env: {
        ...process.env,
        PYTHONIOENCODING: "utf-8",
        PYTHONUNBUFFERED: "1",
      },
      stdio: ["pipe", "pipe", "pipe"],
      windowsHide: true,
    });

    let stdout = "";
    let stderr = "";
    let settled = false;
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      child.kill();
      resolve({
        ok: false,
        timedOut: true,
        exitCode: null,
        raw: JSON.stringify({
          ok: false,
          error: {
            type: "Timeout",
            message: "Backtest exceeded 90s. Simplify signals or reduce ASSETS.",
            line: null,
            traceback: stderr.slice(-1500),
          },
        }),
      });
    }, 90_000);

    child.stdout.on("data", (d) => {
      stdout += d.toString("utf8");
    });
    child.stderr.on("data", (d) => {
      stderr += d.toString("utf8");
    });
    child.on("error", (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({
        ok: false,
        exitCode: 1,
        raw: JSON.stringify({
          ok: false,
          error: {
            type: "SpawnError",
            message: err.message,
            line: null,
            traceback: "",
          },
        }),
      });
    });
    child.on("close", (code) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      const trimmed = stdout.trim();
      if (trimmed) {
        resolve({ ok: code === 0, exitCode: code, raw: trimmed });
        return;
      }
      resolve({
        ok: false,
        exitCode: code,
        raw: JSON.stringify({
          ok: false,
          error: {
            type: "EmptyOutput",
            message: stderr.trim() || `Sandbox exited with code ${code}`,
            line: null,
            traceback: stderr.slice(-2000),
          },
        }),
      });
    });

    child.stdin.write(
      JSON.stringify({
        code,
        start,
        max_points: 90,
      }),
    );
    child.stdin.end();
  });
}

export async function POST(request: Request) {
  if (!draftPreviewEnabled()) {
    return NextResponse.json({ error: "NOT_FOUND" }, { status: 404 });
  }

  const parsed = bodySchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json({ error: "BAD_REQUEST" }, { status: 400 });
  }

  const { slug, code, start } = parsed.data;
  if (!labStrategyExists(slug) && !findDraftPost(slug)) {
    return NextResponse.json({ error: "UNKNOWN_DRAFT" }, { status: 404 });
  }
  const idx = loadLabIndex();
  const entry = idx.strategies.find((s) => s.slug === slug);
  const title = entry?.title || slug;
  const runnableCode = toLabPythonSource(slug, code);

  const result = await runSandbox(runnableCode, start || "2000-01-01");
  let payload: Record<string, unknown>;
  try {
    // Prefer last JSON object in stdout (in case of prints)
    const lines = result.raw
      .split(/\r?\n/)
      .map((l) => l.trim())
      .filter(Boolean);
    let jsonText = lines[lines.length - 1] || result.raw;
    // If multi-line pretty JSON, take from first { to last }
    const first = result.raw.indexOf("{");
    const last = result.raw.lastIndexOf("}");
    if (first >= 0 && last > first) {
      jsonText = result.raw.slice(first, last + 1);
    }
    payload = JSON.parse(jsonText) as Record<string, unknown>;
  } catch {
    payload = {
      ok: false,
      error: {
        type: "ParseError",
        message: "Could not parse sandbox output.",
        line: null,
        traceback: result.raw.slice(-2000),
      },
    };
  }

  return NextResponse.json({
    ...payload,
    slug,
    title,
    baseline: {
      annualisedReturn: entry?.annualisedReturn ?? null,
      sharpeRatio: entry?.sharpeRatio ?? null,
      maxDrawdown: entry?.maxDrawdown ?? null,
      volatility: entry?.volatility ?? null,
    },
  });
}
