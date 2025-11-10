"""Tests for the workflow graph."""

import pytest

from src.graph.state import QueryType, create_initial_state
from src.graph.workflow import create_workflow, route_after_triage


def test_create_initial_state():
    """Test initial state creation."""
    message = "Test message"
    context = {"policy_id": "POL-123"}

    state = create_initial_state(message, context)

    assert len(state["messages"]) == 1
    assert state["messages"][0].content == message
    assert state["user_context"]["policy_id"] == "POL-123"
    assert state["query_type"] == QueryType.UNKNOWN
    assert state["confidence_score"] == 0.0
    assert state["escalation_needed"] is False


def test_route_after_triage_policy():
    """Test routing to policy specialist."""
    state = {
        "next_agent": "policy_specialist",
        "query_type": QueryType.POLICY_QUESTION,
    }

    result = route_after_triage(state)
    assert result == "policy_specialist"


def test_route_after_triage_provider():
    """Test routing to provider specialist."""
    state = {
        "next_agent": "provider_specialist",
        "query_type": QueryType.PROVIDER_LOOKUP,
    }

    result = route_after_triage(state)
    assert result == "provider_specialist"


def test_route_after_triage_scheduler():
    """Test routing to scheduler specialist."""
    state = {
        "next_agent": "scheduler_specialist",
        "query_type": QueryType.SCHEDULE_AGENT,
    }

    result = route_after_triage(state)
    assert result == "scheduler_specialist"


def test_route_after_triage_invalid():
    """Test routing with invalid agent defaults to scheduler."""
    state = {
        "next_agent": "invalid_agent",
        "query_type": QueryType.UNKNOWN,
    }

    result = route_after_triage(state)
    assert result == "scheduler_specialist"


def test_create_workflow():
    """Test workflow creation."""
    workflow = create_workflow()

    assert workflow is not None

    # Test that workflow has the correct nodes
    # Note: This is a basic test, more detailed tests would require mocking the LLM
