export interface CheckResult {
  label: string;
  status: "good" | "warning" | "critical" | "unknown";
  detail: string;
  points: number;
  maxPoints: number;
}

export interface ScanReport {
  owner: string;
  repo: string;
  fullName: string;
  score: number;
  grade: string;
  color: string;
  checks: {
    ci: CheckResult;
    issues: CheckResult;
    prs: CheckResult;
    activity: CheckResult;
    security: CheckResult;
  };
  badgeUrl: string;
  embedCode: string;
  stars: number;
  description: string | null;
}
