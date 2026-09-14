"""Decisions ledger: append-only record of recommendation lifecycle.

Purpose: stop the DRC bot re-raising the same work item as a new P0.

Each recommendation gets a normalised `signature` (action_verb|repo|path).
Before posting, the recommender calls should_post(r) — if an open/assigned
match exists inside its debounce window, the post is suppressed (logged).

Status transitions (open -> assigned -> inflight -> done|dropped) are written
by the executor agent, NOT the recommender — keeps concerns separate.

Concurrency: all reads+writes are guarded by an fcntl.flock on POSIX so the
recommender (record) and executor (transition) agents can't interleave appends
or race on _next_seq. Falls back to no-op locking on non-POSIX platforms.
Debounce windows and status tags are read from config.yaml via config_loader.

On-disk format: every append writes a checksummed line

    <payload_json>|<sha256(payload_json.encode()).hexdigest()[:16]>

_load verifies the checksum (splitting on the LAST "|", since the payload's
signature itself contains pipes) and skips a mismatching line with a WARNING
naming its line number. Legacy plain-JSON lines written before the checksum
format are still read, silently.

Corruption tolerance: a torn write, undecodable bytes, a non-object JSON line,
or a non-numeric timestamp never crashes a reader — the bad line is skipped or
the bad field reads as 0 (reported once per call as a summary WARNING) — and
the next append starts on a fresh line so it is not glued onto a torn one.
"""

from __future__ import annotations

import hashlib
import json
import logging
import math
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone

from config_loader import get_debounce_hours, get_ledger_path
from recommendation_contract import VALID_STATUSES, Recommendation

try:
    import fcntl  # POSIX only

    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False

logger = logging.getLogger(__name__)

CHECKSUM_LEN = 16
# Greedy (.*) makes the split happen on the last pipe.
_CHECKSUMMED_LINE_RE = re.compile(rf"(.*)\|([0-9a-f]{{{CHECKSUM_LEN}}})")


