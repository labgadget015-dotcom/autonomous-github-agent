"""Global incident freeze — the Phase 0 "stop everything" kill switch.

Per the 2026-08-04 handover (Workstream B), this is the single control that
defaults write-capable execution to DENY while preserving ingestion, read-only
analysis, and audit visibility. It is checked by every write path (Python
executors, n8n write nodes/callbacks, GitHub Actions, retries, scheduled jobs,
delayed callbacks, manual dispatches).

Design rules (from the handover):
  * Defaults to NOT frozen — normal operation is governed by dry_run / approval.
    The freeze is an explicit operator override that escalates the posture.
  * When frozen, ALL write actions are denied for the affected scope; read-only
    and audit paths remain alive.
  * Enabling/disabling records who, why, when, scope, and (for enable) expiry.
  * Safe under repeated activation: re-enabling while already frozen is
    idempotent (state unchanged, no error); disabling while not frozen is a
    no-op (not an error).
  * Does NOT silently discard work — callers must defer + retain status; this
    module only answers "may I write?".
  * Verifiable with a no-op test (see tests/unit/test_incident_freeze.py).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_STATE_PATH = Path(__file__).resolve().parent.parent / "state" / "freeze.json"

# Scopes: "global" covers everything; specific scopes can be frozen independently
# (e.g. "n8n", "github-actions", "agent-core"). "global" implies all scopes.
GLOBAL_SCOPE = "global"


@dataclass
class FreezeState:
    frozen: bool = False
    scope: str = GLOBAL_SCOPE
    enabled_by: str | None = None
    enabled_at: str | None = None
    reason: str | None = None
    expires_at: str | None = None
    last_disabled_by: str | None = None
    last_disabled_at: str | None = None
    audit: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "frozen": self.frozen,
            "scope": self.scope,
            "enabled_by": self.enabled_by,
            "enabled_at": self.enabled_at,
            "reason": self.reason,
            "expires_at": self.expires_at,
            "last_disabled_by": self.last_disabled_by,
            "last_disabled_at": self.last_disabled_at,
            "audit": self.audit,
        }


class FreezeControl:
    """Operational wrapper around the persisted FreezeState."""

    def __init__(self, state_path: Path = DEFAULT_STATE_PATH):
        self.state_path = Path(state_path)
        self._state = self._load()

    # --- persistence ---
    def _load(self) -> FreezeState:
        if self.state_path.exists():
            try:
                raw = json.loads(self.state_path.read_text())
                return FreezeState(
                    **{k: raw.get(k, v) for k, v in FreezeState().__dict__.items()}
                )
            except Exception:
                # Corrupt state file -> fail safe to NOT frozen (we never want a
                # broken file to wedge the agent; the watchdog will flag it).
                return FreezeState()
        return FreezeState()

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        # write atomically
        tmp = self.state_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state.to_dict(), indent=2))
        tmp.replace(self.state_path)

    # --- queries ---
    def is_frozen(self, scope: str = GLOBAL_SCOPE) -> bool:
        s = self._state
        if not s.frozen:
            return False
        # expired freeze auto-clears on read
        if s.expires_at and self._now_iso() >= s.expires_at:
            self._clear_if_expired()
            return False
        if s.scope == GLOBAL_SCOPE:
            return True
        return scope == s.scope or scope == GLOBAL_SCOPE

    def is_write_allowed(self, action: str = "any", scope: str = GLOBAL_SCOPE) -> bool:
        """The contract every write path consults.

        Returns True only if the freeze is NOT active for the scope. Dry-run and
        approval gates are handled separately by agent_config.
        """
        if self.is_frozen(scope):
            return False
        return True

    def status(self) -> dict:
        return self._state.to_dict()

    # --- mutations (operator-only) ---
    def freeze(
        self,
        by: str,
        reason: str,
        scope: str = GLOBAL_SCOPE,
        expires_at: str | None = None,
    ) -> dict:
        """Enable the freeze. Idempotent if already frozen with same scope."""
        s = self._state
        # If already frozen for an equal-or-broader scope, just refresh metadata
        # without clobbering the original enable timestamp (preserve first cause).
        if s.frozen and (
            s.scope == GLOBAL_SCOPE or scope == s.scope or scope == GLOBAL_SCOPE
        ):
            entry = {
                "event": "freeze-refreshed",
                "by": by,
                "at": self._now_iso(),
                "scope": scope,
                "reason": reason,
            }
            s.audit.append(entry)
            if expires_at:
                s.expires_at = expires_at
            self._save()
            return s.to_dict()
        # New freeze (broadening scope or first enable)
        s.frozen = True
        s.scope = scope
        s.enabled_by = by
        s.enabled_at = self._now_iso()
        s.reason = reason
        s.expires_at = expires_at
        s.audit.append(
            {
                "event": "freeze-enabled",
                "by": by,
                "at": s.enabled_at,
                "scope": scope,
                "reason": reason,
                "expires_at": expires_at,
            }
        )
        self._save()
        return s.to_dict()

    def unfreeze(self, by: str, reason: str = "operator cleared") -> dict:
        """Disable the freeze. Idempotent if not frozen."""
        s = self._state
        if not s.frozen:
            s.audit.append({"event": "unfreeze-noop", "by": by, "at": self._now_iso()})
            self._save()
            return s.to_dict()
        s.frozen = False
        s.last_disabled_by = by
        s.last_disabled_at = self._now_iso()
        s.audit.append(
            {
                "event": "freeze-disabled",
                "by": by,
                "at": s.last_disabled_at,
                "reason": reason,
            }
        )
        self._save()
        return s.to_dict()

    # --- helpers ---
    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _clear_if_expired(self) -> None:
        s = self._state
        if s.frozen and s.expires_at and self._now_iso() >= s.expires_at:
            s.frozen = False
            s.audit.append({"event": "freeze-expired", "at": self._now_iso()})
            self._save()


# Module-level singleton — import and use directly:
#   from core.incident_freeze import freeze
#   if not freeze.is_write_allowed(scope="n8n"): defer()
freeze = FreezeControl()
