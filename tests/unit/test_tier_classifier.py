"""Unit tests for .github/scripts/tier_classifier.py"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

import importlib
import types

# We import the module but test its helpers directly to avoid needing
# GITHUB_OUTPUT / GITHUB_STEP_SUMMARY in the environment.
import tier_classifier


# ---------------------------------------------------------------------------
# _load_exceptions
# ---------------------------------------------------------------------------


class TestLoadExceptions:
    def test_loads_pip_blocklist(self, tmp_path):
        cfg = tmp_path / "exc.yml"
        cfg.write_text("pip:\n  - stripe\n  - cryptography\n")
        result = tier_classifier._load_exceptions(str(cfg))
        assert "stripe" in result["pip"]
        assert "cryptography" in result["pip"]

    def test_missing_file_returns_empty(self, tmp_path):
        result = tier_classifier._load_exceptions(str(tmp_path / "nonexistent.yml"))
        assert result == {}

    def test_normalises_to_lowercase(self, tmp_path):
        cfg = tmp_path / "exc.yml"
        cfg.write_text("pip:\n  - Stripe\n  - CRYPTOGRAPHY\n")
        result = tier_classifier._load_exceptions(str(cfg))
        assert "stripe" in result["pip"]
        assert "cryptography" in result["pip"]


# ---------------------------------------------------------------------------
# _is_blocklisted
# ---------------------------------------------------------------------------


class TestIsBlocklisted:
    _exceptions = {"pip": ["stripe", "cryptography", "scipy"]}

    def test_blocklisted_package_flagged(self):
        blocked = tier_classifier._is_blocklisted(["stripe"], "pip", self._exceptions)
        assert "stripe" in blocked

    def test_safe_package_not_flagged(self):
        blocked = tier_classifier._is_blocklisted(["requests"], "pip", self._exceptions)
        assert blocked == []

    def test_wrong_ecosystem_not_flagged(self):
        # stripe is only on the pip blocklist, not npm
        blocked = tier_classifier._is_blocklisted(["stripe"], "npm", self._exceptions)
        assert blocked == []

    def test_multiple_packages_partial_match(self):
        blocked = tier_classifier._is_blocklisted(
            ["requests", "stripe", "pyyaml"], "pip", self._exceptions
        )
        assert blocked == ["stripe"]

    def test_case_insensitive_match(self):
        blocked = tier_classifier._is_blocklisted(["Stripe"], "pip", self._exceptions)
        assert blocked == ["Stripe"]


# ---------------------------------------------------------------------------
# classify() via environment variable injection
# ---------------------------------------------------------------------------


class TestClassify:
    """Run classify() with a mocked environment and capture GITHUB_OUTPUT."""

    def _run(
        self, env_overrides: dict, tmp_path: Path, exceptions_content: str = ""
    ) -> dict:
        exc_file = tmp_path / "exc.yml"
        if exceptions_content:
            exc_file.write_text(exceptions_content)
        else:
            exc_file.write_text("pip:\n  - stripe\n  - cryptography\n  - scipy\n")

        output_file = tmp_path / "github_output"
        output_file.touch()
        summary_file = tmp_path / "github_summary"
        summary_file.touch()

        env = {
            "PR_TITLE": "chore(deps): bump requests from 2.31.0 to 2.34.2",
            "UPDATE_TYPE": "version-update:semver-patch",
            "DEPENDENCY_NAMES": "requests",
            "PACKAGE_ECOSYSTEM": "pip",
            "EXCEPTIONS_FILE": str(exc_file),
            "DRY_RUN": "true",
            "GITHUB_OUTPUT": str(output_file),
            "GITHUB_STEP_SUMMARY": str(summary_file),
        }
        env.update(env_overrides)

        old_env = {k: os.environ.get(k) for k in env}
        for k, v in env.items():
            os.environ[k] = v
        try:
            tier_classifier.classify()
        finally:
            for k, old_v in old_env.items():
                if old_v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = old_v

        outputs = {}
        for line in output_file.read_text().splitlines():
            if "=" in line:
                k, _, v = line.partition("=")
                outputs[k] = v
        return outputs

    def test_patch_bump_is_tier1_auto_merge(self, tmp_path):
        out = self._run(
            {
                "UPDATE_TYPE": "version-update:semver-patch",
                "DEPENDENCY_NAMES": "requests",
            },
            tmp_path,
        )
        assert out["tier"] == "1"
        assert out["merge_decision"] == "auto-merge"

    def test_minor_bump_is_tier1_auto_merge(self, tmp_path):
        out = self._run(
            {
                "UPDATE_TYPE": "version-update:semver-minor",
                "DEPENDENCY_NAMES": "pyyaml",
            },
            tmp_path,
        )
        assert out["tier"] == "1"
        assert out["merge_decision"] == "auto-merge"

    def test_major_bump_is_tier2_needs_review(self, tmp_path):
        out = self._run(
            {
                "PR_TITLE": "chore(deps): bump stripe from 8.1.0 to 9.0.0",
                "UPDATE_TYPE": "version-update:semver-major",
                "DEPENDENCY_NAMES": "stripe",
            },
            tmp_path,
        )
        assert out["tier"] == "2"
        assert out["merge_decision"] == "needs-review"

    def test_blocklisted_patch_is_tier2_needs_review(self, tmp_path):
        out = self._run(
            {
                "PR_TITLE": "chore(deps): bump stripe from 8.1.0 to 8.1.1",
                "UPDATE_TYPE": "version-update:semver-patch",
                "DEPENDENCY_NAMES": "stripe",
            },
            tmp_path,
        )
        assert out["tier"] == "2"
        assert out["merge_decision"] == "needs-review"
        assert "stripe" in out["blocklisted_names"]

    def test_blocklisted_minor_is_tier2_needs_review(self, tmp_path):
        out = self._run(
            {
                "PR_TITLE": "chore(deps): bump scipy from 1.11.4 to 1.17.1",
                "UPDATE_TYPE": "version-update:semver-minor",
                "DEPENDENCY_NAMES": "scipy",
            },
            tmp_path,
        )
        assert out["tier"] == "2"
        assert out["merge_decision"] == "needs-review"

    def test_unknown_update_type_is_tier2(self, tmp_path):
        out = self._run(
            {
                "PR_TITLE": "feat: add new feature",
                "UPDATE_TYPE": "",
                "DEPENDENCY_NAMES": "",
            },
            tmp_path,
        )
        assert out["tier"] == "2"
        assert out["merge_decision"] == "needs-review"

    def test_multiple_deps_one_blocklisted(self, tmp_path):
        out = self._run(
            {
                "UPDATE_TYPE": "version-update:semver-minor",
                "DEPENDENCY_NAMES": "pyyaml,stripe,requests",
            },
            tmp_path,
        )
        assert out["tier"] == "2"
        assert "stripe" in out["blocklisted_names"]
