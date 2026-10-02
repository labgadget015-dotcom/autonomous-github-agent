#!/usr/bin/env python3
"""Evaluate GitHub -> DRC intake health from the Neon audit tables.

Why Neon and not the n8n executions API: since the 2026-09-30 cutover the Event
Router and DRC run on the M900's self-hosted n8n, whose API sits behind Caddy
basic_auth and is not reachable from GitHub-hosted runners. Neon is.

Two signals, both written by the pipeline itself:

* ``tim.intake_events`` - the Event Router's "Shadow Log Intake Event" node
  writes one row per delivery that passed HMAC. Router liveness = recency of the
  newest row. A total HMAC rejection (the 2026-08-22 outage) writes nothing, so
  it surfaces as silence.
* ``tim.agent_runs`` - the DRC's audit write. A ``path='forwarded'`` intake row
  is logged AFTER the Forward node returns; Forward has ``neverError`` so it is
  logged even when the DRC fails. A forwarded row with no matching audit row is
  therefore a DRC failure - including the "green execution, no row" class the
  old executions-API canary could not see.

Input: one JSON object on stdin, produced by the query in intake-canary.yml.
Output: ``status``/``detail``/``slack`` lines appended to ``$GITHUB_OUTPUT``.
Exit 0 only on positive evidence of health.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

SILENCE_THRESHOLD_HOURS = float(os.environ.get("SILENCE_THRESHOLD_HOURS", "26"))
ALERT_WINDOW_MINUTES = float(os.environ.get("ALERT_WINDOW_MINUTES", "60"))


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value)


def evaluate(snapshot: dict, remind: bool) -> dict:
    """Return {"status", "detail", "slack", "exit"} for a DB snapshot."""
    try:
        now = _ts(snapshot["now"])
        latest = snapshot.get("latest_at")
        unmatched = snapshot["unmatched"]
        forwarded = int(snapshot["forwarded"])
        if not isinstance(unmatched, list):
            raise TypeError("unmatched is not a list")
    except (KeyError, TypeError, ValueError) as exc:
        return {
            "status": "canary_broken",
            "detail": f"Neon snapshot had an unexpected shape ({exc}). Query or schema changed.",
            "slack": remind,
            "exit": 1,
        }

    if not latest:
        return {
            "status": "pipeline_down",
            "detail": "tim.intake_events is EMPTY. The Event Router has never logged a delivery.",
            "slack": remind,
            "exit": 1,
        }

    age_h = (now - _ts(latest)).total_seconds() / 3600
    if age_h > SILENCE_THRESHOLD_HOURS:
        return {
            "status": "pipeline_down",
            "detail": (
                f"Event Router has logged NOTHING for {age_h:.1f}h (threshold "
                f"{SILENCE_THRESHOLD_HOURS:g}h). Webhook deleted/repointed, workflow "
                "inactive, M900/Funnel down, or HMAC rejecting every delivery."
            ),
            "slack": remind,
            "exit": 1,
        }

    if unmatched:
        newest = unmatched[0]
        age_m = (now - _ts(newest["received_at"])).total_seconds() / 60
        issues = ", ".join(f"#{u.get('issue_number')}" for u in unmatched)
        return {
            "status": "drc_failing",
            "detail": (
                f"{len(unmatched)} of {forwarded} forwarded event(s) in the last 48h have "
                f"NO tim.agent_runs row ({issues}; newest {age_m:.0f}m ago). The Event "
                "Router forwarded them but the DRC council did not complete its audit write."
            ),
            "slack": remind or age_m <= ALERT_WINDOW_MINUTES,
            "exit": 1,
        }

    return {
        "status": "healthy",
        "detail": (
            f"Event Router last logged {age_h:.1f}h ago; {forwarded} forwarded event(s) "
            "in 48h, all with an audit row."
        ),
        "slack": False,
        "exit": 0,
    }


def main() -> int:
    remind = os.environ.get("REMIND", "false") == "true"
    raw = sys.stdin.read()
    try:
        snapshot = json.loads(raw)
    except json.JSONDecodeError:
        snapshot = {}
    result = evaluate(snapshot if isinstance(snapshot, dict) else {}, remind)

    out = os.environ.get("GITHUB_OUTPUT")
    lines = [
        f"status={result['status']}",
        f"detail={result['detail']}",
        f"slack={'true' if result['slack'] else 'false'}",
    ]
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    level = "notice" if result["exit"] == 0 else "error"
    print(f"::{level}::{result['status']}: {result['detail']}")
    return result["exit"]


if __name__ == "__main__":
    sys.exit(main())
