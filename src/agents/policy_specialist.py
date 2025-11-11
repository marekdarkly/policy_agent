"""Policy specialist agent for answering policy-related questions."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from ..graph.state import AgentState
from ..tools.policy_db import get_policy_info
from ..tools.bedrock_rag import retrieve_policy_documents
from ..utils.llm_config import get_model_invoker
from ..utils.prompts import POLICY_SPECIALIST_PROMPT


def policy_specialist_node(state: AgentState) -> dict[str, Any]:
    """Policy specialist agent node.

    Answers questions about insurance coverage, benefits, and policy details.

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

    # Retrieve policy information using RAG + traditional database
    print(f"\n{'─'*80}")
    print(f"🔍 POLICY SPECIALIST: Retrieving policy information")
    print(f"{'─'*80}")
    
    # Try RAG retrieval first
    rag_documents = retrieve_policy_documents(query, policy_id)
    
    # Also get structured policy data from database
    policy_info = get_policy_info(policy_id)

    # Check if there was an error
    if "error" in policy_info:
        response_text = (
            f"{policy_info['message']}\n\n"
            "I can still try to answer general policy questions, but for specific "
            "information about your coverage, I'll need a valid policy ID."
        )
    else:
        # Format policy info for the prompt
        policy_info_str = json.dumps(policy_info, indent=2)
        
        # Format RAG documents if available
        rag_context = ""
        if rag_documents:
            print(f"  📄 Retrieved {len(rag_documents)} relevant policy documents via RAG")
            rag_context = "\n\n=== RELEVANT POLICY DOCUMENTS ===\n"
            for i, doc in enumerate(rag_documents, 1):
                score = doc.get("score", 0.0)
                content = doc.get("content", "")
                print(f"    Doc {i}: Score {score:.3f}, Length {len(content)} chars")
                rag_context += f"\n[Document {i} - Relevance: {score:.2f}]\n{content}\n"
        else:
            print(f"  ℹ️  No RAG documents retrieved, using database only")

        # Enhanced prompt with RAG context
        enhanced_prompt = POLICY_SPECIALIST_PROMPT.format(
            policy_id=policy_id or "Not provided",
            coverage_type=coverage_type,
            user_context=json.dumps(user_context, indent=2),
            policy_info=policy_info_str,
            query=query,
        )
        
        # Add RAG context if available
        if rag_context:
            enhanced_prompt = f"{rag_context}\n\n{enhanced_prompt}"
        
        prompt = enhanced_prompt

        # Get LLM response with LaunchDarkly AI Config (required)
        model_invoker = get_model_invoker(
            config_key="policy_agent",
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
            "policy_specialist": {
                "policy_info": policy_info,
                "rag_documents_retrieved": len(rag_documents),
                "rag_enabled": len(rag_documents) > 0,
                "response": response_text,
            },
        },
    }

    return updates
