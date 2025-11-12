"""Workflow graph for the multi-agent system."""

from typing import Literal

from langgraph.graph import END, StateGraph

from ..agents import (
    policy_specialist_node,
    provider_specialist_node,
    scheduler_specialist_node,
    triage_node,
    brand_voice_node,
)
from .state import AgentState


def route_after_triage(state: AgentState) -> Literal["policy_specialist", "provider_specialist", "scheduler_specialist"]:
    """Routing function after triage.

    Determines which specialist agent to route to based on triage results.

    Args:
        state: Current agent state

    Returns:
        Name of the next agent
    """
    next_agent = state.get("next_agent", "scheduler_specialist")

    # Ensure valid routing
    valid_agents = ["policy_specialist", "provider_specialist", "scheduler_specialist"]
    if next_agent not in valid_agents:
        return "scheduler_specialist"

    return next_agent  # type: ignore


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for the multi-agent system.

    Returns:
        Compiled workflow graph
    """
    # Create the graph
    workflow = StateGraph(AgentState)

    # Add nodes for each agent
    workflow.add_node("triage", triage_node)
    workflow.add_node("policy_specialist", policy_specialist_node)
    workflow.add_node("provider_specialist", provider_specialist_node)
    workflow.add_node("scheduler_specialist", scheduler_specialist_node)
    workflow.add_node("brand_voice", brand_voice_node)

    # Set entry point
    workflow.set_entry_point("triage")

    # Add conditional edges from triage to specialists
    workflow.add_conditional_edges(
        "triage",
        route_after_triage,
        {
            "policy_specialist": "policy_specialist",
            "provider_specialist": "provider_specialist",
            "scheduler_specialist": "scheduler_specialist",
        },
    )

    # Add edges from specialists to brand voice agent (final synthesis)
    workflow.add_edge("policy_specialist", "brand_voice")
    workflow.add_edge("provider_specialist", "brand_voice")
    workflow.add_edge("scheduler_specialist", "brand_voice")
    
    # Brand voice agent produces final customer response
    workflow.add_edge("brand_voice", END)

    # Compile the graph
    return workflow.compile()


def run_workflow(user_message: str, user_context: dict | None = None, request_id: str | None = None) -> dict:
    """Run the workflow with a user message.

    Args:
        user_message: The user's query
        user_context: Optional user context (policy_id, location, etc.)
        request_id: Optional request ID for tracking evaluation results

    Returns:
        Final state after workflow execution
    """
    from .state import create_initial_state

    # Create initial state
    initial_state = create_initial_state(user_message, user_context, request_id)

    # Get workflow
    workflow = create_workflow()

    # Run workflow
    final_state = workflow.invoke(initial_state)

    return final_state
