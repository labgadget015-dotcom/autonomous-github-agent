"""Recommendation contract: dataclass + validator.

Enforces the executive-grade message contract for DRC recommendations:
  - Headline = outcome (not run_id)
  - Mandatory impact_if_ignored for P0/P1
  - Mandatory owner + due_date for P0 (P1: due_date required, owner may be TBD)
  - Steps are one-line (<=120 chars), no inline run_ids
  - Status lifecycle tracked for de-dup + closure loop

Wired into the DRC recommendation pipeline: a recommendation that fails
validate() is withheld (P0) or warned (P1) before posting to Slack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

Severity = Literal["P0", "P1", "P2"]
Status = Literal["open", "assigned", "inflight", "done", "dropped"]

# Lifecycle statuses a ledger entry may hold. Used by ledger.transition() to
# reject typos that would silently break de-dup (e.g. "assiged").
VALID_STATUSES = {"open", "assigned", "inflight", "done", "dropped"}

SEVERITY_EMOJI = {"P0": "🔴", "P1": "🟠", "P2": "🟡"}
# Fallback only — the live value is read from config.yaml via config_loader.
MAX_STEP_LEN = 120
RUN_ID_TOKEN = "run_"


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
        """Normalised work-item signature for de-dup matching."""
        parts = [self.action_verb, self.target_repo, self.file_or_workflow_path]
        return "|".join(p.strip().lower() for p in parts if p.strip())


def validate(r: Recommendation) -> tuple[bool, list[str]]:
    """Return (ok, errors). ok=False => withhold from Slack.

    Severity/step/owner rules are read from config.yaml (message_contract)
    via config_loader, with stdlib fallbacks if PyYAML/file is absent.
    """
    from config_loader import get_contract

    contract = get_contract()
    max_step_len = contract.get("max_step_len", MAX_STEP_LEN)
    require_impact_for = set(contract.get("require_impact_for", ["P0", "P1"]))
    require_due_for = set(contract.get("require_due_for", ["P0", "P1"]))
    require_owner_for = set(contract.get("require_owner_for", ["P0"]))

    errs: list[str] = []

    # Headline must not be a raw run_id
    if r.headline.strip().startswith(RUN_ID_TOKEN) or len(r.headline) < 8:
        errs.append("headline must be an outcome, not a run_id")

    # Impact required for anything that claims urgency
    if r.severity in require_impact_for and not r.impact_if_ignored.strip():
        errs.append(f"{r.severity} missing impact_if_ignored")

    # Due date required for P0/P1
    if r.severity in require_due_for and not r.due_date.strip():
        errs.append(f"{r.severity} missing due_date")

    # P0 must have an owner; else withhold + escalate
    if r.severity in require_owner_for and r.owner == "unassigned":
        errs.append("P0 with no owner — withhold, escalate to #morning-digest")

    # Steps: one-line, bounded length, no run_ids
    for i, s in enumerate(r.steps, 1):
        if not s.strip():
            errs.append(f"step {i} empty")
        if len(s) > max_step_len:
            errs.append(f"step {i} > {max_step_len} chars (split it)")
        if RUN_ID_TOKEN in s:
            errs.append(f"step {i} contains run_id (move to Ref: footer)")

    # Signature required for de-dup to work
    if not r.signature():
        errs.append("missing signature fields (action_verb + target + path)")

    return (len(errs) == 0, errs)
