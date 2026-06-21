import { NextRequest, NextResponse } from "next/server";
import crypto from "crypto";

// Verifies the request came from Slack
function verifySlackSignature(req: NextRequest, rawBody: string): boolean {
  const secret = process.env.SLACK_SIGNING_SECRET;
  if (!secret) return false;

  const timestamp = req.headers.get("x-slack-request-timestamp") ?? "";
  const signature = req.headers.get("x-slack-signature") ?? "";

  // Reject replays older than 5 minutes
  if (Math.abs(Date.now() / 1000 - Number(timestamp)) > 300) return false;

  const baseString = `v0:${timestamp}:${rawBody}`;
  const expected = "v0=" + crypto.createHmac("sha256", secret).update(baseString).digest("hex");
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

function slackText(text: string) {
  return NextResponse.json({ response_type: "in_channel", text });
}

async function handleStatus(): Promise<NextResponse> {
  const repo = process.env.GITHUB_REPOSITORY ?? "labgadget015-dotcom/autonomous-github-agent";
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (process.env.GH_PAT) headers["Authorization"] = `Bearer ${process.env.GH_PAT}`;

  try {
    const runsRes = await fetch(
      `https://api.github.com/repos/${repo}/actions/runs?per_page=3`,
      { headers }
    );
    if (!runsRes.ok) throw new Error("GitHub API error");

    const { workflow_runs: runs } = await runsRes.json();
    if (!runs?.length) return slackText("No recent workflow runs found.");

    const lines = runs.map((r: { name: string; conclusion: string | null; status: string; html_url: string; created_at: string }) => {
      const icon = r.conclusion === "success" ? "✅" : r.status === "in_progress" ? "🔄" : "❌";
      const when = new Date(r.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" });
      return `${icon} *${r.name}* — ${r.conclusion ?? r.status} (${when}) <${r.html_url}|view>`;
    });

    return slackText(`*GadgetLab Pipeline Status*\n${lines.join("\n")}`);
  } catch {
    return slackText("Could not fetch pipeline status. Check GitHub API access.");
  }
}

async function handleScan(repoArg: string): Promise<NextResponse> {
  if (!repoArg) return slackText("Usage: `/gadgetlab scan owner/repo`");

  const origin = process.env.NEXT_PUBLIC_APP_URL ?? "https://gadgetlab.uk";
  try {
    const res = await fetch(`${origin}/api/scan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo: repoArg }),
    });
    if (res.status === 404) return slackText(`Repository \`${repoArg}\` not found or is private.`);
    if (!res.ok) return slackText("Scan failed. Please try again.");

    const report = await res.json();
    const checkLines = Object.values(report.checks as Record<string, { label: string; status: string; detail: string; points: number; maxPoints: number }>)
      .map((c) => {
        const icon = c.status === "good" ? "✅" : c.status === "warning" ? "⚠️" : c.status === "critical" ? "❌" : "⬜";
        return `${icon} ${c.label}: ${c.detail} _(${c.points}/${c.maxPoints})_`;
      })
      .join("\n");

    return slackText(
      `*${report.fullName}* — *${report.grade}* (${report.score}/100)\n\n${checkLines}\n\n` +
        `Badge: \`${report.embedCode}\``
    );
  } catch {
    return slackText("Scan error. Please try again.");
  }
}

function handleHelp(): NextResponse {
  return slackText(
    "*GadgetLab Slash Commands*\n" +
      "`/gadgetlab status` — show recent CI workflow runs\n" +
      "`/gadgetlab scan owner/repo` — health scan any public GitHub repo\n" +
      "`/gadgetlab help` — show this message\n\n" +
      "Powered by <https://gadgetlab.uk|GadgetLab Agent>"
  );
}

export async function POST(req: NextRequest) {
  const rawBody = await req.text();

  // In production, reject unverified requests
  if (process.env.SLACK_SIGNING_SECRET && !verifySlackSignature(req, rawBody)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const params = new URLSearchParams(rawBody);
  const text = (params.get("text") ?? "").trim();
  const [command, ...args] = text.split(/\s+/);

  switch (command.toLowerCase()) {
    case "status":
    case "":
      return handleStatus();
    case "scan":
      return handleScan(args[0] ?? "");
    case "help":
    default:
      return handleHelp();
  }
}
