#!/usr/bin/env python3
"""
GitHub Actions Status Monitor
Real-time monitoring of GitHub Actions workflow runs.
"""

import os
import sys
import time
from datetime import datetime

try:
    import requests
except ImportError:
    print("❌ requests library not installed. Run: pip install requests")
    sys.exit(1)


class GitHubActionsMonitor:
    """Monitor GitHub Actions workflows."""

    def __init__(self, repo: str, token: str | None = None):
        self.repo = repo  # Format: owner/repo
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = f"https://api.github.com/repos/{repo}"

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }

        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
        else:
            print("⚠️ No GitHub token provided. API rate limits will be lower.")

    def get_workflow_runs(
        self,
        workflow_id: str | None = None,
        branch: str | None = None,
        status: str | None = None,
        limit: int = 10,
    ) -> list[dict]:
        """Get workflow runs."""
        url = f"{self.base_url}/actions/runs"
        params = {"per_page": limit}

        if workflow_id:
            params["workflow_id"] = workflow_id
        if branch:
            params["branch"] = branch
        if status:
            params["status"] = status

        try:
            response = requests.get(
                url, headers=self.headers, params=params, timeout=30
            )
            response.raise_for_status()
            return response.json()["workflow_runs"]
        except requests.RequestException as e:
            print(f"❌ Error fetching workflow runs: {e}")
            return []

    def get_run_details(self, run_id: int) -> dict | None:
        """Get details of a specific run."""
        url = f"{self.base_url}/actions/runs/{run_id}"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Error fetching run details: {e}")
            return None

    def get_run_jobs(self, run_id: int) -> list[dict]:
        """Get jobs for a workflow run."""
        url = f"{self.base_url}/actions/runs/{run_id}/jobs"

        try:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return response.json()["jobs"]
        except requests.RequestException as e:
            print(f"❌ Error fetching jobs: {e}")
            return []

    def format_duration(self, seconds: int) -> str:
        """Format duration in human-readable format."""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            return f"{seconds // 60}m {seconds % 60}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

    def get_status_emoji(self, status: str, conclusion: str | None = None) -> str:
        """Get emoji for status."""
        if status == "completed":
            if conclusion == "success":
                return "✅"
            elif conclusion == "failure":
                return "❌"
            elif conclusion == "cancelled":
                return "🚫"
            elif conclusion == "skipped":
                return "⏭️"
            else:
                return "❓"
        elif status == "in_progress":
            return "🔄"
        elif status == "queued":
            return "⏳"
        else:
            return "❓"

    def display_run_summary(self, run: dict):
        """Display summary of a workflow run."""
        status = run["status"]
        conclusion = run.get("conclusion")
        emoji = self.get_status_emoji(status, conclusion)

        created_at = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))

        duration = (updated_at - created_at).total_seconds()
        duration_str = self.format_duration(int(duration))

        print(f"\n{emoji} Run #{run['run_number']}: {run['name']}")
        print(f"   Branch: {run['head_branch']}")
        print(
            f"   Commit: {run['head_sha'][:7]} - {run['head_commit']['message'].split(chr(10))[0][:50]}"
        )
        print(
            f"   Status: {status.title()}" + (f" ({conclusion})" if conclusion else "")
        )
        print(f"   Duration: {duration_str}")
        print(f"   Started: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   URL: {run['html_url']}")

    def display_jobs(self, run_id: int):
        """Display jobs for a run."""
        jobs = self.get_run_jobs(run_id)

        if not jobs:
            print("   No jobs found")
            return

        print("\n   Jobs:")
        for job in jobs:
            emoji = self.get_status_emoji(job["status"], job.get("conclusion"))

            if job.get("started_at") and job.get("completed_at"):
                started = datetime.fromisoformat(
                    job["started_at"].replace("Z", "+00:00")
                )
                completed = datetime.fromisoformat(
                    job["completed_at"].replace("Z", "+00:00")
                )
                duration = (completed - started).total_seconds()
                duration_str = self.format_duration(int(duration))
            else:
                duration_str = "N/A"

            print(
                f"   {emoji} {job['name']}: {job['status']}"
                + (f" ({job.get('conclusion')})" if job.get("conclusion") else "")
                + f" - {duration_str}"
            )

    def monitor_run(self, run_id: int, interval: int = 10):
        """Monitor a specific run in real-time."""
        print(f"📊 Monitoring run #{run_id}...")
        print(f"   Refresh interval: {interval}s")
        print("   Press Ctrl+C to stop\n")

        try:
            while True:
                run = self.get_run_details(run_id)

                if not run:
                    print("❌ Could not fetch run details")
                    break

                # Clear screen (works on most terminals)
                print("\033[2J\033[H", end="")

                self.display_run_summary(run)
                self.display_jobs(run_id)

                if run["status"] == "completed":
                    print(f"\n✅ Run completed with status: {run['conclusion']}")
                    break

                print(f"\nNext update in {interval}s... (Ctrl+C to stop)")
                time.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped")

    def display_recent_runs(self, limit: int = 5):
        """Display recent workflow runs."""
        print(f"📋 Recent workflow runs (last {limit}):\n")

        runs = self.get_workflow_runs(limit=limit)

        if not runs:
            print("No runs found")
            return

        for run in runs:
            self.display_run_summary(run)

    def get_workflow_statistics(self, days: int = 30) -> dict:
        """Get workflow statistics."""
        runs = self.get_workflow_runs(limit=100)  # Get more runs for stats

        if not runs:
            return {}

        total = len(runs)
        successful = sum(1 for r in runs if r.get("conclusion") == "success")
        failed = sum(1 for r in runs if r.get("conclusion") == "failure")
        cancelled = sum(1 for r in runs if r.get("conclusion") == "cancelled")

        durations = []
        for run in runs:
            if (
                run["status"] == "completed"
                and run.get("created_at")
                and run.get("updated_at")
            ):
                created = datetime.fromisoformat(
                    run["created_at"].replace("Z", "+00:00")
                )
                updated = datetime.fromisoformat(
                    run["updated_at"].replace("Z", "+00:00")
                )
                duration = (updated - created).total_seconds()
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_runs": total,
            "successful": successful,
            "failed": failed,
            "cancelled": cancelled,
            "success_rate": (successful / total * 100) if total > 0 else 0,
            "avg_duration": avg_duration,
        }


def main():
    """Main execution."""
    import argparse

    parser = argparse.ArgumentParser(description="Monitor GitHub Actions workflows")
    parser.add_argument("repo", help="Repository (owner/repo)")
    parser.add_argument("--token", help="GitHub personal access token")
    parser.add_argument("--monitor", type=int, help="Monitor specific run ID")
    parser.add_argument("--recent", type=int, default=5, help="Show recent runs")
    parser.add_argument("--stats", action="store_true", help="Show workflow statistics")

    args = parser.parse_args()

    monitor = GitHubActionsMonitor(args.repo, args.token)

    if args.monitor:
        monitor.monitor_run(args.monitor)
    elif args.stats:
        stats = monitor.get_workflow_statistics()
        print("\n📊 Workflow Statistics (last 100 runs):\n")
        print(f"Total runs: {stats['total_runs']}")
        print(f"✅ Successful: {stats['successful']}")
        print(f"❌ Failed: {stats['failed']}")
        print(f"🚫 Cancelled: {stats['cancelled']}")
        print(f"📈 Success rate: {stats['success_rate']:.1f}%")
        print(f"⏱️ Avg duration: {monitor.format_duration(int(stats['avg_duration']))}")
    else:
        monitor.display_recent_runs(args.recent)


if __name__ == "__main__":
    main()
