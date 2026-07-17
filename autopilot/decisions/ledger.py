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
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime

from config_loader import get_debounce_hours, get_ledger_path
from recommendation_contract import VALID_STATUSES, Recommendation

try:
    import fcntl  # POSIX only

    _HAS_FCNTL = True
except ImportError:
    _HAS_FCNTL = False


def _today_iso() -> str:
    """Current UTC date as YYYY-MM-DD (for the first_raised ledger field)."""
    return datetime.now(UTC).strftime("%Y-%m-%d")


DEFAULT_LEDGER_PATH = os.environ.get("DECISIONS_LEDGER_PATH", get_ledger_path())


def _load(path: str = DEFAULT_LEDGER_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                # Partial/corrupt line (e.g. a write was interrupted). Skip
                # rather than crash — locking makes this rare, not impossible.
                continue
    return out

def _lock(fd):
    """Exclusive lock the ledger file handle (POSIX). No-op elsewhere."""
    if _HAS_FCNTL:
        fcntl.flock(fd.fileno(), fcntl.LOCK_EX)


def _unlock(fd):
    if _HAS_FCNTL:
        fcntl.flock(fd.fileno(), fcntl.LOCK_UN)


def _append_with_seq(entry: dict, path: str = DEFAULT_LEDGER_PATH) -> dict:
    """Atomic: assign seq under lock, then append. Prevents _next_seq races."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a+", encoding="utf-8") as f:
        _lock(f)
        try:
            f.seek(0, os.SEEK_END)
            # count existing lines for seq
            f.seek(0)
            seq = sum(1 for line in f if line.strip())
            entry["seq"] = seq
            f.seek(0, os.SEEK_END)
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        finally:
            _unlock(f)
    return entry


def latest_match(sig: str, path: str = DEFAULT_LEDGER_PATH) -> dict | None:
    """Return the most recent ledger entry with this signature, or None.

    Ordering key = (max ts, seq) so the latest-written entry wins even when
    record and transition land in the same second.
    """
    matches = [e for e in _load(path) if e.get("sig") == sig]
    if not matches:
        return None
    return max(
        matches,
        key=lambda e: (
            max(e.get("first_raised_ts", 0), e.get("transitioned_ts", 0)),
            e.get("seq", 0),
        ),
    )


def should_post(r: Recommendation, path: str = DEFAULT_LEDGER_PATH) -> tuple[bool, str]:
    """Decide whether a recommendation may be posted to Slack.

    Returns (allow, reason). When False, the caller must suppress + log.
    """
    sig = r.signature()
    if not sig:
        return True, "no signature — cannot de-dup, allowing"

    existing = latest_match(sig, path)
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
    latest_ts = max(
        existing.get("first_raised_ts", 0), existing.get("transitioned_ts", 0)
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
