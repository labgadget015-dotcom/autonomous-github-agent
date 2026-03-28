"""Tests for remaining .github/scripts/ modules to achieve 80% coverage."""
import asyncio
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.github', 'scripts'))


# ===========================================================================
# ai_agent_main.py
# ===========================================================================

class TestAIAgentMain:
    def test_load_context_valid(self, tmp_path):
        from ai_agent_main import load_context
        ctx = {'repository': 'owner/repo', 'event_name': 'push'}
        f = tmp_path / 'context.json'
        f.write_text(json.dumps(ctx))
        result = load_context(str(f))
        assert result == ctx

    def test_load_context_missing_file(self):
        from ai_agent_main import load_context
        result = load_context('/nonexistent/path.json')
        assert result == {}

    def test_load_context_invalid_json(self, tmp_path):
        from ai_agent_main import load_context
        f = tmp_path / 'bad.json'
        f.write_text('not json')
        result = load_context(str(f))
        assert result == {}

    def test_run_ai_agent_returns_success(self, tmp_path, monkeypatch):
        from ai_agent_main import run_ai_agent
        monkeypatch.chdir(tmp_path)
        ctx = {'repository': 'owner/repo', 'event_name': 'push', 'ref': 'main', 'actor': 'bot'}
        result = run_ai_agent(ctx)
        assert result['status'] == 'success'
        assert 'agent_actions' in result
        assert 'recommendations' in result

    def test_run_ai_agent_saves_results_file(self, tmp_path, monkeypatch):
        from ai_agent_main import run_ai_agent
        monkeypatch.chdir(tmp_path)
        run_ai_agent({})
        assert (tmp_path / 'results.json').exists()

    def test_run_ai_agent_unknown_context_fields(self, tmp_path, monkeypatch, capsys):
        from ai_agent_main import run_ai_agent
        monkeypatch.chdir(tmp_path)
        run_ai_agent({})
        out = capsys.readouterr().out
        assert 'unknown' in out


# ===========================================================================
# check_policy.py
# ===========================================================================

class TestCheckPolicy:
    def test_check_policies_no_results_file(self, tmp_path, monkeypatch):
        from check_policy import check_policies
        monkeypatch.chdir(tmp_path)
        audit = check_policies()
        assert audit['status'] == 'passed'
        assert 'Results file not found' in audit['warnings']

    def test_check_policies_with_results_file(self, tmp_path, monkeypatch):
        from check_policy import check_policies
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'results.json').write_text(json.dumps({'status': 'success'}))
        audit = check_policies()
        assert audit['status'] == 'passed'
        assert len(audit['violations']) == 0

    def test_check_policies_saves_audit_log(self, tmp_path, monkeypatch):
        from check_policy import check_policies
        monkeypatch.chdir(tmp_path)
        check_policies()
        assert (tmp_path / 'audit.log').exists()

    def test_check_policies_audit_structure(self, tmp_path, monkeypatch):
        from check_policy import check_policies
        monkeypatch.chdir(tmp_path)
        audit = check_policies()
        assert 'policies' in audit
        assert 'violations' in audit
        assert 'warnings' in audit
        assert 'status' in audit


# ===========================================================================
# cot_selector.py
# ===========================================================================

class TestCoTSelector:
    @pytest.fixture
    def selector(self):
        from cot_selector import CoTSelector
        return CoTSelector()  # uses default fallback config

    def test_zero_shot_for_simple(self, selector):
        from cot_selector import CoTTemplate
        result = selector.select_template({'files_changed': 1, 'lines_changed': 10})
        assert result == CoTTemplate.ZERO_SHOT

    def test_few_shot_for_moderate(self, selector):
        from cot_selector import CoTTemplate
        result = selector.select_template({'files_changed': 12, 'lines_changed': 10})
        assert result == CoTTemplate.FEW_SHOT

    def test_compositional_for_complex(self, selector):
        from cot_selector import CoTTemplate
        result = selector.select_template({'files_changed': 12, 'lines_changed': 600})
        assert result == CoTTemplate.COMPOSITIONAL

    def test_security_label_adds_score(self, selector):
        # files_changed>10 (+0.3) + lines_changed>500 (+0.3) + security (+0.2) = 0.8 >= 0.6 → COMPOSITIONAL
        from cot_selector import CoTTemplate
        result = selector.select_template({'files_changed': 12, 'lines_changed': 600, 'labels': ['security']})
        assert result == CoTTemplate.COMPOSITIONAL

    def test_analyze_complexity_no_context(self, selector):
        score = selector._analyze_complexity({})
        assert score == 0.0

    def test_analyze_complexity_files_changed(self, selector):
        score = selector._analyze_complexity({'files_changed': 11})
        assert score == pytest.approx(0.3)

    def test_analyze_complexity_lines_changed(self, selector):
        score = selector._analyze_complexity({'lines_changed': 501})
        assert score == pytest.approx(0.3)

    def test_analyze_complexity_max_score(self, selector):
        # max achievable: files(+0.3) + lines(+0.3) + security(+0.2) = 0.8
        score = selector._analyze_complexity({
            'files_changed': 20, 'lines_changed': 1000, 'labels': ['security']
        })
        assert score == pytest.approx(0.8)

    def test_loads_fallback_config_on_missing_file(self):
        from cot_selector import CoTSelector
        selector = CoTSelector(config_path=Path('/nonexistent/policy.yml'))
        assert selector.config is not None
        assert 'ai_agent' in selector.config


