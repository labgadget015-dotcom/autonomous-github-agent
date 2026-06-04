#!/usr/bin/env python3
"""
LLM Provider

Provides an abstraction layer for LLM providers (OpenAI, Anthropic, etc.)
with unified interface, error handling, and per-session cost tracking.
"""

import asyncio
import json
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from .exceptions import LLMConfigError, LLMError  # noqa: F401 – re-exported for callers

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class LLMClient:
    """
    Unified LLM client supporting multiple providers.

    Features:
    - Support for OpenAI and Anthropic
    - Automatic provider detection
    - Error handling and retries
    - Token usage tracking
    """

    def __init__(self, config: dict[str, Any]):
        """
        Initialize LLM client.

        Args:
            config: Configuration dictionary containing:
                - llm_provider: 'openai' or 'anthropic'
                - openai_api_key: OpenAI API key (if using OpenAI)
                - anthropic_api_key: Anthropic API key (if using Anthropic)
                - model: Model name (optional)
        """
        self.config = config
        self.provider = config.get("llm_provider", "openai")
        self.model = config.get("model", self._get_default_model())

        self._client = None
        self._initialize_client()

        self.total_tokens = 0

        # Cost tracking — prices per 1k tokens (input, output) in USD
        self._PRICING: dict[str, tuple[float, float]] = {
            "gpt-4o": (0.005, 0.015),
            "gpt-4o-mini": (0.00015, 0.0006),
            "gpt-4": (0.03, 0.06),
            "gpt-4-turbo": (0.01, 0.03),
            "gpt-3.5-turbo": (0.0005, 0.0015),
            "claude-3-5-sonnet-20241022": (0.003, 0.015),
            "claude-3-5-haiku-20241022": (0.001, 0.005),
            "claude-3-opus-20240229": (0.015, 0.075),
        }
        self._session_input_tokens: int = 0
        self._session_output_tokens: int = 0
        self._session_cost_usd: float = 0.0
        self._costs_file = Path(self.config.get("llm_costs_file", ".llm_costs.jsonl"))
        logger.info(
            f"LLM client initialized with provider: {self.provider}, model: {self.model}"  # noqa: E501
        )

    def _get_default_model(self) -> str:
        """Get default model for the provider"""
        defaults = {"openai": "gpt-4", "anthropic": "claude-3-opus-20240229"}
        return defaults.get(self.provider, "gpt-4")

    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        import os

        try:
            if self.provider == "openai":
                import openai

                # Prefer environment variable to keep secrets out of config dicts
                api_key = (
                    os.getenv("OPENAI_API_KEY")
                    or self.config.get("openai_api_key")
                    or self.config.get("OPENAI_API_KEY")
                )
                if not api_key:
                    raise LLMConfigError("OpenAI API key not found in configuration")
                self._client = openai.OpenAI(api_key=api_key)

            elif self.provider == "anthropic":
                import anthropic

                # Prefer environment variable to keep secrets out of config dicts
                api_key = (
                    os.getenv("ANTHROPIC_API_KEY")
                    or self.config.get("anthropic_api_key")
                    or self.config.get("ANTHROPIC_API_KEY")
                )
                if not api_key:
                    raise LLMConfigError("Anthropic API key not found in configuration")
                self._client = anthropic.Anthropic(api_key=api_key)

            else:
                raise LLMConfigError(f"Unsupported LLM provider: {self.provider}")

        except ImportError as e:
            logger.error(f"Failed to import LLM library: {str(e)}")
            raise

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> dict[str, Any]:
        """
        Generate text using the LLM.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0-1)

        Returns:
            Dictionary with 'content' and 'usage' keys
        """
        try:
            if self.provider == "openai":
                return await self._generate_openai(
                    prompt, system_prompt, max_tokens, temperature
                )
            elif self.provider == "anthropic":
                return await self._generate_anthropic(
                    prompt, system_prompt, max_tokens, temperature
                )
            else:
                raise LLMConfigError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        """Generate text using OpenAI"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = await asyncio.to_thread(
            self._client.chat.completions.create,  # type: ignore[attr-defined]
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

        # Track token usage
        if hasattr(response, "usage"):
            self.total_tokens += response.usage.total_tokens
            self._record_cost(
                response.usage.prompt_tokens, response.usage.completion_tokens
            )

        return {
            "content": response.choices[0].message.content,
            "usage": (
                {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }
                if hasattr(response, "usage")
                else {}
            ),
        }

    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: str | None,
        max_tokens: int,
        temperature: float,
    ) -> dict[str, Any]:
        """Generate text using Anthropic"""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = await asyncio.to_thread(
            self._client.messages.create,  # type: ignore[attr-defined]
            **kwargs,
        )

        # Track token usage
        if hasattr(response, "usage"):
            self.total_tokens += (
                response.usage.input_tokens + response.usage.output_tokens
            )
            self._record_cost(response.usage.input_tokens, response.usage.output_tokens)

        return {
            "content": response.content[0].text,
            "usage": (
                {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens
                    + response.usage.output_tokens,
                }
                if hasattr(response, "usage")
                else {}
            ),
        }

    def get_token_usage(self) -> int:
        """
        Get total token usage across all requests.

        Returns:
            Total tokens used
        """
        return self.total_tokens

    def reset_token_usage(self):
        """Reset token usage counter"""
        self.total_tokens = 0

    # ------------------------------------------------------------------
    # Cost tracking
    # ------------------------------------------------------------------

    def _record_cost(self, input_tokens: int, output_tokens: int) -> None:
        """Accumulate cost and append a record to the costs JSONL file."""
        price_in, price_out = self._PRICING.get(self.model, (0.01, 0.03))
        call_cost = (input_tokens / 1000 * price_in) + (
            output_tokens / 1000 * price_out
        )
        self._session_input_tokens += input_tokens
        self._session_output_tokens += output_tokens
        self._session_cost_usd += call_cost
        record = {
            "timestamp": datetime.now().isoformat(),
            "model": self.model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(call_cost, 6),
            "session_total_usd": round(self._session_cost_usd, 6),
        }
        logger.info(
            "LLM cost: $%.4f (in=%d, out=%d) session_total=$%.4f",
            call_cost,
            input_tokens,
            output_tokens,
            self._session_cost_usd,
        )
        try:
            with open(self._costs_file, "a") as f:
                f.write(json.dumps(record) + "\n")
        except Exception as exc:
            logger.warning("Failed to write cost record: %s", exc)

    def get_session_cost(self) -> dict[str, Any]:
        """Return session-level token and cost summary."""
        return {
            "model": self.model,
            "input_tokens": self._session_input_tokens,
            "output_tokens": self._session_output_tokens,
            "total_tokens": self._session_input_tokens + self._session_output_tokens,
            "cost_usd": round(self._session_cost_usd, 6),
        }

    def cost_limit_exceeded(self, max_usd: float) -> bool:
        """Return True if session cost has exceeded *max_usd*."""
        return self._session_cost_usd > max_usd
