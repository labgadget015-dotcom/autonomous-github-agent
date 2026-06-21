import { notFound } from "next/navigation";
import type { Metadata } from "next";
import { runScan } from "@/lib/scan";
import type { CheckResult, ScanReport } from "@/lib/scan-types";

export const revalidate = 3600;

type Props = { params: Promise<{ owner: string; repo: string }> };

async function getScan(owner: string, repo: string): Promise<ScanReport | null> {
  try {
    return await runScan(owner, repo);
  } catch (err) {
    if ((err as Error & { status?: number }).status === 404) return null;
    throw err;
  }
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { owner, repo } = await params;
  const report = await getScan(owner, repo);
  if (!report) return { title: "Repo not found — GadgetLab" };

  const critical = Object.values(report.checks).filter((c) => c.status === "critical");
  const desc =
    critical.length > 0
      ? `Score: ${report.grade} (${report.score}/100). Needs attention: ${critical.map((c) => c.label).join(", ")}.`
      : `Score: ${report.grade} (${report.score}/100). All checks passing.`;

  return {
    title: `${report.fullName} — ${report.grade} (${report.score}/100) | GadgetLab`,
    description: desc,
    openGraph: {
      title: `${report.fullName} scored ${report.grade} on GadgetLab`,
      description: desc,
      url: `https://gadgetlab.uk/scan/${owner}/${repo}`,
      siteName: "GadgetLab",
    },
    twitter: { card: "summary", title: `${report.fullName} — ${report.grade} (${report.score}/100)`, description: desc },
  };
}

const ICONS = { good: "✅", warning: "⚠️", critical: "❌", unknown: "⬜" } as const;
const COLORS = { good: "text-green-700", warning: "text-yellow-700", critical: "text-red-700", unknown: "text-gray-500" } as const;

function CheckRow({ check }: { check: CheckResult }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <div className="flex items-center gap-2">
        <span>{ICONS[check.status]}</span>
        <span className="text-sm font-medium text-gray-700">{check.label}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className={`text-xs ${COLORS[check.status]}`}>{check.detail}</span>
        <span className="text-xs text-gray-400 tabular-nums">{check.points}/{check.maxPoints}</span>
      </div>
    </div>
  );
}

const GROWTH_LINK = process.env.NEXT_PUBLIC_STRIPE_GROWTH_PAYMENT_LINK ?? "https://gadgetlab.uk/#pricing";

export default async function ScanPage({ params }: Props) {
  const { owner, repo } = await params;
  const report = await getScan(owner, repo);
  if (!report) notFound();

  const shareText = encodeURIComponent(
    `🤖 ${report.fullName} scored ${report.grade} (${report.score}/100) on GadgetLab's free repo health scanner`
  );
  const shareUrl = encodeURIComponent(`https://gadgetlab.uk/scan/${owner}/${repo}`);
  const tweetHref = `https://twitter.com/intent/tweet?text=${shareText}&url=${shareUrl}`;

  return (
    <main className="min-h-screen bg-gradient-to-b from-brand-50 to-white text-gray-900">
      <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <a href="/" className="font-bold text-lg tracking-tight">🤖 GadgetLab Agent</a>
          <div className="flex items-center gap-3">
            <a href="/scanner" className="text-sm text-gray-600 hover:text-gray-900">Scan a repo</a>
            <a
              href={GROWTH_LINK}
              className="bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors text-sm"
            >
              Start free trial
            </a>
          </div>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-4 pt-32 pb-20 space-y-4">
        {/* Score card */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-gray-500 mb-1">{report.fullName}</p>
              {report.description && (
                <p className="text-gray-700 text-sm mb-3">{report.description}</p>
              )}
              <div className="flex items-baseline gap-3">
                <span className="text-6xl font-extrabold" style={{ color: report.color }}>
                  {report.grade}
                </span>
                <span className="text-2xl font-bold text-gray-400">{report.score}/100</span>
              </div>
            </div>
            <span className="text-xs text-gray-400">⭐ {report.stars.toLocaleString()} stars</span>
          </div>
        </div>

        {/* Checks */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
          {Object.values(report.checks).map((check) => (
            <CheckRow key={check.label} check={check} />
          ))}
        </div>

        {/* Badge embed */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
          <p className="text-sm font-medium text-gray-700 mb-2">Add to your README</p>
          <code className="block text-xs bg-gray-50 border border-gray-200 rounded px-3 py-2 text-gray-600 break-all">
            {report.embedCode}
          </code>
        </div>

        {/* Share + scan row */}
        <div className="flex gap-3">
          <a
            href={tweetHref}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-1 flex items-center justify-center bg-black text-white rounded-xl py-3 text-sm font-medium hover:bg-gray-800 transition-colors"
          >
            Share on X
          </a>
          <a
            href="/scanner"
            className="flex-1 flex items-center justify-center bg-white border border-gray-200 text-gray-700 rounded-xl py-3 text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            Scan another repo
          </a>
        </div>

        {/* CTA */}
        <div className="bg-brand-600 rounded-2xl p-6 text-white text-center">
          <p className="font-bold text-lg mb-1">Want the full DRC deep analysis?</p>
          <p className="text-brand-100 text-sm mb-4">
            The Dreamer / Realist / Critic agent loop runs on every issue and PR — recommending fixes, flagging risks, and auto-triaging your backlog.
          </p>
          <a
            href={GROWTH_LINK}
            className="inline-block bg-white text-brand-700 font-semibold px-6 py-2.5 rounded-lg hover:bg-brand-50 transition-colors text-sm"
          >
            Start 14-day free trial →
          </a>
        </div>

        <p className="text-center text-xs text-gray-400">
          Scores refresh hourly ·{" "}
          <a
            href={`https://github.com/${owner}/${repo}`}
            target="_blank"
            rel="noopener noreferrer"
            className="underline"
          >
            View on GitHub
          </a>
        </p>
      </div>
    </main>
  );
}