# ===========================================================================
# docgen.py
# ===========================================================================

class TestDocgen:
    def test_generates_autodoc_md(self, tmp_path, monkeypatch):
        from docgen import generate_documentation
        monkeypatch.chdir(tmp_path)
        result = generate_documentation()
        assert result is True
        assert (tmp_path / 'AUTODOC.md').exists()

    def test_generates_diagram_file(self, tmp_path, monkeypatch):
        from docgen import generate_documentation
        monkeypatch.chdir(tmp_path)
        generate_documentation()
        assert (tmp_path / 'diagrams' / 'workflow.txt').exists()

    def test_autodoc_content(self, tmp_path, monkeypatch):
        from docgen import generate_documentation
        monkeypatch.chdir(tmp_path)
        generate_documentation()
        content = (tmp_path / 'AUTODOC.md').read_text()
        assert 'Automated Documentation' in content

    def test_creates_diagrams_dir(self, tmp_path, monkeypatch):
        from docgen import generate_documentation
        monkeypatch.chdir(tmp_path)
        generate_documentation()
        assert (tmp_path / 'diagrams').is_dir()


# ===========================================================================
# gather_context.py
# ===========================================================================

class TestGatherContext:
    def test_reads_github_env_vars(self, tmp_path, monkeypatch):
        from gather_context import gather_repo_context
        monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/repo')
        monkeypatch.setenv('GITHUB_EVENT_NAME', 'push')
        monkeypatch.setenv('GITHUB_REF', 'refs/heads/main')
        monkeypatch.setenv('GITHUB_SHA', 'abc123')
        monkeypatch.setenv('GITHUB_ACTOR', 'bot')
        monkeypatch.setenv('GITHUB_WORKFLOW', 'ci')
        monkeypatch.setenv('GITHUB_WORKSPACE', str(tmp_path))
        ctx = gather_repo_context()
        assert ctx['repository'] == 'owner/repo'
        assert ctx['event_name'] == 'push'
        assert ctx['actor'] == 'bot'

    def test_saves_context_json(self, tmp_path, monkeypatch):
        from gather_context import gather_repo_context
        monkeypatch.setenv('GITHUB_WORKSPACE', str(tmp_path))
        gather_repo_context()
        assert (tmp_path / 'context.json').exists()

    def test_files_list_capped_at_100(self, tmp_path, monkeypatch):
        from gather_context import gather_repo_context
        # Create 150 files
        for i in range(150):
            (tmp_path / f'file{i}.txt').write_text('x')
        monkeypatch.setenv('GITHUB_WORKSPACE', str(tmp_path))
        ctx = gather_repo_context()
        assert len(ctx['files']) <= 100

    def test_defaults_to_unknown_when_env_missing(self, tmp_path, monkeypatch):
        from gather_context import gather_repo_context
        for var in ['GITHUB_REPOSITORY', 'GITHUB_EVENT_NAME', 'GITHUB_REF',
                    'GITHUB_SHA', 'GITHUB_ACTOR', 'GITHUB_WORKFLOW']:
            monkeypatch.delenv(var, raising=False)
        monkeypatch.setenv('GITHUB_WORKSPACE', str(tmp_path))
        ctx = gather_repo_context()
        assert ctx['repository'] == 'unknown'


