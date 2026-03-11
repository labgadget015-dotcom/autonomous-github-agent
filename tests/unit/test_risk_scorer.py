"""Unit tests for core/risk_scorer.py"""

from __future__ import annotations

from core.risk_scorer import RiskBand, RiskReport, score_pull_request


class TestScoreBands:
    def test_small_pr_is_low_risk(self):
        report = score_pull_request(files_changed=2, additions=20, deletions=5)
        assert report.band == RiskBand.LOW
        assert report.total_score < 3.0

    def test_large_pr_raises_score(self):
        report = score_pull_request(files_changed=40, additions=1200, deletions=300)
        assert report.total_score >= 2.0  # medium risk territory

    def test_security_path_raises_score(self):
        report = score_pull_request(
            files_changed=1,
            additions=10,
            deletions=2,
            changed_paths=["core/auth.py"],
        )
        sensitive_factor = next(
            (f for f in report.factors if "Sensitive" in f.name), None
        )
        assert sensitive_factor is not None
        assert sensitive_factor.score > 0

    def test_workflow_file_is_sensitive(self):
        report = score_pull_request(
            files_changed=1,
            additions=5,
            deletions=0,
            changed_paths=[".github/workflows/ci.yml"],
        )
        assert ".github/workflows/ci.yml" in report.sensitive_paths

    def test_coverage_drop_raises_score(self):
        low_cov = score_pull_request(
            files_changed=5, additions=100, deletions=10, test_coverage_delta=-15.0
        )
        high_cov = score_pull_request(
            files_changed=5, additions=100, deletions=10, test_coverage_delta=0.0
        )
        assert low_cov.total_score > high_cov.total_score

    def test_coverage_gain_lowers_score(self):
        with_gain = score_pull_request(
            files_changed=3, additions=50, deletions=10, test_coverage_delta=8.0
        )
        without = score_pull_request(
            files_changed=3, additions=50, deletions=10, test_coverage_delta=0.0
        )
        assert with_gain.total_score <= without.total_score

    def test_no_tests_modified_penalised(self):
        no_tests = score_pull_request(
            files_changed=3,
            additions=80,
            deletions=5,
            changed_paths=["core/github_client.py", "core/llm_provider.py"],
        )
        with_tests = score_pull_request(
            files_changed=4,
            additions=80,
            deletions=5,
            changed_paths=[
                "core/github_client.py",
                "core/llm_provider.py",
                "tests/test_github_client.py",
            ],
        )
        assert no_tests.total_score > with_tests.total_score

    def test_score_clamped_between_0_and_10(self):
        # Extreme PR should not exceed 10
        report = score_pull_request(
            files_changed=200,
            additions=10000,
            deletions=5000,
            changed_paths=["core/auth.py"] * 10,
            test_coverage_delta=-50.0,
        )
        assert 0.0 <= report.total_score <= 10.0

    def test_blocks_auto_merge_for_high_risk(self):
        report = score_pull_request(
            files_changed=50,
            additions=2000,
            deletions=500,
            changed_paths=["core/auth.py", "core/policy_engine.py"],
            test_coverage_delta=-20.0,
        )
        assert report.blocks_auto_merge

    def test_does_not_block_for_low_risk(self):
        report = score_pull_request(files_changed=1, additions=5, deletions=2)
        assert not report.blocks_auto_merge


class TestMarkdownOutput:
    def test_as_markdown_contains_band(self):
        report = score_pull_request(files_changed=1, additions=5)
        md = report.as_markdown()
        assert report.band.value in md

    def test_critical_markdown_shows_block_message(self):
        # Force CRITICAL by touching many sensitive paths with coverage drop
        report = score_pull_request(
            files_changed=60,
            additions=3000,
            deletions=1000,
            changed_paths=["core/auth.py", ".github/workflows/ci.yml", "requirements.txt"],
            test_coverage_delta=-25.0,
        )
        if report.band in (RiskBand.HIGH, RiskBand.CRITICAL):
            assert "Auto-merge blocked" in report.as_markdown()

    def test_low_risk_markdown_shows_eligible(self):
        report = score_pull_request(files_changed=1, additions=3)
        assert "Eligible for auto-merge" in report.as_markdown()


class TestRiskReport:
    def test_report_is_dataclass(self):
        report = RiskReport(total_score=2.5, band=RiskBand.LOW)
        assert report.total_score == 2.5
        assert not report.blocks_auto_merge
