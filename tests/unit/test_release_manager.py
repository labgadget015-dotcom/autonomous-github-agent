"""Unit tests for .github/scripts/release_manager.py"""

from __future__ import annotations

import sys
from pathlib import Path
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from release_manager import ReleaseManager


class TestReleaseManagerInit:
    def test_creates_with_defaults(self):
        rm = ReleaseManager()
        assert rm.dry_run is False

    def test_creates_with_dry_run(self):
        rm = ReleaseManager(dry_run=True)
        assert rm.dry_run is True


class TestParseVersion:
    def _rm(self):
        return ReleaseManager()

    def test_parses_simple_version(self):
        rm = self._rm()
        major, minor, patch, pre = rm.parse_version("1.2.3")
        assert major == 1
        assert minor == 2
        assert patch == 3
        assert pre is None

    def test_parses_prerelease_version(self):
        rm = self._rm()
        major, minor, patch, pre = rm.parse_version("2.0.0-alpha.1")
        assert major == 2
        assert minor == 0
        assert patch == 0
        assert pre == "alpha.1"

    def test_raises_on_invalid_format(self):
        rm = self._rm()
        with pytest.raises(ValueError):
            rm.parse_version("not-a-version")

    def test_raises_on_partial_version(self):
        rm = self._rm()
        with pytest.raises(ValueError):
            rm.parse_version("1.2")

    def test_parses_zero_version(self):
        rm = self._rm()
        major, minor, patch, pre = rm.parse_version("0.0.0")
        assert major == 0
        assert minor == 0
        assert patch == 0


class TestBumpVersion:
    def _rm(self):
        return ReleaseManager()

    def test_bump_patch(self):
        rm = self._rm()
        assert rm.bump_version("1.2.3", "patch") == "1.2.4"

    def test_bump_minor_resets_patch(self):
        rm = self._rm()
        assert rm.bump_version("1.2.3", "minor") == "1.3.0"

    def test_bump_major_resets_minor_and_patch(self):
        rm = self._rm()
        assert rm.bump_version("1.2.3", "major") == "2.0.0"

    def test_bump_invalid_type_raises(self):
        rm = self._rm()
        with pytest.raises(ValueError):
            rm.bump_version("1.2.3", "invalid")

    def test_bump_from_zero(self):
        rm = self._rm()
        assert rm.bump_version("0.0.0", "patch") == "0.0.1"


class TestUpdateFileVersion:
    def test_updates_version_in_init_py(self, tmp_path):
        rm = ReleaseManager(dry_run=False)
        rm.root = tmp_path
        init_file = tmp_path / "__init__.py"
        init_file.write_text('__version__ = "1.0.0"\n')
        rm._update_file_version(init_file, "1.0.0", "1.1.0")
        assert '1.1.0' in init_file.read_text()

    def test_updates_version_in_setup_py(self, tmp_path):
        rm = ReleaseManager(dry_run=False)
        rm.root = tmp_path
        setup_file = tmp_path / "setup.py"
        setup_file.write_text('version = "0.5.0"\n')
        rm._update_file_version(setup_file, "0.5.0", "0.6.0")
        assert '0.6.0' in setup_file.read_text()

    def test_dry_run_doesnt_write(self, tmp_path):
        rm = ReleaseManager(dry_run=True)
        init_file = tmp_path / "__init__.py"
        init_file.write_text('__version__ = "1.0.0"\n')
        rm._update_file_version(init_file, "1.0.0", "2.0.0")
        assert '1.0.0' in init_file.read_text()

    def test_no_version_pattern_doesnt_crash(self, tmp_path):
        rm = ReleaseManager(dry_run=False)
        init_file = tmp_path / "__init__.py"
        init_file.write_text("# No version here\n")
        rm._update_file_version(init_file, "1.0.0", "2.0.0")
        assert "# No version here" in init_file.read_text()


class TestUpdateVersionFiles:
    def test_updates_existing_version_files(self, tmp_path):
        rm = ReleaseManager(dry_run=False)
        rm.root = tmp_path
        init = tmp_path / "__init__.py"
        init.write_text('__version__ = "1.0.0"\n')
        rm.update_version_files("1.0.0", "2.0.0")
        assert '2.0.0' in init.read_text()

    def test_skips_nonexistent_files(self, tmp_path):
        rm = ReleaseManager(dry_run=False)
        rm.root = tmp_path
        # No version files exist
        rm.update_version_files("1.0.0", "2.0.0")  # Should not raise


class TestCreateGitTagDryRun:
    def test_dry_run_prints_message(self, capsys):
        rm = ReleaseManager(dry_run=True)
        rm.create_git_tag("1.0.0", "Release")
        out = capsys.readouterr().out
        assert "DRY RUN" in out
        assert "1.0.0" in out


class TestCommitChangesDryRun:
    def test_dry_run_prints_message(self, capsys):
        rm = ReleaseManager(dry_run=True)
        rm.commit_changes("1.0.0")
        out = capsys.readouterr().out
        assert "DRY RUN" in out


class TestPushReleaseDryRun:
    def test_dry_run_prints_message(self, capsys):
        rm = ReleaseManager(dry_run=True)
        rm.push_release()
        out = capsys.readouterr().out
        assert "DRY RUN" in out


class TestCreateGithubReleaseDryRun:
    def test_dry_run_prints_message(self, capsys):
        rm = ReleaseManager(dry_run=True)
        rm.create_github_release("1.0.0", "See CHANGELOG")
        out = capsys.readouterr().out
        assert "DRY RUN" in out
