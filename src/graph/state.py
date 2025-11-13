"""State management for the multi-agent system."""

from enum import Enum
from typing import Annotated, Any, Sequence

from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class QueryType(str, Enum):
    """Types of customer queries."""

    POLICY_QUESTION = "policy_question"
    PROVIDER_LOOKUP = "provider_lookup"
    SCHEDULE_AGENT = "schedule_agent"
    UNKNOWN = "unknown"


class AgentState(TypedDict):
    """State for the agent graph.

    This state is passed between nodes in the LangGraph workflow.
    Each agent can read from and write to this state.
    """

    # Conversation messages
    messages: Annotated[Sequence[BaseMessage], "The conversation messages"]

    # Routing information
    next_agent: Annotated[str, "The name of the next agent to route to"]
    query_type: Annotated[QueryType, "The classified query type"]

    # User context
    user_context: Annotated[dict[str, Any], "Customer metadata (policy_id, location, etc.)"]

    # Routing metadata
    confidence_score: Annotated[float, "Router confidence in classification (0-1)"]
    escalation_needed: Annotated[bool, "Whether query needs human escalation"]

    # Agent-specific data
    agent_data: Annotated[dict[str, Any], "Data collected by specialist agents"]

    # Final response
    final_response: Annotated[str | None, "The final response to the user"]

    # Request tracking
    request_id: Annotated[str | None, "Unique request ID for tracking evaluation results"]
    evaluation_results_store: Annotated[dict[str, Any] | None, "Shared dict for storing evaluation results"]
    brand_trackers_store: Annotated[dict[str, Any] | None, "Shared dict for storing brand voice trackers"]


def create_initial_state(
    user_message: str,
    user_context: dict[str, Any] | None = None,
    request_id: str | None = None,
    evaluation_results_store: dict[str, Any] | None = None,
    brand_trackers_store: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create an initial state for the workflow.

    Args:
        user_message: The initial message from the user
        user_context: Optional customer context (policy_id, location, etc.)
        request_id: Optional unique request ID for tracking
        evaluation_results_store: Optional shared dict for storing evaluation results
        brand_trackers_store: Optional shared dict for storing brand voice trackers

    Returns:
        Initial state dictionary
    """
    from langchain_core.messages import HumanMessage

    return {
        "messages": [HumanMessage(content=user_message)],
        "next_agent": "triage",
        "query_type": QueryType.UNKNOWN,
        "user_context": user_context or {},
        "confidence_score": 0.0,
        "escalation_needed": False,
        "agent_data": {},
        "final_response": None,
        "request_id": request_id,
        "evaluation_results_store": evaluation_results_store,
        "brand_trackers_store": brand_trackers_store,
    }
