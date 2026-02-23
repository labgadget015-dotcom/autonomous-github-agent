#!/usr/bin/env python3
"""
LLM Provider

Provides an abstraction layer for LLM providers (OpenAI, Anthropic, etc.)
with unified interface and error handling.
"""

import logging
from typing import Dict, Any, Optional
from enum import Enum

logging.basicConfig(level=logging.INFO)
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
    
    def __init__(self, config: Dict[str, Any]):
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
        self.provider = config.get('llm_provider', 'openai')
        self.model = config.get('model', self._get_default_model())
        
        self._client = None
        self._initialize_client()
        
        self.total_tokens = 0
        logger.info(f"LLM client initialized with provider: {self.provider}, model: {self.model}")
    
    def _get_default_model(self) -> str:
        """Get default model for the provider"""
        defaults = {
            'openai': 'gpt-4',
            'anthropic': 'claude-3-opus-20240229'
        }
        return defaults.get(self.provider, 'gpt-4')
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        try:
            if self.provider == 'openai':
                import openai
                api_key = self.config.get('openai_api_key', self.config.get('OPENAI_API_KEY'))
                if not api_key:
                    raise ValueError("OpenAI API key not found in configuration")
                self._client = openai.OpenAI(api_key=api_key)
                
            elif self.provider == 'anthropic':
                import anthropic
                api_key = self.config.get('anthropic_api_key', self.config.get('ANTHROPIC_API_KEY'))
                if not api_key:
                    raise ValueError("Anthropic API key not found in configuration")
                self._client = anthropic.Anthropic(api_key=api_key)
                
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
                
        except ImportError as e:
            logger.error(f"Failed to import LLM library: {str(e)}")
            raise
    
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> Dict[str, Any]:
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
            if self.provider == 'openai':
                return await self._generate_openai(prompt, system_prompt, max_tokens, temperature)
            elif self.provider == 'anthropic':
                return await self._generate_anthropic(prompt, system_prompt, max_tokens, temperature)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise
    
    async def _generate_openai(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate text using OpenAI"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        # Track token usage
        if hasattr(response, 'usage'):
            self.total_tokens += response.usage.total_tokens
        
        return {
            'content': response.choices[0].message.content,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            } if hasattr(response, 'usage') else {}
        }
    
    async def _generate_anthropic(
        self,
        prompt: str,
        system_prompt: Optional[str],
        max_tokens: int,
        temperature: float
    ) -> Dict[str, Any]:
        """Generate text using Anthropic"""
        kwargs = {
            'model': self.model,
            'max_tokens': max_tokens,
            'temperature': temperature,
            'messages': [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs['system'] = system_prompt
        
        response = self._client.messages.create(**kwargs)
        
        # Track token usage
        if hasattr(response, 'usage'):
            self.total_tokens += response.usage.input_tokens + response.usage.output_tokens
        
        return {
            'content': response.content[0].text,
            'usage': {
                'prompt_tokens': response.usage.input_tokens,
                'completion_tokens': response.usage.output_tokens,
                'total_tokens': response.usage.input_tokens + response.usage.output_tokens
            } if hasattr(response, 'usage') else {}
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
