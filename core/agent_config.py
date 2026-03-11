"""Agent configuration and feature flags.

Reads [tool.autonomous-agent] from pyproject.toml (or env overrides).
All flags default to safe values: dry_run=True, auto_merge=False.

Usage::

    from core.agent_config import cfg
    if cfg.auto_merge:
        merge_pr(pr)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore[no-reuse-stubs,assignment,no-redef]


def _load_flags() -> dict:
    """Load [tool.autonomous-agent] from pyproject.toml, if present."""
    root = Path(__file__).resolve().parent.parent
    toml_path = root / "pyproject.toml"
    if not toml_path.exists():
        return {}
    try:
        with open(toml_path, "rb") as f:
            data = tomllib.load(f)
        return data.get("tool", {}).get("autonomous-agent", {})
    except Exception:
        return {}


@dataclass
class AgentConfig:
    """Feature-flag config for the autonomous agent system.

    All boolean flags can be overridden with environment variables:
    ``AGENT_<FLAG_UPPER>=true|false``, e.g. ``AGENT_AUTO_MERGE=true``.
    """

    # --- Safety gates ---
    dry_run: bool = True
    """When True, log planned actions but do not execute destructive writes."""

    require_approval: bool = True
    """Require a /approve comment before merging or closing issues."""

    # --- Automation toggles ---
    auto_merge: bool = False
    """Automatically merge PRs when risk_score <= risk_score_threshold."""

    auto_close_issues: bool = True
    """Auto-close issues resolved by a merged PR."""

    auto_delete_branches: bool = True
    """Delete head branch after PR merge."""

    auto_label: bool = True
    """Automatically apply labels to new PRs and issues."""

    # --- Thresholds ---
    risk_score_threshold: float = 4.0
    """PRs with score above this are blocked from auto-merge."""

    flaky_test_fail_rate: float = 0.30
    """Tests failing at less than this rate are flagged as flaky."""

    max_auto_fix_files: int = 50
    """Refuse auto-fix PRs touching more files than this."""

    # --- LLM cost controls ---
    llm_max_cost_usd: float = 1.0
    """Abort LLM-dependent tasks if session cost exceeds this."""

    # --- Paths ---
    metrics_file: str = "docs/METRICS.md"
    rollback_file: str = "docs/ROLLBACK.md"
    audit_log_file: str = ".audit_log.jsonl"
    llm_costs_file: str = ".llm_costs.jsonl"

    # Internal — populated after __post_init__
    _raw: dict = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        flags = _load_flags()
        self._raw = flags
        bool_fields = {
            "dry_run", "require_approval", "auto_merge", "auto_close_issues",
            "auto_delete_branches", "auto_label",
        }
        float_fields = {
            "risk_score_threshold", "flaky_test_fail_rate", "llm_max_cost_usd"
        }
        int_fields = {"max_auto_fix_files"}
        str_fields = {
            "metrics_file", "rollback_file", "audit_log_file", "llm_costs_file"
        }

        for fname in bool_fields:
            env = os.environ.get(f"AGENT_{fname.upper()}")
            if env is not None:
                object.__setattr__(self, fname, env.lower() in ("1", "true", "yes"))
            elif fname in flags:
                object.__setattr__(self, fname, bool(flags[fname]))

        for fname in float_fields:
            env = os.environ.get(f"AGENT_{fname.upper()}")
            if env is not None:
                object.__setattr__(self, fname, float(env))
            elif fname in flags:
                object.__setattr__(self, fname, float(flags[fname]))

        for fname in int_fields:
            env = os.environ.get(f"AGENT_{fname.upper()}")
            if env is not None:
                object.__setattr__(self, fname, int(env))
            elif fname in flags:
                object.__setattr__(self, fname, int(flags[fname]))

        for fname in str_fields:
            env = os.environ.get(f"AGENT_{fname.upper()}")
            if env is not None:
                object.__setattr__(self, fname, env)
            elif fname in flags:
                object.__setattr__(self, fname, str(flags[fname]))

    def is_action_allowed(self, action: str) -> bool:
        """Return True if the named action may proceed given current flags.

        Checks dry_run and specific action toggles.
        Actions: 'merge', 'close_issue', 'delete_branch', 'label', 'auto_fix'.
        """
        if self.dry_run:
            return False
        mapping = {
            "merge": self.auto_merge,
            "close_issue": self.auto_close_issues,
            "delete_branch": self.auto_delete_branches,
            "label": self.auto_label,
        }
        return mapping.get(action, True)

    def __repr__(self) -> str:
        return (
            f"AgentConfig(dry_run={self.dry_run}, auto_merge={self.auto_merge}, "
            f"risk_threshold={self.risk_score_threshold}, "
            f"require_approval={self.require_approval})"
        )


# Module-level singleton — import and use directly
cfg = AgentConfig()
