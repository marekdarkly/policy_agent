"""LLM configuration and initialization."""

import os
from functools import lru_cache
from typing import Any, Optional, Tuple

from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel

from .launchdarkly_config import ModelInvoker, get_ld_client

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


def get_llm_from_config(
    config_key: str,
    context: Optional[dict[str, Any]] = None,
    default_temperature: float = 0.7,
) -> Tuple[BaseChatModel, Any]:
    """Get LLM instance from LaunchDarkly AI Config.

    Args:
        config_key: The AI config key in LaunchDarkly
        context: User/session context for targeting
        default_temperature: Default temperature if not specified in config

    Returns:
        Tuple of (LLM instance, tracker) for metrics tracking
    """
    ld_client = get_ld_client()

    # Get AI config from LaunchDarkly
    config, tracker = ld_client.get_ai_config(config_key, context)

    # Extract model configuration
    model_config = config.get("model", {})
    model_name = model_config.get("name", os.getenv("LLM_MODEL", "gpt-4-turbo-preview"))
    provider = config.get("provider", os.getenv("LLM_PROVIDER", "openai")).lower()

    # Extract parameters
    params = model_config.get("parameters", {})
    temperature = params.get("temperature", default_temperature)
    max_tokens = params.get("maxTokens", 2000)

    # Create the LLM instance based on provider
    llm = _create_llm_for_provider(provider, model_name, temperature, max_tokens)

    return llm, tracker


def get_model_invoker(
    config_key: str,
    context: Optional[dict[str, Any]] = None,
    default_temperature: float = 0.7,
) -> ModelInvoker:
    """Get a ModelInvoker with tracking for the specified config.

    Args:
        config_key: The AI config key in LaunchDarkly
        context: User/session context for targeting
        default_temperature: Default temperature if not specified in config

    Returns:
        ModelInvoker instance with tracking
    """
    llm, tracker = get_llm_from_config(config_key, context, default_temperature)
    return ModelInvoker(llm, tracker)


def _create_llm_for_provider(
    provider: str, model_name: str, temperature: float, max_tokens: int
) -> BaseChatModel:
    """Create LLM instance for the specified provider.

    Args:
        provider: Provider name (openai, anthropic, etc.)
        model_name: Model name
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set in environment")

        return ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    elif provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")

        return ChatAnthropic(
            model=model_name,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key,
        )

    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
