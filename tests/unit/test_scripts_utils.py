"""Unit tests for .github/scripts/utils.py

Tests pure utility functions that don't require external services.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest


class TestLoadJsonFile:
    def test_load_valid_json(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps({"key": "value", "num": 42}))
        result = load_json_file(str(f))
        assert result == {"key": "value", "num": 42}

    def test_returns_none_for_missing_file(self, tmp_path):
        result = load_json_file(str(tmp_path / "nonexistent.json"))
        assert result is None

    def test_raises_on_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{invalid json}")
        with pytest.raises(json.JSONDecodeError):
            load_json_file(str(f))


# Use direct import by manipulating sys.path at module level
import sys as _sys

_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in _sys.path:
    _sys.path.insert(0, _scripts_path)

from utils import (  # noqa: E402
    calculate_quality_score,
    find_files_by_extension,
    format_file_size,
    get_env_variable,
    load_json_file,
    save_json_file,
    validate_threshold,
)


class TestSaveJsonFile:
    def test_save_creates_file(self, tmp_path):
        out = tmp_path / "output.json"
        result = save_json_file({"a": 1}, str(out))
        assert result is True
        assert out.exists()
        data = json.loads(out.read_text())
        assert data == {"a": 1}

    def test_save_creates_parent_dirs(self, tmp_path):
        out = tmp_path / "nested" / "deep" / "output.json"
        save_json_file({"x": 2}, str(out))
        assert out.exists()

    def test_save_returns_false_on_error(self):
        result = save_json_file({"a": 1}, "/nonexistent_root_dir/file.json")
        assert result is False


class TestGetEnvVariable:
    def test_returns_env_variable_value(self, monkeypatch):
        monkeypatch.setenv("MY_TEST_VAR", "hello")
        assert get_env_variable("MY_TEST_VAR") == "hello"

    def test_returns_default_when_not_set(self, monkeypatch):
        monkeypatch.delenv("MISSING_VAR", raising=False)
        assert get_env_variable("MISSING_VAR", "default_val") == "default_val"

    def test_returns_none_when_not_set_no_default(self, monkeypatch):
        monkeypatch.delenv("MISSING_VAR2", raising=False)
        assert get_env_variable("MISSING_VAR2") is None


class TestCalculateQualityScore:
    def test_perfect_score_with_no_issues(self):
        score = calculate_quality_score()
        assert score == 10.0

    def test_pylint_issues_reduce_score(self):
        score = calculate_quality_score(pylint_issues=10)
        assert score < 10.0

    def test_flake8_issues_reduce_score(self):
        score = calculate_quality_score(flake8_issues=10)
        assert score < 10.0

    def test_high_security_issues_reduce_score(self):
        score = calculate_quality_score(security_high=3)
        assert score < 10.0

    def test_medium_security_issues_reduce_score(self):
        score = calculate_quality_score(security_medium=5)
        assert score < 10.0

    def test_score_heavily_penalized(self):
        score = calculate_quality_score(
            pylint_issues=100, flake8_issues=100, security_high=10, security_medium=30
        )
        # Max deductions: 3.0 + 3.0 + 2.0 + 1.0 = 9.0 → minimum score = 1.0
        assert score <= 2.0

    def test_pylint_penalty_capped_at_3(self):
        s1 = calculate_quality_score(pylint_issues=30)
        s2 = calculate_quality_score(pylint_issues=300)
        assert s1 == s2  # Both hit the 3.0 cap

    def test_combined_issues(self):
        score = calculate_quality_score(
            pylint_issues=5, flake8_issues=3, security_high=1, security_medium=2
        )
        assert 0.0 <= score <= 10.0


class TestFormatFileSize:
    def test_bytes(self):
        assert format_file_size(512) == "512.0 B"

    def test_kilobytes(self):
        result = format_file_size(1024)
        assert "KB" in result or "1.0" in result

    def test_megabytes(self):
        result = format_file_size(1024 * 1024)
        assert "MB" in result

    def test_gigabytes(self):
        result = format_file_size(1024**3)
        assert "GB" in result

    def test_zero_bytes(self):
        assert "0.0" in format_file_size(0)


class TestFindFilesByExtension:
    def test_finds_files_with_extension(self, tmp_path):
        (tmp_path / "a.py").write_text("# a")
        (tmp_path / "b.py").write_text("# b")
        (tmp_path / "c.txt").write_text("text")
        result = find_files_by_extension(tmp_path, ".py")
        assert len(result) == 2

    def test_returns_empty_for_missing_dir(self, tmp_path):
        result = find_files_by_extension(tmp_path / "nonexistent", ".py")
        assert result == []

    def test_finds_files_recursively(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.py").write_text("")
        result = find_files_by_extension(tmp_path, ".py")
        assert len(result) >= 1


class TestValidateThreshold:
    def test_value_above_threshold_higher_is_better(self):
        assert validate_threshold(80.0, 70.0, higher_is_better=True) is True

    def test_value_below_threshold_higher_is_better(self):
        assert validate_threshold(60.0, 70.0, higher_is_better=True) is False

    def test_exact_threshold_meets_requirement(self):
        assert validate_threshold(70.0, 70.0, higher_is_better=True) is True

    def test_lower_is_better_mode(self):
        assert validate_threshold(0.5, 1.0, higher_is_better=False) is True
        assert validate_threshold(1.5, 1.0, higher_is_better=False) is False
