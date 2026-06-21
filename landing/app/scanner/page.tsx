"use client";

import { useState } from "react";
import type { ScanReport, CheckResult } from "@/lib/scan-types";

const GROWTH_LINK = process.env.NEXT_PUBLIC_STRIPE_GROWTH_PAYMENT_LINK ?? "https://gadgetlab.uk/#pricing";

export default function ScannerPage() {
  const [repo, setRepo] = useState("");
  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState<ScanReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function handleScan(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setReport(null);
    setError(null);

    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ repo }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error ?? "Something went wrong");
      } else {
        setReport(data as ScanReport);
      }
    } catch {
      setError("Network error — please try again");
    } finally {
      setLoading(false);
    }
  }

  function copyEmbed() {
    if (!report) return;
    navigator.clipboard.writeText(report.embedCode).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-brand-50 to-white text-gray-900">
      {/* Nav */}
      <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <a href="/" className="font-bold text-lg tracking-tight">🤖 GadgetLab Agent</a>
          <a
            href={GROWTH_LINK}
            className="bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors text-sm"
          >
            Start free trial
          </a>
        </div>
      </nav>

      <div className="max-w-2xl mx-auto px-4 pt-32 pb-20">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 bg-brand-50 border border-brand-200 text-brand-700 text-sm font-medium px-4 py-1.5 rounded-full mb-4">
            Free · No login required
          </div>
          <h1 className="text-4xl font-extrabold tracking-tight text-gray-900 mb-3">
            Repo Health Scanner
          </h1>
          <p className="text-gray-500 text-lg">
            Get an instant health score for any public GitHub repository.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleScan} className="flex gap-2 mb-8">
          <input
            type="text"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            placeholder="owner/repo or https://github.com/owner/repo"
            className="flex-1 border border-gray-200 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
            required
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-brand-600 text-white px-6 py-3 rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium disabled:opacity-50"
          >
            {loading ? "Scanning…" : "Analyze"}
          </button>
        </form>

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm mb-6">
            {error}
          </div>
        )}

        {/* Results */}
        {report && (
          <div className="space-y-4">
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
                <div className="text-right">
                  <span className="text-xs text-gray-400">⭐ {report.stars.toLocaleString()} stars</span>
                </div>
              </div>
            </div>

            {/* Checks */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 space-y-2">
              {Object.values(report.checks).map((check) => (
                <CheckRow key={check.label} check={check} />
              ))}
            </div>

            {/* Badge embed */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4">
              <p className="text-sm font-medium text-gray-700 mb-2">Add to your README</p>
              <div className="flex items-center gap-2">
                <code className="flex-1 text-xs bg-gray-50 border border-gray-200 rounded px-3 py-2 text-gray-600 truncate">
                  {report.embedCode}
                </code>
                <button
                  onClick={copyEmbed}
                  className="text-sm text-brand-600 hover:text-brand-700 font-medium whitespace-nowrap"
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
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
          </div>
        )}

        {/* How it works */}
        {!report && !loading && (
          <div className="text-center text-sm text-gray-400 mt-8 space-y-1">
            <p>Works with any public GitHub repository.</p>
            <p>Checks CI status, open issues, stale PRs, commit activity, and security hygiene.</p>
          </div>
        )}
      </div>
    </main>
  );
}

function CheckRow({ check }: { check: CheckResult }) {
  const icons = { good: "✅", warning: "⚠️", critical: "❌", unknown: "⬜" };
  const colors = {
    good: "text-green-700",
    warning: "text-yellow-700",
    critical: "text-red-700",
    unknown: "text-gray-500",
  };

  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-50 last:border-0">
      <div className="flex items-center gap-2">
        <span>{icons[check.status]}</span>
        <span className="text-sm font-medium text-gray-700">{check.label}</span>
      </div>
      <div className="flex items-center gap-3">
        <span className={`text-xs ${colors[check.status]}`}>{check.detail}</span>
        <span className="text-xs text-gray-400 tabular-nums">
          {check.points}/{check.maxPoints}
        </span>
      </div>
    </div>
  );
}
