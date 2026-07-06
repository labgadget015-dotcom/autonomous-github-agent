"""Smoke tests for recommendation_contract + ledger + formatter.

Run:  python -m pytest autopilot/tests/test_recommendation_contract.py -q
  or:  python autopilot/tests/test_recommendation_contract.py
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recommendation_contract import Recommendation, validate
from decisions.ledger import should_post, record, latest_match
from message_formatter import format


def _good() -> Recommendation:
    return Recommendation(
        severity="P0",
        headline="Smoke Test Harness: needs owner + 2 secrets before workflow code",
        impact_if_ignored="DRC loop stays unverified; silent agent failures go undetected",
        steps=[
            "Create manual-test label in GitHub repo Settings > Labels",
            "Add SMOKE_TEST_WEBHOOK_URL + SMOKE_TEST_AUTH_TOKEN to Actions secrets",
            "Commit .github/workflows/smoke-test.yml with label trigger + curl assertion",
        ],
        due_date="2026-07-05",
        owner="U0AKJK1J7GR",
        action_verb="create",
        target_repo="autonomous-github-agent",
        file_or_workflow_path=".github/workflows/smoke-test.yml",
        run_id="run_1782796553291",
    )


def test_valid_recommendation_passes():
    ok, errs = validate(_good())
    assert ok, errs
    assert errs == []


def test_p0_without_owner_rejected():
    r = _good()
    r.owner = "unassigned"
    ok, errs = validate(r)
    assert not ok
    assert any("no owner" in e for e in errs)


def test_missing_impact_rejected():
    r = _good()
    r.impact_if_ignored = ""
    ok, errs = validate(r)
    assert not ok
    assert any("impact" in e for e in errs)


def test_run_id_in_headline_rejected():
    r = _good()
    r.headline = "run_1782796553291"
    ok, errs = validate(r)
    assert not ok
    assert any("headline" in e for e in errs)


def test_oversize_step_rejected():
    r = _good()
    r.steps[0] = "x" * 200
    ok, errs = validate(r)
    assert not ok
    assert any("step 1" in e for e in errs)


def test_ledger_debounce_suppresses_duplicate():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
        path = tf.name
    try:
        r = _good()
        assert should_post(r, path)[0] is True   # first raise allowed
        record(r, path)

        # immediate re-raise of same signature -> suppressed
        allow, reason = should_post(r, path)
        assert allow is False, reason
        assert "debounce" in reason or "never" in reason
    finally:
        os.unlink(path)


def test_done_status_blocks_repost():
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
        path = tf.name
    try:
        r = _good()
        record(r, path)
        from decisions.ledger import transition
        transition(r.signature(), "done", path=path)

        allow, reason = should_post(r, path)
        assert allow is False
        assert "done" in reason
    finally:
        os.unlink(path)


def test_assigned_status_debounces_repost():
    """Regression: transition() entries only carry transitioned_ts, not
    first_raised_ts. should_post() must use max(ts) so assigned/inflight
    items stay suppressed within their debounce window (not always repost)."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tf:
        path = tf.name
    try:
        r = _good()
        record(r, path)
        from decisions.ledger import transition
        transition(r.signature(), "assigned", owner="U0AKJK1J7GR",
                   due="2026-07-05", path=path)

        # Immediate re-raise while assigned must be suppressed.
        allow, reason = should_post(r, path)
        assert allow is False, f"expected suppress, got: {reason}"
        assert "assigned" in reason or "debounce" in reason
    finally:
        os.unlink(path)


def test_formatter_renders_template():
    msg = format(_good())
    assert "P0 — Smoke Test Harness" in msg
    assert "If not done by 2026-07-05" in msg
    assert "Owner: U0AKJK1J7GR" in msg
    assert "run_1782796553291" not in msg.split("\n")[0]  # not in headline


def test_formatter_rejects_invalid():
    r = _good()
    r.owner = "unassigned"
    msg = format(r)
    assert "REJECTED" in msg


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    passed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS  {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {fn.__name__}: {e}")
    print(f"\n{passed}/{len(fns)} passed")
    sys.exit(0 if passed == len(fns) else 1)
