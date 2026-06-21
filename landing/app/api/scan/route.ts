import { NextRequest, NextResponse } from "next/server";
import type { CheckResult, ScanReport } from "@/lib/scan-types";

function grade(score: number) {
  if (score >= 90) return { grade: "A+", color: "#22c55e" };
  if (score >= 80) return { grade: "A", color: "#4ade80" };
  if (score >= 70) return { grade: "B", color: "#a3e635" };
  if (score >= 60) return { grade: "C", color: "#facc15" };
  return { grade: "D", color: "#ef4444" };
}

function parseRepo(input: string): { owner: string; repo: string } | null {
  const cleaned = input.trim().replace(/\/$/, "");
  const ghMatch = cleaned.match(/github\.com\/([^/]+)\/([^/]+)/);
  if (ghMatch) return { owner: ghMatch[1], repo: ghMatch[2] };
  const plainMatch = cleaned.match(/^([^/]+)\/([^/]+)$/);
  if (plainMatch) return { owner: plainMatch[1], repo: plainMatch[2] };
  return null;
}

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

  const { owner, repo } = parsed;
  const headers: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  if (process.env.GH_PAT) headers["Authorization"] = `Bearer ${process.env.GH_PAT}`;

  const base = `https://api.github.com/repos/${owner}/${repo}`;

  try {
    const [repoRes, runsRes, prsRes] = await Promise.all([
      fetch(base, { headers }),
      fetch(`${base}/actions/runs?per_page=5&branch=main`, { headers }),
      fetch(`${base}/pulls?state=open&per_page=100`, { headers }),
    ]);

    if (repoRes.status === 404) {
      return NextResponse.json({ error: "Repository not found or is private" }, { status: 404 });
    }
    if (!repoRes.ok) {
      return NextResponse.json({ error: "GitHub API error" }, { status: 502 });
    }

    const repoData = await repoRes.json();
    const runsData = runsRes.ok ? await runsRes.json() : null;
    const prsData = prsRes.ok ? await prsRes.json() : [];

    // --- CI check (30 pts) ---
    const latestRun = runsData?.workflow_runs?.[0];
    let ciCheck: CheckResult;
    if (!latestRun) {
      ciCheck = { label: "CI / CD", status: "unknown", detail: "No workflow runs found", points: 15, maxPoints: 30 };
    } else if (latestRun.conclusion === "success") {
      ciCheck = { label: "CI / CD", status: "good", detail: `${latestRun.name} passing`, points: 30, maxPoints: 30 };
    } else if (latestRun.status === "in_progress") {
      ciCheck = { label: "CI / CD", status: "unknown", detail: "Run in progress", points: 20, maxPoints: 30 };
    } else {
      ciCheck = {
        label: "CI / CD",
        status: "critical",
        detail: `${latestRun.name} ${latestRun.conclusion ?? "failed"}`,
        points: 0,
        maxPoints: 30,
      };
    }

    // --- Issues check (25 pts) ---
    const openIssues: number = repoData.open_issues_count ?? 0;
    let issueCheck: CheckResult;
    if (openIssues === 0) {
      issueCheck = { label: "Open Issues", status: "good", detail: "No open issues", points: 25, maxPoints: 25 };
    } else if (openIssues <= 5) {
      issueCheck = { label: "Open Issues", status: "good", detail: `${openIssues} open`, points: 20, maxPoints: 25 };
    } else if (openIssues <= 15) {
      issueCheck = { label: "Open Issues", status: "warning", detail: `${openIssues} open`, points: 13, maxPoints: 25 };
    } else {
      issueCheck = { label: "Open Issues", status: "critical", detail: `${openIssues} open`, points: 5, maxPoints: 25 };
    }

    // --- PR staleness check (20 pts) ---
    const now = Date.now();
    const stalePrs = Array.isArray(prsData)
      ? prsData.filter((pr: { updated_at: string }) => {
          const age = (now - new Date(pr.updated_at).getTime()) / (1000 * 60 * 60 * 24);
          return age > 30;
        }).length
      : 0;
    let prCheck: CheckResult;
    if (stalePrs === 0) {
      prCheck = { label: "Stale PRs", status: "good", detail: "No PRs stale >30d", points: 20, maxPoints: 20 };
    } else if (stalePrs <= 2) {
      prCheck = { label: "Stale PRs", status: "warning", detail: `${stalePrs} PR${stalePrs > 1 ? "s" : ""} stale >30d`, points: 12, maxPoints: 20 };
    } else {
      prCheck = { label: "Stale PRs", status: "critical", detail: `${stalePrs} PRs stale >30d`, points: 4, maxPoints: 20 };
    }

    // --- Activity check (15 pts) ---
    const pushedAt = repoData.pushed_at ? new Date(repoData.pushed_at) : null;
    const daysSince = pushedAt ? (now - pushedAt.getTime()) / (1000 * 60 * 60 * 24) : 999;
    let activityCheck: CheckResult;
    if (daysSince <= 3) {
      activityCheck = { label: "Activity", status: "good", detail: "Pushed in last 3 days", points: 15, maxPoints: 15 };
    } else if (daysSince <= 14) {
      activityCheck = { label: "Activity", status: "good", detail: `Last push ${Math.round(daysSince)}d ago`, points: 12, maxPoints: 15 };
    } else if (daysSince <= 60) {
      activityCheck = { label: "Activity", status: "warning", detail: `Last push ${Math.round(daysSince)}d ago`, points: 7, maxPoints: 15 };
    } else {
      activityCheck = { label: "Activity", status: "critical", detail: `Last push ${Math.round(daysSince)}d ago`, points: 2, maxPoints: 15 };
    }

    // --- Security check (10 pts) — has Dependabot or SECURITY.md ---
    let securityCheck: CheckResult;
    try {
      const [depRes, secRes] = await Promise.all([
        fetch(`${base}/contents/.github/dependabot.yml`, { headers }),
        fetch(`${base}/contents/SECURITY.md`, { headers }),
      ]);
      const hasDep = depRes.ok;
      const hasSec = secRes.ok;
      if (hasDep && hasSec) {
        securityCheck = { label: "Security", status: "good", detail: "Dependabot + SECURITY.md", points: 10, maxPoints: 10 };
      } else if (hasDep || hasSec) {
        securityCheck = { label: "Security", status: "warning", detail: hasDep ? "Dependabot configured" : "SECURITY.md present", points: 6, maxPoints: 10 };
      } else {
        securityCheck = { label: "Security", status: "warning", detail: "No Dependabot or SECURITY.md", points: 3, maxPoints: 10 };
      }
    } catch {
      securityCheck = { label: "Security", status: "unknown", detail: "Could not check", points: 5, maxPoints: 10 };
    }

    const totalScore = ciCheck.points + issueCheck.points + prCheck.points + activityCheck.points + securityCheck.points;
    const { grade: g, color: c } = grade(totalScore);

    const badgeUrl = `https://img.shields.io/endpoint?url=https://gadgetlab.uk/api/badge/${owner}/${repo}`;
    const embedCode = `[![GadgetLab Score](${badgeUrl})](https://gadgetlab.uk)`;

    const report: ScanReport = {
      owner,
      repo,
      fullName: `${owner}/${repo}`,
      score: totalScore,
      grade: g,
      color: c,
      checks: { ci: ciCheck, issues: issueCheck, prs: prCheck, activity: activityCheck, security: securityCheck },
      badgeUrl,
      embedCode,
      stars: repoData.stargazers_count ?? 0,
      description: repoData.description ?? null,
    };

    return NextResponse.json(report);
  } catch (err) {
    console.error("Scan error:", err);
    return NextResponse.json({ error: "Internal error during scan" }, { status: 500 });
  }
}
