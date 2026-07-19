"""
Agent Drift Eval / Regression Harness.

WHY: the core decision functions (RiskScorer, LLM router classify) are DETERMINISTIC
and PURE. As prompts, models, and guardrails evolve, a refactor can silently change
their output on inputs that used to be safe. That is "agent drift" — and it is exactly
what breaks a self-regulating system, because nobody notices until a wrong merge lands.

This harness pins golden inputs -> expected outputs so drift is caught in a test run,
not in production. Add new cases to tests/fixtures/agent_drift_golden.json.

Run:
    cd /home/ai/autonomous-github-agent
    python3 -m pytest tests/agent_drift_eval.py -q --no-cov
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / ".github" / "scripts"))

from llm_router import LLMRouter  # noqa: E402

from core.risk_scorer import score_pull_request  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "agent_drift_golden.json"


def _load() -> dict:
    return json.loads(FIXTURE.read_text())


def test_risk_scorer_golden():
    for case in _load()["risk_scorer"]:
        r = score_pull_request(**case["input"])
        assert r.total_score == pytest.approx(
            case["expected_score"], abs=0.001
        ), f"score drift: {case['name']} -> {r.total_score} != {case['expected_score']}"
        assert (
            r.band.value == case["expected_band"]
        ), f"band drift: {case['name']} -> {r.band.value} != {case['expected_band']}"


def test_router_classify_golden():
    router = LLMRouter()
    for case in _load()["router_classify"]:
        got = router.classify(case["task_type"], case.get("context", {}))
        assert (
            got.value == case["expected"]
        ), f"classify drift: {case['name']} -> {got.value} != {case['expected']}"


if __name__ == "__main__":
    data = _load()
    print(
        f"golden fixture OK: "
        f"{len(data['risk_scorer'])} risk cases, "
        f"{len(data['router_classify'])} router cases. Run via pytest."
    )
