"""Live agent scheduler specialist."""

import json
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from ..graph.state import AgentState
from ..tools.calendar import get_available_slots
from ..utils.llm_config import get_model_invoker
from ..utils.prompts import SCHEDULER_SPECIALIST_PROMPT


def scheduler_specialist_node(state: AgentState) -> dict[str, Any]:
    """Scheduler specialist agent node.

    Handles complex queries and schedules callbacks with human agents.

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

    # Prepare prompt
    prompt = SCHEDULER_SPECIALIST_PROMPT.format(
        policy_id=policy_id,
        user_context=json.dumps(user_context, indent=2),
        available_slots=slots_str,
        query=query,
    )

    # Get LLM response with LaunchDarkly AI Config (required)
    model_invoker = get_model_invoker(
        config_key="scheduler_agent",
        context=user_context,
        default_temperature=0.7,
    )
    response = model_invoker.invoke([HumanMessage(content=prompt)])

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
