"""Recommendation contract: dataclass facade + Pydantic V2 validation engine.

Enforces the executive-grade message contract for DRC recommendations:
  - Headline = outcome (not run_id)
  - Mandatory impact_if_ignored for P0/P1
  - Mandatory owner + due_date for P0 (P1: due_date required, owner may be TBD)
  - Steps are one-line (<=120 chars), no inline run_ids
  - Status lifecycle tracked for de-dup + closure loop

Intended gate for the DRC recommendation pipeline: a recommendation that fails
validate() is withheld before posting to Slack. As of 2026-09-13 nothing in the
repo calls it yet — the live DRC council runs in n8n.

Architecture:
  - ``Recommendation`` (dataclass) stays the public, mutable input type used by
    the ledger, formatter and callers.
  - ``RecommendationContract`` (Pydantic V2 ``BaseModel``, strict + frozen) is
    the validation engine: strict field types, then one ``mode="after"`` model
    validator that applies the cross-field rules in a fixed order.
  - ``validate()`` is the never-raise facade: it resolves config-driven rules,
    runs the model, catches ``ValidationError`` and translates it back into the
    exact ``(ok, list[str])`` contract downstream consumers depend on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, fields
from datetime import date
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictStr,
    ValidationError,
    ValidationInfo,
    model_validator,
)
from pydantic_core import PydanticCustomError

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
# fromisoformat() alone is not strict enough: since Python 3.11 it also accepts
# basic-format dates such as "20270430". The regex pins the extended form.
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
_CONTRACT_ERROR = "recommendation_contract"


def _sig_part(value: str) -> str:
    """Normalise one signature slot; escape the delimiter so a field cannot
    forge a slot boundary."""
    return value.strip().lower().replace("\\", "\\\\").replace("|", "\\|")


def _signature(action_verb: str, target_repo: str, file_or_workflow_path: str) -> str:
    parts = [_sig_part(p) for p in (action_verb, target_repo, file_or_workflow_path)]
    return "|".join(parts) if any(parts) else ""


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
        return _signature(
            self.action_verb, self.target_repo, self.file_or_workflow_path
        )


@dataclass(frozen=True)
class ContractRules:
    """Resolved message_contract rules. Defaults mirror config_loader.DEFAULTS."""

    max_step_len: int = MAX_STEP_LEN
    headline_is_outcome: bool = True
    require_impact_for: frozenset[str] = frozenset({"P0", "P1"})
    require_due_for: frozenset[str] = frozenset({"P0", "P1"})
    require_owner_for: frozenset[str] = frozenset({"P0"})


def _is_iso_date(value: str) -> bool:
    if not _ISO_DATE_RE.fullmatch(value):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _identity_errors(m: RecommendationContract) -> list[str]:
    # Unknown severity/status would silently skip every severity rule / break
    # the ledger lifecycle ("p0" is not "P0").
    errs = []
    if m.severity not in SEVERITY_EMOJI:
        errs.append(
            f"unknown severity {m.severity!r}; expected one of {sorted(SEVERITY_EMOJI)}"
        )
    if m.status not in VALID_STATUSES:
        errs.append(
            f"unknown status {m.status!r}; expected one of {sorted(VALID_STATUSES)}"
        )
    return errs


def _headline_errors(m: RecommendationContract, rules: ContractRules) -> list[str]:
    headline = m.headline.strip()
    if rules.headline_is_outcome and (RUN_ID_RE.match(headline) or len(headline) < 8):
        return ["headline must be an outcome, not a run_id"]
    return []


def _impact_errors(m: RecommendationContract, rules: ContractRules) -> list[str]:
    if m.severity in rules.require_impact_for and not m.impact_if_ignored.strip():
        return [f"{m.severity} missing impact_if_ignored"]
    return []


def _due_date_errors(m: RecommendationContract, rules: ContractRules) -> list[str]:
    """Required per config; when given it must be a real, strict YYYY-MM-DD date."""
    errs = []
    due = m.due_date.strip()
    if m.severity in rules.require_due_for and not due:
        errs.append(f"{m.severity} missing due_date")
    if due and not _is_iso_date(due):
        errs.append(f"due_date {m.due_date!r} is not a YYYY-MM-DD date")
    return errs


def _owner_errors(m: RecommendationContract, rules: ContractRules) -> list[str]:
    """Owner required for the severities in require_owner_for (default P0)."""
    if m.severity in rules.require_owner_for and m.owner.strip() in ("", "unassigned"):
        return [f"{m.severity} with no owner — withhold, escalate to #morning-digest"]
    return []


def _step_errors(m: RecommendationContract, rules: ContractRules) -> list[str]:
    """Steps: non-empty, single-line, bounded length, no run ids."""
    errs = []
    for i, s in enumerate(m.steps, 1):
        if not s.strip():
            errs.append(f"step {i} empty")
            continue
        if len(s) > rules.max_step_len:
            errs.append(f"step {i} > {rules.max_step_len} chars (split it)")
        if "\n" in s or "\r" in s:
            errs.append(f"step {i} spans multiple lines (one line per step)")
        if RUN_ID_RE.search(s):
            errs.append(f"step {i} contains run_id (move to Ref: footer)")
    return errs


def _signature_errors(m: RecommendationContract) -> list[str]:
    if not _signature(m.action_verb, m.target_repo, m.file_or_workflow_path):
        return ["missing signature fields (action_verb + target + path)"]
    return []


class RecommendationContract(BaseModel):
    """Pydantic V2 validation engine for a recommendation.

    Strict and frozen: no type coercion (``None`` or ``123`` is never silently
    turned into a string) and a validated instance cannot be mutated. Rules come
    from validation context key ``"resolve_rules"`` (a zero-argument callable
    returning ``ContractRules``); without context the built-in defaults apply.
    Prefer ``validate()``, which supplies config-driven rules and never raises.
    """

    model_config = ConfigDict(strict=True, frozen=True, extra="forbid")

    severity: StrictStr
    headline: StrictStr
    impact_if_ignored: StrictStr
    steps: list[StrictStr]
    due_date: StrictStr
    owner: StrictStr = "unassigned"
    status: StrictStr = "open"
    blocked_by: StrictStr = ""
    target_repo: StrictStr = ""
    file_or_workflow_path: StrictStr = ""
    action_verb: StrictStr = ""
    prior_run_id: StrictStr = ""
    run_id: StrictStr = ""

    @model_validator(mode="after")
    def _enforce_contract(self, info: ValidationInfo) -> RecommendationContract:
        # One hook, not one per rule: pydantic stops at the first after-validator
        # that raises, and callers need every violation, in a stable order.
        # Runs only once all field types are valid.
        resolve = (info.context or {}).get("resolve_rules")
        rules = resolve() if resolve is not None else ContractRules()
        errs = [
            *_identity_errors(self),
            *_headline_errors(self, rules),
            *_impact_errors(self, rules),
            *_due_date_errors(self, rules),
            *_owner_errors(self, rules),
            *_step_errors(self, rules),
            *_signature_errors(self),
        ]
        if errs:
            raise PydanticCustomError(
                _CONTRACT_ERROR,
                "{count} contract violation(s)",
                {"count": len(errs), "violations": errs},
            )
        return self


def _messages_from(exc: ValidationError) -> list[str]:
    """Translate a ValidationError into the legacy error strings.

    Field-type errors are ordered like the legacy validator (string fields in
    declaration order, then ``steps``); contract violations keep rule order.
    """
    typed: list[tuple[int, int, str]] = []
    violations: list[str] = []
    steps_rank = len(_STR_FIELDS)
    for err in exc.errors():
        loc = err["loc"]
        got = type(err.get("input")).__name__
        if err["type"] == _CONTRACT_ERROR:
            violations.extend(err["ctx"]["violations"])
        elif loc == ("steps",):
            typed.append((steps_rank, 0, f"steps must be a list of strings, got {got}"))
        elif len(loc) == 2 and loc[0] == "steps" and isinstance(loc[1], int):
            n = loc[1] + 1
            typed.append((steps_rank, n, f"step {n} must be a string, got {got}"))
        elif len(loc) == 1 and loc[0] in _STR_FIELDS:
            rank = _STR_FIELDS.index(str(loc[0]))
            typed.append((rank, 0, f"{loc[0]} must be a string, got {got}"))
        else:  # not produced today; keep never-raise if the model grows
            where = ".".join(str(p) for p in loc) or "recommendation"
            typed.append((steps_rank + 1, 0, f"{where}: {err['msg']}"))
    return [msg for _, _, msg in sorted(typed)] + violations


def validate(r: Recommendation) -> tuple[bool, list[str]]:
    """Return (ok, errors). ok=False => withhold from Slack.

    Severity/step/owner rules are read from config.yaml (message_contract)
    via config_loader, with stdlib fallbacks if PyYAML/file is absent.
    Never raises for a malformed Recommendation.
    """
    from config_loader import get_contract

    def resolve_rules() -> ContractRules:
        # Called by the model only after field types pass, so a wrong-typed
        # recommendation is reported without touching config.
        contract = get_contract()
        return ContractRules(
            max_step_len=contract.get("max_step_len", MAX_STEP_LEN),
            headline_is_outcome=contract.get("headline_is_outcome", True),
            require_impact_for=frozenset(
                contract.get("require_impact_for", ["P0", "P1"])
            ),
            require_due_for=frozenset(contract.get("require_due_for", ["P0", "P1"])),
            require_owner_for=frozenset(contract.get("require_owner_for", ["P0"])),
        )

    data = {f.name: getattr(r, f.name) for f in fields(Recommendation)}
    try:
        RecommendationContract.model_validate(
            data, context={"resolve_rules": resolve_rules}
        )
    except ValidationError as exc:
        return (False, _messages_from(exc))
    return (True, [])
