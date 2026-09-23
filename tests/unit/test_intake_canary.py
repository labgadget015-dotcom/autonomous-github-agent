"""Tests for .github/scripts/intake_canary.py.

One test per branch of the pre-refactor bash canary (parity), plus the
invariants it violated: stale incidents reported as healthy, DRC-only failures
judged on the router's timestamp, and unparseable data read as zero errors.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2] / ".github" / "scripts" / "intake_canary.py"
)
_spec = importlib.util.spec_from_file_location("intake_canary", SCRIPT)
canary = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules["intake_canary"] = canary  # dataclasses resolve annotations via sys.modules
_spec.loader.exec_module(canary)

# 09:40 UTC: outside the hour%6 reminder gate, so ``slack`` reflects the verdict alone.
NOW = datetime(2026, 9, 23, 9, 40, 0, tzinfo=timezone.utc)
CFG = canary.Config(router_id="ROUTER", drc_id="DRC")
WINDOW_S = CFG.alert_window_minutes * 60


def ex(exec_id, status, age_s):
    """One execution entry shaped like the live n8n v1 API (fields as of 2026-09-23)."""
    started = (NOW - timedelta(seconds=age_s)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {
        "id": str(exec_id),
        "status": status,
        "startedAt": started,
        "stoppedAt": started,
        "finished": status == "success",
        "mode": "webhook",
        "retryOf": None,
        "retrySuccessId": None,
        "waitTill": None,
        "workflowId": "x",
    }


def ok(*items):
    return canary.Fetch(200, {"data": list(items), "nextCursor": None})


HEALTHY_ROUTER = ok(ex(10, "success", 120))
HEALTHY_DRC = ok(ex(20, "success", 300))


def run(router=HEALTHY_ROUTER, drc=HEALTHY_DRC, now=NOW, key=True):
    return canary.evaluate(CFG, router, drc, now, api_key_present=key)


# --- parity with the bash canary ------------------------------------------


def test_healthy():
    v = run()
    assert (v.verdict, v.status, v.exit_code, v.slack) == (
        "HEALTHY",
        "healthy",
        0,
        False,
    )


def test_missing_api_key_is_unknown():
    v = run(key=False)
    assert (v.verdict, v.status, v.exit_code) == ("UNKNOWN", "canary_broken", 1)


@pytest.mark.parametrize("http", [401, 403, 500, 502, "transport_error:URLError"])
@pytest.mark.parametrize("which", ["router", "drc"])
def test_non_200_or_transport_failure_is_unknown(http, which):
    # The body parses and has no errors in it; it must still not read as healthy.
    bad = canary.Fetch(http, {"data": []})
    v = run(**{which: bad})
    assert (v.verdict, v.status, v.exit_code) == ("UNKNOWN", "canary_broken", 1)
    assert {w.label: w.http_status for w in v.workflows}[
        "Event Router" if which == "router" else "DRC Agent Loop"
    ] == http


@pytest.mark.parametrize(
    "body",
    [None, {}, {"data": None}, {"data": {}}, {"message": "unauthorized"}, [], "html"],
)
def test_bad_shape_is_unknown(body):
    for kwargs in (
        {"router": canary.Fetch(200, body)},
        {"drc": canary.Fetch(200, body)},
    ):
        v = run(**kwargs)
        assert (v.verdict, v.exit_code) == ("UNKNOWN", 1)


def test_router_with_no_executions_is_pipeline_down():
    v = run(router=ok())
    assert (v.verdict, v.status, v.exit_code) == ("FAIL", "pipeline_down", 1)


def test_router_silence_boundary():
    limit = CFG.silence_threshold_hours * 3600
    assert run(router=ok(ex(1, "success", limit))).verdict == "HEALTHY"
    v = run(router=ok(ex(1, "success", limit + 1)))
    assert (v.verdict, v.status) == ("FAIL", "pipeline_down")


def test_fresh_router_failure_fails_and_pages():
    v = run(router=ok(ex(3, "error", 60), ex(2, "error", 90), ex(1, "success", 200)))
    assert (v.verdict, v.status, v.exit_code, v.slack) == (
        "FAIL",
        "pipeline_down",
        1,
        True,
    )
    router = v.workflows[0]
    assert (router.failure_streak, router.newest_failure_id) == (2, "3")


def test_running_execution_does_not_raise_false_alarm():
    v = run(router=ok(ex(2, "running", 5), ex(1, "success", 60)))
    assert v.verdict == "HEALTHY"


# --- freshness boundary -----------------------------------------------------


@pytest.mark.parametrize(
    "age_s, verdict",
    [
        (-120, "FAIL"),  # clock skew: newest failure "in the future" -> alert
        (0, "FAIL"),
        (WINDOW_S - 1, "FAIL"),
        (WINDOW_S, "FAIL"),  # boundary is inclusive
        (WINDOW_S + 1, "WARN_STALE"),
        (CFG.silence_threshold_hours * 3600, "WARN_STALE"),
    ],
)
def test_freshness_boundary(age_s, verdict):
    assert run(router=ok(ex(5, "error", age_s))).verdict == verdict


def test_stale_incident_is_warning_never_healthy():
    # Mirrors live state on 2026-09-23: router 20/20 errors, newest 100m old.
    # The bash canary printed "Pipeline healthy." and set status=healthy here.
    v = run(router=ok(*(ex(10911 - i, "error", 6000 + i) for i in range(20))))
    assert (v.verdict, v.status, v.exit_code, v.slack) == (
        "WARN_STALE",
        "stale_incident",
        0,
        False,
    )
    assert v.status != "healthy"
    assert "10911" in v.detail and "NOT healthy" in v.detail
    assert v.workflows[0].newest_failure_age_s == 6000


# --- per-workflow freshness and correlation --------------------------------


def test_drc_only_fresh_failure_is_judged_on_drc_timestamp():
    # Router healthy but its newest execution is 5h old; DRC failed 2m ago.
    # Gating on the router timestamp (bash v1) would suppress this.
    v = run(router=ok(ex(10, "success", 5 * 3600)), drc=ok(ex(77, "error", 120)))
    assert (v.verdict, v.exit_code, v.slack) == ("FAIL", 1, True)
    assert "DRC Agent Loop" in v.detail and "77" in v.detail
    assert "Event Router" not in v.detail


def test_drc_only_stale_failure_correlates_drc_execution():
    v = run(drc=ok(ex(88, "error", WINDOW_S + 600), ex(87, "success", WINDOW_S + 900)))
    assert v.verdict == "WARN_STALE"
    assert "(newest id 88," in v.detail


def test_one_fresh_workflow_outranks_one_stale():
    v = run(router=ok(ex(1, "error", 2 * WINDOW_S)), drc=ok(ex(2, "error", 30)))
    assert v.verdict == "FAIL"


def test_running_head_does_not_hide_streak_behind_it():
    v = run(router=ok(ex(3, "running", 1), ex(2, "error", 30), ex(1, "success", 60)))
    assert v.verdict == "FAIL"
    assert v.workflows[0].newest_failure_id == "2"


def test_crashed_counts_as_failure():
    assert run(router=ok(ex(1, "crashed", 30))).verdict == "FAIL"


# --- missing / invalid data -> UNKNOWN --------------------------------------


@pytest.mark.parametrize("status", [None, "unknown", "", "exploded", 3])
def test_unrecognised_status_is_unknown(status):
    item = ex(1, "success", 30)
    item["status"] = status
    v = run(router=ok(item))
    assert (v.verdict, v.status, v.exit_code) == ("UNKNOWN", "canary_broken", 1)


def test_status_key_absent_is_unknown():
    item = ex(1, "success", 30)
    del item["status"]
    assert run(router=ok(item)).verdict == "UNKNOWN"


@pytest.mark.parametrize(
    "started", [None, "", "yesterday", "2026-13-40T00:00:00Z", 1695456000]
)
def test_bad_failure_timestamp_is_unknown(started):
    item = ex(1, "error", 30)
    item["startedAt"] = started
    assert run(drc=ok(item)).verdict == "UNKNOWN"


def test_naive_timestamp_is_unknown():
    item = ex(1, "success", 30)
    item["startedAt"] = "2026-09-23T09:39:00"
    assert run(router=ok(item)).verdict == "UNKNOWN"


def test_non_object_entry_is_unknown_even_after_success():
    assert run(router=ok(ex(1, "success", 30), "garbage")).verdict == "UNKNOWN"


def test_queued_execution_without_start_time_is_skipped():
    queued = ex(2, "new", 0)
    queued["startedAt"] = None
    assert run(router=ok(queued, ex(1, "success", 60))).verdict == "HEALTHY"


# --- reminder gate, evidence, and CLI plumbing -------------------------------


@pytest.mark.parametrize(
    "hh, mm, expected",
    [(0, 0, True), (6, 29, True), (6, 30, False), (8, 5, False), (18, 1, True)],
)
def test_reminder_gate(hh, mm, expected):
    assert canary.remind_now(NOW.replace(hour=hh, minute=mm)) is expected


def test_evidence_is_json_and_carries_no_body():
    v = run(router=ok(ex(3, "error", 60)))
    ev = canary.evidence(CFG, v, NOW)
    parsed = json.loads(json.dumps(ev))
    assert parsed["schema"] == "intake-canary/v1"
    assert (parsed["verdict"], parsed["exit_code"]) == ("FAIL", 1)
    assert {w["label"] for w in parsed["workflows"]} == {
        "Event Router",
        "DRC Agent Loop",
    }
    assert set(parsed["workflows"][0]) == {
        "label",
        "workflow_id",
        "http_status",
        "executions_seen",
        "failure_streak",
        "newest_execution_started_at",
        "newest_failure_id",
        "newest_failure_started_at",
        "newest_failure_age_s",
    }


def test_main_writes_outputs_and_exit_code(tmp_path, monkeypatch, capsys):
    out, summary = tmp_path / "out", tmp_path / "summary"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    monkeypatch.setenv("EVENT_ROUTER_ID", "ROUTER")
    monkeypatch.setenv("DRC_ID", "DRC")
    monkeypatch.setenv("N8N_API_KEY", "")  # no network: exercises the missing-key path

    assert canary.main() == 1

    lines = dict(line.split("=", 1) for line in out.read_text().splitlines())
    assert lines["status"] == "canary_broken"
    assert lines["verdict"] == "UNKNOWN"
    assert json.loads(lines["evidence"])["exit_code"] == 1
    assert "```json" in summary.read_text()
    stdout = capsys.readouterr().out
    assert "::error::[UNKNOWN]" in stdout
    assert "CANARY_EVIDENCE {" in stdout


def test_main_uses_fetched_responses(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "out"))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    monkeypatch.setenv("EVENT_ROUTER_ID", "ROUTER")
    monkeypatch.setenv("DRC_ID", "DRC")
    monkeypatch.setenv("N8N_API_KEY", "test-key")
    stale = ex(9, "error", 3 * 3600)
    stale["startedAt"] = (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat()
    monkeypatch.setattr(
        canary,
        "fetch_executions",
        lambda host, key, wf: ok(stale) if wf == "ROUTER" else ok(),
    )

    assert canary.main() == 0
    out = (tmp_path / "out").read_text()
    assert "status=stale_incident" in out and "status=healthy" not in out
