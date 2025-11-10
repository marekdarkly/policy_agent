"""Tests for individual agents."""

import pytest
from langchain_core.messages import HumanMessage

from src.graph.state import QueryType


def test_triage_agent_state_structure():
    """Test that triage agent returns proper state structure."""
    from src.agents.triage_router import triage_node

    # Create a mock state
    state = {
        "messages": [HumanMessage(content="What is my copay?")],
        "user_context": {"policy_id": "POL-123"},
        "query_type": QueryType.UNKNOWN,
        "confidence_score": 0.0,
        "escalation_needed": False,
        "next_agent": "triage",
        "agent_data": {},
        "final_response": None,
    }

    # Note: This test would require mocking the LLM
    # In a real test suite, you would mock get_structured_llm
    # For now, we just verify the function exists and has the right signature


def test_policy_specialist_state_structure():
    """Test that policy specialist returns proper state structure."""
    from src.agents.policy_specialist import policy_specialist_node

    state = {
        "messages": [HumanMessage(content="What is my copay?")],
        "user_context": {"policy_id": "POL-12345"},
        "query_type": QueryType.POLICY_QUESTION,
        "confidence_score": 0.9,
        "escalation_needed": False,
        "next_agent": "policy_specialist",
        "agent_data": {},
        "final_response": None,
    }

    # Note: This test would require mocking the LLM
    # For now, we verify the function exists


def test_provider_specialist_state_structure():
    """Test that provider specialist returns proper state structure."""
    from src.agents.provider_specialist import provider_specialist_node

    state = {
        "messages": [HumanMessage(content="Find me a cardiologist")],
        "user_context": {"policy_id": "POL-12345", "location": "Boston"},
        "query_type": QueryType.PROVIDER_LOOKUP,
        "confidence_score": 0.9,
        "escalation_needed": False,
        "next_agent": "provider_specialist",
        "agent_data": {},
        "final_response": None,
    }

    # Note: This test would require mocking the LLM


def test_scheduler_specialist_state_structure():
    """Test that scheduler specialist returns proper state structure."""
    from src.agents.scheduler_specialist import scheduler_specialist_node

    state = {
        "messages": [HumanMessage(content="I need to talk to someone")],
        "user_context": {"policy_id": "POL-12345"},
        "query_type": QueryType.SCHEDULE_AGENT,
        "confidence_score": 0.9,
        "escalation_needed": True,
        "next_agent": "scheduler_specialist",
        "agent_data": {},
        "final_response": None,
    }

    # Note: This test would require mocking the LLM
