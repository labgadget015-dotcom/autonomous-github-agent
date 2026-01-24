#!/usr/bin/env python3
"""
Tests for Elite AI Copilot

Validates core functionality of the elite copilot system.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / '.github' / 'scripts'))

from elite_copilot import (
    EliteCopilot,
    CopilotMode,
    TaskPriority,
    CopilotTask,
    CopilotInsight
)


class TestEliteCopilot:
    """Test suite for Elite Copilot"""
    
    def test_copilot_initialization(self):
        """Test copilot initializes correctly"""
        copilot = EliteCopilot()
        
        assert copilot is not None
        assert copilot.mode == CopilotMode.ASSISTANT
        assert copilot.session_id is not None
        assert copilot.session_id.startswith('copilot_')
    
    def test_copilot_modes(self):
        """Test all copilot modes are available"""
        modes = [mode.value for mode in CopilotMode]
        
        assert 'assistant' in modes
        assert 'autopilot' in modes
        assert 'guardian' in modes
        assert 'mentor' in modes
    
    def test_task_priority_levels(self):
        """Test task priority levels"""
        priorities = [p.value for p in TaskPriority]
        
        assert 'critical' in priorities
        assert 'high' in priorities
        assert 'medium' in priorities
        assert 'low' in priorities
    
    def test_copilot_task_creation(self):
        """Test creating a copilot task"""
        task = CopilotTask(
            id="test_1",
            type="code_review",
            description="Review PR #123",
            priority=TaskPriority.HIGH,
            context={'pr_number': 123},
            mode=CopilotMode.ASSISTANT,
            created_at="2024-01-01T00:00:00"
        )
        
        assert task.id == "test_1"
        assert task.type == "code_review"
        assert task.priority == TaskPriority.HIGH
        assert task.status == "pending"
        
        # Test serialization
        task_dict = task.to_dict()
        assert task_dict['priority'] == 'high'
        assert task_dict['mode'] == 'assistant'
    
    def test_copilot_insight_creation(self):
        """Test creating a copilot insight"""
        insight = CopilotInsight(
            category="security",
            severity="high",
            title="Potential vulnerability detected",
            description="Possible SQL injection",
            suggested_action="Use parameterized queries",
            confidence=0.95,
            evidence=["Line 42: direct string interpolation"]
        )
        
        assert insight.category == "security"
        assert insight.severity == "high"
        assert insight.confidence == 0.95
        assert len(insight.evidence) == 1
    
    def test_repository_analysis(self, tmp_path):
        """Test repository analysis functionality"""
        copilot = EliteCopilot()
        
        # Create a temporary repo directory
        repo_path = tmp_path / "test_repo"
        repo_path.mkdir()
        
        # Create some test files
        (repo_path / "README.md").write_text("# Test Repo")
        (repo_path / "main.py").write_text("print('hello')")
        
        # Run analysis
        results = copilot.analyze_repository(str(repo_path))
        
        assert results is not None
        assert 'repository' in results
        assert 'health_score' in results
        assert 'insights' in results
        assert 'recommendations' in results
        assert isinstance(results['insights'], list)
        assert isinstance(results['recommendations'], list)
    
    def test_health_score_calculation(self):
        """Test health score calculation"""
        copilot = EliteCopilot()
        
        # Test with no insights (should be high)
        score = copilot._calculate_health_score([])
        assert score == 75.0
        
        # Test with critical insight
        insights = [
            CopilotInsight(
                category="security",
                severity="critical",
                title="Critical issue",
                description="Test",
                suggested_action="Fix it",
                confidence=1.0,
                evidence=[]
            )
        ]
        score = copilot._calculate_health_score(insights)
        assert score < 100.0  # Should reduce from baseline
        
        # Test with multiple insights
        insights.append(
            CopilotInsight(
                category="quality",
                severity="medium",
                title="Medium issue",
                description="Test",
                suggested_action="Fix it",
                confidence=0.8,
                evidence=[]
            )
        )
        score = copilot._calculate_health_score(insights)
        assert 0 <= score <= 100
    
    def test_recommendations_generation(self):
        """Test generating recommendations from insights"""
        copilot = EliteCopilot()
        
        # Test with no insights
        recommendations = copilot._generate_recommendations([])
        assert len(recommendations) > 0
        assert "excellent shape" in recommendations[0].lower()
        
        # Test with high-severity insights
        insights = [
            CopilotInsight(
                category="security",
                severity="high",
                title="Security issue",
                description="Test",
                suggested_action="Fix",
                confidence=0.9,
                evidence=[]
            ),
            CopilotInsight(
                category="performance",
                severity="critical",
                title="Perf issue",
                description="Test",
                suggested_action="Fix",
                confidence=0.95,
                evidence=[]
            )
        ]
        
        recommendations = copilot._generate_recommendations(insights)
        assert len(recommendations) > 0
        assert any('security' in r.lower() for r in recommendations)
    
    def test_assistance_provision(self):
        """Test providing assistance"""
        copilot = EliteCopilot()
        
        response = copilot.provide_assistance("How do I improve code quality?")
        
        assert response is not None
        assert isinstance(response, str)
        assert len(response) > 0
        assert "copilot" in response.lower() or "assist" in response.lower()
    
    def test_task_creation_from_insights(self):
        """Test creating tasks from insights"""
        copilot = EliteCopilot()
        
        insights = [
            CopilotInsight(
                category="security",
                severity="critical",
                title="Fix vulnerability",
                description="SQL injection",
                suggested_action="Use parameterized queries",
                confidence=0.99,
                evidence=["Line 42"]
            ),
            CopilotInsight(
                category="quality",
                severity="low",
                title="Minor issue",
                description="Formatting",
                suggested_action="Run formatter",
                confidence=0.7,
                evidence=[]
            )
        ]
        
        tasks = copilot._create_tasks_from_insights(insights)
        
        assert len(tasks) == 2
        assert tasks[0].priority == TaskPriority.CRITICAL
        assert tasks[1].priority == TaskPriority.LOW
        assert all(isinstance(task, CopilotTask) for task in tasks)
    
    def test_config_loading(self, tmp_path):
        """Test configuration loading"""
        # Test default config
        copilot = EliteCopilot()
        assert copilot.config is not None
        assert 'mode' in copilot.config
        assert 'capabilities' in copilot.config
        
        # Test with custom config
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("""
mode: autopilot
enable_proactive_analysis: true
max_parallel_tasks: 10
""")
        
        copilot = EliteCopilot(config_path=str(config_file))
        assert copilot.config['mode'] == 'autopilot'
        assert copilot.config['max_parallel_tasks'] == 10
    
    def test_report_generation(self, tmp_path):
        """Test report generation"""
        copilot = EliteCopilot()
        
        # Create test analysis results
        results = {
            'repository': 'test/repo',
            'health_score': 85.5,
            'insights': [
                CopilotInsight(
                    category="security",
                    severity="info",
                    title="All good",
                    description="No issues",
                    suggested_action="Continue monitoring",
                    confidence=0.9,
                    evidence=[]
                )
            ],
            'recommendations': ['Keep up the good work']
        }
        
        output_path = tmp_path / "test_report.md"
        copilot.generate_report(results, str(output_path))
        
        assert output_path.exists()
        content = output_path.read_text()
        assert "Elite AI Copilot Analysis Report" in content
        assert "Health Score" in content
        assert "85.5" in content


class TestCopilotIntegration:
    """Integration tests for copilot system"""
    
    @pytest.mark.asyncio
    async def test_full_integration_flow(self, tmp_path):
        """Test full copilot integration flow"""
        # This would test the copilot_integration.py module
        # For now, just verify the module can be imported
        from copilot_integration import CopilotHub
        
        hub = CopilotHub()
        assert hub is not None
        assert hub.session_id is not None


class TestCopilotModes:
    """Test different copilot operating modes"""
    
    def test_assistant_mode(self):
        """Test assistant mode behavior"""
        copilot = EliteCopilot()
        copilot.mode = CopilotMode.ASSISTANT
        
        assert copilot.mode == CopilotMode.ASSISTANT
        # In assistant mode, should provide suggestions but not execute
    
    def test_autopilot_mode(self):
        """Test autopilot mode behavior"""
        copilot = EliteCopilot()
        copilot.mode = CopilotMode.AUTOPILOT
        
        assert copilot.mode == CopilotMode.AUTOPILOT
        # In autopilot mode, should execute with approval gates
    
    def test_guardian_mode(self):
        """Test guardian mode behavior"""
        copilot = EliteCopilot()
        copilot.mode = CopilotMode.GUARDIAN
        
        assert copilot.mode == CopilotMode.GUARDIAN
        # In guardian mode, should monitor and prevent issues
    
    def test_mentor_mode(self):
        """Test mentor mode behavior"""
        copilot = EliteCopilot()
        copilot.mode = CopilotMode.MENTOR
        
        assert copilot.mode == CopilotMode.MENTOR
        # In mentor mode, should provide educational content


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
