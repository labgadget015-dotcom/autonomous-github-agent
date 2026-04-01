#!/usr/bin/env python3
"""Main AI agent script for autonomous GitHub operations.

Uses the Claude Agent SDK so Claude can directly read changed files,
grep for patterns, and explore the repository — rather than receiving
only a text summary of the diff.
"""

import argparse
import json
import re
import sys
import anyio
from pathlib import Path

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query


def load_context(context_file: str) -> dict:
    """Load context from JSON file."""
    try:
        with open(context_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading context: {e}")
        return {}


def build_prompt(context: dict) -> str:
    """Build analysis prompt from GitHub event context."""
    repo = context.get("repository", "unknown")
    event = context.get("event_name", "unknown")
    ref = context.get("ref", "unknown")
    changed_files = context.get("changed_files", [])
    pr_title = context.get("pr_title", "")
    pr_body = context.get("pr_body", "")

    files_section = (
        "\n".join(f"- {f}" for f in changed_files)
        if changed_files
        else "(not specified — use Glob to discover recent changes)"
    )

    header_parts = [f"GitHub {event} event on {repo} (ref: {ref})."]
    if pr_title:
        header_parts.append(f"PR: {pr_title}")
    if pr_body:
        header_parts.append(f"Description: {pr_body[:500]}")

    return f"""{' '.join(header_parts)}

Changed files:
{files_section}

Perform a thorough code review:
1. Read each changed file listed above (use Glob if the list is empty)
2. Grep for common anti-patterns: hardcoded secrets, SQL string formatting, eval(), shell=True
3. Identify bugs, security issues, and code quality problems
4. Note any missing test coverage for changed logic

For each finding provide:
- File path and approximate line number
- Severity: HIGH / MEDIUM / LOW
- Concise description of the issue
- A concrete fix or suggestion

Respond with a JSON object in exactly this shape (no markdown fences):
{{
  "status": "success",
  "summary": "<one-sentence overall verdict>",
  "agent_actions": ["<tool calls made, e.g. Read src/foo.py>"],
  "recommendations": [
    {{
      "file": "<path>",
      "line": <int or null>,
      "severity": "HIGH|MEDIUM|LOW",
      "issue": "<description>",
      "fix": "<suggestion>"
    }}
  ],
  "issues_found": <int>
}}"""


async def run_ai_agent(context: dict) -> dict:
    """Execute AI agent operations using the Claude Agent SDK."""
    print("=== AI Agent Execution ===")
    print(f"Repository: {context.get('repository', 'unknown')}")
    print(f"Event:      {context.get('event_name', 'unknown')}")
    print(f"Ref:        {context.get('ref', 'unknown')}")

    prompt = build_prompt(context)
    cwd = context.get("workspace", ".")
    result_text = None

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            cwd=cwd,
            allowed_tools=["Read", "Glob", "Grep"],
            max_turns=30,
            permission_mode="default",
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    if result_text:
        json_match = re.search(r"\{[\s\S]*\}", result_text)
        if json_match:
            try:
                results = json.loads(json_match.group())
                results.setdefault("status", "success")
                results.setdefault("agent_actions", [])
                results.setdefault("recommendations", [])
                results.setdefault("issues_found", len(results["recommendations"]))
                return results
            except json.JSONDecodeError:
                pass

    return {
        "status": "success",
        "summary": result_text or "No analysis produced",
        "agent_actions": [],
        "recommendations": [],
        "issues_found": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AI agent")
    parser.add_argument("--context", required=True, help="Context JSON file")
    args = parser.parse_args()

    try:
        context = load_context(args.context)
        results = anyio.run(run_ai_agent, context)

        results_file = Path("results.json")
        with open(results_file, "w") as f:
            json.dump(results, f, indent=2)

        issues = results.get("issues_found", 0)
        print(f"Results saved to {results_file}")
        print(f"Issues found: {issues}")
        print("AI agent completed successfully")
        sys.exit(0)
    except Exception as e:
        print(f"Error running AI agent: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
