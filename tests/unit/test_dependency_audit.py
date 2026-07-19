"""Unit tests for .github/scripts/dependency_audit.py (network-free)."""

import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / ".github" / "scripts"))
import dependency_audit as da  # noqa: E402


def test_parse_requirements_skips_comments_includes_and_flags(tmp_path):
    req_file = tmp_path / "reqs.txt"
    req_file.write_text(
        "# comment\n\nPyGithub>=2.1.1\naiohttp>=3.9.0  # inline\n-r other.txt\n--hash=abc\n"
    )
    reqs = da.parse_requirements(req_file)
    assert [r.name for r in reqs] == ["PyGithub", "aiohttp"]
    assert reqs[0].current == "2.1.1"
    assert reqs[0].constraint == ">=2.1.1"


def test_compare_versions_categories():
    assert da.compare_versions("2.1.1", "2.1.1") == "up-to-date"
    assert da.compare_versions("2.1.1", "2.1.5") == "patch"
    assert da.compare_versions("2.1.1", "2.3.0") == "minor"
    assert da.compare_versions("2.1.1", "3.0.0") == "major"
    assert da.compare_versions(None, "1.0.0") == "unknown"


def test_audit_uses_fetch_mock(monkeypatch):
    def fake(name, timeout=15):
        table = {
            "PyGithub": ("3.0.0", "2024-01-01T00:00:00", None),
            "aiohttp": ("3.9.0", "2024-01-01T00:00:00", None),
        }
        return table[name]

    monkeypatch.setattr(da, "fetch_latest", fake)
    reqs = [
        da.Requirement("PyGithub", ">=2.1.1", "2.1.1"),
        da.Requirement("aiohttp", ">=3.9.0", "3.9.0"),
    ]
    res = da.audit(reqs)
    cats = {r.name: r.category for r in res}
    assert cats["PyGithub"] == "major"
    assert cats["aiohttp"] == "up-to-date"


def test_audit_handles_fetch_error(monkeypatch):
    def fake(name, timeout=15):
        return None, None, "HTTP 500"

    monkeypatch.setattr(da, "fetch_latest", fake)
    res = da.audit([da.Requirement("x", "", None)])
    assert res[0].category == "unknown"
    assert res[0].error == "HTTP 500"


def test_build_report_markdown_and_json():
    res = [da.AuditResult("PyGithub", "2.1.1", "3.0.0", None, "major")]
    md = da.build_report(res)
    assert "Major updates" in md
    js = da.build_report(res, as_json=True)
    assert '"category": "major"' in js
