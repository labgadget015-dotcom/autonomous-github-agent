"""Unit tests for .github/scripts/elite_copilot.py"""

from __future__ import annotations

import sys
from pathlib import Path
from dataclasses import asdict
import pytest

# Add scripts directory to path
_scripts_path = str(Path(__file__).parent.parent.parent / ".github" / "scripts")
if _scripts_path not in sys.path:
    sys.path.insert(0, _scripts_path)

from elite_copilot import (
    CopilotMode, TaskPriority, CopilotTask, CopilotInsight, EliteCopilot
)


class TestCopilotModeEnum:
    def test_assistant_value(self):
        assert CopilotMode.ASSISTANT.value == "assistant"

    def test_autopilot_value(self):
        assert CopilotMode.AUTOPILOT.value == "autopilot"

    def test_guardian_value(self):
        assert CopilotMode.GUARDIAN.value == "guardian"

    def test_mentor_value(self):
        assert CopilotMode.MENTOR.value == "mentor"


class TestTaskPriorityEnum:
    def test_critical_value(self):
        assert TaskPriority.CRITICAL.value == "critical"

    def test_high_value(self):
        assert TaskPriority.HIGH.value == "high"


class TestCopilotTask:
    def test_creates_task(self):
        task = CopilotTask(
            id="task_1",
            type="code_review",
            description="Review PR #42",
            priority=TaskPriority.HIGH,
            context={"pr_number": 42},
            mode=CopilotMode.ASSISTANT,
            created_at="2024-01-01T00:00:00",
        )
        assert task.id == "task_1"
        assert task.status == "pending"

    def test_to_dict_serializes_enums(self):
        task = CopilotTask(
            id="task_1",
            type="test",
            description="Test task",
            priority=TaskPriority.MEDIUM,
            context={},
            mode=CopilotMode.GUARDIAN,
            created_at="2024-01-01T00:00:00",
        )
        d = task.to_dict()
        assert d["priority"] == "medium"
        assert d["mode"] == "guardian"


class TestEliteCopilotInit:
    def test_creates_with_default_config(self):
        copilot = EliteCopilot()
        assert copilot.mode == CopilotMode.ASSISTANT

    def test_session_id_set(self):
        copilot = EliteCopilot()
        assert copilot.session_id.startswith("copilot_")

    def test_initial_tasks_empty(self):
        copilot = EliteCopilot()
        assert copilot.tasks == []

    def test_initial_insights_empty(self):
        copilot = EliteCopilot()
        assert copilot.insights == []

    def test_custom_mode_from_config(self, tmp_path):
        import yaml
        config_file = tmp_path / "config.yml"
        config_file.write_text(yaml.dump({"mode": "guardian"}))
        copilot = EliteCopilot(config_path=str(config_file))
        assert copilot.mode == CopilotMode.GUARDIAN


class TestLoadConfig:
    def test_returns_dict(self):
        copilot = EliteCopilot()
        config = copilot._load_config(None)
        assert isinstance(config, dict)

    def test_default_mode_is_assistant(self):
        copilot = EliteCopilot()
        config = copilot._load_config(None)
        assert config["mode"] == "assistant"

    def test_nonexistent_config_uses_defaults(self):
        copilot = EliteCopilot(config_path="/nonexistent/config.yml")
        assert copilot.mode == CopilotMode.ASSISTANT


class TestAnalyzeRepository:
    def test_returns_dict(self, tmp_path):
        copilot = EliteCopilot()
        result = copilot.analyze_repository(str(tmp_path))
        assert isinstance(result, dict)

    def test_health_score_in_result(self, tmp_path):
        copilot = EliteCopilot()
        result = copilot.analyze_repository(str(tmp_path))
        assert "health_score" in result
        assert 0 <= result["health_score"] <= 100

    def test_insights_in_result(self, tmp_path):
        copilot = EliteCopilot()
        result = copilot.analyze_repository(str(tmp_path))
        assert isinstance(result["insights"], list)

    def test_recommendations_in_result(self, tmp_path):
        copilot = EliteCopilot()
        result = copilot.analyze_repository(str(tmp_path))
        assert isinstance(result["recommendations"], list)


class TestCalculateHealthScore:
    def test_no_insights_returns_default(self):
        copilot = EliteCopilot()
        score = copilot._calculate_health_score([])
        assert score == 75.0

    def test_critical_insight_reduces_score(self):
        copilot = EliteCopilot()
        critical = CopilotInsight(
            category="security",
            severity="critical",
            title="Critical issue",
            description="Found XSS",
            suggested_action="Fix it",
            confidence=0.99,
            evidence=["Found in auth.py"],
        )
        score = copilot._calculate_health_score([critical])
        assert score == 85.0  # 100 - 15

    def test_multiple_issues_reduce_score(self):
        copilot = EliteCopilot()
        insights = [
            CopilotInsight("sec", "high", "High issue", "", "", 0.9, []),
            CopilotInsight("sec", "medium", "Med issue", "", "", 0.8, []),
            CopilotInsight("sec", "low", "Low issue", "", "", 0.7, []),
        ]
        score = copilot._calculate_health_score(insights)
        expected = 100 - 10 - 5 - 2
        assert score == expected

    def test_score_clamped_to_zero(self):
        copilot = EliteCopilot()
        insights = [
            CopilotInsight("sec", "critical", "Critical", "", "", 0.9, [])
            for _ in range(20)
        ]
        score = copilot._calculate_health_score(insights)
        assert score == 0

    def test_info_severity_not_deducted(self):
        copilot = EliteCopilot()
        info = CopilotInsight("cat", "info", "Info", "", "", 0.9, [])
        score = copilot._calculate_health_score([info])
        assert score == 100.0


class TestGenerateRecommendations:
    def test_no_insights_returns_positive(self):
        copilot = EliteCopilot()
        recs = copilot._generate_recommendations([])
        assert len(recs) == 1
        assert "✅" in recs[0]

    def test_high_insights_generate_recommendation(self):
        copilot = EliteCopilot()
        insights = [
            CopilotInsight("security", "high", "SQL injection", "", "", 0.9, [])
        ]
        recs = copilot._generate_recommendations(insights)
        assert any("security" in r for r in recs)


class TestProvideAssistance:
    def test_returns_string(self):
        copilot = EliteCopilot()
        response = copilot.provide_assistance("How do I improve test coverage?")
        assert isinstance(response, str)

    def test_response_contains_query(self):
        copilot = EliteCopilot()
        response = copilot.provide_assistance("fix the bug")
        assert "fix the bug" in response


class TestGenerateReport:
    def test_creates_report_file(self, tmp_path):
        copilot = EliteCopilot()
        analysis = copilot.analyze_repository(str(tmp_path))
        output = str(tmp_path / "report.md")
        copilot.generate_report(analysis, output)
        assert Path(output).exists()

    def test_report_contains_header(self, tmp_path):
        copilot = EliteCopilot()
        analysis = copilot.analyze_repository(str(tmp_path))
        output = str(tmp_path / "report.md")
        copilot.generate_report(analysis, output)
        content = Path(output).read_text()
        assert "Elite AI Copilot" in content or "Copilot" in content
