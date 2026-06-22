import { NextResponse } from "next/server";

const REPO = "labgadget015-dotcom/autonomous-github-agent";
const GH_API = "https://api.github.com";
const WORKFLOW_FILE = "ai_agent_workflow.yml";

function ghHeaders(): Record<string, string> {
  const h: Record<string, string> = {
    Accept: "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
  };
  const pat = process.env.GH_PAT;
  if (pat) h.Authorization = `Bearer ${pat}`;
  return h;
}

async function ghGet(path: string) {
  try {
    const res = await fetch(`${GH_API}${path}`, {
      headers: ghHeaders(),
      cache: "no-store",
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

function parsePriority(body: string): string {
  const m = body.match(/\*\*Recommendation:\*\*[^`\n]*?(P0|P1|P2|P3|CRITICAL|LOW)/);
  return m?.[1] ?? "DRC";
}

interface GHRun {
  id: number;
  run_number: number;
  status: string;
  conclusion: string | null;
  created_at: string;
  html_url: string;
  head_commit: { message: string };
}

interface GHComment {
  id: number;
  body: string;
  created_at: string;
  issue_url: string;
}

interface GHIssue {
  number: number;
  title: string;
  labels: Array<{ name: string }>;
  updated_at: string;
  html_url: string;
  pull_request?: unknown;
}

export async function GET() {
  if (!process.env.GH_PAT) {
    return NextResponse.json({ needsConfig: true });
  }

  const [repo, runs, comments, issues] = await Promise.all([
    ghGet(`/repos/${REPO}`),
    ghGet(`/repos/${REPO}/actions/workflows/${WORKFLOW_FILE}/runs?per_page=5`),
    ghGet(`/repos/${REPO}/issues/comments?per_page=100&sort=created&direction=desc`),
    ghGet(`/repos/${REPO}/issues?state=open&per_page=10&sort=updated`),
  ]);

  const latestRun: GHRun | undefined = runs?.workflow_runs?.[0];

  const drcRuns = ((comments ?? []) as GHComment[])
    .filter((c) => c.body?.startsWith("## 🤖 DRC Agent Analysis"))
    .slice(0, 6)
    .map((c) => {
      const issueNumber = c.issue_url?.split("/").pop();
      const priority = parsePriority(c.body);
      const runIdMatch = c.body.match(/Run `(run_\d+)`/);
      return {
        id: c.id,
        issueNumber,
        priority,
        runId: runIdMatch?.[1] ?? null,
        createdAt: c.created_at,
        issueUrl: `https://github.com/${REPO}/issues/${issueNumber}`,
      };
    });

  const openIssues = ((issues ?? []) as GHIssue[])
    .filter((i) => !i.pull_request)
    .slice(0, 6)
    .map((i) => ({
      number: i.number,
      title: i.title,
      labels: i.labels?.map((l) => l.name) ?? [],
      updatedAt: i.updated_at,
      htmlUrl: i.html_url,
    }));

  return NextResponse.json({
    needsConfig: false,
    fetchedAt: new Date().toISOString(),
    repo: {
      openIssues: repo?.open_issues_count ?? 0,
      stars: repo?.stargazers_count ?? 0,
      pushedAt: repo?.pushed_at,
    },
    ci: {
      latest: latestRun
        ? {
            conclusion: latestRun.conclusion,
            status: latestRun.status,
            runNumber: latestRun.run_number,
            createdAt: latestRun.created_at,
            htmlUrl: latestRun.html_url,
          }
        : null,
      runs: ((runs?.workflow_runs ?? []) as GHRun[]).slice(0, 5).map((r) => ({
        id: r.id,
        runNumber: r.run_number,
        status: r.status,
        conclusion: r.conclusion,
        createdAt: r.created_at,
        htmlUrl: r.html_url,
        commitMsg: r.head_commit?.message?.split("\n")[0] ?? "",
      })),
    },
    drcRuns,
    openIssues,
  });
}
