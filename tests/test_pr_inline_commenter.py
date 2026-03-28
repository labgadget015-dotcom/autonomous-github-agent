"""Tests for pr_inline_commenter.py — PR analysis and GitHub integration."""
import json
import os
import sys
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, mock_open

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '.github', 'scripts'))

from pr_inline_commenter import PRInlineCommenter, CodeFinding, PRAnalysis


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ENV_VARS = {
    'GITHUB_TOKEN': 'ghp_test',
    'GITHUB_REPOSITORY': 'owner/repo',
    'PR_NUMBER': '42',
    'COMMIT_SHA': 'abc123',
    'ANTHROPIC_API_KEY': 'sk-ant-test',
}


@pytest.fixture
def commenter(monkeypatch):
    for k, v in ENV_VARS.items():
        monkeypatch.setenv(k, v)
    return PRInlineCommenter()


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

class TestInit:
    def test_reads_env_vars(self, commenter):
        assert commenter.github_token == 'ghp_test'
        assert commenter.repo == 'owner/repo'
        assert commenter.pr_number == '42'
        assert commenter.commit_sha == 'abc123'

    def test_missing_env_exits(self, monkeypatch):
        for k in ENV_VARS:
            monkeypatch.delenv(k, raising=False)
        with pytest.raises(SystemExit):
            PRInlineCommenter()


# ---------------------------------------------------------------------------
# _get_headers()
# ---------------------------------------------------------------------------

class TestGetHeaders:
    def test_contains_auth_header(self, commenter):
        headers = commenter._get_headers()
        assert headers['Authorization'] == 'token ghp_test'
        assert 'Accept' in headers


# ---------------------------------------------------------------------------
# _make_request()
# ---------------------------------------------------------------------------

class TestMakeRequest:
    def test_get_request(self, commenter):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'id': 1}
        mock_resp.text = '{"id": 1}'
        with patch('requests.get', return_value=mock_resp) as mock_get:
            result = commenter._make_request('GET', 'pulls/42')
        mock_get.assert_called_once()
        assert result == {'id': 1}

    def test_post_request(self, commenter):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {'created': True}
        mock_resp.text = '{"created": true}'
        with patch('requests.post', return_value=mock_resp) as mock_post:
            result = commenter._make_request('POST', 'pulls/42/reviews', {'body': 'test'})
        mock_post.assert_called_once()
        assert result == {'created': True}

    def test_unsupported_method_raises(self, commenter):
        with pytest.raises(ValueError, match='Unsupported method'):
            commenter._make_request('DELETE', 'pulls/42')

    def test_request_exception_returns_none(self, commenter):
        import requests
        with patch('requests.get', side_effect=requests.exceptions.RequestException('timeout')):
            result = commenter._make_request('GET', 'pulls/42')
        assert result is None

    def test_empty_response_returns_none(self, commenter):
        mock_resp = MagicMock()
        mock_resp.text = ''
        with patch('requests.get', return_value=mock_resp):
            result = commenter._make_request('GET', 'pulls/42')
        assert result is None


# ---------------------------------------------------------------------------
# _fetch_pr_diff()
# ---------------------------------------------------------------------------

class TestFetchPRDiff:
    def test_returns_diff_text(self, commenter):
        mock_resp = MagicMock()
        mock_resp.text = '--- a/foo.py\n+++ b/foo.py\n@@ -1 +1 @@\n+x = 1'
        with patch('requests.get', return_value=mock_resp):
            diff = commenter._fetch_pr_diff()
        assert 'foo.py' in diff

    def test_caps_at_60000_chars(self, commenter):
        mock_resp = MagicMock()
        mock_resp.text = 'x' * 100000
        with patch('requests.get', return_value=mock_resp):
            diff = commenter._fetch_pr_diff()
        assert len(diff) == 60000

    def test_request_error_returns_empty(self, commenter):
        import requests
        with patch('requests.get', side_effect=requests.exceptions.RequestException('err')):
            diff = commenter._fetch_pr_diff()
        assert diff == ''


# ---------------------------------------------------------------------------
# analyze_diff_with_claude()
# ---------------------------------------------------------------------------

