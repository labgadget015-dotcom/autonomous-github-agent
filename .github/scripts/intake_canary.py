"""GitHub -> DRC intake canary: judge n8n pipeline health from the executions API.

Invoked by .github/workflows/intake-canary.yml. See that file for why the
executions API is the only trustworthy signal for this pipeline.

Invariants (each has tests in tests/unit/test_intake_canary.py):
  * fresh failure (newest failure within ALERT_WINDOW_MINUTES) -> exit 1, Slack
  * stale failure (streak still open, newest failure older)   -> exit 0 with a
    warning and status ``stale_incident``, carrying the failing execution id.
    It is NEVER reported as ``healthy``.
  * missing key, transport error, bad shape, missing or unparseable fields,
    unrecognised execution status                              -> UNKNOWN, exit 1
  * every run emits one JSON evidence object (stdout, step output, step summary)

Stdlib only: the canary job installs nothing. The repository is public, so the
evidence carries ids, statuses, timestamps and counts, never response bodies.
"""

from __future__ import annotations

import http.client
import json
import os
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

EVIDENCE_SCHEMA = "intake-canary/v1"

# n8n ExecutionStatus values. Failure statuses extend a streak; in-flight ones
# are skipped so a running execution at the head cannot hide a streak behind
# it; success ends the streak. Anything else (including "unknown" and fields
# n8n may add later) is UNKNOWN, never healthy.
FAILURE_STATUSES = frozenset({"error", "crashed"})
SKIPPED_STATUSES = frozenset({"new", "running", "waiting", "canceled"})
SUCCESS_STATUSES = frozenset({"success"})

# Verdicts -> (``status`` step output consumed by the Alert Slack step, exit code)
HEALTHY = "HEALTHY"
STALE = "WARN_STALE"
FAIL = "FAIL"
UNKNOWN = "UNKNOWN"


class DataError(ValueError):
    """The API answered, but not with something we can judge. Maps to UNKNOWN."""


@dataclass
class Config:
    router_id: str
    drc_id: str
    silence_threshold_hours: int = 26
    alert_window_minutes: int = 60


@dataclass
class Fetch:
    """One executions API call. ``http_status`` is an int, or a string for transport errors."""

    http_status: int | str
    body: Any = None  # parsed JSON, or None if unparseable / not fetched


@dataclass
class WorkflowEvidence:
    label: str
    workflow_id: str
    http_status: int | str
    executions_seen: int = 0
    failure_streak: int | None = None
    newest_execution_started_at: str | None = None
    newest_failure_id: str | None = None
    newest_failure_started_at: str | None = None
    newest_failure_age_s: int | None = None


@dataclass
class Verdict:
    verdict: str
    status: str
    detail: str
    slack: bool
    workflows: list[WorkflowEvidence] = field(default_factory=list)

    @property
    def exit_code(self) -> int:
        return 0 if self.verdict in (HEALTHY, STALE) else 1


def parse_ts(value: Any) -> datetime:
    """Parse an n8n ISO timestamp (``...Z``). Raises DataError when absent or malformed."""
    if not isinstance(value, str) or not value:
        raise DataError(f"timestamp missing or not a string: {value!r}")
    try:
        ts = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DataError(f"unparseable timestamp: {value!r}") from exc
    if ts.tzinfo is None:
        raise DataError(f"timestamp has no timezone: {value!r}")
    return ts


def remind_now(now: datetime) -> bool:
    """Coarse stateless reminder gate: hour % 6 == 0 and minute < 30 (~4 pages/day)."""
    return now.hour % 6 == 0 and now.minute < 30


