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
    provider = os.getenv("LLM_PROVIDER", "bedrock").lower()
    model = os.getenv("LLM_MODEL")

    if provider == "bedrock":
        from .bedrock_llm import BedrockConverseLLM, get_bedrock_model_id

        model_id = get_bedrock_model_id(model or "claude-3-5-sonnet")
        region = os.getenv("AWS_REGION", "us-east-1")
        profile = os.getenv("AWS_PROFILE")

        return BedrockConverseLLM(
            model_id=model_id,
            temperature=temperature,
            max_tokens=2000,
            region=region,
            profile_name=profile,
        )

    elif provider == "openai":
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
    provider_raw = config.get("provider", os.getenv("LLM_PROVIDER", "openai"))
    
    # Parse provider - LaunchDarkly returns formats like "Bedrock:Anthropic" or "Bedrock:Nova"
    # We need to extract just the main provider (the part before the colon)
    provider = provider_raw.split(':')[0].lower() if ':' in provider_raw else provider_raw.lower()

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
) -> Tuple[ModelInvoker, dict[str, Any]]:
    """Get a ModelInvoker with tracking and full config (including messages) from LaunchDarkly.

    Args:
        config_key: The AI config key in LaunchDarkly
        context: User/session context for targeting
        default_temperature: Default temperature if not specified in config

    Returns:
        Tuple of (ModelInvoker instance with tracking, full config dict including messages)
    """
    ld_client = get_ld_client()
    # Get config once from LaunchDarkly
    config, tracker = ld_client.get_ai_config(config_key, context)
    
    # Create LLM directly from the config (don't call get_llm_from_config which would retrieve again)
    provider = config.get("provider", "bedrock")
    # Parse provider name (e.g., "Bedrock:Anthropic" -> "bedrock")
    if ":" in provider:
        provider = provider.split(":")[0]
    provider = provider.lower().strip()
    
    model_config = config.get("model", {})
    model_name = model_config.get("name", "claude-3-5-sonnet")
    
    # Get temperature from config or use default
    parameters = model_config.get("parameters", {})
    temperature = parameters.get("temperature", default_temperature)
    max_tokens = parameters.get("max_tokens") or parameters.get("maxTokens", 2000)
    
    llm = _create_llm_for_provider(provider, model_name, temperature, max_tokens)
    
    return ModelInvoker(llm, tracker), config


def _create_llm_for_provider(
    provider: str, model_name: str, temperature: float, max_tokens: int
) -> BaseChatModel:
    """Create LLM instance for the specified provider.

    Args:
        provider: Provider name (bedrock, openai, anthropic, etc.)
                 Note: LaunchDarkly may return "Bedrock:Anthropic" format, but we parse it to just "bedrock"
        model_name: Model name or Bedrock model ID (e.g., "us.anthropic.claude-sonnet-4-20250514-v1:0")
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Configured LLM instance

    Raises:
        ValueError: If provider is not supported
    """
    # Normalize provider name - handle formats like "Bedrock:Anthropic" from LaunchDarkly
    provider_normalized = provider.split(':')[0].lower() if ':' in provider else provider.lower()
    
    if provider_normalized == "bedrock":
        from .bedrock_llm import BedrockConverseLLM, get_bedrock_model_id

        # Get full Bedrock model ID
        model_id = get_bedrock_model_id(model_name)

        # Get AWS configuration
        region = os.getenv("AWS_REGION", "us-east-1")
        profile = os.getenv("AWS_PROFILE")

        return BedrockConverseLLM(
            model_id=model_id,
            temperature=temperature,
            max_tokens=max_tokens,
            region=region,
            profile_name=profile,
        )

    elif provider_normalized == "openai":
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

    elif provider_normalized == "anthropic":
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
        raise ValueError(
            f"Unsupported LLM provider: {provider} (normalized: {provider_normalized}). "
            f"Supported providers: bedrock, openai, anthropic"
        )
