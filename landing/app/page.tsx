import Link from "next/link";

const GROWTH_LINK = process.env.NEXT_PUBLIC_STRIPE_GROWTH_PAYMENT_LINK ?? "#pricing";
const ENTERPRISE_URL =
  process.env.NEXT_PUBLIC_STRIPE_ENTERPRISE_CONTACT_URL ??
  "mailto:labgadget015@gmail.com?subject=Enterprise%20Inquiry";

export default function Home() {
  return (
    <main className="min-h-screen bg-white text-gray-900">
      <Nav />
      <Hero />
      <Features />
      <HowItWorks />
      <Pricing />
      <Footer />
    </main>
  );
}

function Nav() {
  return (
    <nav className="fixed top-0 w-full z-50 bg-white/90 backdrop-blur border-b border-gray-100">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <span className="font-bold text-lg tracking-tight">🤖 GadgetLab Agent</span>
        <div className="flex items-center gap-6 text-sm">
          <a href="#features" className="text-gray-600 hover:text-gray-900">Features</a>
          <a href="#how-it-works" className="text-gray-600 hover:text-gray-900">How it works</a>
          <a href="#pricing" className="text-gray-600 hover:text-gray-900">Pricing</a>
          <a href="/scanner" className="text-gray-600 hover:text-gray-900">Free scan</a>
          <a
            href="https://github.com/labgadget015-dotcom/autonomous-github-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-gray-900"
          >
            GitHub
          </a>
          <a
            href={GROWTH_LINK}
            className="bg-brand-600 text-white px-4 py-2 rounded-lg hover:bg-brand-700 transition-colors"
          >
            Start free trial
          </a>
        </div>
      </div>
    </nav>
  );
}

function Hero() {
  return (
    <section className="pt-32 pb-20 px-4 text-center bg-gradient-to-b from-brand-50 to-white">
      <div className="max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 bg-brand-50 border border-brand-200 text-brand-700 text-sm font-medium px-4 py-1.5 rounded-full mb-6">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
          Now live — 14-day free trial, no card required
        </div>
        <h1 className="text-5xl sm:text-6xl font-extrabold tracking-tight text-gray-900 mb-6">
          Your GitHub repo,{" "}
          <span className="text-brand-600">autonomously managed</span>
        </h1>
        <p className="text-xl text-gray-500 max-w-2xl mx-auto mb-10">
          The Dreamer-Realist-Critic pipeline reviews every issue and PR, posts
          actionable recommendations, and routes LLM calls intelligently — cutting
          token costs by <strong>90%</strong>.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <a
            href={GROWTH_LINK}
            className="bg-brand-600 text-white px-8 py-4 rounded-xl text-lg font-semibold hover:bg-brand-700 transition-colors shadow-lg shadow-brand-200"
          >
            Start 14-day free trial →
          </a>
          <a
            href="https://github.com/labgadget015-dotcom/autonomous-github-agent"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white border border-gray-200 text-gray-700 px-8 py-4 rounded-xl text-lg font-semibold hover:border-gray-400 transition-colors"
          >
            ⭐ Star on GitHub
          </a>
        </div>
        <p className="mt-6 text-sm text-gray-400">
          Open source · Self-host for free · Growth tier from £199/mo
        </p>
      </div>
    </section>
  );
}

const features = [
  {
    icon: "🧠",
    title: "Dreamer-Realist-Critic pipeline",
    desc: "Three Claude Sonnet agents in sequence: generate bold ideas, stress-test them for feasibility, then synthesise the best path forward.",
  },
  {
    icon: "💬",
    title: "Auto GitHub comments",
    desc: "Every issue gets a full P0–P2 priority analysis posted directly as a comment within ~100 seconds of creation.",
  },
  {
    icon: "💰",
    title: "90% token cost reduction",
    desc: "Smart local/cloud routing sends simple tasks to a local LLM and only sends complex work to Claude — dramatically cutting API costs.",
  },
  {
    icon: "🔔",
    title: "Slack notifications",
    desc: "DRC recommendations posted to #drc-recommendations with priority label, top pick, and next steps — no dashboard to check.",
  },
  {
    icon: "🔒",
    title: "HMAC webhook validation",
    desc: "Every GitHub event is signature-verified before processing. No unauthenticated code execution, ever.",
  },
  {
    icon: "🚀",
    title: "12 GitHub Actions workflows",
    desc: "Parallel test matrix (Py 3.10/3.11/3.12), security scanning, overseer, pre-commit CI — all pre-configured out of the box.",
  },
  {
    icon: "🔍",
    title: "Free repo health scanner",
    desc: "Instant health score for any public GitHub repo — CI status, open issues, stale PRs, commit activity, and security hygiene. No login required.",
  },
  {
    icon: "📊",
    title: "Live README health badge",
    desc: "One-line embed that shows a live A+–D grade in your README, updating every 5 minutes based on real repo data.",
  },
];