class TestAnalyzeDiffWithClaude:
    def test_returns_empty_when_no_api_key(self, commenter, monkeypatch):
        monkeypatch.delenv('ANTHROPIC_API_KEY', raising=False)
        result = commenter.analyze_diff_with_claude('diff content')
        assert result == []

    def test_returns_empty_when_diff_is_empty(self, commenter):
        result = commenter.analyze_diff_with_claude('')
        assert result == []

    def test_successful_analysis(self, commenter):
        finding = CodeFinding(
            path='src/auth.py',
            line=42,
            severity='HIGH',
            category='security',
            message='SQL injection risk',
            suggestion='Use parameterised queries'
        )
        parsed = PRAnalysis(findings=[finding])
        mock_response = MagicMock()
        mock_response.parsed_output = parsed

        with patch('anthropic.Anthropic') as MockClient:
            MockClient.return_value.messages.parse.return_value = mock_response
            results = commenter.analyze_diff_with_claude('diff content')

        assert len(results) == 1
        assert results[0]['path'] == 'src/auth.py'
        assert results[0]['line'] == 42
        assert results[0]['severity'] == 'HIGH'
        assert '🔴' in results[0]['body']
        assert 'SQL injection' in results[0]['body']

    def test_severity_icons(self, commenter):
        findings = [
            CodeFinding(path='a.py', line=1, severity='HIGH', category='security', message='h', suggestion='s'),
            CodeFinding(path='b.py', line=2, severity='MEDIUM', category='bug', message='m', suggestion='s'),
            CodeFinding(path='c.py', line=3, severity='LOW', category='style', message='l', suggestion='s'),
        ]
        parsed = PRAnalysis(findings=findings)
        mock_response = MagicMock()
        mock_response.parsed_output = parsed

        with patch('anthropic.Anthropic') as MockClient:
            MockClient.return_value.messages.parse.return_value = mock_response
            results = commenter.analyze_diff_with_claude('diff')

        assert '🔴' in results[0]['body']
        assert '🟡' in results[1]['body']
        assert '🟢' in results[2]['body']

    def test_none_parsed_output_returns_empty(self, commenter):
        mock_response = MagicMock()
        mock_response.parsed_output = None
        with patch('anthropic.Anthropic') as MockClient:
            MockClient.return_value.messages.parse.return_value = mock_response
            results = commenter.analyze_diff_with_claude('diff')
        assert results == []

    def test_api_exception_returns_empty(self, commenter):
        with patch('anthropic.Anthropic') as MockClient:
            MockClient.return_value.messages.parse.side_effect = Exception('API error')
            results = commenter.analyze_diff_with_claude('diff')
        assert results == []

    def test_uses_cache_control_on_system_prompt(self, commenter):
        mock_response = MagicMock()
        mock_response.parsed_output = PRAnalysis(findings=[])
        with patch('anthropic.Anthropic') as MockClient:
            mock_parse = MockClient.return_value.messages.parse
            mock_parse.return_value = mock_response
            commenter.analyze_diff_with_claude('diff')
            call_kwargs = mock_parse.call_args[1]
            system = call_kwargs['system']
            assert system[0]['cache_control'] == {'type': 'ephemeral'}


# ---------------------------------------------------------------------------
# parse_pylint_report()
# ---------------------------------------------------------------------------

class TestParsePylintReport:
    def test_parses_valid_report(self, commenter, tmp_path):
        data = [{'path': './src/foo.py', 'line': 10, 'message': 'unused import', 'message-id': 'W0611', 'type': 'warning'}]
        report = tmp_path / 'pylint.json'
        report.write_text(json.dumps(data))

        results = commenter.parse_pylint_report(report)
        assert len(results) == 1
        assert results[0]['path'] == 'src/foo.py'
        assert results[0]['line'] == 10
        assert 'unused import' in results[0]['body']

    def test_strips_dot_slash_prefix(self, commenter, tmp_path):
        data = [{'path': './module/bar.py', 'line': 5, 'message': 'msg', 'message-id': 'C0001', 'type': 'convention'}]
        report = tmp_path / 'pylint.json'
        report.write_text(json.dumps(data))
        results = commenter.parse_pylint_report(report)
        assert results[0]['path'] == 'module/bar.py'

    def test_missing_file_returns_empty(self, commenter, tmp_path):
        results = commenter.parse_pylint_report(tmp_path / 'nonexistent.json')
        assert results == []

    def test_invalid_json_returns_empty(self, commenter, tmp_path):
        report = tmp_path / 'pylint.json'
        report.write_text('not json')
        results = commenter.parse_pylint_report(report)
        assert results == []


