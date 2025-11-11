"""Provider lookup specialist agent."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from ..graph.state import AgentState
from ..tools.provider_db import search_providers
from ..tools.bedrock_rag import retrieve_provider_documents
from ..utils.llm_config import get_model_invoker
from ..utils.prompts import PROVIDER_SPECIALIST_PROMPT


def provider_specialist_node(state: AgentState) -> dict[str, Any]:
    """Provider lookup specialist agent node.

    Helps customers find in-network providers.

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
    # In a real system, this would use NER or more sophisticated extraction
    specialty = user_context.get("specialty")

    # Simple keyword matching for specialty (can be enhanced)
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

    # Retrieve provider information using RAG + traditional database
    print(f"\n{'─'*80}")
    print(f"🔍 PROVIDER SPECIALIST: Searching for providers")
    print(f"{'─'*80}")
    
    # Try RAG retrieval first
    rag_documents = retrieve_provider_documents(
        query,
        specialty=specialty,
        location=location,
        network=network if network != "Unknown" else None
    )
    
    # Also search structured provider database
    providers = search_providers(
        specialty=specialty,
        location=location,
        network=network if network != "Unknown" else None,
        accepting_new_patients=True,
    )

    # Format provider information
    if providers:
        provider_info_str = json.dumps(providers, indent=2)
        print(f"  📋 Found {len(providers)} providers in structured database")
    else:
        provider_info_str = "No providers found matching the criteria."
        print(f"  ⚠️  No providers found in structured database")
    
    # Format RAG documents if available
    rag_context = ""
    if rag_documents:
        print(f"  📄 Retrieved {len(rag_documents)} relevant provider documents via RAG")
        rag_context = "\n\n=== RELEVANT PROVIDER NETWORK INFORMATION ===\n"
        for i, doc in enumerate(rag_documents, 1):
            score = doc.get("score", 0.0)
            content = doc.get("content", "")
            print(f"    Doc {i}: Score {score:.3f}, Length {len(content)} chars")
            rag_context += f"\n[Document {i} - Relevance: {score:.2f}]\n{content}\n"
    else:
        print(f"  ℹ️  No RAG documents retrieved, using database only")

    # Enhanced prompt with RAG context
    enhanced_prompt = PROVIDER_SPECIALIST_PROMPT.format(
        policy_id=policy_id or "Not provided",
        network=network,
        location=location or "Not specified",
        user_context=json.dumps(user_context, indent=2),
        provider_info=provider_info_str,
        query=query,
    )
    
    # Add RAG context if available
    if rag_context:
        enhanced_prompt = f"{rag_context}\n\n{enhanced_prompt}"
    
    prompt = enhanced_prompt

    # Get LLM response with LaunchDarkly AI Config (required)
    model_invoker = get_model_invoker(
        config_key="provider_agent",
        context=user_context,
        default_temperature=0.7,
    )
    response = model_invoker.invoke([HumanMessage(content=prompt)])

    response_text = response.content

    # Update state
    updates: dict[str, Any] = {
        "messages": messages + [AIMessage(content=response_text)],
        "final_response": response_text,
        "next_agent": "END",
        "agent_data": {
            **state.get("agent_data", {}),
            "provider_specialist": {
                "providers_found": providers,
                "rag_documents_retrieved": len(rag_documents),
                "rag_enabled": len(rag_documents) > 0,
                "search_params": {
                    "specialty": specialty,
                    "location": location,
                    "network": network,
                },
                "response": response_text,
            },
        },
    }

    return updates