function Features() {
  return (
    <section id="features" className="py-20 px-4 bg-white">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4">Everything you need to ship faster</h2>
        <p className="text-gray-500 text-center mb-12 max-w-xl mx-auto">
          Built on n8n, GitHub Actions, and Anthropic Claude — the full stack from webhook to recommendation in one pipeline.
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f) => (
            <div key={f.title} className="p-6 border border-gray-100 rounded-2xl hover:border-brand-200 hover:shadow-sm transition-all">
              <div className="text-3xl mb-3">{f.icon}</div>
              <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function HowItWorks() {
  const steps = [
    { n: "1", title: "GitHub fires a webhook", desc: "Issue opened or PR created triggers an HMAC-validated event to n8n." },
    { n: "2", title: "Event Router filters & routes", desc: "Validates signature, extracts payload, forwards only actionable events." },
    { n: "3", title: "DRC agents analyse in sequence", desc: "DREAMER proposes 3–5 solutions. REALIST stress-tests feasibility. CRITIC picks the winner." },
    { n: "4", title: "Results delivered everywhere", desc: "Comment posted on the GitHub issue. Slack notification in #drc-recommendations. Stored in Postgres." },
  ];
  return (
    <section id="how-it-works" className="py-20 px-4 bg-gray-50">
      <div className="max-w-4xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-12">How it works</h2>
        <div className="space-y-6">
          {steps.map((s) => (
            <div key={s.n} className="flex gap-5 items-start">
              <div className="flex-shrink-0 w-10 h-10 bg-brand-600 text-white rounded-full flex items-center justify-center font-bold text-sm">
                {s.n}
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">{s.title}</h3>
                <p className="text-sm text-gray-500 mt-1">{s.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function Pricing() {
  return (
    <section id="pricing" className="py-20 px-4 bg-white">
      <div className="max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold text-center mb-4">Simple, transparent pricing</h2>
        <p className="text-gray-500 text-center mb-12">Start free. Upgrade when you need cloud hosting and premium features.</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 items-start">
          <PricingCard
            name="Open Source"
            price="Free"
            desc="Self-hosted. Forever."
            features={[
              "Unlimited repos (self-hosted)",
              "Local LLM support",
              "DRC agent pipeline",
              "GitHub Actions CI",
              "Community support",
            ]}
            cta="Get started on GitHub"
            ctaHref="https://github.com/labgadget015-dotcom/autonomous-github-agent"
            ctaStyle="secondary"
          />
          <PricingCard
            name="Growth"
            price="£199"
            priceSuffix="/mo"
            desc="Fully managed. Zero setup."
            badge="Most popular"
            features={[
              "Everything in Open Source",
              "☁️ Cloud-hosted, ready in 60s",
              "📊 Analytics dashboard",
              "⚡ 2× faster processing",
              "🛡️ 99.5% uptime SLA",
              "📧 Email support",
              "50 repos · 10 members · 10K analyses/mo",
            ]}
            cta="Start 14-day free trial →"
            ctaHref={GROWTH_LINK}
            ctaStyle="primary"
          />
          <PricingCard
            name="Enterprise"
            price="$2,499"
            priceSuffix="/mo+"
            desc="Custom. Unlimited. Dedicated."
            features={[
              "Everything in Growth",
              "Unlimited everything",
              "Self-hosted or private cloud",
              "SOC 2 / GDPR compliance",
              "Dedicated account manager",
              "24/7 phone + Slack support",
              "Custom LLM training",
            ]}
            cta="Contact sales"
            ctaHref={ENTERPRISE_URL}
            ctaStyle="secondary"
          />
        </div>
      </div>
    </section>
  );
}

function PricingCard({
  name, price, priceSuffix, desc, badge, features, cta, ctaHref, ctaStyle,
}: {
  name: string; price: string; priceSuffix?: string; desc: string;
  badge?: string; features: string[]; cta: string; ctaHref: string;
  ctaStyle: "primary" | "secondary";
}) {
  return (
    <div className={`relative rounded-2xl border p-8 ${badge ? "border-brand-500 shadow-lg shadow-brand-100 ring-1 ring-brand-500" : "border-gray-200"}`}>
      {badge && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-600 text-white text-xs font-semibold px-3 py-1 rounded-full">
          {badge}
        </div>
      )}
      <div className="mb-6">
        <p className="text-sm font-medium text-gray-500 mb-1">{name}</p>
        <div className="flex items-end gap-1">
          <span className="text-4xl font-extrabold text-gray-900">{price}</span>
          {priceSuffix && <span className="text-gray-400 mb-1">{priceSuffix}</span>}
        </div>
        <p className="text-sm text-gray-500 mt-1">{desc}</p>
      </div>
      <ul className="space-y-3 mb-8">
        {features.map((f) => (
          <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
            <span className="text-green-500 mt-0.5 flex-shrink-0">✓</span>
            {f}
          </li>
        ))}
      </ul>
      <a
        href={ctaHref}
        className={`block w-full text-center py-3 rounded-xl font-semibold transition-colors ${
          ctaStyle === "primary"
            ? "bg-brand-600 text-white hover:bg-brand-700"
            : "border border-gray-300 text-gray-700 hover:border-gray-400 bg-white"
        }`}
      >
        {cta}
      </a>
    </div>
  );
}

function Footer() {
  return (
    <footer className="border-t border-gray-100 py-10 px-4 bg-white">
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-gray-400">
        <span>© {new Date().getFullYear()} GadgetLab · labgadget015@gmail.com</span>
        <div className="flex gap-6">
          <a href="https://github.com/labgadget015-dotcom/autonomous-github-agent" target="_blank" rel="noopener noreferrer" className="hover:text-gray-600">GitHub</a>
          <a href="mailto:labgadget015@gmail.com?subject=Enterprise%20Inquiry" className="hover:text-gray-600">Contact</a>
          <a href="#pricing" className="hover:text-gray-600">Pricing</a>
        </div>
      </div>
    </footer>
  );
}