# ---------------------------------------------------------------------------
# parse_bandit_report()
# ---------------------------------------------------------------------------

class TestParseBanditReport:
    def _make_report(self, tmp_path, severity='HIGH'):
        data = {'results': [{'filename': './src/auth.py', 'line_number': 20,
                              'issue_text': 'hardcoded password', 'issue_severity': severity,
                              'issue_confidence': 'HIGH', 'test_id': 'B105', 'code': 'pwd = "secret"'}]}
        report = tmp_path / 'bandit.json'
        report.write_text(json.dumps(data))
        return report

    def test_parses_high_severity(self, commenter, tmp_path):
        results = commenter.parse_bandit_report(self._make_report(tmp_path, 'HIGH'))
        assert len(results) == 1
        assert '🔴' in results[0]['body']
        assert results[0]['severity'] == 'HIGH'
        assert results[0]['path'] == 'src/auth.py'

    def test_parses_medium_severity(self, commenter, tmp_path):
        results = commenter.parse_bandit_report(self._make_report(tmp_path, 'MEDIUM'))
        assert '🟡' in results[0]['body']

    def test_parses_low_severity(self, commenter, tmp_path):
        results = commenter.parse_bandit_report(self._make_report(tmp_path, 'LOW'))
        assert '🟢' in results[0]['body']

    def test_missing_file_returns_empty(self, commenter, tmp_path):
        assert commenter.parse_bandit_report(tmp_path / 'missing.json') == []

    def test_invalid_json_returns_empty(self, commenter, tmp_path):
        report = tmp_path / 'bandit.json'
        report.write_text('bad json')
        assert commenter.parse_bandit_report(report) == []


# ---------------------------------------------------------------------------
# parse_radon_report()
# ---------------------------------------------------------------------------

class TestParseRadonReport:
    def _make_report(self, tmp_path, complexity=25):
        data = {'src/complex.py': [{'name': 'big_func', 'lineno': 5, 'complexity': complexity}]}
        report = tmp_path / 'radon-cc.json'
        report.write_text(json.dumps(data))
        return report

    def test_flags_high_complexity(self, commenter, tmp_path):
        results = commenter.parse_radon_report(self._make_report(tmp_path, 25))
        assert len(results) == 1
        assert 'big_func' in results[0]['body']
        assert results[0]['path'] == 'src/complex.py'

    def test_skips_low_complexity(self, commenter, tmp_path):
        results = commenter.parse_radon_report(self._make_report(tmp_path, 5))
        assert results == []

    def test_boundary_complexity_skipped(self, commenter, tmp_path):
        results = commenter.parse_radon_report(self._make_report(tmp_path, 10))
        assert results == []

    def test_complexity_above_20_is_red(self, commenter, tmp_path):
        results = commenter.parse_radon_report(self._make_report(tmp_path, 21))
        assert '🔴' in results[0]['body']

    def test_complexity_16_to_20_is_yellow(self, commenter, tmp_path):
        results = commenter.parse_radon_report(self._make_report(tmp_path, 16))
        assert '🟡' in results[0]['body']

    def test_complexity_11_to_15_is_orange(self, commenter, tmp_path):
        results = commenter.parse_radon_report(self._make_report(tmp_path, 11))
        assert '🟠' in results[0]['body']

    def test_missing_file_returns_empty(self, commenter, tmp_path):
        assert commenter.parse_radon_report(tmp_path / 'missing.json') == []


