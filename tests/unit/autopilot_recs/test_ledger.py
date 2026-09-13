"""Tests for autopilot/decisions/ledger.py.

Every ledger function takes an explicit ``path``, so these tests use ``tmp_path``
for the JSONL file — mocking ``open`` would only test the mock, and the seq/
append logic depends on real read-after-append semantics. What IS mocked:
the clock (``ledger.time`` / ``_today_iso``), ``fcntl`` and ``os.fsync`` to
assert lock ordering, and the config/ledger collaborators of should_post().
"""

from __future__ import annotations

import inspect
import json
import re
import threading
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest import mock

import pytest

from tests.unit.autopilot_recs._support import SIG

# isort: split
from decisions import ledger  # noqa: E402

NOW = 1_800_000_000  # 2027-01-15T08:00:00Z
HOUR = 3600
STATUSES_MSG = "expected one of ['assigned', 'done', 'dropped', 'inflight', 'open']"


@pytest.fixture
def ledger_path(tmp_path):
    return tmp_path / "nested" / "decisions" / "recs.jsonl"


@pytest.fixture
def clock(monkeypatch):
    """Freeze ledger time at NOW; advance with ``clock["now"] += ...``."""
    state = {"now": NOW}
    monkeypatch.setattr(ledger, "time", SimpleNamespace(time=lambda: state["now"]))
    monkeypatch.setattr(ledger, "_today_iso", lambda: "2027-01-15")
    return state