# ===========================================================================
# test_runner.py (the script, not pytest)
# ===========================================================================

class TestTestRunner:
    def test_run_tests_returns_true(self):
        from test_runner import run_tests
        assert run_tests() is True

    def test_run_tests_prints_summary(self, capsys):
        from test_runner import run_tests
        run_tests()
        out = capsys.readouterr().out
        assert 'Passed' in out
        assert 'Failed' in out
        assert 'Skipped' in out

    def test_run_tests_counts_passed(self, capsys):
        from test_runner import run_tests
        run_tests()
        out = capsys.readouterr().out
        assert 'Passed: 1' in out


# ===========================================================================
# error_handler.py
# ===========================================================================

class TestErrorHandler:
    def test_no_input_files_returns_success(self, tmp_path, monkeypatch):
        from error_handler import handle_errors
        monkeypatch.chdir(tmp_path)
        report = handle_errors()
        assert report['status'] == 'success'
        assert report['branch_decision'] == 'continue'

    def test_with_audit_violations_returns_failed(self, tmp_path, monkeypatch):
        from error_handler import handle_errors
        monkeypatch.chdir(tmp_path)
        audit = {'violations': ['missing tests'], 'warnings': []}
        (tmp_path / 'audit.log').write_text(json.dumps(audit))
        report = handle_errors()
        assert report['status'] == 'failed'
        assert report['branch_decision'] == 'stop'
        assert 'missing tests' in report['errors']

    def test_with_audit_warnings_only_still_success(self, tmp_path, monkeypatch):
        from error_handler import handle_errors
        monkeypatch.chdir(tmp_path)
        audit = {'violations': [], 'warnings': ['consider upgrading']}
        (tmp_path / 'audit.log').write_text(json.dumps(audit))
        report = handle_errors()
        assert report['status'] == 'success'
        assert 'consider upgrading' in report['warnings']

    def test_failed_results_json_adds_error(self, tmp_path, monkeypatch):
        from error_handler import handle_errors
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'results.json').write_text(json.dumps({'status': 'failure'}))
        report = handle_errors()
        assert report['status'] == 'failed'
        assert any('non-success' in e for e in report['errors'])

    def test_success_results_json_no_error(self, tmp_path, monkeypatch):
        from error_handler import handle_errors
        monkeypatch.chdir(tmp_path)
        (tmp_path / 'results.json').write_text(json.dumps({'status': 'success'}))
        report = handle_errors()
        assert report['status'] == 'success'

    def test_saves_error_report_json(self, tmp_path, monkeypatch):
        from error_handler import handle_errors
        monkeypatch.chdir(tmp_path)
        handle_errors()
        assert (tmp_path / 'error_report.json').exists()


# ===========================================================================
# issue_auto_creator.py
# ===========================================================================

ENV_ISSUE = {'GITHUB_TOKEN': 'ghp_test', 'GITHUB_REPOSITORY': 'owner/repo'}


@pytest.fixture
def creator(monkeypatch):
    for k, v in ENV_ISSUE.items():
        monkeypatch.setenv(k, v)
    from issue_auto_creator import IssueAutoCreator
    return IssueAutoCreator()