# ---------------------------------------------------------------------------
# post_review_comments()
# ---------------------------------------------------------------------------

class TestPostReviewComments:
    def test_no_comments_skips_api_call(self, commenter, capsys):
        with patch.object(commenter, '_make_request') as mock_req:
            commenter.post_review_comments([])
        mock_req.assert_not_called()
        assert 'No issues' in capsys.readouterr().out

    def test_deduplicates_by_path_and_line(self, commenter):
        comments = [
            {'path': 'a.py', 'line': 1, 'body': 'first', 'severity': 'LOW'},
            {'path': 'a.py', 'line': 1, 'body': 'second HIGH', 'severity': 'HIGH'},
        ]
        with patch.object(commenter, '_make_request', return_value={'id': 1}) as mock_req:
            commenter.post_review_comments(comments)
        posted = mock_req.call_args[0][2]['comments']
        assert len(posted) == 1

    def test_high_severity_wins_dedup(self, commenter):
        comments = [
            {'path': 'a.py', 'line': 5, 'body': 'low issue', 'severity': 'LOW'},
            {'path': 'a.py', 'line': 5, 'body': 'high issue', 'severity': 'HIGH'},
        ]
        with patch.object(commenter, '_make_request', return_value={'id': 1}) as mock_req:
            commenter.post_review_comments(comments)
        posted = mock_req.call_args[0][2]['comments']
        assert 'high issue' in posted[0]['body']

    def test_caps_at_20_comments(self, commenter):
        comments = [{'path': f'f{i}.py', 'line': i, 'body': 'x', 'severity': 'LOW'} for i in range(30)]
        with patch.object(commenter, '_make_request', return_value={'id': 1}) as mock_req:
            commenter.post_review_comments(comments)
        posted = mock_req.call_args[0][2]['comments']
        assert len(posted) == 20

    def test_posts_to_correct_endpoint(self, commenter):
        comments = [{'path': 'a.py', 'line': 1, 'body': 'issue', 'severity': 'HIGH'}]
        with patch.object(commenter, '_make_request', return_value={'id': 1}) as mock_req:
            commenter.post_review_comments(comments)
        endpoint = mock_req.call_args[0][1]
        assert 'pulls/42/reviews' in endpoint

    def test_failed_api_call_prints_warning(self, commenter, capsys):
        comments = [{'path': 'a.py', 'line': 1, 'body': 'issue', 'severity': 'HIGH'}]
        with patch.object(commenter, '_make_request', return_value=None):
            commenter.post_review_comments(comments)
        assert 'Failed' in capsys.readouterr().out


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------

class TestRun:
    def test_run_calls_all_parsers(self, commenter, tmp_path):
        # Create mock report files
        (tmp_path / 'pylint-report.json').write_text('[]')
        (tmp_path / 'bandit-report.json').write_text('{"results": []}')
        (tmp_path / 'radon-cc-report.json').write_text('{}')

        with patch.object(commenter, '_fetch_pr_diff', return_value=''), \
             patch.object(commenter, 'analyze_diff_with_claude', return_value=[]) as mock_claude, \
             patch.object(commenter, 'post_review_comments') as mock_post:
            commenter.run(tmp_path)

        mock_claude.assert_called_once()
        mock_post.assert_called_once()

    def test_run_aggregates_findings(self, commenter, tmp_path):
        pylint_data = [{'path': 'a.py', 'line': 1, 'message': 'msg', 'message-id': 'W0001', 'type': 'warning'}]
        (tmp_path / 'pylint-report.json').write_text(json.dumps(pylint_data))

        claude_finding = {'path': 'b.py', 'line': 5, 'body': 'issue', 'severity': 'HIGH'}

        with patch.object(commenter, '_fetch_pr_diff', return_value='diff'), \
             patch.object(commenter, 'analyze_diff_with_claude', return_value=[claude_finding]), \
             patch.object(commenter, 'post_review_comments') as mock_post:
            commenter.run(tmp_path)

        all_comments = mock_post.call_args[0][0]
        paths = [c['path'] for c in all_comments]
        assert 'b.py' in paths
        assert 'a.py' in paths
