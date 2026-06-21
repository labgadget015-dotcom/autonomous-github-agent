"""LLM client for AI-powered code analysis and generation."""

from anthropic import Anthropic
from openai import OpenAI

from autonomous_agent.core.config import get_config


class LLMClient:
    """Unified interface for different LLM providers."""

    def __init__(self):
        """Initialize LLM client based on configuration."""
        config = get_config()
        self.provider = config.llm.provider
        self.model = config.llm.model
        self.temperature = config.llm.temperature
        self.max_tokens = config.llm.max_tokens

        if self.provider == "openai":
            self.client = OpenAI(api_key=config.llm.api_key)
        elif self.provider == "anthropic":
            self.client = Anthropic(api_key=config.llm.api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def complete(self, prompt: str, system: str | None = None) -> str:
        """Get a completion from the LLM."""
        if self.provider == "openai":
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content

        elif self.provider == "anthropic":
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system or "",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text

        raise ValueError(f"Unsupported provider: {self.provider}")

    def analyze_code(self, code: str, task: str) -> str:
        """Analyze code with a specific task."""
        system = "You are an expert code reviewer and security analyst."
        prompt = f"{task}\n\nCode:\n```\n{code}\n```"
        return self.complete(prompt, system=system)
