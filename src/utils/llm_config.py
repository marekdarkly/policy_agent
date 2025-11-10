"""LLM configuration and initialization."""

import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

# Load environment variables
load_dotenv()


@lru_cache(maxsize=1)
def get_llm(temperature: float = 0.7) -> BaseChatModel:
    """Get configured LLM instance.

    Args:
        temperature: Sampling temperature (0-1)

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If LLM provider is not configured correctly
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("LLM_MODEL")

    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        return ChatOpenAI(
            model=model or "gpt-4-turbo-preview",
            temperature=temperature,
            api_key=api_key,
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        return ChatAnthropic(
            model=model or "claude-3-5-sonnet-20241022",
            temperature=temperature,
            api_key=api_key,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")


def get_structured_llm(temperature: float = 0.0):
    """Get LLM configured for structured output (JSON mode).

    Args:
        temperature: Sampling temperature (lower for more deterministic output)

    Returns:
        LLM configured for JSON output
    """
    llm = get_llm(temperature=temperature)

    # Configure for JSON output based on provider
    provider = os.getenv("LLM_PROVIDER", "openai").lower()

    if provider == "openai":
        # OpenAI supports JSON mode
        llm.model_kwargs = {"response_format": {"type": "json_object"}}

    # Anthropic doesn't have native JSON mode, but will follow instructions

    return llm
