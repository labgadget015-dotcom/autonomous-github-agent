"""Unit tests for .github/scripts/check_policy.py and generate_rollback_manifest.py"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)


class TestCheckPolicies:
    def test_check_policies_no_results_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import check_policy

        audit = check_policy.check_policies()
        assert audit["status"] == "passed"
        assert len(audit["violations"]) == 0
        assert "Results file not found" in audit["warnings"]

    def test_check_policies_with_results_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "results.json").write_text(json.dumps({"status": "success"}))
        import check_policy

        audit = check_policy.check_policies()
        assert audit["status"] == "passed"

    def test_check_policies_creates_audit_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import check_policy

        check_policy.check_policies()
        assert (tmp_path / "audit.log").exists()

    def test_audit_file_has_correct_structure(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import check_policy

        check_policy.check_policies()
        data = json.loads((tmp_path / "audit.log").read_text())
        assert "policies" in data
        assert "violations" in data
        assert "warnings" in data
        assert "status" in data


class TestRollbackManifest:
    def test_main_creates_docs_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("SHA", "abc123def456")
        monkeypatch.setenv("SHORT_SHA", "abc123d")
        monkeypatch.setenv("MSG", "feat: add feature")
        monkeypatch.setenv("AUTHOR", "Alice")
        monkeypatch.setenv("FILES_CHANGED", "src/main.py tests/test_main.py")
        import generate_rollback_manifest

        generate_rollback_manifest.main()
        assert (tmp_path / "docs").exists()
        assert (tmp_path / "docs" / "ROLLBACK.md").exists()

    def test_main_creates_rollback_entry(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("SHA", "abc123def456")
        monkeypatch.setenv("SHORT_SHA", "abc123d")
        monkeypatch.setenv("MSG", "fix: fix bug")
        monkeypatch.setenv("AUTHOR", "Bob")
        monkeypatch.setenv("FILES_CHANGED", "core/module.py")
        import generate_rollback_manifest

        generate_rollback_manifest.main()
        content = (tmp_path / "docs" / "ROLLBACK.md").read_text()
        assert "abc123d" in content
        assert "Bob" in content
        assert "fix: fix bug" in content

    def test_main_with_existing_rollback_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "docs").mkdir()
        (tmp_path / "docs" / "ROLLBACK.md").write_text(
            "# Rollback Manifest\n\nExisting content here.\n\n---\n"
        )
        monkeypatch.setenv("SHA", "def456")
        monkeypatch.setenv("SHORT_SHA", "def456")
        monkeypatch.setenv("MSG", "chore: update")
        monkeypatch.setenv("AUTHOR", "Charlie")
        monkeypatch.setenv("FILES_CHANGED", "")
        import generate_rollback_manifest

        generate_rollback_manifest.main()
        content = (tmp_path / "docs" / "ROLLBACK.md").read_text()
        assert "def456" in content
        assert "Rollback Manifest" in content  # Header preserved

    def test_main_caps_files_at_20(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("SHA", "abc123")
        monkeypatch.setenv("SHORT_SHA", "abc123")
        monkeypatch.setenv("MSG", "big commit")
        monkeypatch.setenv("AUTHOR", "Dev")
        files = " ".join([f"file_{i}.py" for i in range(25)])
        monkeypatch.setenv("FILES_CHANGED", files)
        import generate_rollback_manifest

        generate_rollback_manifest.main()
        content = (tmp_path / "docs" / "ROLLBACK.md").read_text()
        # Should show 25 files changed but only list 20
        assert "25 file(s)" in content
        assert "file_20.py" not in content  # 21st file should not be listed

    def test_main_without_files_changed(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("SHA", "abc123")
        monkeypatch.setenv("SHORT_SHA", "abc123")
        monkeypatch.setenv("MSG", "empty commit")
        monkeypatch.setenv("AUTHOR", "Dev")
        monkeypatch.setenv("FILES_CHANGED", "")
        import generate_rollback_manifest

        generate_rollback_manifest.main()
        content = (tmp_path / "docs" / "ROLLBACK.md").read_text()
        assert "0 file(s)" in content
