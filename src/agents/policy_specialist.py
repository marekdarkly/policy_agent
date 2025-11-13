"""Policy specialist agent for answering policy-related questions."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..graph.state import AgentState
from ..tools.bedrock_rag import retrieve_policy_documents
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client


def policy_specialist_node(state: AgentState) -> dict[str, Any]:
    """Policy specialist agent node.

    Answers questions about insurance coverage, benefits, and policy details.
    Uses prompts from LaunchDarkly AI Config.

    Args:
        state: Current agent state

    Returns:
        Updated state with agent response
    """
    # Get the original user query
    messages = state["messages"]
    user_message = None

    for msg in messages:
        if isinstance(msg, HumanMessage):
            user_message = msg
            break

    if not user_message:
        query = "Unable to retrieve query"
    else:
        query = user_message.content

    # Get user context
    user_context = state.get("user_context", {})
    policy_id = user_context.get("policy_id")
    coverage_type = user_context.get("coverage_type", "Unknown")

    # Retrieve policy information using RAG
    print(f"\n{'─'*80}")
    print(f"🔍 POLICY SPECIALIST: Retrieving policy information")
    print(f"{'─'*80}")
    
    # Get LaunchDarkly config (including messages and KB ID)
    ld_client = get_ld_client()
    ld_config, _, _ = ld_client.get_ai_config("policy_agent", user_context)
    
    # Retrieve from Bedrock Knowledge Base via RAG (ONLY source)
    rag_documents = retrieve_policy_documents(query, policy_id, ld_config=ld_config)

    # Format RAG documents from Bedrock Knowledge Base
    if not rag_documents:
        raise RuntimeError(
            f"❌ CATASTROPHIC: No policy documents retrieved from Bedrock Knowledge Base!\n"
            f"  Query: {query}\n"
            f"  Policy ID: {policy_id}\n"
            f"  This indicates either:\n"
            f"  1. The Knowledge Base is empty\n"
            f"  2. The query doesn't match any documents\n"
            f"  3. The KB is not properly configured"
        )
    
    print(f"  📄 Retrieved {len(rag_documents)} policy documents from Bedrock KB")
    policy_info_str = "\n\n=== POLICY DOCUMENTATION (from Bedrock Knowledge Base) ===\n"
    for i, doc in enumerate(rag_documents, 1):
        score = doc.get("score", 0.0)
        content = doc.get("content", "")
        print(f"    Doc {i}: Score {score:.3f}, Length {len(content)} chars")
        policy_info_str += f"\n[Document {i} - Relevance: {score:.2f}]\n{content}\n"

    # Get LLM and messages from LaunchDarkly AI Config
    model_invoker, ld_config = get_model_invoker(
        config_key="policy_agent",
        context=user_context,
        default_temperature=0.7,
    )
    
    # Extract model ID from config for tracking
    model_id = ld_config.get("model", {}).get("name", "unknown")
    
    # Build LangChain messages from LaunchDarkly config (supports both agent-based and completion-based)
    context_vars = {
        **user_context,
        "query": query,
        "policy_id": policy_id or "Not provided",
        "coverage_type": coverage_type,
        "policy_info": policy_info_str,
    }
    langchain_messages = ld_client.build_langchain_messages(ld_config, context_vars)

    # Track start time for duration measurement
    import time
    start_time = time.time()
    
    response = model_invoker.invoke(langchain_messages)
    
    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Extract token usage and TTFT if available
    tokens = {"input": 0, "output": 0}
    ttft_ms = None
    
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = {
            "input": response.usage_metadata.get("input_tokens", 0),
            "output": response.usage_metadata.get("output_tokens", 0)
        }
    
    # Extract Time to First Token (TTFT) from response metadata
    if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
        ttft_ms = response.response_metadata.get("ttft_ms")
    
    response_text = response.content

    # Update state
    updates: dict[str, Any] = {
        "messages": messages + [AIMessage(content=response_text)],
        "final_response": response_text,
        "next_agent": "END",
        "agent_data": {
            **state.get("agent_data", {}),
            "policy_specialist": {
                "model": model_id,  # Track which model was used
                "source": "bedrock_kb_only",
                "rag_enabled": True,
                "rag_documents_retrieved": len(rag_documents),
                "rag_documents": rag_documents,  # Store actual documents for evaluation
                "query": query,
                "policy_id": policy_id,
                "response": response_text,  # Store raw specialist output for debugging/testing
                "tokens": tokens,
                "ttft_ms": ttft_ms,  # Time to first token from Bedrock streaming
                "duration_ms": duration_ms,  # Total time to generate response
            },
        },
    }

    return updates
