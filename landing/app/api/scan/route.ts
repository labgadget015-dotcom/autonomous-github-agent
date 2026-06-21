import { NextRequest, NextResponse } from "next/server";
import { parseRepo, runScan } from "@/lib/scan";

export async function POST(req: NextRequest) {
  const body = await req.json().catch(() => null);
  if (!body?.repo) {
    return NextResponse.json({ error: "Missing repo" }, { status: 400 });
  }

  const parsed = parseRepo(body.repo as string);
  if (!parsed) {
    return NextResponse.json(
      { error: "Could not parse repo — use owner/repo or a GitHub URL" },
      { status: 400 }
    );
  }

  try {
    const report = await runScan(parsed.owner, parsed.repo);
    return NextResponse.json(report);
  } catch (err) {
    const status = (err as Error & { status?: number }).status;
    if (status === 404) {
      return NextResponse.json({ error: "Repository not found or is private" }, { status: 404 });
    }
    console.error("Scan error:", err);
    return NextResponse.json({ error: "Internal error during scan" }, { status: 500 });
  }
}
