import { NextRequest, NextResponse } from "next/server";

interface ShieldsResponse {
  schemaVersion: 1;
  label: string;
  message: string;
  color: string;
  cacheSeconds?: number;
}

function grade(score: number): string {
  if (score >= 90) return "A+";
  if (score >= 80) return "A";
  if (score >= 70) return "B";
  if (score >= 60) return "C";
  return "D";
}

function color(score: number): string {
  if (score >= 90) return "brightgreen";
  if (score >= 80) return "green";
  if (score >= 70) return "yellowgreen";
  if (score >= 60) return "yellow";
  return "red";
}

async function computeScore(owner: string, repo: string): Promise<number> {
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (process.env.GH_PAT) headers["Authorization"] = `Bearer ${process.env.GH_PAT}`;

  const [repoRes, runsRes] = await Promise.all([
    fetch(`https://api.github.com/repos/${owner}/${repo}`, { headers, next: { revalidate: 300 } }),
    fetch(`https://api.github.com/repos/${owner}/${repo}/actions/runs?per_page=1&branch=main`, {
      headers,
      next: { revalidate: 300 },
    }),
  ]);

  if (!repoRes.ok) throw new Error(`GitHub API ${repoRes.status}`);

  const repoData = await repoRes.json();
  const runsData = runsRes.ok ? await runsRes.json() : null;

  let score = 0;

  // CI status: 40 points
  const latestRun = runsData?.workflow_runs?.[0];
  if (latestRun?.conclusion === "success") score += 40;
  else if (latestRun?.conclusion === "skipped") score += 30;
  else if (!latestRun) score += 20; // no CI configured

  // Open issues: 40 points (fewer = better)
  const openIssues = repoData.open_issues_count ?? 0;
  if (openIssues === 0) score += 40;
  else if (openIssues <= 3) score += 35;
  else if (openIssues <= 10) score += 25;
  else if (openIssues <= 25) score += 15;
  else score += 5;

  // Recent activity: 20 points (pushed within 7 days)
  const pushedAt = repoData.pushed_at ? new Date(repoData.pushed_at) : null;
  if (pushedAt) {
    const daysSincePush = (Date.now() - pushedAt.getTime()) / (1000 * 60 * 60 * 24);
    if (daysSincePush <= 1) score += 20;
    else if (daysSincePush <= 7) score += 15;
    else if (daysSincePush <= 30) score += 10;
    else score += 5;
  }

  return Math.min(score, 100);
}

export async function GET(
  _req: NextRequest,
  { params }: { params: { owner: string; repo: string } }
) {
  const { owner, repo } = params;

  try {
    const score = await computeScore(owner, repo);
    const body: ShieldsResponse = {
      schemaVersion: 1,
      label: "gadgetlab",
      message: `${grade(score)} · ${score}`,
      color: color(score),
      cacheSeconds: 300,
    };
    return NextResponse.json(body);
  } catch {
    const body: ShieldsResponse = {
      schemaVersion: 1,
      label: "gadgetlab",
      message: "unavailable",
      color: "lightgrey",
      cacheSeconds: 60,
    };
    return NextResponse.json(body, { status: 200 });
  }
}
