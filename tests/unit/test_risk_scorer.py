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
            changed_paths=[
                "core/auth.py",
                ".github/workflows/ci.yml",
                "requirements.txt",
            ],
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


class TestPRMetadata:
    def test_draft_pr_adds_penalty(self):
        base = score_pull_request(files_changed=2, additions=10, deletions=3)
        draft = score_pull_request(
            files_changed=2,
            additions=10,
            deletions=3,
            pr_metadata={"is_draft": True},
        )
        assert draft.total_score > base.total_score
        draft_factor = next((f for f in draft.factors if "Draft" in f.name), None)
        assert draft_factor is not None
        assert draft_factor.score == 0.5

    def test_non_draft_pr_has_no_draft_penalty(self):
        report = score_pull_request(
            files_changed=2,
            additions=10,
            deletions=3,
            pr_metadata={"is_draft": False},
        )
        draft_factor = next((f for f in report.factors if "Draft" in f.name), None)
        assert draft_factor is None

    def test_non_default_base_adds_penalty(self):
        default_base = score_pull_request(
            files_changed=2,
            additions=10,
            deletions=3,
            pr_metadata={"base_branch": "main"},
        )
        non_default = score_pull_request(
            files_changed=2,
            additions=10,
            deletions=3,
            pr_metadata={"base_branch": "release/1.0"},
        )
        assert non_default.total_score > default_base.total_score
        base_factor = next(
            (f for f in non_default.factors if "Non-default" in f.name), None
        )
        assert base_factor is not None
        assert base_factor.score == 0.5

    def test_master_and_develop_are_default_bases(self):
        for branch in ("master", "develop"):
            report = score_pull_request(
                files_changed=1,
                additions=5,
                deletions=2,
                pr_metadata={"base_branch": branch},
            )
            base_factor = next(
                (f for f in report.factors if "Non-default" in f.name), None
            )
            assert base_factor is None, f"'{branch}' should be a default base"

    def test_combined_draft_and_non_default_base(self):
        report = score_pull_request(
            files_changed=1,
            additions=5,
            deletions=2,
            pr_metadata={"is_draft": True, "base_branch": "hotfix/urgent"},
        )
        factor_names = [f.name for f in report.factors]
        assert any("Draft" in n for n in factor_names)
        assert any("Non-default" in n for n in factor_names)


class TestRiskyExtensions:
    def test_sql_file_raises_score(self):
        no_sql = score_pull_request(
            files_changed=1,
            additions=20,
            deletions=5,
        )
        with_sql = score_pull_request(
            files_changed=1,
            additions=20,
            deletions=5,
            changed_paths=["migrations/add_users.sql"],
        )
        assert with_sql.total_score > no_sql.total_score

    def test_shell_script_raises_score(self):
        report = score_pull_request(
            files_changed=1,
            additions=10,
            deletions=0,
            changed_paths=["scripts/deploy.sh"],
        )
        risky_factor = next((f for f in report.factors if "Risky" in f.name), None)
        assert risky_factor is not None

    def test_yaml_file_raises_score(self):
        report = score_pull_request(
            files_changed=1,
            additions=5,
            deletions=2,
            changed_paths=["config/app.yaml"],
        )
        risky_factor = next((f for f in report.factors if "Risky" in f.name), None)
        assert risky_factor is not None

    def test_risky_ext_in_test_path_not_counted(self):
        # The risk scorer excludes paths matching _TEST_PATH (test_|_test.|/tests?/)
        # from risky-extension scoring. "tests/test_migrate.sql" matches via "test_".
        report = score_pull_request(
            files_changed=1,
            additions=10,
            deletions=0,
            changed_paths=["tests/test_migrate.sql"],
        )
        risky_factor = next((f for f in report.factors if "Risky" in f.name), None)
        assert risky_factor is None

    def test_multiple_risky_ext_score_capped_at_1_5(self):
        many_sql = ["migrations/step_{}.sql".format(i) for i in range(10)]
        report = score_pull_request(
            files_changed=10,
            additions=100,
            deletions=10,
            changed_paths=many_sql,
        )
        risky_factor = next((f for f in report.factors if "Risky" in f.name), None)
        assert risky_factor is not None
        assert risky_factor.score <= 1.5


class TestRiskBands:
    def test_medium_band_score_range(self):
        # A PR with moderate changes should land in MEDIUM band (3.0–5.9)
        report = score_pull_request(
            files_changed=3,
            additions=350,
            deletions=50,
            changed_paths=["src/api.py"],
        )
        assert report.band == RiskBand.MEDIUM
        assert 3.0 <= report.total_score < 6.0

    def test_high_band_score_range(self):
        report = score_pull_request(
            files_changed=20,
            additions=1200,
            deletions=300,
            changed_paths=["core/auth.py"],
            test_coverage_delta=-5.0,
        )
        assert report.band in (RiskBand.HIGH, RiskBand.CRITICAL)
        assert report.total_score >= 6.0

    def test_all_bands_represented_in_enum(self):
        assert set(RiskBand) == {
            RiskBand.LOW,
            RiskBand.MEDIUM,
            RiskBand.HIGH,
            RiskBand.CRITICAL,
        }

    def test_blocks_auto_merge_property_medium(self):
        report = score_pull_request(
            files_changed=3,
            additions=350,
            deletions=50,
            changed_paths=["src/api.py"],
        )
        if report.band == RiskBand.MEDIUM:
            assert not report.blocks_auto_merge


class TestScoreSummary:
    def test_summary_mentions_files_and_lines(self):
        report = score_pull_request(files_changed=4, additions=100, deletions=30)
        assert "4" in report.summary
        assert "100" in report.summary

    def test_summary_mentions_security_when_sensitive_paths(self):
        report = score_pull_request(
            files_changed=1,
            additions=10,
            deletions=2,
            changed_paths=["core/auth.py"],
        )
        assert "Security" in report.summary or "security" in report.summary

    def test_summary_coverage_improved_note(self):
        report = score_pull_request(
            files_changed=2, additions=20, deletions=5, test_coverage_delta=5.0
        )
        assert "Test coverage unchanged or improved." in report.summary

    def test_as_markdown_contains_breakdown_table(self):
        report = score_pull_request(
            files_changed=5,
            additions=500,
            deletions=100,
            changed_paths=["core/auth.py"],
        )
        md = report.as_markdown()
        assert "| Factor" in md
        assert "|--------|" in md

    def test_sensitive_paths_appear_in_markdown(self):
        report = score_pull_request(
            files_changed=1,
            additions=5,
            deletions=0,
            changed_paths=[".github/workflows/deploy.yml"],
        )
        md = report.as_markdown()
        assert ".github/workflows/deploy.yml" in md

    def test_medium_band_markdown_no_block_message(self):
        report = score_pull_request(
            files_changed=3,
            additions=350,
            deletions=50,
        )
        md = report.as_markdown()
        if report.band == RiskBand.MEDIUM:
            assert "Auto-merge blocked" not in md
