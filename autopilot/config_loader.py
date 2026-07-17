"""Config loader: reads autopilot/config.yaml, falls back to built-in defaults.

Uses PyYAML if installed; otherwise returns DEFAULTS so the module stays
stdlib-runnable for tests. This closes the "declared but never read" gap
flagged in the PR #180 review — ledger/contract/formatter now derive their
constants from config rather than hardcoding them.
"""

from __future__ import annotations

import copy
import os
from typing import Any, Optional

DEFAULT_CONFIG_PATH = os.environ.get("AUTOPILOT_CONFIG_PATH", "autopilot/config.yaml")

DEFAULTS: dict[str, Any] = {
    "recommendation_debounce": {
        "enabled": True,
        "ledger_path": "autopilot/decisions/recommendations.jsonl",
        "repost_policy": {
            "open": {"min_hours_between": 72, "never_repost": False},
            "assigned": {"min_hours_between": 168, "never_repost": False},
            "inflight": {"min_hours_between": 168, "never_repost": False},
            "done": {"never_repost": True},
            "dropped": {"never_repost": True},
        },
    },
    "status_tags": {
        "open": "🟡 Open",
        "assigned": "🔵 Assigned",
        "inflight": "🟠 In-flight",
        "done": "✅ Done",
        "dropped": "❌ Dropped",
    },
    "message_contract": {
        "max_step_len": 120,
        "headline_is_outcome": True,
        "require_impact_for": ["P0", "P1"],
        "require_due_for": ["P0", "P1"],
        "require_owner_for": ["P0"],
    },
}

_cache: Optional[dict[str, Any]] = None


def _deep_merge(base: dict[str, Any], over: dict[str, Any]) -> dict[str, Any]:
    for k, v in over.items():
        if k in base and isinstance(base[k], dict) and isinstance(v, dict):
            _deep_merge(base[k], v)
        else:
            base[k] = v
    return base


def load_config(path: Optional[str] = None) -> dict[str, Any]:
    """Load and cache the merged config. Falls back to DEFAULTS if PyYAML
    is unavailable or the file is missing.

    `path=None` reads the module-level DEFAULT_CONFIG_PATH at call time so
    tests can swap the config file by reassigning the global + reset_cache().
    """
    global _cache
    if _cache is not None:
        return _cache
    if path is None:
        path = DEFAULT_CONFIG_PATH
    cfg = copy.deepcopy(DEFAULTS)
    try:
        import yaml  # optional dependency
    except ImportError:
        pass
    else:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                loaded = yaml.safe_load(f) or {}
            if isinstance(loaded, dict):
                _deep_merge(cfg, loaded)
    _cache = cfg
    return cfg


def get_debounce_hours(status: str) -> Optional[int]:
    """Hours to suppress a re-raise, or None for never-repost."""
    policy = load_config()["recommendation_debounce"]["repost_policy"].get(status, {})
    if policy.get("never_repost"):
        return None
    return policy.get("min_hours_between", 72)


def get_status_tag(status: str) -> str:
    return load_config()["status_tags"].get(status, "🟡 Open")


def get_contract() -> dict[str, Any]:
    return load_config()["message_contract"]


def get_ledger_path() -> str:
    return load_config()["recommendation_debounce"].get(
        "ledger_path", "autopilot/decisions/recommendations.jsonl"
    )


def reset_cache() -> None:
    """Clear the config cache (for tests that swap config files)."""
    global _cache
    _cache = None