def analyse(
    label: str, workflow_id: str, fetch: Fetch, now: datetime
) -> WorkflowEvidence:
    """Validate one executions response and extract streak and freshness. Raises DataError."""
    ev = WorkflowEvidence(
        label=label, workflow_id=workflow_id, http_status=fetch.http_status
    )
    # Transport before body: a 401/5xx body still parses and still has no errors in it.
    if fetch.http_status != 200:
        raise DataError(f"{label}: executions API returned HTTP {fetch.http_status}")
    data = fetch.body.get("data") if isinstance(fetch.body, dict) else None
    if not isinstance(data, list):
        raise DataError(f"{label}: HTTP 200 but the response had no .data array")
    ev.executions_seen = len(data)
    if not all(isinstance(item, dict) for item in data):
        raise DataError(f"{label}: execution entry is not an object")

    streak = 0
    newest_failure: dict | None = None
    for item in data:  # newest first
        status = item.get("status")
        if status in SKIPPED_STATUSES:
            continue
        if status in SUCCESS_STATUSES:
            break
        if status in FAILURE_STATUSES:
            streak += 1
            newest_failure = newest_failure or item
            continue
        raise DataError(f"{label}: unrecognised execution status {status!r}")

    # Silence reference: newest execution that has started. A queued ("new")
    # execution may carry startedAt=null; one that never started proves nothing.
    started = [
        item.get("startedAt") for item in data if item.get("startedAt") is not None
    ]
    if started:
        ev.newest_execution_started_at = parse_ts(started[0]).isoformat()
    elif data:
        raise DataError(f"{label}: no execution carries a startedAt timestamp")
    ev.failure_streak = streak
    if newest_failure is not None:
        failed_at = parse_ts(newest_failure.get("startedAt"))
        ev.newest_failure_id = str(newest_failure.get("id", "?"))
        ev.newest_failure_started_at = failed_at.isoformat()
        ev.newest_failure_age_s = int((now - failed_at).total_seconds())
    return ev


def evaluate(
    cfg: Config, router: Fetch, drc: Fetch, now: datetime, api_key_present: bool = True
) -> Verdict:
    """Pure decision function: no I/O. ``now`` must be timezone-aware UTC."""
    remind = remind_now(now)
    if not api_key_present:
        return Verdict(
            UNKNOWN,
            "canary_broken",
            "N8N_API_KEY secret is not set on this repository. Pipeline state is UNKNOWN.",
            remind,
        )

    workflows: list[WorkflowEvidence] = []
    try:
        for label, wf_id, fetch in (
            ("Event Router", cfg.router_id, router),
            ("DRC Agent Loop", cfg.drc_id, drc),
        ):
            workflows.append(analyse(label, wf_id, fetch, now))
    except DataError as exc:
        # Record transport status for every workflow, even ones not yet analysed.
        seen = {w.label for w in workflows}
        for label, wf_id, fetch in (
            ("Event Router", cfg.router_id, router),
            ("DRC Agent Loop", cfg.drc_id, drc),
        ):
            if label not in seen:
                workflows.append(WorkflowEvidence(label, wf_id, fetch.http_status))
        return Verdict(
            UNKNOWN,
            "canary_broken",
            f"{exc}. Key expired or rotated, n8n Cloud down, or API shape changed. "
            "Pipeline state is UNKNOWN.",
            remind,
            workflows,
        )

    router_ev = workflows[0]

    # Silence check (Event Router only; DRC is kept busy by health-check pings,
    # so silence there would be vacuous).
    if router_ev.newest_execution_started_at is None:
        return Verdict(
            FAIL,
            "pipeline_down",
            "Event Router has NO executions on record. The GitHub webhook may be deleted "
            "or the workflow deactivated.",
            remind,
            workflows,
        )
    silence_s = int(
        (
            now - datetime.fromisoformat(router_ev.newest_execution_started_at)
        ).total_seconds()
    )
    if silence_s > cfg.silence_threshold_hours * 3600:
        return Verdict(
            FAIL,
            "pipeline_down",
            f"Event Router has been SILENT for {silence_s // 3600}h (threshold "
            f"{cfg.silence_threshold_hours}h). No GitHub events are arriving - webhook "
            "deleted, or workflow deactivated.",
            remind,
            workflows,
        )

    # analyse() sets newest_failure_age_s whenever failure_streak > 0.
    failing = [(w, w.newest_failure_age_s or 0) for w in workflows if w.failure_streak]
    if not failing:
        return Verdict(HEALTHY, "healthy", "No open failure streak.", False, workflows)

    # Freshness is per workflow: a DRC-only failure is judged on DRC's own
    # newest failure, not on the router's timestamp. Negative ages (clock skew)
    # count as fresh: when in doubt, alert.
    window_s = cfg.alert_window_minutes * 60
    summary = "; ".join(
        f"{w.label}: {w.failure_streak} consecutive failed executions (newest id "
        f"{w.newest_failure_id}, {max(age, 0) // 60}m old)"
        for w, age in failing
    )
    if any(age <= window_s for _, age in failing):
        return Verdict(
            FAIL,
            "pipeline_down",
            f"{summary}. GitHub events are being dropped - inbound automation is DEAD.",
            True,
            workflows,
        )
    return Verdict(
        STALE,
        "stale_incident",
        f"Known-open incident, NOT healthy: {summary}. No failure within the "
        f"{cfg.alert_window_minutes}m alert window and no success since - the streak "
        "is unresolved.",
        False,
        workflows,
    )


