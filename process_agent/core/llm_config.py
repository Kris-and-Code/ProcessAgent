"""LLM configuration and setup for ProcessAgent."""
from __future__ import annotations
import os
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class LLMConfig:
    """Configuration for LLM integration."""
    
    def __init__(self):
        """Initialize LLM configuration from environment variables."""
        self.api_key = os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")  # Default to cost-effective model
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))  # Low temperature for determinism
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "2000"))
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.use_llm = os.getenv("USE_LLM", "true").lower() == "true"
        
    @property
    def is_available(self) -> bool:
        """Check if LLM is configured and available."""
        return self.use_llm and self.api_key is not None
    
    def get_provider(self) -> str:
        """Determine LLM provider from API key."""
        if os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"
        else:
            return "openai"  # Default


# Global config instance
_llm_config: Optional[LLMConfig] = None


def get_llm_config() -> LLMConfig:
    """Get or create LLM configuration instance."""
    global _llm_config
    if _llm_config is None:
        _llm_config = LLMConfig()
    return _llm_config



