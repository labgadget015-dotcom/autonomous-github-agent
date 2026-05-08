#!/usr/bin/env python3
"""
Notification Manager
Sends notifications to various channels (Slack, Discord, Email)
"""

import json
import os
from typing import Dict, List, Optional

try:
    import requests

    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class NotificationManager:
    """Manage notifications across multiple channels"""

    def __init__(self):
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")
        self.enabled_channels = []

        if self.slack_webhook:
            self.enabled_channels.append("slack")
        if self.discord_webhook:
            self.enabled_channels.append("discord")

    def send_slack_notification(self, message: str, severity: str = "info") -> bool:
        """Send notification to Slack"""
        if not REQUESTS_AVAILABLE or not self.slack_webhook:
            return False

        emoji_map = {
            "success": ":white_check_mark:",
            "error": ":x:",
            "warning": ":warning:",
            "info": ":information_source:",
        }

        payload = {
            "text": f"{emoji_map.get(severity, ':bell:')} {message}",
            "username": "CI/CD Bot",
            "icon_emoji": ":robot_face:",
        }

        try:
            response = requests.post(self.slack_webhook, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False

    def send_discord_notification(self, message: str, severity: str = "info") -> bool:
        """Send notification to Discord"""
        if not REQUESTS_AVAILABLE or not self.discord_webhook:
            return False

        color_map = {
            "success": 3066993,  # Green
            "error": 15158332,  # Red
            "warning": 15105570,  # Orange
            "info": 3447003,  # Blue
        }

        payload = {
            "embeds": [
                {
                    "title": "CI/CD Notification",
                    "description": message,
                    "color": color_map.get(severity, 3447003),
                    "footer": {"text": "Autonomous GitHub Agent"},
                }
            ]
        }

        try:
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            return response.status_code == 204
        except Exception as e:
            print(f"Failed to send Discord notification: {e}")
            return False

    def notify_workflow_status(self, workflow: str, status: str, duration: int):
        """Notify about workflow completion"""
        if status == "success":
            message = f"✅ Workflow '{workflow}' completed successfully in {duration}s"
            severity = "success"
        else:
            message = f"❌ Workflow '{workflow}' failed after {duration}s"
            severity = "error"

        self.send_all_channels(message, severity)

    def notify_security_issue(self, issue: Dict):
        """Notify about security vulnerability"""
        severity = issue.get("severity", "MEDIUM")
        file = issue.get("file", "unknown")
        line = issue.get("line", 0)

        message = f"🚨 Security Issue Detected: {severity}\nFile: {file}:{line}"
        self.send_all_channels(message, "error")

    def notify_coverage_drop(self, old_coverage: float, new_coverage: float):
        """Notify about coverage decrease"""
        drop = old_coverage - new_coverage
        message = f"📉 Test coverage dropped by {drop:.1f}% ({old_coverage:.1f}% → {new_coverage:.1f}%)"
        self.send_all_channels(message, "warning")

    def notify_quality_gate_failure(self, failures: List[str]):
        """Notify about quality gate failures"""
        message = f"⚠️ Quality Gate Failed:\n" + "\n".join(f"- {f}" for f in failures)
        self.send_all_channels(message, "warning")

    def send_all_channels(self, message: str, severity: str = "info"):
        """Send notification to all enabled channels"""
        results = {}

        if "slack" in self.enabled_channels:
            results["slack"] = self.send_slack_notification(message, severity)

        if "discord" in self.enabled_channels:
            results["discord"] = self.send_discord_notification(message, severity)

        return results

    def send_daily_summary(self, stats: Dict):
        """Send daily summary report"""
        message = f"""📊 Daily CI/CD Summary

**Workflow Runs:** {stats.get('total_runs', 0)}
**Success Rate:** {stats.get('success_rate', 0):.1%}
**Avg Duration:** {stats.get('avg_duration', 0):.1f}s
**Coverage:** {stats.get('coverage', 0):.1f}%
**Security Issues:** {stats.get('security_issues', 0)}

Keep up the great work! 🚀"""

        self.send_all_channels(message, "info")


def main():
    """Main entry point"""
    print("📢 Notification Manager\n")

    manager = NotificationManager()

    if not manager.enabled_channels:
        print("⚠️  No notification channels configured")
        print("Set SLACK_WEBHOOK_URL or DISCORD_WEBHOOK_URL environment variables")
        return

    print(f"✅ Enabled channels: {', '.join(manager.enabled_channels)}\n")

    # Example notifications
    print("Sending test notifications...")

    results = manager.send_all_channels(
        "🚀 CI/CD Optimization System Deployed!", "success"
    )

    for channel, success in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {channel.title()}: {'Sent' if success else 'Failed'}")


if __name__ == "__main__":
    main()