def _write(path, *lines):
    """Write raw strings or dicts (as JSON) one per line."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(
        (ln if isinstance(ln, str) else json.dumps(ln)) + "\n" for ln in lines
    )
    path.write_text(body, encoding="utf-8")


# --------------------------------------------------------------------------- #
# _today_iso / import-time defaults
# --------------------------------------------------------------------------- #


def test_today_iso_is_the_utc_date(monkeypatch):
    seen = {}

    class FakeDateTime:
        @staticmethod
        def now(tz):
            seen["tz"] = tz
            return datetime(2026, 12, 31, 23, 59, 59, tzinfo=timezone.utc)

    monkeypatch.setattr(ledger, "datetime", FakeDateTime)
    assert ledger._today_iso() == "2026-12-31"
    assert seen["tz"] is timezone.utc


def test_default_path_is_frozen_at_import(monkeypatch, tmp_path):
    # Why every test passes path=: changing the env var after import has no effect.
    late = str(tmp_path / "late.jsonl")
    monkeypatch.setenv("DECISIONS_LEDGER_PATH", late)
    for fn in (
        ledger._load,
        ledger._append_with_seq,
        ledger.latest_match,
        ledger.should_post,
        ledger.record,
        ledger.transition,
    ):
        assert (
            inspect.signature(fn).parameters["path"].default
            == ledger.DEFAULT_LEDGER_PATH
        )
    assert ledger.DEFAULT_LEDGER_PATH != late


# --------------------------------------------------------------------------- #
# _load
# --------------------------------------------------------------------------- #


def test_load_missing_file(tmp_path):
    assert ledger._load(str(tmp_path / "absent.jsonl")) == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", []),
        ("\n\n   \n\t\n", []),
        ('{"sig": "a"}\n', [{"sig": "a"}]),
        ('{"sig": "a"}', [{"sig": "a"}]),
        ('{"sig": "a"}\n{"sig": "b"', [{"sig": "a"}]),
        ('{"sig": "a"}\nnot json at all\n{"sig": "b"}\n', [{"sig": "a"}, {"sig": "b"}]),
        ('  {"sig": "a"}  \r\n', [{"sig": "a"}]),
        ('{"sig": "✅ done"}\n', [{"sig": "✅ done"}]),
        ('[1, 2]\n5\nnull\n"str"\n{"sig": "a"}\n', [{"sig": "a"}]),
    ],
    ids=[
        "empty",
        "blank-lines",
        "one-entry",
        "no-trailing-newline",
        "truncated-last-line",
        "garbage-line-skipped",
        "crlf-and-padding",
        "unicode",
        "non-object-json-skipped",
    ],
)
def test_load_parsing(ledger_path, raw, expected):
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text(raw, encoding="utf-8")
    assert ledger._load(str(ledger_path)) == expected


def test_load_skips_undecodable_bytes(ledger_path):
    # One invalid UTF-8 byte costs its own line, not the whole ledger.
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_bytes(b'{"sig": "a"}\n\xff\xfe broken\n{"sig": "b"}\n')
    assert ledger._load(str(ledger_path)) == [{"sig": "a"}, {"sig": "b"}]


# --------------------------------------------------------------------------- #
# _append_with_seq: seq, dirs, locking
# --------------------------------------------------------------------------- #


def test_append_creates_parent_dirs_and_numbers_from_zero(ledger_path):
    assert ledger._append_with_seq({"sig": "a"}, str(ledger_path))["seq"] == 0
    assert ledger._append_with_seq({"sig": "b"}, str(ledger_path))["seq"] == 1
    assert ledger._load(str(ledger_path)) == [
        {"sig": "a", "seq": 0},
        {"sig": "b", "seq": 1},
    ]


def test_append_to_bare_filename_uses_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    ledger._append_with_seq({"sig": "a"}, "bare.jsonl")
    assert (tmp_path / "bare.jsonl").read_text(
        encoding="utf-8"
    ) == '{"sig": "a", "seq": 0}\n'


def test_seq_counts_corrupt_lines_too(ledger_path):
    # seq is "non-blank lines so far", so after corruption seq != len(_load()).
    _write(ledger_path, "", "{truncated", "   ", {"sig": "x"})
    assert ledger._append_with_seq({"sig": "y"}, str(ledger_path))["seq"] == 2
    assert len(ledger._load(str(ledger_path))) == 2


def test_append_after_torn_write_starts_a_fresh_line(ledger_path):
    # Without the newline guard the new entry is glued onto the torn line and
    # silently lost on the next _load.
    ledger_path.parent.mkdir(parents=True)
    ledger_path.write_text('{"sig": "a", "seq": 0}\n{"sig": "b", "se', encoding="utf-8")
    assert ledger._append_with_seq({"sig": "c"}, str(ledger_path))["seq"] == 2
    assert ledger._load(str(ledger_path)) == [
        {"sig": "a", "seq": 0},
        {"sig": "c", "seq": 2},
    ]


def test_append_is_utf8_on_disk(ledger_path):
    ledger._append_with_seq({"sig": "✅"}, str(ledger_path))
    assert ledger_path.read_bytes() == '{"sig": "✅", "seq": 0}\n'.encode()


def test_append_locks_writes_fsyncs_unlocks_in_order(ledger_path, monkeypatch):
    events = []
    fake_fcntl = SimpleNamespace(
        LOCK_EX="EX", LOCK_UN="UN", flock=lambda fd, op: events.append(("flock", op))
    )
    monkeypatch.setattr(ledger, "fcntl", fake_fcntl, raising=False)
    monkeypatch.setattr(ledger, "_HAS_FCNTL", True)
    monkeypatch.setattr(ledger.os, "fsync", lambda fd: events.append(("fsync",)))
    ledger._append_with_seq({"sig": "a"}, str(ledger_path))
    assert events == [("flock", "EX"), ("fsync",), ("flock", "UN")]


def test_append_unlocks_when_the_write_fails(ledger_path, monkeypatch):
    events = []
    fake_fcntl = SimpleNamespace(
        LOCK_EX="EX", LOCK_UN="UN", flock=lambda fd, op: events.append(op)
    )
    monkeypatch.setattr(ledger, "fcntl", fake_fcntl, raising=False)
    monkeypatch.setattr(ledger, "_HAS_FCNTL", True)
    entry = {"sig": "a", "bad": object()}
    with pytest.raises(TypeError, match="not JSON serializable"):
        ledger._append_with_seq(entry, str(ledger_path))
    assert events == ["EX", "UN"]
    assert ledger_path.read_text(encoding="utf-8") == ""  # nothing half-written
    assert "seq" not in entry  # caller's dict untouched on failure


def test_append_without_fcntl_skips_locking(ledger_path, monkeypatch):
    boom = mock.Mock(side_effect=AssertionError("flock must not be called"))
    monkeypatch.setattr(ledger, "fcntl", SimpleNamespace(flock=boom), raising=False)
    monkeypatch.setattr(ledger, "_HAS_FCNTL", False)
    assert ledger._append_with_seq({"sig": "a"}, str(ledger_path))["seq"] == 0
    boom.assert_not_called()


def test_concurrent_appends_lose_nothing(ledger_path, make_rec):
    rec, n_threads, n_each, errors = make_rec(), 4, 10, []

    def writer():
        try:
            for _ in range(n_each):
                ledger.record(rec, str(ledger_path))
        except Exception as exc:  # pragma: no cover - surfaced by the assert
            errors.append(exc)

    threads = [threading.Thread(target=writer) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == []
    seqs = sorted(e["seq"] for e in ledger._load(str(ledger_path)))
    assert seqs == list(range(n_threads * n_each))


# --------------------------------------------------------------------------- #
# record / transition: exact entry schema
# --------------------------------------------------------------------------- #


def test_record_writes_exact_schema(clock, ledger_path, make_rec):
    rec = make_rec(
        status="open",
        headline="Rotate the PAT — before expiry ✅",
        run_id="run_42",
        prior_run_id="run_41",
    )
    entry = ledger.record(rec, str(ledger_path))
    expected = {
        "sig": SIG,
        "status": "open",
        "owner": "U0AKJK1J7GR",
        "due": "2027-04-30",
        "severity": "P0",
        "headline": "Rotate the PAT — before expiry ✅",
        "first_raised": "2027-01-15",
        "first_raised_ts": NOW,
        "run_id": "run_42",
        "prior_run_id": "run_41",
        "seq": 0,
    }
    assert entry == expected
    # Key order and raw (non-escaped) unicode on disk.
    assert (
        ledger_path.read_text(encoding="utf-8")
        == json.dumps(expected, ensure_ascii=False) + "\n"
    )


def test_record_does_not_guard_against_an_empty_signature(clock, ledger_path, make_rec):
    rec = make_rec(action_verb="", target_repo="", file_or_workflow_path="")
    assert ledger.record(rec, str(ledger_path))["sig"] == ""


@pytest.mark.parametrize(
    ("owner", "due", "want_owner", "want_due"),
    [(None, None, "", ""), ("U1", "2027-02-01", "U1", "2027-02-01"), ("", "", "", "")],
    ids=["none-coerced", "explicit", "empty"],
)
def test_transition_writes_exact_schema(
    clock, ledger_path, owner, due, want_owner, want_due
):
    entry = ledger.transition(
        SIG, "assigned", owner=owner, due=due, path=str(ledger_path)
    )
    assert entry == {
        "sig": SIG,
        "status": "assigned",
        "owner": want_owner,
        "due": want_due,
        "transitioned_ts": NOW,
        "seq": 0,
    }


@pytest.mark.parametrize("status", sorted(ledger.VALID_STATUSES))
def test_transition_accepts_every_lifecycle_status(clock, ledger_path, status):
    assert ledger.transition(SIG, status, path=str(ledger_path))["status"] == status


@pytest.mark.parametrize(
    "bad", ["assiged", "", "OPEN", "done ", "blocked", None], ids=repr
)
def test_transition_rejects_unknown_status_before_writing(ledger_path, bad):
    with pytest.raises(
        ValueError, match=re.escape(f"unknown status {bad!r}; {STATUSES_MSG}")
    ):
        ledger.transition(SIG, bad, path=str(ledger_path))
    assert not ledger_path.exists()


# --------------------------------------------------------------------------- #
# latest_match
# --------------------------------------------------------------------------- #


def test_latest_match_none_when_absent(ledger_path):
    assert ledger.latest_match(SIG, str(ledger_path)) is None
    _write(ledger_path, {"sig": "other", "first_raised_ts": 1})
    assert ledger.latest_match(SIG, str(ledger_path)) is None


@pytest.mark.parametrize(
    ("entries", "winner"),
    [
        ([{"first_raised_ts": 200, "seq": 0}, {"first_raised_ts": 100, "seq": 1}], 0),
        ([{"first_raised_ts": 100, "seq": 1}, {"transitioned_ts": 100, "seq": 0}], 0),
        ([{"first_raised_ts": 100, "seq": 0}, {"transitioned_ts": 150, "seq": 1}], 1),
        (
            [
                {"first_raised_ts": 10, "transitioned_ts": 500, "seq": 0},
                {"first_raised_ts": 400, "seq": 1},
            ],
            0,
        ),
        ([{"status": "a"}, {"status": "b", "seq": 1}], 1),
        ([{"status": "a"}, {"status": "b"}], 0),
    ],
    ids=[
        "newer-ts-beats-file-order",
        "same-second-higher-seq-wins",
        "transition-newer-than-record",
        "uses-larger-of-both-ts",
        "missing-keys-default-zero",
        "exact-tie-keeps-first-line",
    ],
)
def test_latest_match_ordering(ledger_path, entries, winner):
    rows = [{"sig": SIG, **e} for e in entries]
    _write(ledger_path, {"sig": "other", "first_raised_ts": 10**12, "seq": 99}, *rows)
    assert ledger.latest_match(SIG, str(ledger_path)) == rows[winner]


def test_latest_match_tolerates_non_object_lines(ledger_path):
    _write(ledger_path, "[1, 2]", {"sig": SIG, "status": "open", "first_raised_ts": 1})
    assert ledger.latest_match(SIG, str(ledger_path))["status"] == "open"


@pytest.mark.parametrize(
    "bad",
    ["yesterday", None, True, [1], {"t": 1}],
    ids=["str", "null", "bool", "list", "dict"],
)
def test_non_numeric_timestamps_and_seq_read_as_zero(ledger_path, bad):
    _write(
        ledger_path,
        {"sig": SIG, "status": "open", "first_raised_ts": bad, "seq": bad},
        {"sig": SIG, "status": "assigned", "transitioned_ts": 5, "seq": 1},
    )
    assert ledger.latest_match(SIG, str(ledger_path))["status"] == "assigned"


def test_should_post_with_only_a_corrupt_timestamp_fails_open(
    clock, ledger_path, make_rec
):
    # An unreadable timestamp reads as epoch 0, so the window has long elapsed
    # and the item may repost. Never-repost statuses are unaffected by ts.
    _write(ledger_path, {"sig": SIG, "status": "open", "first_raised_ts": "yesterday"})
    assert ledger.should_post(make_rec(), str(ledger_path)) == (
        True,
        "debounce window elapsed (500000.0h >= 72h)",
    )
    _write(ledger_path, {"sig": SIG, "status": "done", "transitioned_ts": None})
    assert ledger.should_post(make_rec(), str(ledger_path)) == (
        False,
        "existing entry is done — never repost",
    )


# --------------------------------------------------------------------------- #
# should_post
# --------------------------------------------------------------------------- #


def test_should_post_allows_without_signature_and_skips_the_ledger(
    ledger_path, make_rec, monkeypatch
):
    lookup = mock.Mock()
    monkeypatch.setattr(ledger, "latest_match", lookup)
    rec = make_rec(action_verb="", target_repo="", file_or_workflow_path="")
    assert ledger.should_post(rec, str(ledger_path)) == (
        True,
        "no signature — cannot de-dup, allowing",
    )
    lookup.assert_not_called()


def test_should_post_first_raise(ledger_path, make_rec):
    assert ledger.should_post(make_rec(), str(ledger_path)) == (
        True,
        "first raise of this signature",
    )


@pytest.mark.parametrize(
    ("status", "ts_field", "age_s", "allow", "reason"),
    [
        (
            "open",
            "first_raised_ts",
            71 * HOUR,
            False,
            "existing entry is open, raised 71.0h ago (debounce 72h) — suppress",
        ),
        # One second short of the window: suppressed, but the reason rounds to "72.0h".
        (
            "open",
            "first_raised_ts",
            72 * HOUR - 1,
            False,
            "existing entry is open, raised 72.0h ago (debounce 72h) — suppress",
        ),
        (
            "open",
            "first_raised_ts",
            72 * HOUR,
            True,
            "debounce window elapsed (72.0h >= 72h)",
        ),
        (
            "assigned",
            "transitioned_ts",
            167 * HOUR,
            False,
            "existing entry is assigned, raised 167.0h ago (debounce 168h) — suppress",
        ),
        (
            "assigned",
            "transitioned_ts",
            168 * HOUR,
            True,
            "debounce window elapsed (168.0h >= 168h)",
        ),
        (
            "inflight",
            "transitioned_ts",
            0,
            False,
            "existing entry is inflight, raised 0.0h ago (debounce 168h) — suppress",
        ),
        (
            "inflight",
            "transitioned_ts",
            200 * HOUR,
            True,
            "debounce window elapsed (200.0h >= 168h)",
        ),
        ("done", "transitioned_ts", 0, False, "existing entry is done — never repost"),
        (
            "done",
            "transitioned_ts",
            10 * 365 * 24 * HOUR,
            False,
            "existing entry is done — never repost",
        ),
        (
            "dropped",
            "transitioned_ts",
            10 * 365 * 24 * HOUR,
            False,
            "existing entry is dropped — never repost",
        ),
        # Clock skew: an entry from the future is suppressed with a negative age.
        (
            "open",
            "first_raised_ts",
            -1 * HOUR,
            False,
            "existing entry is open, raised -1.0h ago (debounce 72h) — suppress",
        ),
    ],
    ids=[
        "open-inside",
        "open-1s-short-rounds",
        "open-boundary-allows",
        "assigned-inside",
        "assigned-boundary-allows",
        "inflight-just-moved",
        "inflight-elapsed",
        "done-immediately",
        "done-a-decade-later",
        "dropped-a-decade-later",
        "future-timestamp",
    ],
)
def test_should_post_debounce_windows(
    clock, ledger_path, make_rec, status, ts_field, age_s, allow, reason
):
    _write(ledger_path, {"sig": SIG, "status": status, ts_field: NOW - age_s, "seq": 0})
    assert ledger.should_post(make_rec(), str(ledger_path)) == (allow, reason)


@pytest.mark.parametrize(
    ("entry", "reason"),
    [
        (
            {"first_raised_ts": NOW - HOUR},
            "existing entry is open, raised 1.0h ago (debounce 72h) — suppress",
        ),
        (
            {"status": "blocked", "first_raised_ts": NOW - HOUR},
            "existing entry is blocked, raised 1.0h ago (debounce 72h) — suppress",
        ),
        # Regression: a transition-only entry has no first_raised_ts; must not read as 0.
        (
            {"status": "assigned", "transitioned_ts": NOW - HOUR},
            "existing entry is assigned, raised 1.0h ago (debounce 168h) — suppress",
        ),
    ],
    ids=[
        "missing-status-is-open",
        "hand-edited-status-gets-default",
        "transition-only-entry",
    ],
)
def test_should_post_irregular_entries(clock, ledger_path, make_rec, entry, reason):
    _write(ledger_path, {"sig": SIG, **entry})
    assert ledger.should_post(make_rec(), str(ledger_path)) == (False, reason)


def test_should_post_asks_config_for_the_window(
    clock, ledger_path, make_rec, monkeypatch
):
    hours = mock.Mock(return_value=5)
    monkeypatch.setattr(ledger, "get_debounce_hours", hours)
    _write(
        ledger_path,
        {"sig": SIG, "status": "assigned", "transitioned_ts": NOW - 4 * HOUR},
    )
    assert ledger.should_post(make_rec(), str(ledger_path)) == (
        False,
        "existing entry is assigned, raised 4.0h ago (debounce 5h) — suppress",
    )
    hours.assert_called_once_with("assigned")


def test_should_post_honours_config_file(clock, ledger_path, make_rec, write_config):
    write_config(
        "recommendation_debounce:\n  repost_policy:\n    open: {min_hours_between: 1}\n"
    )
    _write(
        ledger_path, {"sig": SIG, "status": "open", "first_raised_ts": NOW - 2 * HOUR}
    )
    assert ledger.should_post(make_rec(), str(ledger_path)) == (
        True,
        "debounce window elapsed (2.0h >= 1h)",
    )


# --------------------------------------------------------------------------- #
# lifecycle
# --------------------------------------------------------------------------- #


def test_full_lifecycle(clock, ledger_path, make_rec):
    rec, path = make_rec(), str(ledger_path)

    assert ledger.should_post(rec, path)[0] is True
    ledger.record(rec, path)
    assert ledger.should_post(rec, path)[0] is False  # immediate re-raise

    clock["now"] += 73 * HOUR
    assert ledger.should_post(rec, path)[0] is True  # open window elapsed

    ledger.transition(rec.signature(), "assigned", owner="U1", path=path)
    clock["now"] += 100 * HOUR
    assert ledger.should_post(rec, path)[0] is False  # transition restarted the window

    clock["now"] += 69 * HOUR
    assert ledger.should_post(rec, path)[0] is True  # 169h >= 168h

    ledger.transition(rec.signature(), "done", path=path)
    clock["now"] += 10 * 365 * 24 * HOUR
    assert ledger.should_post(rec, path) == (
        False,
        "existing entry is done — never repost",
    )
    assert [e["seq"] for e in ledger._load(path)] == [0, 1, 2]
