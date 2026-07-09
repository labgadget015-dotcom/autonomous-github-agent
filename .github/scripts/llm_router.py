#!/usr/bin/env python3
"""
LLM Router - Intelligent Triage System
Routes tasks to local or cloud LLMs based on complexity, saving 90% on token costs.
"""

import os
import time
from dataclasses import dataclass
from enum import Enum

import requests


class TaskComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


@dataclass
class LLMResponse:
    content: str
    model: str
    tokens_used: int
    cost: float
    latency_ms: float
    success: bool


class LLMRouter:
    """
    Intelligent LLM routing: 70-80% tasks → Local (FREE), 20-30% → Cloud

    Decision Matrix:
    - format, lint, doc, triage, changelog, summarize, label, classify,
      rename, comment_simple, security LOW → Local (Llama-70B)
    - security MEDIUM, review/test_generation <200 lines, complexity 5-20 → Moderate (try local, fall back to cloud)
    - refactor, architecture, multi_file, review >200 lines → Cloud (GPT-4-Turbo)
    - security HIGH/CRITICAL → Cloud (GPT-4)
    """

    def __init__(self):
        self.local_url = os.getenv("LOCAL_LLM_URL", "http://localhost:1234/v1")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        self.cost_matrix = {
            "local": 0.0,
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "claude-3-sonnet": 0.003,
        }

        self.stats = {"total": 0, "local": 0, "cloud": 0, "cost": 0.0, "tokens": 0}

    # Task types cheap enough to always serve locally.
    # Criteria: short output, low-stakes errors, no multi-step reasoning needed.
    _LOCAL_TASK_TYPES = frozenset([
        "format",
        "lint_simple",
        "doc",
        "doc_simple",
        "triage",          # issue label suggestion
        "changelog",       # changelog entry generation
        "summarize",       # short text summaries
        "label",           # PR / issue label selection
        "classify",        # single-dimension classification
        "rename",          # identifier / file rename suggestion
        "comment_simple",  # short inline code comments
    ])

    def classify(self, task_type: str, context: dict) -> TaskComplexity:
        if task_type in self._LOCAL_TASK_TYPES:
            return TaskComplexity.SIMPLE

        if task_type == "security":
            severity = context.get("severity", "LOW")
            if severity in ["HIGH", "CRITICAL"]:
                return TaskComplexity.CRITICAL
            if severity == "MEDIUM":
                return TaskComplexity.MODERATE
            return TaskComplexity.SIMPLE  # LOW → local

        if task_type == "complexity":
            score = context.get("score", 0)
            if score > 20:
                return TaskComplexity.COMPLEX
            if score >= 5:
                return TaskComplexity.MODERATE
            return TaskComplexity.SIMPLE  # trivial functions → local

        if task_type in ["refactor", "architecture", "multi_file"]:
            return TaskComplexity.COMPLEX

        if task_type in ["review", "test_generation"]:
            lines = context.get("lines_changed", 0)
            return TaskComplexity.COMPLEX if lines > 200 else TaskComplexity.MODERATE

        return TaskComplexity.MODERATE

    def call_local(self, prompt: str) -> LLMResponse:
        start = time.time()
        try:
            r = requests.post(
                f"{self.local_url}/chat/completions",
                json={
                    "model": "local",
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            data = r.json()
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model="local-llama-70b",
                tokens_used=data.get("usage", {}).get("total_tokens", 0),
                cost=0.0,
                latency_ms=(time.time() - start) * 1000,
                success=True,
            )
        except Exception:
            return LLMResponse("", "local", 0, 0.0, 0, False)

    def call_cloud(self, prompt: str, model="gpt-4-turbo") -> LLMResponse:
        start = time.time()
        try:
            r = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.openai_key}"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                },
                timeout=60,
            )
            data = r.json()
            tokens = data["usage"]["total_tokens"]
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                model=model,
                tokens_used=tokens,
                cost=(tokens / 1000) * self.cost_matrix[model],
                latency_ms=(time.time() - start) * 1000,
                success=True,
            )
        except Exception:
            return LLMResponse("", model, 0, 0.0, 0, False)

    def route(
        self, prompt: str, task_type: str, context: dict | None = None
    ) -> LLMResponse:
        context = context or {}
        complexity = self.classify(task_type, context)
        self.stats["total"] += 1

        # Try local for simple/moderate
        if complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
            print(f"🔹 LOCAL ({complexity.value})...")
            resp = self.call_local(prompt)
            if resp.success:
                self.stats["local"] += 1
                print(f"✅ {resp.latency_ms:.0f}ms $0")
                return resp

        # Fallback to cloud
        print(f"☁️  CLOUD ({complexity.value})...")
        model = "gpt-4" if complexity == TaskComplexity.CRITICAL else "gpt-4-turbo"
        resp = self.call_cloud(prompt, model)
        if resp.success:
            self.stats["cloud"] += 1
            self.stats["cost"] += resp.cost
            self.stats["tokens"] += resp.tokens_used
            print(f"✅ {resp.latency_ms:.0f}ms ${resp.cost:.4f}")
        return resp

    def report(self):
        t = self.stats["total"]
        l_pct = (self.stats["local"] / t * 100) if t > 0 else 0
        cloud_cost = (self.stats["tokens"] / 1000) * 0.01
        savings = cloud_cost - self.stats["cost"]

        print("\n" + "=" * 60)
        print("💰 LLM ROUTING REPORT")
        print("=" * 60)
        print(
            f"Requests: {t} ({self.stats['local']} local, {self.stats['cloud']} cloud)"
        )
        print(f"Local: {l_pct:.1f}% (FREE)")
        print(f"Actual: ${self.stats['cost']:.2f}")
        print(f"Would be: ${cloud_cost:.2f}")
        print(f"SAVINGS: ${savings:.2f} ({(savings/cloud_cost*100):.1f}%)")
        print("=" * 60)


if __name__ == "__main__":
    router = LLMRouter()
    print("🚀 Testing LLM Router\n")

    router.route("Fix formatting", "format")
    router.route("Suggest issue labels", "triage")
    router.route("Generate changelog entry", "changelog")
    router.route("Security LOW vuln", "security", {"severity": "LOW"})
    router.route("Security MEDIUM vuln", "security", {"severity": "MEDIUM"})
    router.route("Security HIGH vuln", "security", {"severity": "HIGH"})
    router.route("Small review", "review", {"lines_changed": 50})
    router.route("Large review", "review", {"lines_changed": 300})
    router.route("Architecture redesign", "architecture")

    router.report()
