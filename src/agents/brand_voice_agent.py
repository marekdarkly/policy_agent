"""Brand voice synthesis agent for customer-facing responses."""

import asyncio
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..graph.state import AgentState
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client
from ..evaluation.judge import evaluate_brand_voice_async


def brand_voice_node(state: AgentState) -> dict[str, Any]:
    """Brand voice synthesis agent node.

    Takes the specialist's response and transforms it to match ToggleHealth's
    brand voice - friendly, empathetic, clear, and helpful.
    Uses prompts from LaunchDarkly AI Config.

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

    # Get LLM and messages from LaunchDarkly AI Config
    model_invoker, ld_config = get_model_invoker(
        config_key="brand_agent",
        context=user_context,
        default_temperature=0.7,  # Slightly creative for natural language
    )
    
    # Build LangChain messages from LaunchDarkly config (supports both agent-based and completion-based)
    ld_client = get_ld_client()
    context_vars = {
        **user_context,
        "customer_name": customer_name,
        "original_query": original_query,
        "query_type": str(query_type),
        "specialist_response": specialist_response,
    }
    langchain_messages = ld_client.build_langchain_messages(ld_config, context_vars)

    response = model_invoker.invoke(langchain_messages)

    # Store the brand-voiced response
    final_response = response.content
    
    # Start async evaluation without blocking (fire-and-forget)
    # This will run in the background and send metrics to LaunchDarkly
    try:
        asyncio.create_task(
            evaluate_brand_voice_async(
                original_query=original_query,
                specialist_response=specialist_response,
                brand_voice_output=final_response,
                user_context=user_context,
                brand_tracker=model_invoker.tracker
            )
        )
        print("🔍 Background evaluation started for brand voice output")
    except Exception as e:
        # Never let evaluation errors affect the main flow
        print(f"⚠️  Failed to start background evaluation: {e}")

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
        "final_response": final_response,  # CRITICAL: Set this so the customer sees the brand-voiced response!
        "agent_data": updated_agent_data,
        "next_agent": "END",
    }
