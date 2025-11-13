"""Live agent scheduler specialist."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..graph.state import AgentState
from ..tools.calendar import get_available_slots
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client


def scheduler_specialist_node(state: AgentState) -> dict[str, Any]:
    """Scheduler specialist agent node.

    Handles complex queries and schedules callbacks with human agents.
    Uses prompts from LaunchDarkly AI Config.

    Args:
        state: Current agent state

    Returns:
        Updated state with scheduling information
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
    policy_id = user_context.get("policy_id", "Not provided")

    # Get available time slots
    available_slots = get_available_slots(days_ahead=7)

    # Format slots for display
    slots_str = "\n".join(
        [
            f"- {slot['datetime_str']} (ID: {slot['slot_id']})"
            for slot in available_slots[:10]  # Show first 10 slots
        ]
    )

    # Get LLM and messages from LaunchDarkly AI Config
    model_invoker, ld_config = get_model_invoker(
        config_key="scheduler_agent",
        context=user_context,
        default_temperature=0.7,
    )
    
    # Extract model ID from config for tracking
    model_id = ld_config.get("model", {}).get("name", "unknown")
    
    # Build LangChain messages from LaunchDarkly config (supports both agent-based and completion-based)
    ld_client = get_ld_client()
    context_vars = {
        **user_context,
        "query": query,
        "policy_id": policy_id,
        "available_slots": slots_str,
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

    # Check if escalation was needed
    escalation_info = ""
    if state.get("escalation_needed", False):
        escalation_info = (
            "\n\n**Note:** Your query requires specialized assistance from our team. "
            "A live agent will be better equipped to help you with this matter."
        )
        response_text = response_text + escalation_info

    # Update state
    updates: dict[str, Any] = {
        "messages": messages + [AIMessage(content=response_text)],
        "final_response": response_text,
        "next_agent": "END",
        "agent_data": {
            **state.get("agent_data", {}),
            "scheduler_specialist": {
                "model": model_id,  # Track which model was used
                "available_slots": available_slots[:10],
                "response": response_text,
                "escalation_reason": state.get("escalation_needed", False),
                "tokens": tokens,
                "ttft_ms": ttft_ms,
                "duration_ms": duration_ms,
            },
        },
    }

    return updates
