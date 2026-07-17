"""Smoke tests for recommendation_contract + ledger + formatter.

Run:  python -m pytest autopilot/tests/test_recommendation_contract.py -q
  or:  python autopilot/tests/test_recommendation_contract.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decisions.ledger import record, should_post
from message_formatter import format
from recommendation_contract import Recommendation, validate


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
        assert should_post(r, path)[0] is True  # first raise allowed
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

        transition(
            r.signature(), "assigned", owner="U0AKJK1J7GR", due="2026-07-05", path=path
        )

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


# --- New: config-driven behaviour ---


def test_config_overrides_max_step_len():
    """validate() should honour max_step_len from a custom config file."""
    import config_loader

    config_loader.reset_cache()
    cfg = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    cfg.write("message_contract:\n  max_step_len: 20\n")
    cfg.close()
    try:
        config_loader.DEFAULT_CONFIG_PATH = cfg.name
        config_loader.reset_cache()
        r = _good()
        r.steps[0] = "x" * 25  # over the custom 20 limit, under default 120
        ok, errs = validate(r)
        assert not ok
        assert any("step 1" in e and "20" in e for e in errs)
    finally:
        config_loader.reset_cache()
        os.unlink(cfg.name)


def test_config_overrides_debounce_window():
    """should_post() should honour repost_policy from a custom config file."""
    import config_loader

    config_loader.reset_cache()
    cfg = tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False, encoding="utf-8"
    )
    cfg.write(
        "recommendation_debounce:\n"
        "  repost_policy:\n"
        "    open: {min_hours_between: 100000, never_repost: false}\n"
    )
    cfg.close()
    ledger = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    ledger.close()
    try:
        config_loader.DEFAULT_CONFIG_PATH = cfg.name
        config_loader.reset_cache()
        r = _good()
        from decisions.ledger import record, should_post

        record(r, ledger.name)
        allow, reason = should_post(r, ledger.name)
        assert allow is False, reason  # 100000h window always suppresses
    finally:
        config_loader.reset_cache()
        os.unlink(cfg.name)
        os.unlink(ledger.name)


# --- New: status validation ---


def test_transition_rejects_unknown_status():
    from decisions.ledger import transition

    ledger = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    ledger.close()
    try:
        r = _good()
        from decisions.ledger import record

        record(r, ledger.name)
        try:
            transition(r.signature(), "assiged", path=ledger.name)  # typo
            raise AssertionError("expected ValueError for unknown status")
        except ValueError as e:
            assert "assiged" in str(e)
    finally:
        os.unlink(ledger.name)


# --- New: concurrent-writer safety ---


def test_concurrent_writers_do_not_lose_entries():
    """Parallel record() calls must all land — file locking prevents races."""
    import threading

    from decisions.ledger import record

    ledger = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    ledger.close()
    try:
        r = _good()
        n_writers = 8
        n_each = 25
        errors = []

        def writer():
            try:
                for _ in range(n_each):
                    record(r, ledger.name)
            except Exception as e:  # noqa
                errors.append(e)

        threads = [threading.Thread(target=writer) for _ in range(n_writers)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], errors
        from decisions.ledger import _load

        entries = _load(ledger.name)
        assert (
            len(entries) == n_writers * n_each
        ), f"expected {n_writers * n_each}, got {len(entries)} (lost entries)"
        # seq values should be unique 0..N-1 (no collisions from the race)
        seqs = sorted(e.get("seq", -1) for e in entries)
        assert seqs == list(range(n_writers * n_each)), "seq collisions detected"
    finally:
        os.unlink(ledger.name)


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
