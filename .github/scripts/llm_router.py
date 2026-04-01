#!/usr/bin/env python3
"""
LLM Router - Intelligent Triage System
Routes tasks to local or cloud LLMs based on complexity, saving 90% on token costs.
"""

import logging
import os
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict

import anthropic
import requests

logger = logging.getLogger(__name__)


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
    - Formatting, simple lint → Local (Llama-70B)
    - Security LOW/MED → Local
    - Complex refactoring → Claude Opus 4.6
    - Security HIGH/CRITICAL → Claude Opus 4.6 + adaptive thinking
    """
    
    def __init__(self):
        self.local_url = os.getenv('LOCAL_LLM_URL', 'http://localhost:1234/v1')
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.anthropic_key = os.getenv('ANTHROPIC_API_KEY')
        
        self.cost_matrix = {
            'local': 0.0,
            'claude-opus-4-6': {'input': 5.0, 'output': 25.0},  # per 1M tokens
        }
        
        self.stats = {
            'total': 0, 'local': 0, 'cloud': 0,
            'cost': 0.0, 'tokens': 0,
            'cache_read_tokens': 0, 'cache_write_tokens': 0,
        }
    
    def classify(self, task_type: str, context: Dict) -> TaskComplexity:
        if task_type in ['format', 'lint_simple', 'doc']:
            return TaskComplexity.SIMPLE
        
        if task_type == 'security':
            severity = context.get('severity', 'LOW')
            return TaskComplexity.CRITICAL if severity in ['HIGH', 'CRITICAL'] else TaskComplexity.SIMPLE
        
        if task_type == 'complexity':
            score = context.get('score', 0)
            return TaskComplexity.COMPLEX if score > 20 else TaskComplexity.MODERATE
        
        return TaskComplexity.MODERATE
    
    def call_local(self, prompt: str) -> LLMResponse:
        start = time.time()
        try:
            r = requests.post(
                f"{self.local_url}/chat/completions",
                json={"model": "local", "messages": [{"role": "user", "content": prompt}]},
                timeout=30
            )
            data = r.json()
            return LLMResponse(
                content=data['choices'][0]['message']['content'],
                model='local-llama-70b',
                tokens_used=data.get('usage', {}).get('total_tokens', 0),
                cost=0.0,
                latency_ms=(time.time()-start)*1000,
                success=True
            )
        except Exception:
            logger.exception("Local LLM call failed (url=%s)", self.local_url)
            return LLMResponse("", "local", 0, 0.0, 0, False)
    
    _SYSTEM_PROMPT = (
        "You are an expert software engineer and security researcher embedded in a GitHub CI/CD pipeline. "
        "Your job is to analyze code changes, identify issues, and provide specific, actionable feedback. "
        "For security findings: describe the vulnerability class, exploitability, and a concrete fix. "
        "For complexity findings: identify the problematic function, explain the cognitive burden, and suggest a refactor. "
        "For bugs: explain the failure condition and provide corrected code. "
        "Be direct and precise. Avoid generic advice."
    )

    def call_claude(self, prompt: str, complexity: TaskComplexity) -> LLMResponse:
        start = time.time()
        try:
            client = anthropic.Anthropic(api_key=self.anthropic_key)
            params = {
                "model": "claude-opus-4-6",
                "max_tokens": 16000,
                "system": [{"type": "text", "text": self._SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
                "messages": [{"role": "user", "content": prompt}],
            }
            if complexity == TaskComplexity.CRITICAL:
                params["thinking"] = {"type": "adaptive"}

            with client.messages.stream(**params) as stream:
                message = stream.get_final_message()

            text = next((b.text for b in message.content if b.type == "text"), "")
            pricing = self.cost_matrix["claude-opus-4-6"]
            cache_read = getattr(message.usage, "cache_read_input_tokens", 0) or 0
            cache_write = getattr(message.usage, "cache_creation_input_tokens", 0) or 0
            self.stats["cache_read_tokens"] += cache_read
            self.stats["cache_write_tokens"] += cache_write
            cost = max(
                message.usage.input_tokens / 1_000_000 * pricing["input"]
                + message.usage.output_tokens / 1_000_000 * pricing["output"]
                + cache_write / 1_000_000 * pricing["input"] * 0.25   # cache write premium
                - cache_read / 1_000_000 * pricing["input"] * 0.90,   # cache read discount
                0.0,
            )
            return LLMResponse(
                content=text,
                model="claude-opus-4-6",
                tokens_used=message.usage.input_tokens + message.usage.output_tokens,
                cost=cost,
                latency_ms=(time.time() - start) * 1000,
                success=True,
            )
        except Exception:
            logger.exception("Claude API call failed")
            return LLMResponse("", "claude-opus-4-6", 0, 0.0, 0, False)
    
    def route(self, prompt: str, task_type: str, context: Dict = None) -> LLMResponse:
        context = context or {}
        complexity = self.classify(task_type, context)
        self.stats['total'] += 1
        
        # Try local for simple/moderate
        if complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
            print(f"🔹 LOCAL ({complexity.value})...")
            resp = self.call_local(prompt)
            if resp.success:
                self.stats['local'] += 1
                print(f"✅ {resp.latency_ms:.0f}ms $0")
                return resp
        
        # Escalate to Claude — adaptive thinking enabled for CRITICAL
        thinking = " + thinking" if complexity == TaskComplexity.CRITICAL else ""
        print(f"☁️  CLAUDE ({complexity.value}{thinking})...")
        resp = self.call_claude(prompt, complexity)
        if resp.success:
            self.stats['cloud'] += 1
            self.stats['cost'] += resp.cost
            self.stats['tokens'] += resp.tokens_used
            print(f"✅ {resp.latency_ms:.0f}ms ${resp.cost:.4f}")
        return resp
    
    def report(self):
        t = self.stats['total']
        l_pct = (self.stats['local']/t*100) if t > 0 else 0
        # Baseline: all tokens at Claude Opus 4.6 blended rate (~$0.015/1K)
        cloud_cost = (self.stats['tokens'] / 1_000_000) * 15.0
        savings = cloud_cost - self.stats['cost']
        
        print("\n" + "="*60)
        print("💰 LLM ROUTING REPORT")
        print("="*60)
        print(f"Requests: {t} ({self.stats['local']} local, {self.stats['cloud']} cloud)")
        print(f"Local: {l_pct:.1f}% (FREE)")
        print(f"Cache writes: {self.stats['cache_write_tokens']:,} tokens")
        print(f"Cache reads:  {self.stats['cache_read_tokens']:,} tokens")
        print(f"Actual: ${self.stats['cost']:.2f}")
        print(f"Would be: ${cloud_cost:.2f}")
        pct = (savings / cloud_cost * 100) if cloud_cost > 0 else 0.0
        print(f"SAVINGS: ${savings:.2f} ({pct:.1f}% if > 0)")
        print("="*60)


if __name__ == '__main__':
    router = LLMRouter()
    print("🚀 Testing LLM Router\n")
    
    # Test cases
    router.route("Fix formatting", "format")
    router.route("High security vuln", "security", {'severity': 'HIGH'})
    router.route("Generate doc", "doc")
    
    router.report()
