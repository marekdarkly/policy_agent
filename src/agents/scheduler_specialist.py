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
    
    # Use messages from LaunchDarkly AI Config
    ld_messages = ld_config.get("messages", [])
    
    if not ld_messages:
        raise RuntimeError("CATASTROPHIC: No messages found in LaunchDarkly AI Config for scheduler_agent. Please configure messages in LaunchDarkly.")
    
    # Format messages with context variables
    ld_client = get_ld_client()
    context_vars = {
        **user_context,
        "query": query,
        "policy_id": policy_id,
        "available_slots": slots_str,
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
                "available_slots": available_slots[:10],
                "response": response_text,
                "escalation_reason": state.get("escalation_needed", False),
            },
        },
    }

    return updates
