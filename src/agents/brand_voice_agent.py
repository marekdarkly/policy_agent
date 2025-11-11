"""Brand voice synthesis agent for customer-facing responses."""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from ..graph.state import AgentState
from ..utils.llm_config import get_model_invoker
from ..utils.prompts import BRAND_VOICE_PROMPT


def brand_voice_node(state: AgentState) -> dict[str, Any]:
    """Brand voice synthesis agent node.

    Takes the specialist's response and transforms it to match ToggleHealth's
    brand voice - friendly, empathetic, clear, and helpful.

    Args:
        state: Current agent state with specialist response

    Returns:
        Updated state with brand-voiced customer response
    """
    # Get the specialist's raw response (last message)
    messages = state["messages"]
    specialist_response = messages[-1].content if messages else ""

    # Get user context for personalization
    user_context = state.get("user_context", {})
    customer_name = user_context.get("name", "there")
    query_type = state.get("query_type", "unknown")
    
    # Get original customer query (first human message)
    original_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            original_query = msg.content
            break

    # Get agent-specific context if available
    agent_data = state.get("agent_data", {})
    specialist_name = state.get("next_agent", "specialist")
    specialist_context = agent_data.get(specialist_name, {})

    # Prepare prompt with all context
    prompt = BRAND_VOICE_PROMPT.format(
        customer_name=customer_name,
        original_query=original_query,
        query_type=query_type,
        specialist_response=specialist_response,
        user_context=str(user_context),
    )

    # Get LLM response with LaunchDarkly AI Config
    model_invoker = get_model_invoker(
        config_key="brand_agent",
        context=user_context,
        default_temperature=0.7,  # Slightly creative for natural language
    )

    response = model_invoker.invoke([HumanMessage(content=prompt)])

    # Store the brand-voiced response
    final_response = response.content

    # Add debug info to agent_data
    brand_data = {
        "original_specialist_response": specialist_response[:200] + "..." if len(specialist_response) > 200 else specialist_response,
        "final_customer_response": final_response[:200] + "..." if len(final_response) > 200 else final_response,
        "brand_voice_applied": True,
        "personalization": {
            "customer_name": customer_name,
            "query_type": str(query_type),
        }
    }

    # Update agent_data
    updated_agent_data = state.get("agent_data", {}).copy()
    updated_agent_data["brand_voice"] = brand_data

    # Create the final customer message
    final_message = AIMessage(content=final_response)

    return {
        "messages": [final_message],
        "agent_data": updated_agent_data,
        "next_agent": "END",
    }
