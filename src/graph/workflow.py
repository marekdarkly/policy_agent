"""Workflow graph for the multi-agent system."""

import functools
from typing import Any, Callable, Literal

from langgraph.graph import END, StateGraph
from opentelemetry import trace
from opentelemetry.trace import StatusCode

from ..agents import (
    policy_specialist_node,
    provider_specialist_node,
    scheduler_specialist_node,
    triage_node,
    brand_voice_node,
)
from .state import AgentState

_tracer = trace.get_tracer("togglehealth.workflow", "1.0.0")


def _traced_node(name: str, fn: Callable) -> Callable:
    """Wrap a LangGraph node function with an OpenTelemetry span."""

    @functools.wraps(fn)
    def wrapper(state: AgentState) -> dict[str, Any]:
        user_context = state.get("user_context", {})
        with _tracer.start_as_current_span(
            f"agent.{name}",
            attributes={
                "agent.name": name,
                "agent.user_key": user_context.get("user_key", ""),
            },
        ) as span:
            try:
                result = fn(state)
                agent_data = result.get("agent_data", {}).get(name, {})
                if agent_data:
                    model = agent_data.get("model", "")
                    if model:
                        span.set_attribute("agent.model", model)
                    tokens = agent_data.get("tokens", {})
                    if tokens:
                        span.set_attribute("agent.tokens.input", tokens.get("input", 0))
                        span.set_attribute("agent.tokens.output", tokens.get("output", 0))
                    duration = agent_data.get("duration_ms")
                    if duration is not None:
                        span.set_attribute("agent.duration_ms", duration)
                span.set_status(StatusCode.OK)
                return result
            except Exception as e:
                span.set_status(StatusCode.ERROR, str(e))
                span.record_exception(e)
                raise

    return wrapper


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


def route_after_specialist(state: AgentState) -> Literal["brand_voice", "__end__"]:
    """Routing function after specialist agents.
    
    If in evaluation mode (evaluate_agent is set), terminates after specialist.
    - "auto" mode: Always terminate (for auto-evaluation of whatever agent triage chose)
    - Specific agent name: Terminate after that specific agent (except brand_agent)
    - "brand_agent": Proceed to brand_voice (to evaluate brand agent)
    - None: Proceed to brand_voice (normal flow)
    
    Args:
        state: Current agent state
        
    Returns:
        "brand_voice" for normal flow or brand_agent evaluation, "__end__" for specialist evaluation
    """
    # Check if we're in evaluation mode
    evaluate_agent = state.get("evaluate_agent")
    if evaluate_agent:
        # If evaluating brand_agent, proceed to brand_voice
        if evaluate_agent == "brand_agent":
            return "brand_voice"  # type: ignore
        
        # Otherwise, terminate after specialist to evaluate that agent only
        return "__end__"  # type: ignore
    
    return "brand_voice"  # type: ignore


def create_workflow() -> StateGraph:
    """Create the LangGraph workflow for the multi-agent system.

    Returns:
        Compiled workflow graph
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("triage", _traced_node("triage", triage_node))
    workflow.add_node("policy_specialist", _traced_node("policy_specialist", policy_specialist_node))
    workflow.add_node("provider_specialist", _traced_node("provider_specialist", provider_specialist_node))
    workflow.add_node("scheduler_specialist", _traced_node("scheduler_specialist", scheduler_specialist_node))
    workflow.add_node("brand_voice", _traced_node("brand_voice", brand_voice_node))

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

    # Add conditional edges from specialists (can terminate early for evaluation)
    # In evaluation mode, stops after specialist. Otherwise goes to brand_voice.
    workflow.add_conditional_edges(
        "policy_specialist",
        route_after_specialist,
        {
            "brand_voice": "brand_voice",
            "__end__": END,
        },
    )
    workflow.add_conditional_edges(
        "provider_specialist",
        route_after_specialist,
        {
            "brand_voice": "brand_voice",
            "__end__": END,
        },
    )
    workflow.add_conditional_edges(
        "scheduler_specialist",
        route_after_specialist,
        {
            "brand_voice": "brand_voice",
            "__end__": END,
        },
    )
    
    # Brand voice agent produces final customer response
    workflow.add_edge("brand_voice", END)

    # Compile the graph
    return workflow.compile()


def run_workflow(
    user_message: str,
    user_context: dict | None = None,
    request_id: str | None = None,
    evaluation_results_store: dict | None = None,
    brand_trackers_store: dict | None = None,
    evaluate_agent: str | None = None,
    guardrail_enabled: bool = True
) -> dict:
    """Run the workflow with a user message.

    Args:
        user_message: The user's query
        user_context: Optional user context (policy_id, location, etc.)
        request_id: Optional request ID for tracking evaluation results
        evaluation_results_store: Optional shared dict for storing evaluation results
        brand_trackers_store: Optional shared dict for storing brand voice trackers
        evaluate_agent: Optional agent to evaluate (stops workflow after this agent)
        guardrail_enabled: Whether to use guardrails (default True)

    Returns:
        Final state after workflow execution
    """
    from .state import create_initial_state

    span_attributes = {
        "workflow.user_message": user_message[:200],
        "workflow.guardrail_enabled": guardrail_enabled,
    }
    if request_id:
        span_attributes["workflow.request_id"] = request_id
    if evaluate_agent:
        span_attributes["workflow.evaluate_agent"] = evaluate_agent
    if user_context:
        span_attributes["workflow.user_key"] = user_context.get("user_key", "")
        span_attributes["workflow.coverage_type"] = user_context.get("coverage_type", "")

    with _tracer.start_as_current_span(
        "multi-agent-workflow",
        attributes=span_attributes,
    ) as span:
        initial_state = create_initial_state(
            user_message,
            user_context,
            request_id,
            evaluation_results_store,
            brand_trackers_store,
            evaluate_agent,
            guardrail_enabled
        )

        workflow = create_workflow()

        try:
            final_state = workflow.invoke(initial_state)
        except Exception as e:
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            raise

        query_type = final_state.get("query_type", "unknown")
        span.set_attribute("workflow.query_type", str(query_type))
        span.set_attribute("workflow.next_agent", final_state.get("next_agent", ""))
        final_response = final_state.get("final_response", "")
        span.set_attribute("workflow.response_length", len(final_response))
        span.set_status(StatusCode.OK)

        return final_state
