#!/usr/bin/env python3
"""
Dependency Graph Resolver — Block-Chain of PR Dependencies.

Scans open PRs in the three active repos for explicit or implicit dependency
references, builds a NetworkX DAG, and applies tier labels via the GitHub API.

Environment variables:
    GITHUB_TOKEN          GitHub personal access token
    ANTHROPIC_API_KEY     Anthropic API key (used for LLM extraction fallback)
    ENABLE_LIVE_MODE      Set to "true" to apply labels (default: dry-run only)

Active repos (MVP scope — paused repos are deferred until validated):
    labgadget015-dotcom/autonomous-github-agent
    labgadget015-dotcom/ai-automation-engine
    labgadget015-dotcom/github-multi-agent-system

Tier definitions:
    tier-0-blocker      PR that at least one other PR depends on
    tier-1-dependent    PR that depends on at least one other PR
    tier-2-leaf         PR with no dependencies and no dependents

DAG edge direction:
    A → B  means "A depends on B"
    So tier-0-blocker = nodes with in-degree > 0 (others point to them)
       tier-1-dependent = nodes with out-degree > 0 (they point to others)
       tier-2-leaf = nodes with in-degree == 0 AND out-degree == 0
    A node that is both a dependency of others AND depends on others gets
    tier-0-blocker (higher priority).
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from github import Github, GithubException

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ACTIVE_REPOS: list[dict[str, str]] = [
    {"owner": "labgadget015-dotcom", "name": "autonomous-github-agent"},
    {"owner": "labgadget015-dotcom", "name": "ai-automation-engine"},
    {"owner": "labgadget015-dotcom", "name": "github-multi-agent-system"},
]

TIER_LABELS: dict[int, str] = {
    0: "tier-0-blocker",
    1: "tier-1-dependent",
    2: "tier-2-leaf",
}

LABEL_COLORS: dict[int, str] = {
    0: "b60205",  # red
    1: "e4e669",  # yellow
    2: "0e8a16",  # green
}

LABEL_DESCRIPTIONS: dict[int, str] = {
    0: "This PR blocks other PRs — merge first",
    1: "This PR depends on at least one other PR",
    2: "This PR has no dependencies and no dependents",
}

# Sentinel used to distinguish "caller did not pass llm_client" from explicit None
_UNSET = object()

# Regex pre-pass — matches "Depends on #123", "depends-on #45", "Depends on owner/repo#67"
_DEPENDS_ON_LOCAL_RE = re.compile(
    r"depends[\s_-]+on\s+#(\d+)", re.IGNORECASE
)
_DEPENDS_ON_QUALIFIED_RE = re.compile(
    r"depends[\s_-]+on\s+[\w.\-]+/[\w.\-]+#(\d+)", re.IGNORECASE
)

# LLM model for extraction (cheap, fast)
_HAIKU_MODEL = "claude-3-5-haiku-20241022"

_EXTRACTION_SYSTEM_PROMPT = (
    "You extract PR dependency information from pull request descriptions. "
    "Return ONLY a valid JSON object — no prose, no markdown fences. "
    "Schema: "
    '{"pr_id": <int>, "repo": "<owner/name>", '
    '"depends_on": [<int>, ...], "confidence_score": <float 0-1>}'
)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class PRNode:
    """Lightweight descriptor for an open pull request."""

    pr_id: int
    repo: str  # "owner/name"
    title: str
    body: str
    url: str
    depends_on: list[int] = field(default_factory=list)
    confidence: float = 1.0


@dataclass
class ExtractionResult:
    """Structured result from LLM dependency extraction."""

    pr_id: int
    repo: str
    depends_on: list[int]
    confidence_score: float


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------


def extract_deps_regex(text: str) -> list[int]:
    """Return PR numbers referenced by explicit ``Depends on #X`` patterns.

    Handles both local (``#123``) and qualified (``owner/repo#123``) forms.
    Deduplicates and preserves order of first occurrence.
    """
    if not text:
        return []
    seen: set[int] = set()
    result: list[int] = []
    for pattern in (_DEPENDS_ON_LOCAL_RE, _DEPENDS_ON_QUALIFIED_RE):
        for match in pattern.finditer(text):
            num = int(match.group(1))
            if num not in seen:
                seen.add(num)
                result.append(num)
    return result


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------


def _build_extraction_prompt(node: PRNode) -> str:
    body_snippet = (node.body or "")[:1500]
    return (
        f"PR #{node.pr_id} in repo {node.repo}\n"
        f"Title: {node.title}\n"
        f"Body:\n{body_snippet}\n\n"
        "Identify which PR numbers this PR depends on. "
        "A dependency is an explicit statement like 'Depends on #X', "
        "'blocked by #X', or 'requires #X to be merged first'. "
        "If there are no dependencies, return an empty depends_on list. "
        "Return JSON only."
    )


def extract_deps_llm(
    node: PRNode,
    llm_client: Any,
) -> ExtractionResult:
    """Call the LLM to extract dependencies and return a structured result.

    Falls back to an empty result on any error so the caller can proceed.
    """
    import asyncio

    prompt = _build_extraction_prompt(node)
    try:
        result = asyncio.run(
            llm_client.generate(
                prompt,
                system_prompt=_EXTRACTION_SYSTEM_PROMPT,
                max_tokens=200,
                temperature=0.0,
            )
        )
        raw = result.get("content", "{}").strip()
        # Strip accidental markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        data = json.loads(raw)
        return ExtractionResult(
            pr_id=int(data.get("pr_id", node.pr_id)),
            repo=str(data.get("repo", node.repo)),
            depends_on=[int(x) for x in data.get("depends_on", [])],
            confidence_score=float(data.get("confidence_score", 0.0)),
        )
    except Exception as exc:
        logger.warning(
            "LLM extraction failed for %s#%d (falling back to regex): %s",
            node.repo,
            node.pr_id,
            exc,
        )
        return ExtractionResult(
            pr_id=node.pr_id,
            repo=node.repo,
            depends_on=[],
            confidence_score=0.0,
        )


# ---------------------------------------------------------------------------
# Main engine
# ---------------------------------------------------------------------------


class DependencyGraph:
    """Builds and labels a PR dependency DAG across the three active repos.

    Args:
        github_token:      GitHub PAT. Defaults to ``GITHUB_TOKEN`` env var.
        anthropic_api_key: Anthropic API key for LLM extraction. Defaults to
                           ``ANTHROPIC_API_KEY`` env var.
        dry_run:           When *True* (default) no labels are applied.
                           Set *False* or ``ENABLE_LIVE_MODE=true`` to write.
        max_llm_calls:     Hard cap on LLM calls per run (default 30).
    """

    def __init__(
        self,
        github_token: str | None = None,
        anthropic_api_key: str | None = None,
        dry_run: bool | None = None,
        max_llm_calls: int = 30,
    ) -> None:
        token = github_token or os.getenv("GITHUB_TOKEN")
        if not token:
            raise ValueError("GITHUB_TOKEN is required")
        self._github = Github(token)

        self._anthropic_api_key = anthropic_api_key or os.getenv("ANTHROPIC_API_KEY")
        self.max_llm_calls = max_llm_calls
        self._llm_calls_used = 0

        if dry_run is None:
            dry_run = os.getenv("ENABLE_LIVE_MODE", "").lower() != "true"
        self.dry_run = dry_run

    # ------------------------------------------------------------------
    # LLM client (lazy)
    # ------------------------------------------------------------------

    def _make_llm_client(self) -> Any | None:
        """Return a configured LLMClient or None if no API key is available."""
        if not self._anthropic_api_key:
            logger.info("No ANTHROPIC_API_KEY — LLM extraction disabled")
            return None
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from core.llm_provider import LLMClient

            return LLMClient(
                {
                    "llm_provider": "anthropic",
                    "anthropic_api_key": self._anthropic_api_key,
                    "model": _HAIKU_MODEL,
                    "llm_max_cost_usd": 5.0,
                }
            )
        except Exception as exc:
            logger.warning("Failed to initialise LLMClient: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Repo scanning
    # ------------------------------------------------------------------

    def scan_repos(
        self, repos: list[dict[str, str]] | None = None
    ) -> list[PRNode]:
        """Fetch all open PRs from *repos* and return a list of PRNode objects.

        Args:
            repos: List of ``{owner, name}`` dicts. Defaults to
                   :data:`ACTIVE_REPOS`.

        Returns:
            List of :class:`PRNode` instances (one per open PR).
        """
        if repos is None:
            repos = ACTIVE_REPOS

        nodes: list[PRNode] = []
        for repo_cfg in repos:
            full_name = f"{repo_cfg['owner']}/{repo_cfg['name']}"
            try:
                repo = self._github.get_repo(full_name)
                for pr in repo.get_pulls(state="open"):
                    nodes.append(
                        PRNode(
                            pr_id=pr.number,
                            repo=full_name,
                            title=pr.title or "",
                            body=pr.body or "",
                            url=pr.html_url,
                        )
                    )
                logger.info(
                    "[dep-graph] Fetched %d open PRs from %s",
                    sum(1 for n in nodes if n.repo == full_name),
                    full_name,
                )
            except Exception as exc:
                logger.error("[dep-graph] Failed to fetch PRs from %s: %s", full_name, exc)

        return nodes

    # ------------------------------------------------------------------
    # Dependency extraction
    # ------------------------------------------------------------------

    def _resolve_deps(
        self, node: PRNode, all_ids: set[int], llm_client: Any | None
    ) -> list[int]:
        """Return a validated dependency list for *node*.

        Steps:
        1. Regex pre-pass (cheap, zero API cost).
        2. If regex finds nothing AND an LLM client is available AND the
           LLM call budget is not exhausted, attempt LLM extraction.
        3. Filter to IDs that exist in *all_ids* (avoids phantom edges).
        """
        deps = extract_deps_regex(node.body)

        if not deps and llm_client is not None and self._llm_calls_used < self.max_llm_calls:
            result = extract_deps_llm(node, llm_client)
            self._llm_calls_used += 1
            if result.confidence_score >= 0.5:
                deps = result.depends_on
                node.confidence = result.confidence_score

        # Only keep IDs that actually exist as open PRs in the scanned repos
        return [d for d in deps if d in all_ids]

    # ------------------------------------------------------------------
    # DAG construction
    # ------------------------------------------------------------------

    def build_dag(
        self,
        nodes: list[PRNode],
        llm_client: Any | None = None,
    ):
        """Build a directed acyclic graph from *nodes*.

        Edge ``A → B`` means "PR A depends on PR B".

        Args:
            nodes:      List of PR nodes returned by :meth:`scan_repos`.
            llm_client: Optional LLM client for dependency extraction.

        Returns:
            A ``networkx.DiGraph`` where each node key is ``"repo#pr_id"``
            and nodes carry ``pr_id``, ``repo``, ``title``, ``url`` attrs.
        """
        import networkx as nx

        dag: nx.DiGraph = nx.DiGraph()

        all_ids: set[int] = {n.pr_id for n in nodes}

        # First pass: add all nodes so edges can safely reference them
        for node in nodes:
            key = f"{node.repo}#{node.pr_id}"
            dag.add_node(
                key,
                pr_id=node.pr_id,
                repo=node.repo,
                title=node.title,
                url=node.url,
            )

        # Second pass: resolve dependencies and add edges
        for node in nodes:
            key = f"{node.repo}#{node.pr_id}"
            deps = self._resolve_deps(node, all_ids, llm_client)
            node.depends_on = deps
            for dep_id in deps:
                # Find the dep's repo (assume same repo if not qualified)
                dep_node = next(
                    (n for n in nodes if n.pr_id == dep_id), None
                )
                dep_repo = dep_node.repo if dep_node else node.repo
                dep_key = f"{dep_repo}#{dep_id}"
                dag.add_edge(key, dep_key)

        # Remove cycles (shouldn't happen with PRs, but guard defensively)
        if not _is_dag(dag):
            logger.warning("[dep-graph] Cycle detected — removing back-edges")
            dag = _break_cycles(dag)

        return dag

    # ------------------------------------------------------------------
    # Tier assignment
    # ------------------------------------------------------------------

    def assign_tiers(self, dag: Any) -> dict[str, int]:
        """Return a mapping of node key → tier integer.

        Tier rules (in priority order):
            0 — node has in-degree > 0 (other PRs depend on it → blocker)
            1 — node has out-degree > 0 (it depends on others → dependent)
            2 — no in-edges AND no out-edges (leaf)
        """
        tiers: dict[str, int] = {}
        for node in dag.nodes:
            in_deg = dag.in_degree(node)
            out_deg = dag.out_degree(node)
            if in_deg > 0:
                tiers[node] = 0
            elif out_deg > 0:
                tiers[node] = 1
            else:
                tiers[node] = 2
        return tiers

    # ------------------------------------------------------------------
    # Label management
    # ------------------------------------------------------------------

    def _ensure_label(self, repo_obj: Any, tier: int) -> None:
        """Create the tier label in *repo_obj* if it does not already exist."""
        label_name = TIER_LABELS[tier]
        try:
            repo_obj.get_label(label_name)
        except GithubException:
            try:
                repo_obj.create_label(
                    name=label_name,
                    color=LABEL_COLORS[tier],
                    description=LABEL_DESCRIPTIONS[tier],
                )
                logger.info("[dep-graph] Created label '%s'", label_name)
            except GithubException as exc:
                logger.warning("[dep-graph] Could not create label '%s': %s", label_name, exc)

    def apply_labels(
        self,
        nodes: list[PRNode],
        tier_map: dict[str, int],
        dag: Any,
    ) -> dict[str, Any]:
        """Apply tier labels to each PR via the GitHub API.

        In dry-run mode, logs what *would* be applied without making API calls.

        Returns:
            Summary dict with ``labels_applied``, ``dry_run_previews``, and
            ``errors`` counts.
        """
        repo_cache: dict[str, Any] = {}
        labels_applied = 0
        dry_run_previews = 0
        errors = 0

        for node in nodes:
            key = f"{node.repo}#{node.pr_id}"
            tier = tier_map.get(key, 2)
            label_name = TIER_LABELS[tier]

            if self.dry_run:
                logger.info(
                    "[dep-graph] DRY-RUN: would apply '%s' to %s", label_name, key
                )
                dry_run_previews += 1
                continue

            try:
                if node.repo not in repo_cache:
                    repo_cache[node.repo] = self._github.get_repo(node.repo)
                repo_obj = repo_cache[node.repo]

                self._ensure_label(repo_obj, tier)

                pr_obj = repo_obj.get_pull(node.pr_id)
                existing_tier_labels = [
                    lbl for lbl in pr_obj.labels
                    if lbl.name in TIER_LABELS.values()
                ]
                # Remove stale tier labels before applying new one
                for lbl in existing_tier_labels:
                    if lbl.name != label_name:
                        pr_obj.remove_from_labels(lbl)
                pr_obj.add_to_labels(label_name)
                logger.info("[dep-graph] Applied '%s' to %s", label_name, key)
                labels_applied += 1
            except GithubException as exc:
                logger.error("[dep-graph] Failed to label %s: %s", key, exc)
                errors += 1

        return {
            "labels_applied": labels_applied,
            "dry_run_previews": dry_run_previews,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------

    def run(
        self,
        repos: list[dict[str, str]] | None = None,
        llm_client: Any = _UNSET,
    ) -> dict[str, Any]:
        """End-to-end scan → build → label pipeline.

        Args:
            repos:      Repo list (defaults to :data:`ACTIVE_REPOS`).
            llm_client: LLM client for extraction. Pass ``None`` to disable.
                        When omitted, a client is created automatically if
                        ``ANTHROPIC_API_KEY`` is set.

        Returns:
            Summary dict with DAG stats and label counts.
        """
        if llm_client is _UNSET:
            llm_client = self._make_llm_client()

        mode = "DRY-RUN" if self.dry_run else "LIVE"
        logger.info("[dep-graph] Starting (%s, max_llm_calls=%d)", mode, self.max_llm_calls)

        nodes = self.scan_repos(repos)
        logger.info("[dep-graph] Scanned %d open PRs", len(nodes))

        dag = self.build_dag(nodes, llm_client=llm_client)
        logger.info(
            "[dep-graph] DAG: %d nodes, %d edges", dag.number_of_nodes(), dag.number_of_edges()
        )

        tier_map = self.assign_tiers(dag)
        tier_counts = {TIER_LABELS[t]: sum(1 for v in tier_map.values() if v == t) for t in TIER_LABELS}
        logger.info("[dep-graph] Tier distribution: %s", tier_counts)

        label_summary = self.apply_labels(nodes, tier_map, dag)

        summary: dict[str, Any] = {
            "prs_scanned": len(nodes),
            "dag_nodes": dag.number_of_nodes(),
            "dag_edges": dag.number_of_edges(),
            "tier_counts": tier_counts,
            "llm_calls_used": self._llm_calls_used,
            **label_summary,
        }

        if self.dry_run:
            print(
                f"[dep-graph] DRY-RUN complete — {len(nodes)} PRs scanned, "
                f"{dag.number_of_edges()} dependency edges, "
                f"{label_summary['dry_run_previews']} labels previewed."
            )
        else:
            print(
                f"[dep-graph] LIVE run complete — {label_summary['labels_applied']} labels applied, "
                f"{label_summary['errors']} errors."
            )

        return summary


# ---------------------------------------------------------------------------
# DAG cycle-breaking utilities
# ---------------------------------------------------------------------------


def _is_dag(g: Any) -> bool:
    """Return True if *g* is a directed acyclic graph."""
    import networkx as nx

    return nx.is_directed_acyclic_graph(g)


def _break_cycles(g: Any) -> Any:
    """Remove the minimum set of back-edges needed to eliminate all cycles."""
    import networkx as nx

    g = g.copy()
    for cycle in nx.simple_cycles(g):
        if len(cycle) >= 2:
            g.remove_edge(cycle[-1], cycle[0])
            logger.warning("[dep-graph] Removed back-edge %s → %s", cycle[-1], cycle[0])
            if _is_dag(g):
                break
    return g


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> None:
    """CLI entry point for the Dependency Graph Resolver."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Dependency Graph Resolver — PR dependency chain analyser"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Enable live mode (apply labels). Default is dry-run.",
    )
    parser.add_argument(
        "--max-llm-calls",
        type=int,
        default=30,
        help="Hard cap on LLM calls per run (default: 30)",
    )
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM extraction (regex pre-pass only)",
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    engine = DependencyGraph(
        dry_run=not args.live,
        max_llm_calls=args.max_llm_calls,
    )
    llm_client = None if args.no_llm else engine._make_llm_client()
    summary = engine.run(llm_client=llm_client)

    print(
        f"LLM calls used: {summary['llm_calls_used']} / {args.max_llm_calls}"
    )


if __name__ == "__main__":
    main()
