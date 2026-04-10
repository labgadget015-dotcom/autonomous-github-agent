"""Unit tests for .github/scripts/changelog_generator.py"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from changelog_generator import ChangelogGenerator


class TestParseCommitType:
    def _gen(self):
        return ChangelogGenerator()

    def test_feat_type_parsed(self):
        gen = self._gen()
        ctype, scope, msg, breaking = gen.parse_commit_type("feat: add user auth")
        assert ctype == "feat"
        assert msg == "add user auth"
        assert breaking is False

    def test_fix_with_scope(self):
        gen = self._gen()
        ctype, scope, msg, breaking = gen.parse_commit_type("fix(auth): correct token handling")
        assert ctype == "fix"
        assert scope == "auth"
        assert msg == "correct token handling"

    def test_breaking_change_detected(self):
        gen = self._gen()
        ctype, scope, msg, breaking = gen.parse_commit_type("feat!: remove deprecated API")
        assert breaking is True

    def test_breaking_with_scope(self):
        gen = self._gen()
        ctype, scope, msg, breaking = gen.parse_commit_type("refactor(core)!: rename module")
        assert ctype == "refactor"
        assert scope == "core"
        assert breaking is True

    def test_unknown_format_returns_other(self):
        gen = self._gen()
        ctype, scope, msg, breaking = gen.parse_commit_type("Some random commit message")
        assert ctype == "other"
        assert breaking is False

    def test_empty_scope_when_no_parentheses(self):
        gen = self._gen()
        ctype, scope, msg, breaking = gen.parse_commit_type("docs: update README")
        assert scope == ""

    def test_all_commit_types_parse_correctly(self):
        gen = self._gen()
        for commit_type in ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore"]:
            ctype, _, _, _ = gen.parse_commit_type(f"{commit_type}: some message")
            assert ctype == commit_type


class TestGroupCommits:
    def _gen(self):
        return ChangelogGenerator()

    def test_groups_by_type(self):
        gen = self._gen()
        commits = [
            {"hash": "abc1234", "message": "feat: add feature", "author": "Alice", "email": "a@test.com", "date": "2024-01-01"},
            {"hash": "def5678", "message": "fix: fix bug", "author": "Bob", "email": "b@test.com", "date": "2024-01-02"},
            {"hash": "ghi9012", "message": "feat: another feature", "author": "Alice", "email": "a@test.com", "date": "2024-01-03"},
        ]
        groups = gen.group_commits(commits)
        assert "feat" in groups
        assert len(groups["feat"]) == 2
        assert "fix" in groups
        assert len(groups["fix"]) == 1

    def test_breaking_change_prefixed(self):
        gen = self._gen()
        commits = [
            {"hash": "abc1234", "message": "feat!: breaking change", "author": "Alice", "email": "a@test.com", "date": "2024-01-01"}
        ]
        groups = gen.group_commits(commits)
        assert groups["feat"][0]["breaking"] is True
        assert "BREAKING" in groups["feat"][0]["parsed_message"]

    def test_unknown_type_grouped_as_other(self):
        gen = self._gen()
        commits = [
            {"hash": "abc1234", "message": "just a commit", "author": "Alice", "email": "a@test.com", "date": "2024-01-01"}
        ]
        groups = gen.group_commits(commits)
        assert "other" in groups


class TestFormatSection:
    def _gen(self):
        return ChangelogGenerator()

    def test_unknown_type_returns_empty(self):
        gen = self._gen()
        section = gen.format_section("unknown_type", [])
        assert section == ""

    def test_feat_section_formatted(self):
        gen = self._gen()
        commits = [
            {
                "hash": "abc1234",
                "scope": "",
                "parsed_message": "add dark mode",
                "breaking": False,
            }
        ]
        section = gen.format_section("feat", commits)
        assert "Features" in section
        assert "add dark mode" in section
        assert "abc1234" in section

    def test_section_with_scope(self):
        gen = self._gen()
        commits = [
            {
                "hash": "abc1234",
                "scope": "ui",
                "parsed_message": "update button colors",
                "breaking": False,
            }
        ]
        section = gen.format_section("feat", commits)
        assert "**ui**" in section

    def test_all_known_types_produce_section(self):
        gen = self._gen()
        commit = [{"hash": "abc1234", "scope": "", "parsed_message": "some change", "breaking": False}]
        for commit_type in ChangelogGenerator.COMMIT_TYPES:
            section = gen.format_section(commit_type, commit)
            assert len(section) > 0


class TestGenerateVersionSection:
    def _gen(self):
        return ChangelogGenerator()

    def test_version_section_header(self):
        gen = self._gen()
        commits = [
            {"hash": "abc1234", "message": "feat: add login", "author": "Alice", "email": "a@test.com", "date": "2024-01-01"}
        ]
        section = gen.generate_version_section("v1.0.0", "2024-01-01", commits)
        assert "v1.0.0" in section
        assert "2024-01-01" in section

    def test_empty_commits_returns_version_header(self):
        gen = self._gen()
        section = gen.generate_version_section("v1.0.0", "2024-01-01", [])
        assert "v1.0.0" in section

    def test_multiple_types_ordered(self):
        gen = self._gen()
        commits = [
            {"hash": "abc1234", "message": "fix: fix bug", "author": "Alice", "email": "a@test.com", "date": "2024-01-01"},
            {"hash": "def5678", "message": "feat: add feature", "author": "Bob", "email": "b@test.com", "date": "2024-01-01"},
        ]
        section = gen.generate_version_section("v1.0.0", "2024-01-01", commits)
        # feat should appear before fix in ordered output
        feat_pos = section.find("Features")
        fix_pos = section.find("Bug Fixes")
        assert feat_pos < fix_pos
