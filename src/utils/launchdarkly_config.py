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
from ldai.client import LDAIClient

# Load environment variables
load_dotenv()


class LaunchDarklyClient:
    """LaunchDarkly client wrapper for AI Configs."""

    def __init__(self):
        """Initialize LaunchDarkly client."""
        self.sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
        self.enabled = os.getenv("LAUNCHDARKLY_ENABLED", "false").lower() == "true"

        if self.enabled and self.sdk_key:
            # Initialize LaunchDarkly SDK
            ldclient.set_config(Config(self.sdk_key))
            if ldclient.get().is_initialized():
                self.client = ldclient.get()
                self.ai_client = LDAIClient(self.client)
                print("✅ LaunchDarkly AI Config initialized")
            else:
                print("⚠️  LaunchDarkly SDK failed to initialize")
                self.enabled = False
                self.client = None
                self.ai_client = None
        else:
            self.client = None
            self.ai_client = None
            if not self.enabled:
                print("ℹ️  LaunchDarkly AI Config disabled (using default LLM config)")

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
            default_config: Default configuration if LaunchDarkly is unavailable

        Returns:
            Tuple of (config_value, tracker) for the AI config
        """
        if not self.enabled or not self.ai_client:
            # Return default config with no-op tracker
            default = default_config or self._get_default_config()
            return default, NoOpTracker()

        # Create LaunchDarkly context
        ld_context = self._create_context(context or {})

        # Default configuration
        default = default_config or self._get_default_config()

        try:
            # Get AI config from LaunchDarkly
            config_value, tracker = self.ai_client.config(
                config_key, ld_context, default, {}
            )
            return config_value, tracker
        except Exception as e:
            print(f"⚠️  Error retrieving AI config '{config_key}': {e}")
            return default, NoOpTracker()

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
        """Get default AI configuration.

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

    def close(self):
        """Close the LaunchDarkly client."""
        if self.client:
            self.client.close()


class NoOpTracker:
    """No-op tracker for when LaunchDarkly is disabled."""

    def track_success(self, duration: float, tokens: dict[str, int]):
        """No-op track success."""
        pass

    def track_error(self, error: Exception):
        """No-op track error."""
        pass

    def track_duration(self, duration: float):
        """No-op track duration."""
        pass


class ModelInvoker:
    """Helper class to invoke models with tracking."""

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
        start_time = time.time()

        try:
            # Invoke the model
            response = self.model.invoke(messages)

            # Calculate duration
            duration = time.time() - start_time

            # Extract token usage if available
            tokens = self._extract_tokens(response)

            # Track success
            self.tracker.track_success(duration=duration, tokens=tokens)

            return response

        except Exception as e:
            # Track error
            self.tracker.track_error(e)
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