def _today_iso() -> str:
    """Current timezone.utc date as YYYY-MM-DD (for the first_raised ledger field)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


DEFAULT_LEDGER_PATH = os.environ.get("DECISIONS_LEDGER_PATH", get_ledger_path())


def _checksum(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode()).hexdigest()[:CHECKSUM_LEN]


def _format_line(entry: dict) -> str:
    """Serialise one entry in the checksummed on-disk format (with newline)."""
    payload_json = json.dumps(entry, ensure_ascii=False)
    return f"{payload_json}|{_checksum(payload_json)}\n"


def _num_safe(entry: dict, key: str, tally: Counter[str]) -> float:
    """Numeric field, or 0 for a missing one.

    A present but unusable value (string, null, bool, list, NaN, inf) also reads
    as 0 so ordering never crashes — but unlike a missing key it is counted in
    `tally`, which the public caller reports once via _report_coercions().
    """
    if key not in entry:
        return 0
    value = entry[key]
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
    ):
        tally[key] += 1
        return 0
    return value


def _report_coercions(tally: Counter[str], path: str) -> None:
    """One summary WARNING per read call — never one per line."""
    if not tally:
        return
    detail = ", ".join(f"{key}={count}" for key, count in sorted(tally.items()))
    logger.warning(
        "ledger %s: coerced %d non-numeric value(s) to 0 (%s)",
        path,
        sum(tally.values()),
        detail,
    )


def _load(path: str = DEFAULT_LEDGER_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    out: list[dict] = []
    # Binary + per-line decode: one bad byte costs one line, not the whole file.
    with open(path, "rb") as f:
        for lineno, raw in enumerate(f, 1):
            try:
                text = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            if not text:
                continue
            match = _CHECKSUMMED_LINE_RE.fullmatch(text)
            if match:
                payload_json, digest = match.groups()
                if _checksum(payload_json) != digest:
                    logger.warning(
                        "ledger %s line %d: checksum mismatch — line skipped",
                        path,
                        lineno,
                    )
                    continue
            else:
                payload_json = text  # legacy plain-JSON line (pre-checksum)
            try:
                entry = json.loads(payload_json)
            except json.JSONDecodeError:
                # Partial/corrupt line (e.g. a write was interrupted). Skip
                # rather than crash — locking makes this rare, not impossible.
                continue
            if isinstance(entry, dict):
                out.append(entry)
    return out


def _lock(fd):
    """Exclusive lock the ledger file handle (POSIX). No-op elsewhere."""
    if _HAS_FCNTL:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)


def _unlock(fd):
    if _HAS_FCNTL:
        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)


def _append_with_seq(entry: dict, path: str = DEFAULT_LEDGER_PATH) -> dict:
    """Atomic: assign seq under lock, then append. Prevents _next_seq races.

    `entry` is only updated with its seq once the line is durably written, so a
    failed append leaves the caller's dict untouched.
    """
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a+b") as f:
        _lock(f)
        try:
            f.seek(0)
            seq, tail = 0, b"\n"
            for line in f:
                if line.strip():
                    seq += 1
                tail = line
            line_out = _format_line({**entry, "seq": seq})
            # A torn previous write has no trailing newline; start a fresh line
            # or this entry would be glued onto it and lost on the next _load.
            prefix = b"" if tail.endswith(b"\n") else b"\n"
            f.write(prefix + line_out.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        finally:
            _unlock(f)
    entry["seq"] = seq
    return entry


def _latest(sig: str, path: str, tally: Counter[str]) -> dict | None:
    matches = [e for e in _load(path) if e.get("sig") == sig]
    if not matches:
        return None
    return max(
        matches,
        key=lambda e: (
            max(
                _num_safe(e, "first_raised_ts", tally),
                _num_safe(e, "transitioned_ts", tally),
            ),
            _num_safe(e, "seq", tally),
        ),
    )


def latest_match(sig: str, path: str = DEFAULT_LEDGER_PATH) -> dict | None:
    """Return the most recent ledger entry with this signature, or None.

    Ordering key = (max ts, seq) so the latest-written entry wins even when
    record and transition land in the same second.
    """
    tally: Counter[str] = Counter()
    try:
        return _latest(sig, path, tally)
    finally:
        _report_coercions(tally, path)


def should_post(r: Recommendation, path: str = DEFAULT_LEDGER_PATH) -> tuple[bool, str]:
    """Decide whether a recommendation may be posted to Slack.

    Returns (allow, reason). When False, the caller must suppress + log.
    """
    sig = r.signature()
    if not sig:
        return True, "no signature — cannot de-dup, allowing"

    tally: Counter[str] = Counter()
    try:
        return _decide(sig, path, tally)
    finally:
        _report_coercions(tally, path)


def _decide(sig: str, path: str, tally: Counter[str]) -> tuple[bool, str]:
    existing = _latest(sig, path, tally)
    if existing is None:
        return True, "first raise of this signature"

    status = existing.get("status", "open")
    window = get_debounce_hours(status)

    if window is None:
        return False, f"existing entry is {status} — never repost"

    # Use the latest activity timestamp (record OR transition) so the debounce
    # window restarts when an item is reassigned/moved to in-flight. Without
    # this, transition entries (which only carry transitioned_ts) default to
    # first_raised_ts=0 -> ~495k hours elapsed -> always reposts.
    # This entry's coercions were already tallied by _latest(); don't re-count.
    recount: Counter[str] = Counter()
    latest_ts = max(
        _num_safe(existing, "first_raised_ts", recount),
        _num_safe(existing, "transitioned_ts", recount),
    )
    elapsed_h = (time.time() - latest_ts) / 3600.0
    if elapsed_h < window:
        return False, (
            f"existing entry is {status}, raised {elapsed_h:.1f}h ago "
            f"(debounce {window}h) — suppress"
        )
    return True, f"debounce window elapsed ({elapsed_h:.1f}h >= {window}h)"


def record(r: Recommendation, path: str = DEFAULT_LEDGER_PATH) -> dict:
    """Append a new ledger entry. Called only AFTER should_post() == True."""
    entry = {
        "sig": r.signature(),
        "status": r.status,
        "owner": r.owner,
        "due": r.due_date,
        "severity": r.severity,
        "headline": r.headline,
        "first_raised": _today_iso(),
        "first_raised_ts": int(time.time()),
        "run_id": r.run_id,
        "prior_run_id": r.prior_run_id,
    }
    return _append_with_seq(entry, path)


def transition(
    sig: str,
    new_status: str,
    owner: str | None = None,
    due: str | None = None,
    path: str = DEFAULT_LEDGER_PATH,
) -> dict:
    """Append a status transition for an existing work item.

    Used by the executor agent when work starts / merges / is dropped.
    Raises ValueError if new_status is not a known lifecycle status.
    """
    if new_status not in VALID_STATUSES:
        raise ValueError(
            f"unknown status {new_status!r}; expected one of {sorted(VALID_STATUSES)}"
        )
    entry = {
        "sig": sig,
        "status": new_status,
        "owner": owner or "",
        "due": due or "",
        "transitioned_ts": int(time.time()),
    }
    return _append_with_seq(entry, path)
