"""LaunchDarkly AI Config integration."""

import os
import time
from functools import lru_cache
from typing import Any, Optional

import ldclient
from dotenv import load_dotenv
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from ldclient import Context
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig, ModelConfig, ProviderConfig

# Load environment variables
load_dotenv()


class LaunchDarklyClient:
    """LaunchDarkly client wrapper for AI Configs."""

    def __init__(self):
        """Initialize LaunchDarkly client.
        
        Raises:
            ValueError: If LaunchDarkly is not enabled or SDK key is missing
        """
        self.sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
        self.enabled = os.getenv("LAUNCHDARKLY_ENABLED", "false").lower() == "true"

        if not self.enabled:
            raise ValueError(
                "LaunchDarkly is required. Set LAUNCHDARKLY_ENABLED=true in your environment."
            )
        
        if not self.sdk_key:
            raise ValueError(
                "LAUNCHDARKLY_SDK_KEY is required. Set it in your environment variables."
            )

        # Initialize LaunchDarkly SDK (following LaunchDarkly Python SDK pattern)
        ldclient.set_config(Config(self.sdk_key))
        
        # Wait briefly for async initialization (LaunchDarkly SDK initializes asynchronously)
        import time
        max_wait = 5  # seconds
        start_time = time.time()
        while not ldclient.get().is_initialized():
            if time.time() - start_time > max_wait:
                raise RuntimeError(
                    "LaunchDarkly SDK failed to initialize. Please check your internet connection "
                    "and SDK credential for any typo."
                )
            time.sleep(0.1)
        
        self.client = ldclient.get()
        self.ai_client = LDAIClient(self.client)
        print("✅ LaunchDarkly AI Config initialized")

    def get_ai_config(
        self,
        config_key: str,
        context: Optional[dict[str, Any]] = None,
        default_config: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], Any]:
        """Retrieve AI configuration from LaunchDarkly.

        Args:
            config_key: The AI config key in LaunchDarkly
            context: User/session context for targeting
            default_config: Default configuration fallback

        Returns:
            Tuple of (config_value, tracker) for the AI config
            
        Raises:
            RuntimeError: If LaunchDarkly client is not initialized
        """
        if not self.ai_client:
            raise RuntimeError("LaunchDarkly client is not initialized. Check your SDK key.")

        # Create LaunchDarkly context
        ld_context = self._create_context(context or {})

        # Default configuration - convert dict to AIConfig if needed
        if default_config:
            default_ai_config = self._dict_to_ai_config(default_config)
        else:
            default_ai_config = self._get_default_ai_config()

        # Try agent-based config first (using .agents() method)
        try:
            result = self.ai_client.agents([config_key], ld_context, {})
            agents = result.get("agents", {})
            
            if config_key in agents and agents[config_key].get("enabled"):
                agent = agents[config_key]
                
                # Extract and convert agent config to standard dict format
                config_dict = {
                    "enabled": agent.get("enabled", True),
                    "provider": agent.get("provider", {}).get("name", "") if isinstance(agent.get("provider"), dict) else str(agent.get("provider", "")),
                }
                
                # Extract model config
                if agent.get("model"):
                    model = agent["model"]
                    config_dict["model"] = {
                        "name": model.get("name", ""),
                        "parameters": model.get("parameters", {}),
                    }
                    if model.get("custom"):
                        config_dict["model"]["custom"] = model["custom"]
                
                # Convert instructions to messages format for consistency
                if agent.get("instructions"):
                    config_dict["messages"] = [
                        {"role": "system", "content": agent["instructions"]}
                    ]
                
                tracker = agent.get("tracker")
                print(f"✅ Retrieved AI config '{config_key}' from LaunchDarkly (agent-based)")
                return config_dict, tracker
        except Exception as e:
            print(f"  ℹ️  Agent-based config not found, trying completion-based...")

        # Fall back to completion-based config (using .config() method)
        try:
            config_value, tracker = self.ai_client.config(
                config_key, ld_context, default_ai_config, {}
            )
            
            # Convert AIConfig to dict
            config_dict = self._ai_config_to_dict(config_value)
            
            # Check if config came from LaunchDarkly
            default_dict = self._ai_config_to_dict(default_ai_config)
            
            is_from_ld = (
                config_dict.get("model", {}).get("name") != default_dict.get("model", {}).get("name") or
                config_dict.get("provider") != default_dict.get("provider") or
                "custom" in config_dict.get("model", {}) or
                config_dict.get("messages")
            )
            
            if is_from_ld:
                print(f"✅ Retrieved AI config '{config_key}' from LaunchDarkly (completion-based)")
            else:
                error_msg = f"CATASTROPHIC: AI config '{config_key}' not found in LaunchDarkly!"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            return config_dict, tracker
            
        except Exception as e:
            print(f"❌ CATASTROPHIC: Error retrieving AI config '{config_key}': {e}")
            raise RuntimeError(f"Failed to retrieve AI config '{config_key}' from LaunchDarkly: {e}")

    def _create_context(self, context_dict: dict[str, Any]) -> Context:
        """Create LaunchDarkly context from dictionary.

        Args:
            context_dict: Context attributes

        Returns:
            LaunchDarkly Context object
        """
        # Extract user key (or use default)
        user_key = context_dict.get("user_key", "anonymous")

        # Build context with additional attributes
        context_builder = Context.builder(user_key)

        # Add custom attributes
        for key, value in context_dict.items():
            if key != "user_key":
                context_builder.set(key, value)

        return context_builder.build()

    def _get_default_config(self) -> dict[str, Any]:
        """Get default AI configuration as dict.

        Returns:
            Default configuration dictionary
        """
        provider = os.getenv("LLM_PROVIDER", "bedrock")
        model = os.getenv("LLM_MODEL", "claude-3-5-sonnet")

        return {
            "model": {
                "name": model,
                "parameters": {"temperature": 0.7, "maxTokens": 2000},
            },
            "provider": provider,
            "enabled": True,
        }

    def _get_default_ai_config(self) -> AIConfig:
        """Get default AI configuration as AIConfig object.

        Returns:
            Default AIConfig object
        """
        provider = os.getenv("LLM_PROVIDER", "bedrock")
        model = os.getenv("LLM_MODEL", "claude-3-5-sonnet")

        model_config = ModelConfig(
            name=model,
            parameters={"temperature": 0.7, "maxTokens": 2000}
        )
        provider_config = ProviderConfig(name=provider)
        return AIConfig(
            enabled=True,
            model=model_config,
            provider=provider_config
        )

    def _dict_to_ai_config(self, config_dict: dict[str, Any]) -> AIConfig:
        """Convert dict config to AIConfig object.

        Args:
            config_dict: Configuration dictionary

        Returns:
            AIConfig object
        """
        model_dict = config_dict.get("model", {})
        model_config = ModelConfig(
            name=model_dict.get("name", "claude-3-5-sonnet"),
            parameters=model_dict.get("parameters", {"temperature": 0.7, "maxTokens": 2000})
        )
        provider_config = ProviderConfig(name=config_dict.get("provider", "bedrock"))
        return AIConfig(
            enabled=config_dict.get("enabled", True),
            model=model_config,
            provider=provider_config
        )

    def _ai_config_to_dict(self, ai_config: AIConfig) -> dict[str, Any]:
        """Convert AIConfig object to dict.

        Args:
            ai_config: AIConfig object

        Returns:
            Configuration dictionary
        """
        # Use to_dict() method which handles all the conversion
        config_dict = ai_config.to_dict()
        
        # Extract the structure we need
        result = {
            "enabled": config_dict.get("_ldMeta", {}).get("enabled", True),
        }
        
        # Extract prompts from LaunchDarkly AI Config
        # Support both prompt-based (messages array) and agent-based (_prompt field)
        if config_dict.get("messages"):
            # Prompt-based AI Config: uses messages array with roles
            result["messages"] = config_dict["messages"]
        elif config_dict.get("_prompt"):
            # Agent-based AI Config: uses _prompt field (Goal or task in UI)
            # Convert to messages format for consistency
            result["messages"] = [
                {"role": "system", "content": config_dict["_prompt"]}
            ]

        if config_dict.get("model"):
            model_dict = config_dict["model"]
            result["model"] = {
                "name": model_dict.get("name", ""),
                "parameters": model_dict.get("parameters", {}),
            }
            
            # Extract custom parameters from model.custom
            if model_dict.get("custom"):
                result["model"]["custom"] = model_dict["custom"]

        if config_dict.get("provider"):
            provider_dict = config_dict["provider"]
            result["provider"] = provider_dict.get("name", "")

        return result

    def format_messages(self, messages: list[dict], context_vars: dict[str, Any]) -> list[dict]:
        """Format LaunchDarkly messages with context variables.
        
        Replaces template variables like {{ldctx.name}} or {{variable_name}} with actual values.
        
        Args:
            messages: List of message dicts with 'role' and 'content' from LaunchDarkly
            context_vars: Dictionary of variables to substitute
            
        Returns:
            List of formatted messages
        """
        import re
        
        formatted_messages = []
        for msg in messages:
            content = msg.get("content", "")
            
            # Replace {{ldctx.attribute}} with context values
            def replace_ldctx(match):
                attr = match.group(1)
                return str(context_vars.get(attr, f"{{{{ldctx.{attr}}}}}"))  # Keep original if not found
            
            content = re.sub(r'\{\{ldctx\.(\w+)\}\}', replace_ldctx, content)
            
            # Replace {{variable_name}} with values
            def replace_var(match):
                var = match.group(1)
                return str(context_vars.get(var, f"{{{{{var}}}}}"))  # Keep original if not found
            
            content = re.sub(r'\{\{(\w+)\}\}', replace_var, content)
            
            formatted_messages.append({
                "role": msg.get("role", "user"),
                "content": content
            })
        
        return formatted_messages

    def close(self):
        """Close the LaunchDarkly client."""
        if self.client:
            self.client.close()


