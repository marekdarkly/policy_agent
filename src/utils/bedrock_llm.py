"""AWS Bedrock LLM wrapper using the Converse API with streaming support."""

import json
import time
from typing import Any, Dict, Iterator, List, Optional

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from .aws_sso import get_sso_manager


class BedrockConverseLLM(BaseChatModel):
    """AWS Bedrock LLM using the Converse API.

    This wrapper uses Bedrock's Converse API which provides a unified interface
    across different model providers (Anthropic Claude, Meta Llama, etc.).
    """

    model_id: str
    """Bedrock model ID (e.g., 'anthropic.claude-3-sonnet-20240229-v1:0')"""

    temperature: float = 0.7
    """Sampling temperature (0-1)"""

    max_tokens: int = 2000
    """Maximum tokens to generate"""

    region: Optional[str] = None
    """AWS region for Bedrock"""

    profile_name: Optional[str] = None
    """AWS profile name"""

    aws_sso_manager: Any = None
    """AWS SSO manager instance"""

    _bedrock_client: Any = None
    """Cached Bedrock client to avoid creating new connections on every call"""

    def __init__(self, **kwargs):
        """Initialize Bedrock Converse LLM."""
        super().__init__(**kwargs)
        # Initialize SSO manager
        self.aws_sso_manager = get_sso_manager(
            profile_name=self.profile_name, region=self.region
        )
        # Create and cache the Bedrock client ONCE
        self._bedrock_client = self.aws_sso_manager.get_bedrock_client("bedrock-runtime")
        print(f"✅ Bedrock client cached for model {self.model_id}")

    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "bedrock-converse"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Get identifying parameters."""
        return {
            "model_id": self.model_id,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "region": self.region,
        }

    def _convert_messages_to_converse_format(
        self, messages: List[BaseMessage]
    ) -> tuple[List[Dict], Optional[List[Dict]]]:
        """Convert LangChain messages to Bedrock Converse format.

        Args:
            messages: List of LangChain messages

        Returns:
            Tuple of (messages, system_messages) in Bedrock format
        """
        converse_messages = []
        system_messages = []

        for message in messages:
            if isinstance(message, SystemMessage):
                system_messages.append({"text": message.content})
            elif isinstance(message, HumanMessage):
                converse_messages.append(
                    {"role": "user", "content": [{"text": message.content}]}
                )
            elif isinstance(message, AIMessage):
                converse_messages.append(
                    {"role": "assistant", "content": [{"text": message.content}]}
                )
            else:
                # Default to user message
                converse_messages.append(
                    {"role": "user", "content": [{"text": str(message.content)}]}
                )

        return converse_messages, system_messages if system_messages else None

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate a response from Bedrock Converse API (non-streaming).

        Uses the synchronous converse() API so that the full request duration is
        captured by auto-instrumented OTEL spans (e.g. BedrockInstrumentor).
        For streaming with TTFT tracking, callers should use stream() instead.

        Args:
            messages: List of messages
            stop: Stop sequences
            run_manager: Callback manager
            **kwargs: Additional arguments

        Returns:
            ChatResult with the response
        """
        bedrock_client = self._bedrock_client

        converse_messages, system_messages = self._convert_messages_to_converse_format(
            messages
        )

        inference_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "maxTokens": kwargs.get("max_tokens", self.max_tokens),
        }

        if stop:
            inference_config["stopSequences"] = stop

        api_params = {
            "modelId": self.model_id,
            "messages": converse_messages,
            "inferenceConfig": inference_config,
        }

        if system_messages:
            api_params["system"] = system_messages

        try:
            response = bedrock_client.converse(**api_params)

            output_message = response.get("output", {}).get("message", {})
            content_blocks = output_message.get("content", [])
            response_text = "".join(
                block.get("text", "") for block in content_blocks if "text" in block
            )

            usage = response.get("usage", {})
            token_usage = {
                "input_tokens": usage.get("inputTokens", 0),
                "output_tokens": usage.get("outputTokens", 0),
                "total_tokens": usage.get("totalTokens", 0),
            }
            stop_reason = response.get("stopReason")

            message = AIMessage(
                content=response_text,
                response_metadata={
                    "model_id": self.model_id,
                    "stop_reason": stop_reason,
                    "token_usage": token_usage,
                },
            )
            message.usage_metadata = token_usage

            return ChatResult(
                generations=[ChatGeneration(message=message)],
                llm_output={
                    "token_usage": token_usage,
                    "model_id": self.model_id,
                    "stop_reason": stop_reason,
                },
            )

        except Exception as e:
            if "credentials" in str(e).lower() or "expired" in str(e).lower():
                print("🔄 Credentials may be expired, attempting refresh...")
                if self.aws_sso_manager.force_refresh():
                    self._bedrock_client = self.aws_sso_manager.get_bedrock_client(
                        "bedrock-runtime"
                    )

                    response = self._bedrock_client.converse(**api_params)

                    output_message = response.get("output", {}).get("message", {})
                    content_blocks = output_message.get("content", [])
                    response_text = "".join(
                        block.get("text", "") for block in content_blocks
                        if "text" in block
                    )

                    usage = response.get("usage", {})
                    token_usage = {
                        "input_tokens": usage.get("inputTokens", 0),
                        "output_tokens": usage.get("outputTokens", 0),
                        "total_tokens": usage.get("totalTokens", 0),
                    }
                    stop_reason = response.get("stopReason")

                    message = AIMessage(
                        content=response_text,
                        response_metadata={
                            "model_id": self.model_id,
                            "stop_reason": stop_reason,
                            "token_usage": token_usage,
                        },
                    )
                    message.usage_metadata = token_usage

                    return ChatResult(
                        generations=[ChatGeneration(message=message)],
                        llm_output={
                            "token_usage": token_usage,
                            "model_id": self.model_id,
                            "stop_reason": stop_reason,
                        },
                    )

            raise

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """Stream responses from Bedrock using converseStream API.
        
        Yields chunks as they arrive from Bedrock.
        """
        bedrock_client = self._bedrock_client
        converse_messages, system_messages = self._convert_messages_to_converse_format(
            messages
        )
        inference_config = {
            "temperature": kwargs.get("temperature", self.temperature),
            "maxTokens": kwargs.get("max_tokens", self.max_tokens),
        }
        if stop:
            inference_config["stopSequences"] = stop
        api_params = {
            "modelId": self.model_id,
            "messages": converse_messages,
            "inferenceConfig": inference_config,
        }
        if system_messages:
            api_params["system"] = system_messages

        try:
            start_time = time.time()
            ttft_ms = None
            
            response_stream = bedrock_client.converse_stream(**api_params)
            
            accumulated_text = ""
            token_usage = {}
            stop_reason = None
            
            for event in response_stream["stream"]:
                # Capture TTFT on first content delta
                if ttft_ms is None and "contentBlockDelta" in event:
                    ttft_ms = int((time.time() - start_time) * 1000)
                
                # Yield each chunk as it arrives
                if "contentBlockDelta" in event:
                    delta = event["contentBlockDelta"].get("delta", {})
                    if "text" in delta:
                        chunk_text = delta["text"]
                        accumulated_text += chunk_text
                        
                        # Create a chunk with the incremental text
                        message = AIMessage(
                            content=chunk_text,
                            response_metadata={
                                "model_id": self.model_id,
                                "ttft_ms": ttft_ms,
                                "is_chunk": True,
                            },
                        )
                        yield ChatGeneration(message=message)
                
                # Capture final metadata
                if "metadata" in event:
                    metadata = event["metadata"]
                    usage = metadata.get("usage", {})
                    token_usage = {
                        "input_tokens": usage.get("inputTokens", 0),
                        "output_tokens": usage.get("outputTokens", 0),
                        "total_tokens": usage.get("totalTokens", 0),
                    }
                    stop_reason = metadata.get("stopReason")
            
            # Yield final metadata chunk
            if ttft_ms is None:
                ttft_ms = int((time.time() - start_time) * 1000)
            
            final_message = AIMessage(
                content="",  # Empty content for metadata-only message
                response_metadata={
                    "model_id": self.model_id,
                    "stop_reason": stop_reason,
                    "token_usage": token_usage,
                    "ttft_ms": ttft_ms,
                    "is_final": True,
                },
            )
            final_message.usage_metadata = token_usage
            yield ChatGeneration(message=final_message)

        except Exception as e:
            if "credentials" in str(e).lower() or "expired" in str(e).lower():
                print("🔄 Credentials may be expired, attempting refresh...")
                if self.aws_sso_manager.force_refresh():
                    self._bedrock_client = self.aws_sso_manager.get_bedrock_client(
                        "bedrock-runtime"
                    )
                    
                    # Retry streaming after refresh
                    start_time = time.time()
                    ttft_ms = None
                    
                    response_stream = self._bedrock_client.converse_stream(**api_params)
                    
                    accumulated_text = ""
                    token_usage = {}
                    stop_reason = None
                    
                    for event in response_stream["stream"]:
                        if ttft_ms is None and "contentBlockDelta" in event:
                            ttft_ms = int((time.time() - start_time) * 1000)
                        
                        if "contentBlockDelta" in event:
                            delta = event["contentBlockDelta"].get("delta", {})
                            if "text" in delta:
                                chunk_text = delta["text"]
                                accumulated_text += chunk_text
                                
                                message = AIMessage(
                                    content=chunk_text,
                                    response_metadata={
                                        "model_id": self.model_id,
                                        "ttft_ms": ttft_ms,
                                        "is_chunk": True,
                                    },
                                )
                                yield ChatGeneration(message=message)
                        
                        if "metadata" in event:
                            metadata = event["metadata"]
                            usage = metadata.get("usage", {})
                            token_usage = {
                                "input_tokens": usage.get("inputTokens", 0),
                                "output_tokens": usage.get("outputTokens", 0),
                                "total_tokens": usage.get("totalTokens", 0),
                            }
                            stop_reason = metadata.get("stopReason")
                    
                    if ttft_ms is None:
                        ttft_ms = int((time.time() - start_time) * 1000)
                    
                    final_message = AIMessage(
                        content="",
                        response_metadata={
                            "model_id": self.model_id,
                            "stop_reason": stop_reason,
                            "token_usage": token_usage,
                            "ttft_ms": ttft_ms,
                            "is_final": True,
                        },
                    )
                    final_message.usage_metadata = token_usage
                    yield ChatGeneration(message=final_message)

            raise


# Common Bedrock model IDs
BEDROCK_MODELS = {
    # Anthropic Claude models
    "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
    "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
    "claude-3-opus": "anthropic.claude-3-opus-20240229-v1:0",
    "claude-3-5-sonnet": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    # Meta Llama models
    "llama-3-8b": "meta.llama3-8b-instruct-v1:0",
    "llama-3-70b": "meta.llama3-70b-instruct-v1:0",
    "llama-3-1-8b": "meta.llama3-1-8b-instruct-v1:0",
    "llama-3-1-70b": "meta.llama3-1-70b-instruct-v1:0",
    "llama-3-1-405b": "meta.llama3-1-405b-instruct-v1:0",
    # Amazon Titan
    "titan-text-express": "amazon.titan-text-express-v1",
    "titan-text-lite": "amazon.titan-text-lite-v1",
}


def get_bedrock_model_id(model_name: str) -> str:
    """Get full Bedrock model ID from short name.

    Args:
        model_name: Short model name or full model ID

    Returns:
        Full Bedrock model ID
    """
    # If it's already a full model ID, return it
    if "." in model_name and ":" in model_name:
        return model_name

    # Otherwise, look up the short name
    return BEDROCK_MODELS.get(model_name, model_name)