class TestIssueAutoCreator:
    def test_init_reads_env(self, creator):
        assert creator.github_token == 'ghp_test'
        assert creator.repo == 'owner/repo'

    def test_init_missing_env_exits(self, monkeypatch):
        monkeypatch.delenv('GITHUB_TOKEN', raising=False)
        monkeypatch.delenv('GITHUB_REPOSITORY', raising=False)
        from issue_auto_creator import IssueAutoCreator
        with pytest.raises(SystemExit):
            IssueAutoCreator()

    def test_check_quality_missing_file(self, creator, tmp_path):
        issues = creator.check_quality_metrics(tmp_path / 'missing.json')
        assert issues == []

    def test_check_quality_below_threshold(self, creator, tmp_path):
        data = {'quality_score': 5.0}
        f = tmp_path / 'summary.json'
        f.write_text(json.dumps(data))
        issues = creator.check_quality_metrics(f)
        assert any('Quality' in i['title'] for i in issues)

    def test_check_quality_above_threshold_no_issue(self, creator, tmp_path):
        data = {'quality_score': 9.0}
        f = tmp_path / 'summary.json'
        f.write_text(json.dumps(data))
        issues = creator.check_quality_metrics(f)
        assert not any('Quality' in i['title'] for i in issues)

    def test_check_security_high_severity_creates_issue(self, creator, tmp_path):
        data = {'security': {'high': 3, 'medium': 1, 'low': 0}}
        f = tmp_path / 'summary.json'
        f.write_text(json.dumps(data))
        issues = creator.check_quality_metrics(f)
        assert any('Security' in i['title'] for i in issues)

    def test_check_security_no_high_no_issue(self, creator, tmp_path):
        data = {'security': {'high': 0, 'medium': 2, 'low': 5}}
        f = tmp_path / 'summary.json'
        f.write_text(json.dumps(data))
        issues = creator.check_quality_metrics(f)
        assert not any('Security' in i['title'] for i in issues)

    def test_check_complexity_over_5_creates_issue(self, creator, tmp_path):
        data = {'high_complexity_functions': [{'name': f'fn{i}', 'complexity': 15} for i in range(6)]}
        f = tmp_path / 'summary.json'
        f.write_text(json.dumps(data))
        issues = creator.check_quality_metrics(f)
        assert any('Complexity' in i['title'] for i in issues)

    def test_check_complexity_5_or_fewer_no_issue(self, creator, tmp_path):
        data = {'high_complexity_functions': [{'name': 'fn', 'complexity': 15}] * 5}
        f = tmp_path / 'summary.json'
        f.write_text(json.dumps(data))
        issues = creator.check_quality_metrics(f)
        assert not any('Complexity' in i['title'] for i in issues)

    def test_generate_quality_body_contains_score(self, creator):
        body = creator._generate_quality_issue_body({'pylint_issues': 5}, 4.5)
        assert '4.5' in body
        assert 'Pylint' in body

    def test_generate_security_body_contains_counts(self, creator):
        body = creator._generate_security_issue_body({'high': 3, 'medium': 2, 'low': 1})
        assert '3' in body
        assert 'HIGH' in body

    def test_generate_complexity_body_lists_functions(self, creator):
        fns = [{'name': f'fn{i}', 'complexity': 15 + i} for i in range(3)]
        body = creator._generate_complexity_issue_body(fns)
        assert 'fn0' in body
        assert 'fn1' in body

    def test_generate_complexity_body_caps_at_10(self, creator):
        fns = [{'name': f'fn{i}', 'complexity': 20} for i in range(15)]
        body = creator._generate_complexity_issue_body(fns)
        assert 'fn9' in body
        assert 'fn10' not in body

    def test_create_issues_no_issues(self, creator, capsys):
        with patch.object(creator, '_make_request') as mock_req:
            creator.create_issues([])
        mock_req.assert_not_called()
        assert 'No issues' in capsys.readouterr().out

    def test_create_issues_successful(self, creator, capsys):
        with patch.object(creator, '_make_request', return_value={'number': 42}):
            creator.create_issues([{'title': 'Test Issue', 'body': 'body', 'labels': []}])
        assert '#42' in capsys.readouterr().out

    def test_create_issues_failed_api(self, creator, capsys):
        with patch.object(creator, '_make_request', return_value=None):
            creator.create_issues([{'title': 'Test', 'body': 'b', 'labels': []}])
        assert 'Failed' in capsys.readouterr().out

    def test_make_request_success(self, creator):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'number': 1}
        with patch('requests.post', return_value=mock_resp):
            result = creator._make_request('issues', {'title': 'x'})
        assert result == {'number': 1}

    def test_make_request_failure_returns_none(self, creator):
        import requests
        with patch('requests.post', side_effect=requests.exceptions.RequestException('err')):
            result = creator._make_request('issues', {})
        assert result is None

    def test_run_no_issues(self, creator, tmp_path, capsys):
        data = {'quality_score': 9.0}
        f = tmp_path / 'summary.json'
        f.write_text(json.dumps(data))
        with patch.object(creator, '_make_request'):
            creator.run(f)
        assert 'All metrics' in capsys.readouterr().out


# ===========================================================================
# async_parallel_analyzer.py
# ===========================================================================

