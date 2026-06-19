import Link from "next/link";

const GROWTH_LINK = process.env.NEXT_PUBLIC_STRIPE_GROWTH_PAYMENT_LINK ?? "#pricing";

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-gray-50">
      <nav className="bg-white border-b border-gray-100 px-4 h-16 flex items-center justify-between">
        <Link href="/" className="font-bold text-lg tracking-tight text-gray-900">
          GadgetLab Agent
        </Link>
        <span className="text-sm text-gray-400">Dashboard</span>
      </nav>

      <div className="max-w-5xl mx-auto px-4 py-12">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Monitor your autonomous GitHub agent pipeline.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-8">
          {[
            { label: "Issues analysed", value: "—", sub: "All time" },
            { label: "Avg response time", value: "~100s", sub: "DRC pipeline" },
            { label: "Token cost saved", value: "—", sub: "vs. cloud-only" },
          ].map((stat) => (
            <div key={stat.label} className="bg-white border border-gray-200 rounded-2xl p-6">
              <p className="text-sm text-gray-500">{stat.label}</p>
              <p className="text-3xl font-extrabold text-gray-900 mt-1">{stat.value}</p>
              <p className="text-xs text-gray-400 mt-1">{stat.sub}</p>
            </div>
          ))}
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center">
          <div className="w-12 h-12 bg-brand-50 rounded-full flex items-center justify-center mx-auto mb-4">
            <span className="text-2xl">🚧</span>
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Full dashboard coming soon</h2>
          <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
            Live pipeline logs, per-repo analytics, cost tracking, and team management are in development.
            You&apos;ll be notified when they launch.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href="https://github.com/labgadget015-dotcom/autonomous-github-agent"
              target="_blank"
              rel="noopener noreferrer"
              className="bg-brand-600 text-white px-5 py-2.5 rounded-xl text-sm font-semibold hover:bg-brand-700 transition-colors"
            >
              View pipeline on GitHub
            </a>
            <Link
              href={GROWTH_LINK}
              className="border border-gray-300 text-gray-700 px-5 py-2.5 rounded-xl text-sm font-semibold hover:border-gray-400 transition-colors bg-white"
            >
              Manage subscription
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
