"""Provider lookup specialist agent."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..graph.state import AgentState
from ..tools.bedrock_rag import retrieve_provider_documents
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client


def provider_specialist_node(state: AgentState) -> dict[str, Any]:
    """Provider lookup specialist agent node.

    Helps customers find in-network providers.
    Uses prompts from LaunchDarkly AI Config.

    Args:
        state: Current agent state

    Returns:
        Updated state with provider recommendations
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
    network = user_context.get("network", "Unknown")
    location = user_context.get("location", "")

    # Extract search parameters from context or query
    specialty = user_context.get("specialty")

    # Simple keyword matching for specialty
    query_lower = query.lower()
    if not specialty:
        if "cardiologist" in query_lower or "heart" in query_lower:
            specialty = "cardiologist"
        elif "dermatologist" in query_lower or "skin" in query_lower:
            specialty = "dermatologist"
        elif "orthopedic" in query_lower or "bone" in query_lower or "joint" in query_lower:
            specialty = "orthopedic"
        elif "primary care" in query_lower or "family doctor" in query_lower:
            specialty = "primary care"
        elif "physical therapy" in query_lower or "pt" in query_lower:
            specialty = "physical therapy"

    # Retrieve provider information using RAG
    print(f"\n{'─'*80}")
    print(f"🔍 PROVIDER SPECIALIST: Searching for providers")
    print(f"{'─'*80}")
    
    # Get LaunchDarkly config (including messages and KB ID)
    ld_client = get_ld_client()
    ld_config, _ = ld_client.get_ai_config("provider_agent", user_context)
    
    # Retrieve from Bedrock Knowledge Base via RAG (ONLY source)
    rag_documents = retrieve_provider_documents(
        query,
        specialty=specialty,
        location=location,
        network=network if network != "Unknown" else None,
        ld_config=ld_config
    )

    # Format RAG documents from Bedrock Knowledge Base
    if rag_documents:
        print(f"  📄 Retrieved {len(rag_documents)} provider documents from Bedrock KB")
        provider_info_str = "\n\n=== PROVIDER NETWORK INFORMATION (from Bedrock Knowledge Base) ===\n"
        for i, doc in enumerate(rag_documents, 1):
            score = doc.get("score", 0.0)
            content = doc.get("content", "")
            print(f"    Doc {i}: Score {score:.3f}, Length {len(content)} chars")
            provider_info_str += f"\n[Document {i} - Relevance: {score:.2f}]\n{content}\n"
    else:
        print(f"  ⚠️  No provider documents retrieved from Bedrock KB")
        provider_info_str = "No providers found matching the criteria in the knowledge base."

    # Get LLM and messages from LaunchDarkly AI Config
    model_invoker, ld_config = get_model_invoker(
        config_key="provider_agent",
        context=user_context,
        default_temperature=0.7,
    )
    
    # Build LangChain messages from LaunchDarkly config (supports both agent-based and completion-based)
    context_vars = {
        **user_context,
        "query": query,
        "policy_id": policy_id or "Not provided",
        "network": network,
        "location": location or "Not specified",
        "provider_info": provider_info_str,
    }
    langchain_messages = ld_client.build_langchain_messages(ld_config, context_vars)

    response = model_invoker.invoke(langchain_messages)
    response_text = response.content

    # Update state
    updates: dict[str, Any] = {
        "messages": messages + [AIMessage(content=response_text)],
        "final_response": response_text,
        "next_agent": "END",
        "agent_data": {
            **state.get("agent_data", {}),
            "provider_specialist": {
                "source": "bedrock_kb_only",
                "rag_enabled": True,
                "rag_documents_retrieved": len(rag_documents),
                "query": query,
                "specialty": specialty,
                "location": location,
                "network": network,
            },
        },
    }

    return updates
