# autopilot

GitHub Autopilot v0 - Automated Daily Repository Summary

Generates a comprehensive daily summary of GitHub repository activity including:
- Open issues and PRs
- Recent commits (last 24h)
- Priority-ranked "Top 3" action items

Usage:
    python autopilot.py [--config config.yaml] [--output DAILY_SUMMARY.md]

Requires:
    GITHUB_TOKEN environment variable for API access

## Class: GitHubAutopilot

Main autopilot orchestrator for GitHub repository summaries

## Function: main

CLI entry point
