"""Decisions ledger: append-only record of recommendation lifecycle.

Purpose: stop the DRC bot re-raising the same work item as a new P0.

Each recommendation gets a normalised `signature` (action_verb|repo|path).
Before posting, the recommender calls should_post(r) — if an open/assigned
match exists inside its debounce window, the post is suppressed (logged).

Status transitions (open -> assigned -> inflight -> done|dropped) are written
by the executor agent, NOT the recommender — keeps concerns separate.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Optional

from recommendation_contract import Recommendation


def _today_iso() -> str:
    """Current UTC date as YYYY-MM-DD (for the first_raised ledger field)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


DEFAULT_LEDGER_PATH = os.environ.get(
    "DECISIONS_LEDGER_PATH", "autopilot/decisions/recommendations.jsonl"
)

# Debounce windows in hours, keyed by status of the existing ledger entry.
DEBOUNCE_HOURS = {
    "open": 72,
    "assigned": 168,
    "inflight": 168,
    "done": None,        # never repost
    "dropped": None,     # never repost (superseded/rejected)
}


def _load(path: str = DEFAULT_LEDGER_PATH) -> list[dict]:
    if not os.path.exists(path):
        return []
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return out


def _next_seq(path: str = DEFAULT_LEDGER_PATH) -> int:
    """Monotonic append counter — breaks sub-second timestamp ties so the
    latest-written entry wins in latest_match()."""
    return len(_load(path))


def _append(entry: dict, path: str = DEFAULT_LEDGER_PATH) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def latest_match(sig: str, path: str = DEFAULT_LEDGER_PATH) -> Optional[dict]:
    """Return the most recent ledger entry with this signature, or None.

    Ordering key = (max ts, seq) so the latest-written entry wins even when
    record and transition land in the same second.
    """
    matches = [e for e in _load(path) if e.get("sig") == sig]
    if not matches:
        return None
    return max(matches, key=lambda e: (max(e.get("first_raised_ts", 0),
                                         e.get("transitioned_ts", 0)),
                                       e.get("seq", 0)))


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
    window = DEBOUNCE_HOURS.get(status, 72)

    if window is None:
        return False, f"existing entry is {status} — never repost"

    # Use the latest activity timestamp (record OR transition) so the debounce
    # window restarts when an item is reassigned/moved to in-flight. Without
    # this, transition entries (which only carry transitioned_ts) default to
    # first_raised_ts=0 -> ~495k hours elapsed -> always reposts.
    latest_ts = max(existing.get("first_raised_ts", 0),
                    existing.get("transitioned_ts", 0))
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
        "seq": _next_seq(path),
        "run_id": r.run_id,
        "prior_run_id": r.prior_run_id,
    }
    _append(entry, path)
    return entry


def transition(
    sig: str, new_status: str, owner: Optional[str] = None,
    due: Optional[str] = None, path: str = DEFAULT_LEDGER_PATH,
) -> dict:
    """Append a status transition for an existing work item.

    Used by the executor agent when work starts / merges / is dropped.
    """
    entry = {
        "sig": sig,
        "status": new_status,
        "owner": owner or "",
        "due": due or "",
        "transitioned_ts": int(time.time()),
        "seq": _next_seq(path),
    }
    _append(entry, path)
    return entry