def evidence(cfg: Config, v: Verdict, now: datetime) -> dict:
    return {
        "schema": EVIDENCE_SCHEMA,
        "checked_at": now.isoformat(),
        "verdict": v.verdict,
        "status": v.status,
        "exit_code": v.exit_code,
        "slack": v.slack,
        "detail": v.detail,
        "thresholds": {
            "silence_threshold_hours": cfg.silence_threshold_hours,
            "alert_window_minutes": cfg.alert_window_minutes,
        },
        "workflows": [w.__dict__ for w in v.workflows],
    }


def fetch_executions(host: str, api_key: str, workflow_id: str) -> Fetch:
    req = urllib.request.Request(
        f"{host}/api/v1/executions?workflowId={workflow_id}&limit=20",
        headers={"X-N8N-API-KEY": api_key, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(
            req, timeout=30
        ) as resp:  # nosec B310 - fixed https host
            status, raw = resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return Fetch(exc.code)
    except (
        urllib.error.URLError,
        http.client.HTTPException,
        TimeoutError,
        OSError,
    ) as exc:
        return Fetch(f"transport_error:{type(exc).__name__}")
    try:
        return Fetch(status, json.loads(raw))
    except ValueError:
        return Fetch(status, None)


def judge(now: datetime) -> tuple[Config, Verdict]:
    cfg = Config(
        router_id=os.environ["EVENT_ROUTER_ID"],
        drc_id=os.environ["DRC_ID"],
        silence_threshold_hours=int(os.environ.get("SILENCE_THRESHOLD_HOURS", "26")),
        alert_window_minutes=int(os.environ.get("ALERT_WINDOW_MINUTES", "60")),
    )
    api_key = os.environ.get("N8N_API_KEY", "")
    host = os.environ.get("N8N_HOST", "https://gadgetlab.app.n8n.cloud")
    if api_key:
        router = fetch_executions(host, api_key, cfg.router_id)
        drc = fetch_executions(host, api_key, cfg.drc_id)
    else:
        router = drc = Fetch("not_fetched")
    return cfg, evaluate(cfg, router, drc, now, api_key_present=bool(api_key))


def main() -> int:
    now = datetime.now(timezone.utc)
    try:
        cfg, v = judge(now)
    except Exception as exc:  # noqa: BLE001 - a crash must still emit UNKNOWN + outputs
        cfg = Config(
            os.environ.get("EVENT_ROUTER_ID", "?"), os.environ.get("DRC_ID", "?")
        )
        v = Verdict(
            UNKNOWN,
            "canary_broken",
            f"Canary crashed ({type(exc).__name__}). Pipeline state is UNKNOWN.",
            remind_now(now),
        )
    ev = evidence(cfg, v, now)
    ev_line = json.dumps(ev, separators=(",", ":"), sort_keys=True)

    for w in v.workflows:
        print(
            f"{w.label}: HTTP {w.http_status}, {w.executions_seen} recent executions, "
            f"{w.failure_streak} consecutive failures, newest failure {w.newest_failure_id} "
            f"at {w.newest_failure_started_at}"
        )
    print(f"CANARY_EVIDENCE {ev_line}")
    annotation = {FAIL: "error", UNKNOWN: "error", STALE: "warning"}.get(v.verdict)
    if annotation:
        print(f"::{annotation}::[{v.verdict}] {v.detail}")
    else:
        print("Pipeline healthy.")

    detail = " ".join(v.detail.split())  # one line: GITHUB_OUTPUT is line-delimited
    if out := os.environ.get("GITHUB_OUTPUT"):
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"status={v.status}\n")
            fh.write(f"verdict={v.verdict}\n")
            fh.write(f"detail={detail}\n")
            fh.write(f"slack={'true' if v.slack else 'false'}\n")
            fh.write(f"evidence={ev_line}\n")
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(f"### Intake canary: {v.verdict}\n\n{v.detail}\n\n")
            fh.write(f"```json\n{json.dumps(ev, indent=2, sort_keys=True)}\n```\n")
    return v.exit_code


if __name__ == "__main__":
    sys.exit(main())