class TestAsyncParallelAnalyzer:
    @pytest.fixture
    def analyzer(self, tmp_path):
        from async_parallel_analyzer import AsyncParallelAnalyzer
        a = AsyncParallelAnalyzer(str(tmp_path))
        a.reports_dir = tmp_path / 'reports'
        a.reports_dir.mkdir()
        return a

    def test_count_issues_pylint(self, analyzer):
        # _count_issues splits on literal '\\n' (escaped), so use that
        output = "file.py:1:0: warning\\nfile.py:2:0: error\\n* summary"
        assert analyzer._count_issues('pylint', output) == 2

    def test_count_issues_flake8(self, analyzer):
        output = "file.py:1:1: E501 line too long\\nfile.py:2:1: W291 trailing"
        assert analyzer._count_issues('flake8', output) == 2

    def test_count_issues_bandit(self, analyzer):
        output = ">> Issue: [B101] use of assert\n>> Issue: [B102] exec used"
        assert analyzer._count_issues('bandit', output) == 2

    def test_count_issues_mypy(self, analyzer):
        output = "file.py:1: error: incompatible\nfile.py:2: error: missing"
        assert analyzer._count_issues('mypy', output) == 2

    def test_count_issues_empty_output(self, analyzer):
        assert analyzer._count_issues('pylint', '') == 0

    def test_count_issues_unknown_tool(self, analyzer):
        assert analyzer._count_issues('unknown', 'some output') == 0

    def test_generate_summary_structure(self, analyzer):
        from async_parallel_analyzer import AnalysisResult
        results = [
            AnalysisResult('pylint', True, 1.5, 'output', '', 3),
            AnalysisResult('flake8', False, 0.5, '', 'error', 0),
        ]
        summary = analyzer.generate_summary(results)
        assert summary['total_tools'] == 2
        assert summary['successful'] == 1
        assert summary['failed'] == 1
        assert summary['total_issues'] == 3
        assert len(summary['results']) == 2

    def test_generate_summary_duration(self, analyzer):
        from async_parallel_analyzer import AnalysisResult
        results = [
            AnalysisResult('t1', True, 1.5, '', '', 0),
            AnalysisResult('t2', True, 2.5, '', '', 0),
        ]
        summary = analyzer.generate_summary(results)
        assert summary['total_duration'] == pytest.approx(4.0)

    def test_save_summary(self, analyzer):
        summary = {'total_tools': 2, 'successful': 2, 'failed': 0,
                   'total_duration': 1.0, 'total_issues': 0, 'results': []}
        analyzer.save_summary(summary)
        saved = json.loads((analyzer.reports_dir / 'analysis-summary.json').read_text())
        assert saved['total_tools'] == 2

    def test_print_summary(self, analyzer, capsys):
        summary = {
            'total_tools': 1, 'successful': 1, 'failed': 0,
            'total_duration': 1.5, 'total_issues': 3,
            'results': [{'tool': 'pylint', 'success': True, 'duration': 1.5, 'issues': 3, 'error': None}]
        }
        analyzer.print_summary(summary)
        out = capsys.readouterr().out
        assert 'ANALYSIS SUMMARY' in out
        assert 'pylint' in out

    def test_print_summary_with_error(self, analyzer, capsys):
        summary = {
            'total_tools': 1, 'successful': 0, 'failed': 1,
            'total_duration': 0.1, 'total_issues': 0,
            'results': [{'tool': 'mypy', 'success': False, 'duration': 0.1, 'issues': 0, 'error': 'timed out'}]
        }
        analyzer.print_summary(summary)
        assert 'timed out' in capsys.readouterr().out

    @pytest.mark.asyncio
    async def test_run_tool_success(self, analyzer):
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = 'all good'
        mock_proc.stderr = ''
        with patch('subprocess.run', return_value=mock_proc):
            result = await analyzer.run_tool('pylint', ['pylint', '.'])
        assert result.success is True
        assert result.tool == 'pylint'

    @pytest.mark.asyncio
    async def test_run_tool_nonzero_exit(self, analyzer):
        mock_proc = MagicMock()
        mock_proc.returncode = 1
        mock_proc.stdout = 'issues found'
        mock_proc.stderr = ''
        with patch('subprocess.run', return_value=mock_proc):
            result = await analyzer.run_tool('flake8', ['flake8', '.'])
        assert result.success is False

    @pytest.mark.asyncio
    async def test_run_tool_timeout(self, analyzer):
        import subprocess
        with patch('subprocess.run', side_effect=subprocess.TimeoutExpired(['cmd'], 300)):
            result = await analyzer.run_tool('slow_tool', ['slow'])
        assert result.success is False
        assert 'Timeout' in result.error

    @pytest.mark.asyncio
    async def test_run_tool_exception(self, analyzer):
        with patch('subprocess.run', side_effect=Exception('binary not found')):
            result = await analyzer.run_tool('missing', ['missing'])
        assert result.success is False
        assert 'binary not found' in result.error


