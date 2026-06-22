"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

const REPO = "labgadget015-dotcom/autonomous-github-agent";
const WORKFLOW_FILE = "ai_agent_workflow.yml";
const REFRESH_INTERVAL = 60_000;

type CiRun = {
  id: number;
  runNumber: number;
  status: string;
  conclusion: string | null;
  createdAt: string;
  htmlUrl: string;
  commitMsg: string;
};

type DrcRun = {
  id: number;
  issueNumber: string;
  priority: string;
  runId: string | null;
  createdAt: string;
  issueUrl: string;
};

type OpenIssue = {
  number: number;
  title: string;
  labels: string[];
  updatedAt: string;
  htmlUrl: string;
};

type DashboardData = {
  needsConfig: boolean;
  fetchedAt?: string;
  repo?: { openIssues: number; stars: number; pushedAt: string };
  ci?: {
    latest: {
      conclusion: string | null;
      status: string;
      runNumber: number;
      createdAt: string;
      htmlUrl: string;
    } | null;
    runs: CiRun[];
  };
  drcRuns?: DrcRun[];
  openIssues?: OpenIssue[];
};

function ago(iso: string): string {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}s ago`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function ciLabel(run: { status: string; conclusion: string | null }): {
  text: string;
  cls: string;
  dot: string;
} {
  const c = run.conclusion;
  const s = run.status;
  if (s === "in_progress" || s === "queued")
    return { text: s === "queued" ? "queued" : "running", cls: "text-yellow-700 bg-yellow-50", dot: "bg-yellow-400" };
  if (c === "success")
    return { text: "passing", cls: "text-green-700 bg-green-50", dot: "bg-green-500" };
  if (c === "failure")
    return { text: "failing", cls: "text-red-700 bg-red-50", dot: "bg-red-500" };
  if (c === "cancelled")
    return { text: "cancelled", cls: "text-gray-500 bg-gray-50", dot: "bg-gray-400" };
  return { text: c ?? s ?? "unknown", cls: "text-gray-500 bg-gray-50", dot: "bg-gray-300" };
}

function PriorityBadge({ p }: { p: string }) {
  const map: Record<string, string> = {
    P0: "bg-red-100 text-red-700",
    P1: "bg-orange-100 text-orange-700",
    P2: "bg-blue-100 text-blue-700",
    P3: "bg-gray-100 text-gray-600",
  };
  return (
    <span className={`text-xs font-semibold px-1.5 py-0.5 rounded ${map[p] ?? "bg-brand-50 text-brand-600"}`}>
      {p}
    </span>
  );
}

function LabelChip({ label }: { label: string }) {
  const color =
    label.startsWith("P0") || label === "critical"
      ? "bg-red-50 text-red-600"
      : label.startsWith("P1") || label === "bug"
      ? "bg-orange-50 text-orange-600"
      : "bg-gray-100 text-gray-500";
  return (
    <span className={`text-xs px-1.5 py-0.5 rounded ${color}`}>{label}</span>
  );
}

function Skeleton({ className }: { className: string }) {
  return <div className={`animate-pulse bg-gray-100 rounded ${className}`} />;
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const res = await fetch("/api/dashboard", { cache: "no-store" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
      setLastUpdated(new Date());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const id = setInterval(fetchData, REFRESH_INTERVAL);
    return () => clearInterval(id);
  }, [fetchData]);

  const ciLatest = data?.ci?.latest;
  const ciStatus = ciLatest ? ciLabel(ciLatest) : null;
  const latestDrc = data?.drcRuns?.[0];

  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-100 px-4 h-16 flex items-center justify-between">
        <Link href="/" className="font-bold text-lg tracking-tight text-gray-900">
          GadgetLab Agent
        </Link>
        <div className="flex items-center gap-3">
          {lastUpdated && (
            <span className="text-xs text-gray-400 hidden sm:block">
              Updated {ago(lastUpdated.toISOString())}
            </span>
          )}
          <button
            onClick={fetchData}
            disabled={loading}
            className="text-xs text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg px-3 py-1.5 bg-white transition-colors disabled:opacity-50"
          >
            {loading ? "Loading…" : "Refresh"}
          </button>
          <span className="flex items-center gap-1.5 text-xs text-gray-400">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 inline-block" />
            live
          </span>
        </div>
      </nav>

      <div className="max-w-5xl mx-auto px-4 py-10">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Pipeline Status</h1>
          <p className="text-gray-500 mt-1">Live data from the autonomous GitHub agent pipeline.</p>
        </div>

        {error && (
          <div className="mb-6 bg-red-50 border border-red-200 text-red-700 text-sm rounded-xl px-4 py-3">
            {error} — <button onClick={fetchData} className="underline">retry</button>
          </div>
        )}

        {data?.needsConfig && (
          <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-xl px-5 py-4">
            <p className="text-sm font-semibold text-yellow-800 mb-1">Configuration required</p>
            <p className="text-sm text-yellow-700">
              Add <code className="bg-yellow-100 px-1 rounded">GH_PAT</code> to your Vercel environment variables to
              enable live pipeline data.
            </p>
          </div>
        )}

        {/* Stat cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {/* CI Status */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <p className="text-sm text-gray-500">CI status</p>
            {loading ? (
              <Skeleton className="h-8 w-24 mt-2" />
            ) : ciStatus ? (
              <div className="flex items-center gap-2 mt-1">
                <span className={`w-2 h-2 rounded-full ${ciStatus.dot}`} />
                <p className="text-2xl font-extrabold text-gray-900 capitalize">{ciStatus.text}</p>
              </div>
            ) : (
              <p className="text-2xl font-extrabold text-gray-400 mt-1">—</p>
            )}
            <p className="text-xs text-gray-400 mt-1">
              {ciLatest ? `Run #${ciLatest.runNumber} · ${ago(ciLatest.createdAt)}` : "Optimized AI Agent"}
            </p>
          </div>

          {/* Last DRC run */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <p className="text-sm text-gray-500">Last DRC run</p>
            {loading ? (
              <Skeleton className="h-8 w-20 mt-2" />
            ) : latestDrc ? (
              <p className="text-2xl font-extrabold text-gray-900 mt-1">{ago(latestDrc.createdAt)}</p>
            ) : (
              <p className="text-2xl font-extrabold text-gray-400 mt-1">—</p>
            )}
            <p className="text-xs text-gray-400 mt-1">
              {latestDrc ? `Issue #${latestDrc.issueNumber} · ${latestDrc.priority}` : "DRC pipeline"}
            </p>
          </div>

          {/* Open issues */}
          <div className="bg-white border border-gray-200 rounded-2xl p-6">
            <p className="text-sm text-gray-500">Open issues</p>
            {loading ? (
              <Skeleton className="h-8 w-16 mt-2" />
            ) : (
              <p className="text-3xl font-extrabold text-gray-900 mt-1">
                {data?.repo?.openIssues ?? "—"}
              </p>
            )}
            <p className="text-xs text-gray-400 mt-1">Awaiting DRC analysis</p>
          </div>
        </div>

        {/* CI Pipeline runs */}
        <section className="bg-white border border-gray-200 rounded-2xl mb-6 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-gray-900">CI Pipeline · last 5 runs</h2>
            <a
              href={`https://github.com/${REPO}/actions/workflows/${WORKFLOW_FILE}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-brand-600 hover:underline"
            >
              View all →
            </a>
          </div>
          {loading ? (
            <div className="p-6 space-y-3">
              {[1, 2, 3].map((i) => <Skeleton key={i} className="h-10 w-full" />)}
            </div>
          ) : !data?.ci?.runs?.length ? (
            <p className="text-sm text-gray-400 px-6 py-8 text-center">No runs available</p>
          ) : (
            <table className="w-full text-sm">
              <tbody>
                {data.ci.runs.map((run, i) => {
                  const label = ciLabel(run);
                  return (
                    <tr key={run.id} className={`border-t border-gray-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50/30"}`}>
                      <td className="px-6 py-3 w-8 text-gray-400 font-mono text-xs">#{run.runNumber}</td>
                      <td className="px-2 py-3 w-24">
                        <span className={`inline-flex items-center gap-1.5 text-xs font-medium px-2 py-0.5 rounded-full ${label.cls}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${label.dot}`} />
                          {label.text}
                        </span>
                      </td>
                      <td className="px-2 py-3 text-gray-700 truncate max-w-xs">{run.commitMsg}</td>
                      <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap text-right">
                        {ago(run.createdAt)}
                      </td>
                      <td className="px-4 py-3 text-right">
                        <a
                          href={run.htmlUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-brand-600 hover:underline"
                        >
                          →
                        </a>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </section>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* DRC Activity */}
          <section className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-900">DRC Activity · recent analyses</h2>
            </div>
            {loading ? (
              <div className="p-6 space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : !data?.drcRuns?.length ? (
              <p className="text-sm text-gray-400 px-6 py-8 text-center">
                No recent DRC runs found in the last 100 comments
              </p>
            ) : (
              <table className="w-full text-sm">
                <tbody>
                  {data.drcRuns.map((run, i) => (
                    <tr key={run.id} className={`border-t border-gray-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50/30"}`}>
                      <td className="px-6 py-3 text-gray-400 font-mono text-xs w-10">#{run.issueNumber}</td>
                      <td className="px-2 py-3 w-12">
                        <PriorityBadge p={run.priority} />
                      </td>
                      <td className="px-2 py-3 text-gray-400 text-xs">{ago(run.createdAt)}</td>
                      <td className="px-4 py-3 text-right">
                        <a
                          href={run.issueUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-xs text-brand-600 hover:underline"
                        >
                          →
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>

          {/* Open issues queue */}
          <section className="bg-white border border-gray-200 rounded-2xl overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
              <h2 className="text-sm font-semibold text-gray-900">Open Issues · DRC queue</h2>
              <a
                href={`https://github.com/${REPO}/issues`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-xs text-brand-600 hover:underline"
              >
                View all →
              </a>
            </div>
            {loading ? (
              <div className="p-6 space-y-3">
                {[1, 2, 3].map((i) => <Skeleton key={i} className="h-8 w-full" />)}
              </div>
            ) : !data?.openIssues?.length ? (
              <p className="text-sm text-gray-400 px-6 py-8 text-center">No open issues</p>
            ) : (
              <table className="w-full text-sm">
                <tbody>
                  {data.openIssues.map((issue, i) => (
                    <tr key={issue.number} className={`border-t border-gray-50 ${i % 2 === 0 ? "bg-white" : "bg-gray-50/30"}`}>
                      <td className="px-6 py-3 text-gray-400 font-mono text-xs w-10">#{issue.number}</td>
                      <td className="px-2 py-3 max-w-0 w-full">
                        <div className="flex flex-col gap-1">
                          <a
                            href={issue.htmlUrl}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-800 hover:text-brand-600 truncate text-xs"
                          >
                            {issue.title}
                          </a>
                          {issue.labels.length > 0 && (
                            <div className="flex gap-1 flex-wrap">
                              {issue.labels.slice(0, 3).map((l) => (
                                <LabelChip key={l} label={l} />
                              ))}
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs whitespace-nowrap">
                        {ago(issue.updatedAt)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
