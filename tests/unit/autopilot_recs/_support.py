"""Shared constants for the autopilot recommendation-pipeline tests.

The modules under test use flat sibling imports (``from config_loader import``),
so ``autopilot/`` must be importable under its own name. It is APPENDED to
sys.path, never inserted at position 0: there, ``autopilot/autopilot.py`` would
shadow the ``autopilot`` package that other suites import.

Always import the modules by their flat names (``config_loader``,
``decisions.ledger``, ...). ``autopilot.config_loader`` would be a second module
object with its own ``_cache``, so resetting one would not reset the other.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
AUTOPILOT_DIR = REPO_ROOT / "autopilot"
if str(AUTOPILOT_DIR) not in sys.path:
    sys.path.append(str(AUTOPILOT_DIR))

REAL_CONFIG = AUTOPILOT_DIR / "config.yaml"
REAL_LEDGER = AUTOPILOT_DIR / "decisions" / "recommendations.jsonl"

# A recommendation that passes validate() under the built-in defaults.
GOOD_FIELDS = {
    "severity": "P0",
    "headline": "Rotate the GitHub PAT before it expires",
    "impact_if_ignored": "Every workflow using the PAT fails and the pipeline goes offline",
    "steps": [
        "Mint a fine-grained PAT with repo + workflow scopes",
        "Replace the GH_PAT repository secret",
        "Re-run the canary workflow and confirm it goes green",
    ],
    "due_date": "2027-04-30",
    "owner": "U0AKJK1J7GR",
    "action_verb": "rotate",
    "target_repo": "autonomous-github-agent",
    "file_or_workflow_path": ".github/workflows/pat-rotation.yml",
}
SIG = "rotate|autonomous-github-agent|.github/workflows/pat-rotation.yml"