# ===========================================================================
# metrics_collector.py
# ===========================================================================

class TestMetricsCollector:
    @pytest.fixture
    def collector(self):
        from metrics_collector import MetricsCollector
        return MetricsCollector(pushgateway_url='localhost:9091')

    def test_record_workflow_duration(self, collector, capsys):
        collector.record_workflow_duration('ci', 'build', 42.5)
        assert '42.50s' in capsys.readouterr().out

    def test_record_workflow_result_success(self, collector, capsys):
        collector.record_workflow_result('ci', 'build', True)
        assert 'succeeded' in capsys.readouterr().out

    def test_record_workflow_result_failure(self, collector, capsys):
        collector.record_workflow_result('ci', 'build', False)
        assert 'failed' in capsys.readouterr().out

    def test_update_code_quality(self, collector, capsys):
        collector.update_code_quality('pylint', 8.5)
        assert '8.50' in capsys.readouterr().out

    def test_update_test_coverage(self, collector, capsys):
        collector.update_test_coverage('main', 85.0)
        assert '85.00%' in capsys.readouterr().out

    def test_update_security_vulnerabilities(self, collector, capsys):
        collector.update_security_vulnerabilities({'HIGH': 2, 'MEDIUM': 3, 'LOW': 5})
        out = capsys.readouterr().out
        assert 'HIGH' in out
        assert '2' in out

    def test_update_complexity(self, collector, capsys):
        collector.update_complexity('cyclomatic', 7.3)
        assert '7.30' in capsys.readouterr().out

    def test_collect_system_metrics(self, collector, capsys):
        with patch('psutil.cpu_percent', return_value=45.0), \
             patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value.percent = 60.0
            collector.collect_system_metrics()
        out = capsys.readouterr().out
        assert 'CPU' in out
        assert 'Memory' in out

    def test_parse_workflow_metrics_bandit(self, collector, tmp_path):
        data = {'results': [
            {'issue_severity': 'HIGH'}, {'issue_severity': 'MEDIUM'}, {'issue_severity': 'LOW'}
        ]}
        (tmp_path / 'bandit-report.json').write_text(json.dumps(data))
        collector.parse_workflow_metrics(tmp_path)
        # no exception = pass

    def test_parse_workflow_metrics_radon(self, collector, tmp_path):
        data = {'src/foo.py': [{'complexity': 5}, {'complexity': 10}]}
        (tmp_path / 'radon-cc.json').write_text(json.dumps(data))
        collector.parse_workflow_metrics(tmp_path)

    def test_parse_workflow_metrics_pylint_with_score(self, collector, tmp_path):
        data = {'score': 8.5}
        (tmp_path / 'pylint-report.json').write_text(json.dumps(data))
        collector.parse_workflow_metrics(tmp_path)

    def test_parse_workflow_metrics_coverage_xml(self, collector, tmp_path):
        xml = '<?xml version="1.0"?><coverage line-rate="0.85"></coverage>'
        (tmp_path / 'coverage.xml').write_text(xml)
        collector.parse_workflow_metrics(tmp_path)

    def test_parse_workflow_metrics_empty_dir(self, collector, tmp_path):
        # Should not raise
        collector.parse_workflow_metrics(tmp_path)

    def test_push_metrics_failure_handled(self, collector, capsys):
        with patch('prometheus_client.push_to_gateway', side_effect=Exception('refused')):
            collector.push_metrics('test_job')
        assert 'Warning' in capsys.readouterr().out

    def test_push_metrics_success(self, collector, capsys):
        with patch('prometheus_client.push_to_gateway'):
            collector.push_metrics('test_job')
        assert 'Pushgateway' in capsys.readouterr().out

    def test_generate_dashboard_data(self, collector, tmp_path):
        output = tmp_path / 'dashboard.json'
        with patch('psutil.cpu_percent', return_value=30.0), \
             patch('psutil.virtual_memory') as mock_mem:
            mock_mem.return_value.percent = 50.0
            collector.generate_dashboard_data(output)
        data = json.loads(output.read_text())
        assert 'timestamp' in data
        assert 'metrics' in data
