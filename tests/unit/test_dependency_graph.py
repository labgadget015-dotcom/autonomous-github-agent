"""Unit tests for autopilot/dependency_graph.py"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_engine(dry_run=True, max_llm_calls=30, token="tok", anthropic_key=None):
    from autopilot.dependency_graph import DependencyGraph

    mock_gh = MagicMock()
    with (
        patch("autopilot.dependency_graph.Github", return_value=mock_gh),
        patch.dict(
            "os.environ",
            {
                "GITHUB_TOKEN": token,
                **({"ANTHROPIC_API_KEY": anthropic_key} if anthropic_key else {}),
            },
        ),
    ):
        engine = DependencyGraph(
            dry_run=dry_run,
            max_llm_calls=max_llm_calls,
        )
    engine._github = mock_gh
    return engine


def _make_pr_node(pr_id=1, repo="owner/repo", title="Test", body="", url="http://x/1"):
    from autopilot.dependency_graph import PRNode

    return PRNode(pr_id=pr_id, repo=repo, title=title, body=body, url=url)


def _make_mock_pr(number, title="Test PR", body="", html_url="http://x/1"):
    pr = MagicMock()
    pr.number = number
    pr.title = title
    pr.body = body
    pr.html_url = html_url
    return pr


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------


class TestDependencyGraphInit:
    def test_requires_github_token(self):
        from autopilot.dependency_graph import DependencyGraph

        with (
            patch.dict("os.environ", {}, clear=True),
            pytest.raises(ValueError, match="GITHUB_TOKEN"),
        ):
            DependencyGraph()

    def test_dry_run_default(self):
        engine = _make_engine()
        assert engine.dry_run is True

    def test_live_mode_via_env(self):
        from autopilot.dependency_graph import DependencyGraph

        mock_gh = MagicMock()
        with (
            patch("autopilot.dependency_graph.Github", return_value=mock_gh),
            patch.dict(
                "os.environ", {"GITHUB_TOKEN": "tok", "ENABLE_LIVE_MODE": "true"}
            ),
        ):
            engine = DependencyGraph()
        assert engine.dry_run is False

    def test_dry_run_explicit_override(self):
        engine = _make_engine(dry_run=False)
        assert engine.dry_run is False

    def test_max_llm_calls_stored(self):
        engine = _make_engine(max_llm_calls=5)
        assert engine.max_llm_calls == 5


# ---------------------------------------------------------------------------
# Regex extraction
# ---------------------------------------------------------------------------


class TestExtractDepsRegex:
    def setup_method(self):
        from autopilot.dependency_graph import extract_deps_regex

        self.extract = extract_deps_regex

    def test_empty_text_returns_empty(self):
        assert self.extract("") == []

    def test_none_like_empty_returns_empty(self):
        # Body may be None — caller guards, but test empty string edge-case
        assert self.extract("No dependencies here") == []

    def test_depends_on_hash_syntax(self):
        result = self.extract("Depends on #42")
        assert result == [42]

    def test_depends_on_case_insensitive(self):
        result = self.extract("DEPENDS ON #10")
        assert 10 in result

    def test_depends_on_hyphen_variant(self):
        result = self.extract("depends-on #7")
        assert 7 in result

    def test_depends_on_underscore_variant(self):
        result = self.extract("depends_on #99")
        assert 99 in result

    def test_multiple_deps_extracted(self):
        text = "Depends on #1\nDepends on #2\nSome text\nDepends on #3"
        result = self.extract(text)
        assert result == [1, 2, 3]

    def test_deduplication(self):
        result = self.extract("Depends on #5\nDepends on #5")
        assert result.count(5) == 1

    def test_qualified_syntax(self):
        result = self.extract("Depends on owner/repo#55")
        assert 55 in result

    def test_unrelated_hash_not_extracted(self):
        result = self.extract("Closes #100\nFixes #200")
        assert result == []

    def test_mixed_content(self):
        text = "## Description\nThis fixes a bug.\n\nDepends on #12\n\nCloses #50"
        result = self.extract(text)
        assert result == [12]
        assert 50 not in result


# ---------------------------------------------------------------------------
# LLM extraction
# ---------------------------------------------------------------------------


class TestExtractDepsLlm:
    def _make_llm(self, response_json: dict) -> MagicMock:
        llm = MagicMock()
        llm.generate = AsyncMock(return_value={"content": json.dumps(response_json)})
        return llm

    def test_happy_path(self):
        from autopilot.dependency_graph import extract_deps_llm

        node = _make_pr_node(pr_id=10, repo="o/r")
        llm = self._make_llm(
            {"pr_id": 10, "repo": "o/r", "depends_on": [5, 7], "confidence_score": 0.9}
        )
        result = extract_deps_llm(node, llm)
        assert result.depends_on == [5, 7]
        assert result.confidence_score == pytest.approx(0.9)

    def test_no_dependencies(self):
        from autopilot.dependency_graph import extract_deps_llm

        node = _make_pr_node(pr_id=3, repo="o/r")
        llm = self._make_llm(
            {"pr_id": 3, "repo": "o/r", "depends_on": [], "confidence_score": 0.8}
        )
        result = extract_deps_llm(node, llm)
        assert result.depends_on == []

    def test_strips_markdown_fences(self):
        from autopilot.dependency_graph import extract_deps_llm

        node = _make_pr_node(pr_id=1, repo="o/r")
        raw = '```json\n{"pr_id": 1, "repo": "o/r", "depends_on": [2], "confidence_score": 0.7}\n```'
        llm = MagicMock()
        llm.generate = AsyncMock(return_value={"content": raw})
        result = extract_deps_llm(node, llm)
        assert result.depends_on == [2]

    def test_llm_exception_returns_empty(self):
        from autopilot.dependency_graph import extract_deps_llm

        node = _make_pr_node(pr_id=1, repo="o/r")
        llm = MagicMock()
        llm.generate = AsyncMock(side_effect=RuntimeError("boom"))
        result = extract_deps_llm(node, llm)
        assert result.depends_on == []
        assert result.confidence_score == 0.0

    def test_invalid_json_returns_empty(self):
        from autopilot.dependency_graph import extract_deps_llm

        node = _make_pr_node(pr_id=1, repo="o/r")
        llm = MagicMock()
        llm.generate = AsyncMock(return_value={"content": "not-json"})
        result = extract_deps_llm(node, llm)
        assert result.depends_on == []


# ---------------------------------------------------------------------------
# DAG building
# ---------------------------------------------------------------------------


class TestBuildDag:
    def setup_method(self):
        self.engine = _make_engine()

    def _nodes(self, specs):
        """Build PRNode list from (pr_id, repo, body) tuples."""
        return [
            _make_pr_node(pr_id=s[0], repo=s[1], body=s[2] if len(s) > 2 else "")
            for s in specs
        ]

    def test_empty_nodes_returns_empty_dag(self):
        dag = self.engine.build_dag([], llm_client=None)
        assert dag.number_of_nodes() == 0
        assert dag.number_of_edges() == 0

    def test_single_node_no_deps(self):
        nodes = self._nodes([(1, "o/r")])
        dag = self.engine.build_dag(nodes, llm_client=None)
        assert dag.number_of_nodes() == 1
        assert dag.number_of_edges() == 0

    def test_explicit_dep_creates_edge(self):
        nodes = self._nodes(
            [
                (1, "o/r", "Depends on #2"),
                (2, "o/r", ""),
            ]
        )
        dag = self.engine.build_dag(nodes, llm_client=None)
        assert dag.has_edge("o/r#1", "o/r#2")

    def test_dep_to_unknown_pr_ignored(self):
        nodes = self._nodes([(1, "o/r", "Depends on #999")])
        dag = self.engine.build_dag(nodes, llm_client=None)
        assert dag.number_of_edges() == 0

    def test_chain_a_depends_on_b_depends_on_c(self):
        nodes = self._nodes(
            [
                (1, "o/r", "Depends on #2"),
                (2, "o/r", "Depends on #3"),
                (3, "o/r", ""),
            ]
        )
        dag = self.engine.build_dag(nodes, llm_client=None)
        assert dag.has_edge("o/r#1", "o/r#2")
        assert dag.has_edge("o/r#2", "o/r#3")

    def test_node_attrs_populated(self):
        nodes = [_make_pr_node(pr_id=7, repo="a/b", title="My PR", url="http://x/7")]
        dag = self.engine.build_dag(nodes, llm_client=None)
        attrs = dag.nodes["a/b#7"]
        assert attrs["pr_id"] == 7
        assert attrs["repo"] == "a/b"
        assert attrs["title"] == "My PR"
        assert attrs["url"] == "http://x/7"

    def test_llm_called_when_no_regex_match(self):

        nodes = self._nodes([(1, "o/r", "No explicit dep"), (2, "o/r", "")])
        llm = MagicMock()
        llm.generate = AsyncMock(
            return_value={
                "content": json.dumps(
                    {
                        "pr_id": 1,
                        "repo": "o/r",
                        "depends_on": [2],
                        "confidence_score": 0.9,
                    }
                )
            }
        )
        dag = self.engine.build_dag(nodes, llm_client=llm)
        assert dag.has_edge("o/r#1", "o/r#2")

    def test_llm_not_called_when_regex_matches(self):
        # Node 1 has an explicit "Depends on #2" — regex resolves this without LLM.
        # Build the DAG with an LLM client that fails loudly if called for node 1.
        llm = MagicMock()
        llm.generate = AsyncMock(return_value={"content": "{}"})
        nodes = self._nodes([(1, "o/r", "Depends on #2"), (2, "o/r", "")])
        dag = self.engine.build_dag(nodes, llm_client=llm)
        # The edge must exist even though LLM returned no dependencies for node 2
        assert dag.has_edge("o/r#1", "o/r#2")
        # LLM was NOT called for node 1 (the one with the regex match)
        for call_args in llm.generate.call_args_list:
            assert "PR #1 in repo o/r" not in call_args[0][0]

    def test_llm_budget_respected(self):
        self.engine.max_llm_calls = 1
        nodes = self._nodes(
            [
                (1, "o/r", "No dep"),
                (2, "o/r", "No dep"),
                (3, "o/r", "No dep"),
            ]
        )
        llm = MagicMock()
        llm.generate = AsyncMock(
            return_value={
                "content": json.dumps(
                    {
                        "pr_id": 1,
                        "repo": "o/r",
                        "depends_on": [],
                        "confidence_score": 0.8,
                    }
                )
            }
        )
        self.engine.build_dag(nodes, llm_client=llm)
        assert llm.generate.call_count == 1


# ---------------------------------------------------------------------------
# Tier assignment
# ---------------------------------------------------------------------------


class TestAssignTiers:
    def _build_simple_dag(self, edges: list[tuple[str, str]]):
        import networkx as nx

        g: nx.DiGraph = nx.DiGraph()
        nodes = set()
        for a, b in edges:
            nodes.add(a)
            nodes.add(b)
        g.add_nodes_from(nodes)
        g.add_edges_from(edges)
        return g

    def test_leaf_no_edges(self):
        import networkx as nx

        engine = _make_engine()
        g: nx.DiGraph = nx.DiGraph()
        g.add_node("x")
        tiers = engine.assign_tiers(g)
        assert tiers["x"] == 2

    def test_blocker_has_incoming_edge(self):
        engine = _make_engine()
        g = self._build_simple_dag([("A", "B")])
        tiers = engine.assign_tiers(g)
        assert tiers["B"] == 0

    def test_dependent_has_outgoing_edge_only(self):
        engine = _make_engine()
        g = self._build_simple_dag([("A", "B")])
        tiers = engine.assign_tiers(g)
        assert tiers["A"] == 1

    def test_middle_node_is_blocker(self):
        engine = _make_engine()
        # A → B → C: A depends on B, B depends on C
        g = self._build_simple_dag([("A", "B"), ("B", "C")])
        tiers = engine.assign_tiers(g)
        # B has in-degree=1 (A depends on B) → tier-0-blocker
        assert tiers["B"] == 0
        # A depends on B, no one depends on A → tier-1-dependent
        assert tiers["A"] == 1
        # C has in-degree=1 (B depends on C) → tier-0-blocker
        assert tiers["C"] == 0


# ---------------------------------------------------------------------------
# apply_labels (dry-run)
# ---------------------------------------------------------------------------


class TestApplyLabelsDryRun:
    def test_dry_run_no_api_calls(self):

        engine = _make_engine(dry_run=True)
        nodes = [_make_pr_node(pr_id=1, repo="o/r")]
        tier_map = {"o/r#1": 2}

        import networkx as nx

        dag: nx.DiGraph = nx.DiGraph()
        dag.add_node("o/r#1")

        result = engine.apply_labels(nodes, tier_map, dag)
        assert result["labels_applied"] == 0
        assert result["dry_run_previews"] == 1
        assert result["errors"] == 0
        engine._github.get_repo.assert_not_called()

    def test_dry_run_multiple_nodes(self):
        engine = _make_engine(dry_run=True)
        node_ids = [1, 2, 3]
        nodes = [_make_pr_node(pr_id=i, repo="o/r") for i in node_ids]
        tier_map = {"o/r#1": 0, "o/r#2": 1, "o/r#3": 2}

        import networkx as nx

        dag: nx.DiGraph = nx.DiGraph()
        for n in nodes:
            dag.add_node(f"o/r#{n.pr_id}")

        result = engine.apply_labels(nodes, tier_map, dag)
        assert result["dry_run_previews"] == 3


# ---------------------------------------------------------------------------
# apply_labels (live mode)
# ---------------------------------------------------------------------------


class TestApplyLabelsLive:
    def _make_live_engine(self):
        return _make_engine(dry_run=False)

    def test_label_applied_to_pr(self):
        from github import GithubException

        from autopilot.dependency_graph import TIER_LABELS

        engine = self._make_live_engine()
        mock_repo = MagicMock()
        mock_repo.get_label.side_effect = GithubException(404, "not found")
        mock_repo.create_label.return_value = MagicMock()
        mock_pr = MagicMock()
        mock_pr.labels = []
        mock_repo.get_pull.return_value = mock_pr
        engine._github.get_repo.return_value = mock_repo

        nodes = [_make_pr_node(pr_id=1, repo="o/r")]
        tier_map = {"o/r#1": 0}

        import networkx as nx

        dag: nx.DiGraph = nx.DiGraph()
        dag.add_node("o/r#1")

        result = engine.apply_labels(nodes, tier_map, dag)
        assert result["labels_applied"] == 1
        assert result["errors"] == 0
        mock_pr.add_to_labels.assert_called_once_with(TIER_LABELS[0])

    def test_stale_tier_label_removed(self):
        from autopilot.dependency_graph import TIER_LABELS

        engine = self._make_live_engine()
        mock_repo = MagicMock()
        mock_repo.get_label.return_value = MagicMock(name=TIER_LABELS[0])

        stale_label = MagicMock()
        stale_label.name = TIER_LABELS[1]
        mock_pr = MagicMock()
        mock_pr.labels = [stale_label]
        mock_repo.get_pull.return_value = mock_pr
        engine._github.get_repo.return_value = mock_repo

        nodes = [_make_pr_node(pr_id=1, repo="o/r")]
        tier_map = {"o/r#1": 0}

        import networkx as nx

        dag: nx.DiGraph = nx.DiGraph()
        dag.add_node("o/r#1")

        engine.apply_labels(nodes, tier_map, dag)
        mock_pr.remove_from_labels.assert_called_once_with(stale_label)

    def test_github_exception_increments_errors(self):
        from github import GithubException

        engine = self._make_live_engine()
        engine._github.get_repo.side_effect = GithubException(500, "server error")

        nodes = [_make_pr_node(pr_id=1, repo="o/r")]
        tier_map = {"o/r#1": 2}

        import networkx as nx

        dag: nx.DiGraph = nx.DiGraph()
        dag.add_node("o/r#1")

        result = engine.apply_labels(nodes, tier_map, dag)
        assert result["errors"] == 1
        assert result["labels_applied"] == 0


# ---------------------------------------------------------------------------
# run() orchestration
# ---------------------------------------------------------------------------


class TestRun:
    def test_run_dry_returns_summary_keys(self):
        engine = _make_engine(dry_run=True)
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        engine._github.get_repo.return_value = mock_repo

        summary = engine.run(llm_client=None)
        assert "prs_scanned" in summary
        assert "dag_nodes" in summary
        assert "dag_edges" in summary
        assert "tier_counts" in summary
        assert "llm_calls_used" in summary

    def test_run_counts_match(self):

        engine = _make_engine(dry_run=True)
        prs = [_make_mock_pr(i) for i in range(1, 4)]
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = prs
        engine._github.get_repo.return_value = mock_repo

        summary = engine.run(repos=[{"owner": "o", "name": "r"}], llm_client=None)
        assert summary["prs_scanned"] == 3
        assert summary["dag_nodes"] == 3

    def test_run_creates_llm_client_when_anthropic_key_set(self):
        engine = _make_engine(anthropic_key="sk-ant-test")
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = []
        engine._github.get_repo.return_value = mock_repo

        with patch.object(engine, "_make_llm_client", return_value=None) as mock_make:
            engine.run(repos=[{"owner": "o", "name": "r"}])
        mock_make.assert_called_once()

    def test_run_uses_explicit_none_llm(self):
        engine = _make_engine()
        mock_repo = MagicMock()
        mock_repo.get_pulls.return_value = [_make_mock_pr(1)]
        engine._github.get_repo.return_value = mock_repo

        with patch.object(engine, "_make_llm_client") as mock_make:
            engine.run(repos=[{"owner": "o", "name": "r"}], llm_client=None)
        mock_make.assert_not_called()


# ---------------------------------------------------------------------------
# Cycle breaking
# ---------------------------------------------------------------------------


class TestCycleBreaking:
    def test_is_dag_true_for_acyclic(self):
        import networkx as nx

        from autopilot.dependency_graph import _is_dag

        g: nx.DiGraph = nx.DiGraph()
        g.add_edges_from([("A", "B"), ("B", "C")])
        assert _is_dag(g) is True

    def test_is_dag_false_for_cycle(self):
        import networkx as nx

        from autopilot.dependency_graph import _is_dag

        g: nx.DiGraph = nx.DiGraph()
        g.add_edges_from([("A", "B"), ("B", "A")])
        assert _is_dag(g) is False

    def test_break_cycles_removes_back_edge(self):
        import networkx as nx

        from autopilot.dependency_graph import _break_cycles, _is_dag

        g: nx.DiGraph = nx.DiGraph()
        g.add_edges_from([("A", "B"), ("B", "A")])
        result = _break_cycles(g)
        assert _is_dag(result) is True
