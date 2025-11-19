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

        # DON'T call ldclient.set_config() here - observability.py already initialized it!
        # Calling set_config() again would overwrite the ObservabilityPlugin.
        # Just get the existing client that was initialized with the plugin.
        
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
        
        # Use the already-initialized client (with ObservabilityPlugin from observability.py)
        self.client = ldclient.get()
        self.ai_client = LDAIClient(self.client)
        print("✅ LaunchDarkly AI Config client ready (using observability-enabled SDK)")

    def get_ai_config(
        self,
        config_key: str,
        context: Optional[dict[str, Any]] = None,
        default_config: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], Any, Context]:
        """Retrieve AI configuration from LaunchDarkly.

        Args:
            config_key: The AI config key in LaunchDarkly
            context: User/session context for targeting
            default_config: Default configuration fallback

        Returns:
            Tuple of (config_value, tracker, ld_context) for the AI config
            
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

        # Get variation detail first to capture variation key
        variation_detail = self.client.variation_detail(config_key, ld_context, False)
        variation_index = variation_detail.variation_index if variation_detail else None
        
        # Debug: show what we got from variation_detail
        print(f"🐛 DEBUG: variation_detail = {variation_detail}")
        print(f"🐛 DEBUG: variation_index = {variation_index}")
        if variation_detail and hasattr(variation_detail, 'value'):
            if isinstance(variation_detail.value, dict):
                print(f"🐛 DEBUG: variation_detail.value keys = {list(variation_detail.value.keys())}")
        
        # Try agent-based config first (using .agents() method)
        try:
            from ldai.client import LDAIAgentConfig, LDAIAgentDefaults
            
            # Create agent config with defaults
            agent_config = LDAIAgentConfig(
                key=config_key,
                default_value=LDAIAgentDefaults(
                    enabled=True,
                    instructions="__DEFAULT_INSTRUCTIONS__"  # Sentinel value to detect if it's actually from LD
                )
            )
            
            agents = self.ai_client.agents([agent_config], ld_context)
            
            if config_key in agents and agents[config_key].enabled:
                agent = agents[config_key]
                
                # Check if this is actually an agent-based config (has non-default instructions)
                has_instructions = (
                    hasattr(agent, 'instructions') and 
                    agent.instructions and 
                    agent.instructions != "__DEFAULT_INSTRUCTIONS__"
                )
                
                if has_instructions:
                    # This is truly an agent-based config (has "Goal or task" field)
                    # Use agent.to_dict() to get all data including custom parameters
                    agent_dict = agent.to_dict()
                    
                    # Debug: print full agent_dict structure
                    print(f"🐛 DEBUG: Full agent_dict keys = {list(agent_dict.keys())}")
                    
                    # Extract provider
                    provider_value = ""
                    if agent_dict.get("provider"):
                        provider_dict = agent_dict["provider"]
                        provider_value = provider_dict.get("name", "") if isinstance(provider_dict, dict) else str(provider_dict)
                    
                    # Get variation name from variation_detail 
                    variation_name = f"variation-{variation_index}" if variation_index is not None else "unknown"
                    
                    config_dict = {
                        "enabled": ld_meta.get("enabled", True),
                        "provider": provider_value,
                        "_variation": variation_name,  # Store variation name in config
                    }
                    
                    # Extract model config with custom parameters
                    if agent_dict.get("model"):
                        model_dict = agent_dict["model"]
                        config_dict["model"] = {
                            "name": model_dict.get("name", ""),
                            "parameters": model_dict.get("parameters", {}),
                        }
                        # Custom parameters (like awskbid) are available in agent.to_dict()!
                        if model_dict.get("custom"):
                            config_dict["model"]["custom"] = model_dict["custom"]
                    
                    # Store instructions separately (not as messages)
                    config_dict["_instructions"] = agent_dict.get("instructions", "")
                    
                    tracker = agent.tracker
                    # Variation logging is now handled by individual agents
                    return config_dict, tracker, ld_context
                # If no instructions, this is a completion-based config, fall through
        except Exception as e:
            # Agent-based retrieval failed, will try completion-based
            pass

        # Fall back to completion-based config (using .config() method)
        try:
            config_value, tracker = self.ai_client.config(
                config_key, ld_context, default_ai_config, {}
            )
            
            # Convert AIConfig to dict
            config_dict = self._ai_config_to_dict(config_value)
            
            # Use variation from variation_detail we fetched earlier
            config_dict["_variation"] = f"variation-{variation_index}" if variation_index is not None else "unknown"
            
            # Check if config came from LaunchDarkly
            default_dict = self._ai_config_to_dict(default_ai_config)
            
            is_from_ld = (
                config_dict.get("model", {}).get("name") != default_dict.get("model", {}).get("name") or
                config_dict.get("provider") != default_dict.get("provider") or
                "custom" in config_dict.get("model", {}) or
                config_dict.get("messages")
            )
            
            if is_from_ld:
                # Variation logging is now handled by individual agents
                pass
            else:
                error_msg = f"CATASTROPHIC: AI config '{config_key}' not found in LaunchDarkly!"
                print(f"❌ {error_msg}")
                raise RuntimeError(error_msg)
            
            return config_dict, tracker, ld_context
            
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

    def build_langchain_messages(self, ld_config: dict[str, Any], context_vars: dict[str, Any]) -> list:
        """Build LangChain messages from LaunchDarkly config (agent-based or completion-based).
        
        Args:
            ld_config: The LaunchDarkly AI config dict
            context_vars: Variables for template replacement
            
        Returns:
            List of LangChain message objects (SystemMessage, HumanMessage, AIMessage)
        """
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        import json
        
        langchain_messages = []
        
        if "_instructions" in ld_config:
            # Agent-based config: instructions + user query
            instructions = ld_config["_instructions"]
            # Replace template variables in instructions
            for key, value in context_vars.items():
                instructions = instructions.replace(f"{{{{{key}}}}}", str(value))
                instructions = instructions.replace(f"{{{{ldctx.{key}}}}}", str(value))
            
            # System message with instructions, then user message with query
            query = context_vars.get("query", "")
            user_context = {k: v for k, v in context_vars.items() if k != "query"}
            langchain_messages = [
                SystemMessage(content=instructions),
                HumanMessage(content=f"User query: {query}\n\nUser context:\n{json.dumps(user_context, indent=2, default=str)}")
            ]
        elif "messages" in ld_config:
            # Completion-based config: use messages from LaunchDarkly
            ld_messages = ld_config["messages"]
            formatted_messages = self.format_messages(ld_messages, context_vars)
            
            # Convert to LangChain message format
            has_user_message = False
            for msg in formatted_messages:
                if msg["role"] == "system":
                    langchain_messages.append(SystemMessage(content=msg["content"]))
                elif msg["role"] == "user":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                    has_user_message = True
                else:
                    langchain_messages.append(AIMessage(content=msg["content"]))
            
            # AWS Bedrock requires conversations to start with a user message
            # If we only have a system message, add a user message with query
            if not has_user_message and langchain_messages:
                query = context_vars.get("query", "")
                user_context_minimal = {k: v for k, v in context_vars.items() if k not in ["query"]}
                user_msg = f"User query: {query}\n\nContext:\n{json.dumps(user_context_minimal, indent=2, default=str)}"
                langchain_messages.append(HumanMessage(content=user_msg))
        else:
            raise RuntimeError(
                f"❌ CATASTROPHIC: No messages or instructions found in LaunchDarkly AI Config!\n"
                f"  This means the config exists but has no prompt/instructions configured.\n"
                f"  Please configure either:\n"
                f"  - For agent-based: Set 'Goal or task' field\n"
                f"  - For completion-based: Add messages in 'Prompt' section"
            )
        
        return langchain_messages

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

    def __init__(
        self,
        model: BaseChatModel,
        tracker: Any,
        config_key: str = "",
        is_agent_config: bool = False,
        user_context: Optional[Context] = None,
        skip_span_annotation: bool = False
    ):
        """Initialize model invoker.

        Args:
            model: The LangChain model to invoke
            tracker: LaunchDarkly tracker for metrics
            config_key: The AI Config key (for observability linking)
            is_agent_config: Whether this is an agent-based config
            user_context: LaunchDarkly user context (for span annotation)
            skip_span_annotation: If True, skip all span annotation (for background threads)
        """
        self.model = model
        self.tracker = tracker
        self.config_key = config_key
        self._is_agent_config = is_agent_config
        self.user_context = user_context
        self.skip_span_annotation = skip_span_annotation

    def invoke(self, messages: list[BaseMessage]) -> Any:
        """Invoke the model with tracking.

        Args:
            messages: List of messages to send to the model

        Returns:
            Model response
        """
        try:
            # Skip span annotation entirely if flag is set (background threads like judges)
            if not self.skip_span_annotation:
                # Set ld.ai_config.key on the CURRENT span for THIS agent
                # Skip span annotation for background threads (judges) - they reference closed spans
                try:
                    from opentelemetry import trace
                    
                    current_span = trace.get_current_span()
                    
                    # Check if span is valid and recording BEFORE any operations
                    # Background threads will have invalid/ended spans - skip them entirely
                    if (current_span and 
                        self.config_key and 
                        hasattr(current_span, 'is_recording') and 
                        current_span.is_recording()):
                        
                        # Additional check: is this a valid span context?
                        span_context = current_span.get_span_context()
                        if not span_context or not span_context.is_valid:
                            # Invalid context - skip annotation (background thread)
                            pass
                        else:
                            # Valid, recording span - safe to annotate
                            try:
                                current_span.set_attribute("ld.ai_config.key", self.config_key)
                                
                                # Add feature_flag event
                                if self.user_context:
                                    ctx_dict = self.user_context.to_dict() if hasattr(self.user_context, 'to_dict') else {}
                                    ctx_id = ctx_dict.get('key') or ctx_dict.get('userKey') or 'anonymous'
                                    
                                    current_span.add_event(
                                        "feature_flag",
                                        attributes={
                                            "feature_flag.key": self.config_key,
                                            "feature_flag.provider.name": "LaunchDarkly",
                                            "feature_flag.context.id": ctx_id,
                                            "feature_flag.result.value": True,
                                        },
                                    )
                                
                                # Trigger LD variation for correlation
                                if self.user_context:
                                    _ = ldclient.get().variation(self.config_key, self.user_context, True)
                            except Exception:
                                # Silently ignore any annotation errors - don't let them break LLM calls
                                pass
                                
                except Exception:
                    # Don't fail model invocation if span annotation fails entirely
                    pass
            
            # Track the LLM call
            result = self.tracker.track_duration_of(lambda: self.model.invoke(messages))
            
            # Track success (no arguments)
            self.tracker.track_success()
            
            # Extract and track token usage if available
            if hasattr(result, "usage_metadata") and result.usage_metadata:
                from ldai.tracker import TokenUsage
                import random
                
                usage_data = result.usage_metadata
                
                # Extract actual token usage (no jitter)
                input_tokens = usage_data.get("input_tokens", 0)
                output_tokens = usage_data.get("output_tokens", 0)
                total_tokens = input_tokens + output_tokens
                
                token_usage = TokenUsage(
                    input=input_tokens,
                    output=output_tokens,
                    total=total_tokens
                )
                self.tracker.track_tokens(token_usage)
            
            # Extract and track Time to First Token (TTFT) if available
            ttft_ms = None
            if hasattr(result, "response_metadata") and isinstance(result.response_metadata, dict):
                ttft_ms = result.response_metadata.get("ttft_ms")
            elif hasattr(result, "generations") and len(result.generations) > 0:
                gen = result.generations[0]
                if hasattr(gen, "message") and hasattr(gen.message, "response_metadata"):
                    ttft_ms = gen.message.response_metadata.get("ttft_ms")
            
            # Track TTFT in LaunchDarkly if available
            if ttft_ms is not None:
                try:
                    self.tracker.track_time_to_first_token(ttft_ms)
                except Exception as e:
                    # Don't fail if TTFT tracking fails
                    import logging
                    logging.debug(f"Failed to track TTFT: {e}")
            
            return result

        except Exception as e:
            # Track error (no arguments)
            self.tracker.track_error()
            
            # Mark span as error if available
            try:
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    from opentelemetry.trace import Status, StatusCode
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
            except:
                pass
                
            raise
    
    def stream(self, messages: list[BaseMessage]):
        """Stream the model response with tracking.
        
        Args:
            messages: List of messages to send to the model
            
        Yields:
            Chunks from the model as they arrive
        """
        try:
            # Skip span annotation for streaming (same as invoke)
            if not self.skip_span_annotation:
                try:
                    from opentelemetry import trace
                    current_span = trace.get_current_span()
                    
                    if (current_span and 
                        self.config_key and 
                        hasattr(current_span, 'is_recording') and 
                        current_span.is_recording()):
                        
                        span_context = current_span.get_span_context()
                        if not span_context or not span_context.is_valid:
                            pass
                        else:
                            try:
                                current_span.set_attribute("ld.ai_config.key", self.config_key)
                                
                                if self.user_context:
                                    ctx_dict = self.user_context.to_dict() if hasattr(self.user_context, 'to_dict') else {}
                                    ctx_id = ctx_dict.get('key') or ctx_dict.get('userKey') or 'anonymous'
                                    
                                    current_span.add_event(
                                        "feature_flag",
                                        attributes={
                                            "feature_flag.key": self.config_key,
                                            "feature_flag.provider.name": "LaunchDarkly",
                                            "feature_flag.context.id": ctx_id,
                                            "feature_flag.result.value": True,
                                        },
                                    )
                                
                                if self.user_context:
                                    _ = ldclient.get().variation(self.config_key, self.user_context, True)
                            except Exception:
                                pass
                except Exception:
                    pass
            
            # Track start time for duration
            import time
            start_time = time.time()
            
            # Stream from the model
            accumulated_tokens = {"input": 0, "output": 0, "total": 0}
            ttft_ms = None
            
            for chunk in self.model.stream(messages):
                # Extract TTFT from first chunk
                if ttft_ms is None:
                    chunk_metadata = chunk.message.response_metadata if hasattr(chunk, 'message') else {}
                    if isinstance(chunk_metadata, dict):
                        ttft_ms = chunk_metadata.get("ttft_ms")
                
                # Extract token usage from final chunk
                if hasattr(chunk, 'message') and hasattr(chunk.message, 'usage_metadata'):
                    if chunk.message.usage_metadata:
                        accumulated_tokens = {
                            "input": chunk.message.usage_metadata.get("input_tokens", 0),
                            "output": chunk.message.usage_metadata.get("output_tokens", 0),
                            "total": chunk.message.usage_metadata.get("total_tokens", 0)
                        }
                
                yield chunk
            
            # Track metrics after streaming completes
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Track success
            self.tracker.track_success()
            
            # Track duration manually
            self.tracker.track_duration(duration_ms)
            
            # Track tokens if we got them
            if accumulated_tokens["total"] > 0:
                from ldai.tracker import TokenUsage
                token_usage = TokenUsage(
                    input=accumulated_tokens["input"],
                    output=accumulated_tokens["output"],
                    total=accumulated_tokens["total"]
                )
                self.tracker.track_tokens(token_usage)
            
            # Track TTFT if we got it
            if ttft_ms is not None:
                try:
                    self.tracker.track_time_to_first_token(ttft_ms)
                except Exception as e:
                    import logging
                    logging.debug(f"Failed to track TTFT: {e}")
        
        except Exception as e:
            self.tracker.track_error()
            
            try:
                from opentelemetry import trace
                span = trace.get_current_span()
                if span and span.is_recording():
                    from opentelemetry.trace import Status, StatusCode
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
            except:
                pass
            
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
