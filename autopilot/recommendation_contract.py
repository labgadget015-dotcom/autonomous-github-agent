"""Recommendation contract: dataclass + validator.

Enforces the executive-grade message contract for DRC recommendations:
  - Headline = outcome (not run_id)
  - Mandatory impact_if_ignored for P0/P1
  - Mandatory owner + due_date for P0 (P1: due_date required, owner may be TBD)
  - Steps are one-line (<=120 chars), no inline run_ids
  - Status lifecycle tracked for de-dup + closure loop

Intended gate for the DRC recommendation pipeline: a recommendation that fails
validate() is withheld before posting to Slack. As of 2026-09-13 nothing in the
repo calls it yet — the live DRC council runs in n8n.

validate() never raises on a malformed Recommendation: wrong-typed fields are
reported as errors so an emitter loop can log a reject block and move on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Literal

Severity = Literal["P0", "P1", "P2"]
Status = Literal["open", "assigned", "inflight", "done", "dropped"]

# Lifecycle statuses a ledger entry may hold. Used by ledger.transition() to
# reject typos that would silently break de-dup (e.g. "assiged").
VALID_STATUSES = {"open", "assigned", "inflight", "done", "dropped"}

SEVERITY_EMOJI = {"P0": "🔴", "P1": "🟠", "P2": "🟡"}
# Fallback only — the live value is read from config.yaml via config_loader.
MAX_STEP_LEN = 120
RUN_ID_TOKEN = "run_"
# A run id is "run_" + digits, not glued to a preceding identifier character —
# so "dry_run_gate.yml" and "rerun_tests" are not run ids.
RUN_ID_RE = re.compile(r"(?<![A-Za-z0-9_])run_\d+")
_ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")

_STR_FIELDS = (
    "severity",
    "headline",
    "impact_if_ignored",
    "due_date",
    "owner",
    "status",
    "blocked_by",
    "target_repo",
    "file_or_workflow_path",
    "action_verb",
    "prior_run_id",
    "run_id",
)


def _sig_part(value: str) -> str:
    """Normalise one signature slot; escape the delimiter so a field cannot
    forge a slot boundary."""
    return value.strip().lower().replace("\\", "\\\\").replace("|", "\\|")


@dataclass
class Recommendation:
    severity: Severity
    headline: str  # outcome, NOT run_id
    impact_if_ignored: str  # required for P0/P1
    steps: list[str]
    due_date: str  # YYYY-MM-DD or ""
    owner: str = "unassigned"  # @user_id or "unassigned"
    status: Status = "open"
    blocked_by: str = ""  # prerequisite, "" if none
    target_repo: str = ""
    file_or_workflow_path: str = ""
    action_verb: str = ""  # "create" | "configure" | "rotate" | ...
    prior_run_id: str = ""  # for Ref: footer + de-dup
    run_id: str = ""  # current raise's id (footer only)

    def signature(self) -> str:
        """Normalised work-item signature for de-dup matching.

        Positional: empty slots are kept, so ("rotate", "", "x") and
        ("rotate", "x", "") are different work items. Returns "" when all three
        fields are blank — callers treat that as "cannot de-dup".
        """
        parts = [
            _sig_part(p)
            for p in (self.action_verb, self.target_repo, self.file_or_workflow_path)
        ]
        return "|".join(parts) if any(parts) else ""


def _type_errors(r: Recommendation) -> list[str]:
    errs = [
        f"{name} must be a string, got {type(getattr(r, name)).__name__}"
        for name in _STR_FIELDS
        if not isinstance(getattr(r, name), str)
    ]
    if not isinstance(r.steps, list):
        errs.append(f"steps must be a list of strings, got {type(r.steps).__name__}")
    else:
        errs.extend(
            f"step {i} must be a string, got {type(s).__name__}"
            for i, s in enumerate(r.steps, 1)
            if not isinstance(s, str)
        )
    return errs


def _is_iso_date(value: str) -> bool:
    if not _ISO_DATE_RE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def validate(r: Recommendation) -> tuple[bool, list[str]]:
    """Return (ok, errors). ok=False => withhold from Slack.

    Severity/step/owner rules are read from config.yaml (message_contract)
    via config_loader, with stdlib fallbacks if PyYAML/file is absent.
    """
    from config_loader import get_contract

    # Wrong types make every later rule meaningless (or crash) — stop here.
    type_errs = _type_errors(r)
    if type_errs:
        return (False, type_errs)

    contract = get_contract()
    max_step_len = contract.get("max_step_len", MAX_STEP_LEN)
    headline_is_outcome = contract.get("headline_is_outcome", True)
    require_impact_for = set(contract.get("require_impact_for", ["P0", "P1"]))
    require_due_for = set(contract.get("require_due_for", ["P0", "P1"]))
    require_owner_for = set(contract.get("require_owner_for", ["P0"]))

    errs: list[str] = []

    # Unknown severity/status would silently skip every severity rule / break
    # the ledger lifecycle ("p0" is not "P0").
    if r.severity not in SEVERITY_EMOJI:
        errs.append(
            f"unknown severity {r.severity!r}; expected one of {sorted(SEVERITY_EMOJI)}"
        )
    if r.status not in VALID_STATUSES:
        errs.append(
            f"unknown status {r.status!r}; expected one of {sorted(VALID_STATUSES)}"
        )

    # Headline must not be a raw run_id
    headline = r.headline.strip()
    if headline_is_outcome and (RUN_ID_RE.match(headline) or len(headline) < 8):
        errs.append("headline must be an outcome, not a run_id")

    # Impact required for anything that claims urgency
    if r.severity in require_impact_for and not r.impact_if_ignored.strip():
        errs.append(f"{r.severity} missing impact_if_ignored")

    # Due date required for P0/P1, and must be a real YYYY-MM-DD date if given
    due = r.due_date.strip()
    if r.severity in require_due_for and not due:
        errs.append(f"{r.severity} missing due_date")
    if due and not _is_iso_date(due):
        errs.append(f"due_date {r.due_date!r} is not a YYYY-MM-DD date")

    # Owner required (P0 by default); else withhold + escalate
    if r.severity in require_owner_for and r.owner.strip() in ("", "unassigned"):
        errs.append(
            f"{r.severity} with no owner — withhold, escalate to #morning-digest"
        )

    # Steps: one-line, bounded length, no run_ids
    for i, s in enumerate(r.steps, 1):
        if not s.strip():
            errs.append(f"step {i} empty")
            continue
        if len(s) > max_step_len:
            errs.append(f"step {i} > {max_step_len} chars (split it)")
        if "\n" in s or "\r" in s:
            errs.append(f"step {i} spans multiple lines (one line per step)")
        if RUN_ID_RE.search(s):
            errs.append(f"step {i} contains run_id (move to Ref: footer)")

    # Signature required for de-dup to work
    if not r.signature():
        errs.append("missing signature fields (action_verb + target + path)")

    return (len(errs) == 0, errs)
