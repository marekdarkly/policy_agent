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
    ld_config, _ = ld_client.get_ai_config("policy_agent", user_context)
    
    # Retrieve from Bedrock Knowledge Base via RAG (ONLY source)
    rag_documents = retrieve_policy_documents(query, policy_id, ld_config=ld_config)

    # Format RAG documents from Bedrock Knowledge Base
    if rag_documents:
        print(f"  📄 Retrieved {len(rag_documents)} policy documents from Bedrock KB")
        policy_info_str = "\n\n=== POLICY DOCUMENTATION (from Bedrock Knowledge Base) ===\n"
        for i, doc in enumerate(rag_documents, 1):
            score = doc.get("score", 0.0)
            content = doc.get("content", "")
            print(f"    Doc {i}: Score {score:.3f}, Length {len(content)} chars")
            policy_info_str += f"\n[Document {i} - Relevance: {score:.2f}]\n{content}\n"
    else:
        print(f"  ⚠️  No policy documents retrieved from Bedrock KB")
        policy_info_str = "No policy information found in the knowledge base."

    # Get LLM and messages from LaunchDarkly AI Config
    model_invoker, ld_config = get_model_invoker(
        config_key="policy_agent",
        context=user_context,
        default_temperature=0.7,
    )
    
    # Use messages from LaunchDarkly AI Config
    ld_messages = ld_config.get("messages", [])
    
    if not ld_messages:
        raise RuntimeError("CATASTROPHIC: No messages found in LaunchDarkly AI Config for policy_agent. Please configure messages in LaunchDarkly.")
    
    # Format messages with context variables (including RAG documents)
    context_vars = {
        **user_context,
        "query": query,
        "policy_id": policy_id or "Not provided",
        "coverage_type": coverage_type,
        "policy_info": policy_info_str,
        "user_context": json.dumps(user_context, indent=2),
    }
    formatted_messages = ld_client.format_messages(ld_messages, context_vars)
    
    # Convert to LangChain message format
    langchain_messages = []
    for msg in formatted_messages:
        if msg["role"] == "system":
            langchain_messages.append(SystemMessage(content=msg["content"]))
        elif msg["role"] == "user":
            langchain_messages.append(HumanMessage(content=msg["content"]))
        else:
            langchain_messages.append(AIMessage(content=msg["content"]))

    response = model_invoker.invoke(langchain_messages)
    response_text = response.content

    # Update state
    updates: dict[str, Any] = {
        "messages": messages + [AIMessage(content=response_text)],
        "final_response": response_text,
        "next_agent": "END",
        "agent_data": {
            **state.get("agent_data", {}),
            "policy_specialist": {
                "source": "bedrock_kb_only",
                "rag_enabled": True,
                "rag_documents_retrieved": len(rag_documents),
                "query": query,
                "policy_id": policy_id,
            },
        },
    }

    return updates
