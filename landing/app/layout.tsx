import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Autonomous GitHub Agent — AI-Powered GitHub Automation",
  description:
    "Reduce LLM token costs by 90% with intelligent local/cloud routing. Auto-review PRs, triage issues, and ship faster with the Dreamer-Realist-Critic agent pipeline.",
  openGraph: {
    title: "Autonomous GitHub Agent",
    description: "AI-powered GitHub automation with 90% cost reduction",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