class NoOpTracker:
    """No-op tracker for when LaunchDarkly is disabled.
    
    Matches LaunchDarkly tracker API.
    """

    def track_duration_of(self, func):
        """Execute function and return result (no tracking)."""
        return func()

    def track_success(self):
        """No-op track success (no arguments)."""
        pass

    def track_error(self):
        """No-op track error (no arguments)."""
        pass

    def track_tokens(self, token_usage):
        """No-op track tokens."""
        pass


class ModelInvoker:
    """Helper class to invoke models with tracking.
    
    Follows the LaunchDarkly AI SDK tracking pattern from:
    https://github.com/launchdarkly/hello-python-ai/blob/main/examples/langchain_example.py
    """

    def __init__(self, model: BaseChatModel, tracker: Any):
        """Initialize model invoker.

        Args:
            model: The LangChain model to invoke
            tracker: LaunchDarkly tracker for metrics
        """
        self.model = model
        self.tracker = tracker

    def invoke(self, messages: list[BaseMessage]) -> Any:
        """Invoke the model with tracking.

        Args:
            messages: List of messages to send to the model

        Returns:
            Model response
        """
        try:
            # Use track_duration_of to wrap the model call (LaunchDarkly API)
            result = self.tracker.track_duration_of(lambda: self.model.invoke(messages))
            
            # Track success (no arguments)
            self.tracker.track_success()
            
            # Extract and track token usage if available
            if hasattr(result, "usage_metadata") and result.usage_metadata:
                from ldai.tracker import TokenUsage
                
                usage_data = result.usage_metadata
                token_usage = TokenUsage(
                    input=usage_data.get("input_tokens", 0),
                    output=usage_data.get("output_tokens", 0),
                    total=usage_data.get("total_tokens", 0)
                )
                self.tracker.track_tokens(token_usage)
            
            return result

        except Exception:
            # Track error (no arguments)
            self.tracker.track_error()
            raise

    def _extract_tokens(self, response: Any) -> dict[str, int]:
        """Extract token counts from response.

        Args:
            response: Model response

        Returns:
            Dictionary with token counts
        """
        tokens = {"input": 0, "output": 0, "total": 0}

        try:
            # Try to get usage metadata from response
            if hasattr(response, "usage_metadata"):
                usage = response.usage_metadata
                tokens["input"] = usage.get("input_tokens", 0)
                tokens["output"] = usage.get("output_tokens", 0)
                tokens["total"] = usage.get("total_tokens", 0)
            elif hasattr(response, "response_metadata"):
                # Alternative location for token data
                metadata = response.response_metadata
                if "token_usage" in metadata:
                    usage = metadata["token_usage"]
                    tokens["input"] = usage.get("prompt_tokens", 0)
                    tokens["output"] = usage.get("completion_tokens", 0)
                    tokens["total"] = usage.get("total_tokens", 0)
        except Exception:
            # If we can't extract tokens, just return zeros
            pass

        return tokens


@lru_cache(maxsize=1)
def get_ld_client() -> LaunchDarklyClient:
    """Get the singleton LaunchDarkly client.

    Returns:
        LaunchDarkly client instance
    """
    return LaunchDarklyClient()
