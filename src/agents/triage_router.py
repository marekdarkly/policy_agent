"""Triage router agent for query classification."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..graph.state import AgentState, QueryType
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client


def triage_node(state: AgentState) -> dict[str, Any]:
    """Triage router agent node.

    Analyzes the customer query and routes to the appropriate specialist.
    Uses prompts from LaunchDarkly AI Config.

    Args:
        state: Current agent state

    Returns:
        Updated state with routing information
    """
    # Get the last message (user query)
    messages = state["messages"]
    last_message = messages[-1]

    if isinstance(last_message, HumanMessage):
        query = last_message.content
    else:
        query = str(last_message.content)

    # Get user context
    user_context = state.get("user_context", {})

    # Get LLM and LaunchDarkly AI Config (including messages/prompts)
    model_invoker, ld_config = get_model_invoker(
        config_key="triage_agent",
        context=user_context,
        default_temperature=0.0,
    )
    
    # Build LangChain messages from LaunchDarkly config (supports both agent-based and completion-based)
    ld_client = get_ld_client()
    context_vars = {**user_context, "query": query}
    langchain_messages = ld_client.build_langchain_messages(ld_config, context_vars)
    
    # Configure for JSON output if OpenAI
    from langchain_openai import ChatOpenAI
    if isinstance(model_invoker.model, ChatOpenAI):
        model_invoker.model.model_kwargs = {"response_format": {"type": "json_object"}}

    response = model_invoker.invoke(langchain_messages)

    # Extract token usage if available
    tokens = {"input": 0, "output": 0}
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = {
            "input": response.usage_metadata.get("input_tokens", 0),
            "output": response.usage_metadata.get("output_tokens", 0)
        }

    # Parse the JSON response
    try:
        result = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback if JSON parsing fails
        result = {
            "query_type": "schedule_agent",
            "confidence_score": 0.5,
            "extracted_context": {},
            "escalation_needed": True,
            "reasoning": "Failed to parse query, routing to human agent for safety",
        }

    # Map query type to enum
    query_type_str = result.get("query_type", "schedule_agent")
    query_type_map = {
        "policy_question": QueryType.POLICY_QUESTION,
        "provider_lookup": QueryType.PROVIDER_LOOKUP,
        "schedule_agent": QueryType.SCHEDULE_AGENT,
    }
    query_type = query_type_map.get(query_type_str, QueryType.SCHEDULE_AGENT)

    # Determine next agent
    agent_map = {
        QueryType.POLICY_QUESTION: "policy_specialist",
        QueryType.PROVIDER_LOOKUP: "provider_specialist",
        QueryType.SCHEDULE_AGENT: "scheduler_specialist",
    }
    next_agent = agent_map[query_type]

    # Check confidence - if low, escalate
    confidence_score = result.get("confidence_score", 0.0)
    escalation_needed = result.get("escalation_needed", False)

    if confidence_score < 0.7:
        escalation_needed = True
        next_agent = "scheduler_specialist"

    # Update state
    updates: dict[str, Any] = {
        "query_type": query_type,
        "next_agent": next_agent,
        "confidence_score": confidence_score,
        "escalation_needed": escalation_needed,
        "messages": messages
        + [
            AIMessage(
                content=f"Routing to {next_agent} (confidence: {confidence_score:.2f})",
                additional_kwargs={"reasoning": result.get("reasoning", "")},
            )
        ],
        "agent_data": {
            **state.get("agent_data", {}),
            "triage_router": {
                "tokens": tokens,
                "confidence": confidence_score,
                "query_type": str(query_type)
            }
        }
    }

    # Merge extracted context
    extracted_context = result.get("extracted_context", {})
    if extracted_context:
        merged_context = {**user_context, **extracted_context}
        updates["user_context"] = merged_context

    return updates
