"""Tests for .github/scripts/intake_canary_neon.py (Neon-backed Intake Canary)."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parents[2]
    / ".github"
    / "scripts"
    / "intake_canary_neon.py"
)
_spec = importlib.util.spec_from_file_location("intake_canary_neon", SCRIPT)
canary = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(canary)

NOW = "2026-10-01T08:30:00+00:00"


def snap(latest="2026-10-01T06:28:26+00:00", forwarded=1, unmatched=None):
    return {
        "now": NOW,
        "latest_at": latest,
        "forwarded": forwarded,
        "unmatched": unmatched or [],
    }


def test_healthy_requires_recent_delivery_and_no_unmatched():
    r = canary.evaluate(snap(), remind=False)
    assert r["status"] == "healthy"
    assert r["exit"] == 0
    assert r["slack"] is False


def test_zero_forwarded_is_still_healthy_when_router_is_live():
    assert canary.evaluate(snap(forwarded=0), remind=False)["status"] == "healthy"


def test_silence_past_threshold_is_pipeline_down():
    r = canary.evaluate(snap(latest="2026-09-30T06:00:00+00:00"), remind=False)
    assert r["status"] == "pipeline_down"
    assert r["exit"] == 1
    assert r["slack"] is False


def test_silence_pages_only_on_reminder_gate():
    r = canary.evaluate(snap(latest="2026-09-29T00:00:00+00:00"), remind=True)
    assert r["slack"] is True


def test_empty_table_is_pipeline_down():
    r = canary.evaluate(snap(latest=None), remind=False)
    assert r["status"] == "pipeline_down"
    assert r["exit"] == 1


def test_fresh_unmatched_forward_pages_immediately():
    u = [{"id": 160, "received_at": "2026-10-01T08:00:00+00:00", "issue_number": 340}]
    r = canary.evaluate(snap(forwarded=1, unmatched=u), remind=False)
    assert r["status"] == "drc_failing"
    assert r["exit"] == 1
    assert r["slack"] is True
    assert "#340" in r["detail"]


def test_stale_unmatched_forward_still_fails_but_waits_for_reminder():
    """Regression for the #316 lesson: an old, unresolved failure must never go green."""
    u = [{"id": 152, "received_at": "2026-09-30T12:00:00+00:00", "issue_number": 338}]
    r = canary.evaluate(snap(forwarded=2, unmatched=u), remind=False)
    assert r["status"] == "drc_failing"
    assert r["exit"] == 1
    assert r["slack"] is False


def test_silence_takes_priority_over_drc_failure():
    u = [{"id": 1, "received_at": "2026-09-29T00:00:00+00:00", "issue_number": 1}]
    r = canary.evaluate(
        snap(latest="2026-09-29T00:00:00+00:00", unmatched=u), remind=False
    )
    assert r["status"] == "pipeline_down"


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"now": NOW},
        {"now": NOW, "latest_at": None, "forwarded": 0, "unmatched": "nope"},
        {"now": "not-a-date", "latest_at": None, "forwarded": 0, "unmatched": []},
    ],
)
def test_bad_shape_is_canary_broken_never_healthy(bad):
    r = canary.evaluate(bad, remind=False)
    assert r["status"] == "canary_broken"
    assert r["exit"] == 1


def _run_cli(stdin: str, tmp_path, remind="false"):
    out = tmp_path / "out"
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        input=stdin,
        text=True,
        capture_output=True,
        env={"GITHUB_OUTPUT": str(out), "REMIND": remind, "PATH": "/usr/bin:/bin"},
    )
    return proc.returncode, out.read_text()


def test_cli_writes_outputs_and_exit_code(tmp_path):
    code, out = _run_cli(json.dumps(snap()), tmp_path)
    assert code == 0
    assert "status=healthy" in out
    assert "slack=false" in out


def test_cli_garbage_input_is_canary_broken(tmp_path):
    code, out = _run_cli("psql: error: connection refused", tmp_path, remind="true")
    assert code == 1
    assert "status=canary_broken" in out
    assert "slack=true" in out
