"""Tests for tool modules."""

import pytest

from src.tools.calendar import get_available_slots, schedule_appointment
from src.tools.policy_db import get_policy_info, search_policy_coverage
from src.tools.provider_db import get_provider_details, search_providers


# Policy DB Tests
def test_get_policy_info_valid():
    """Test getting valid policy info."""
    policy = get_policy_info("POL-12345")

    assert "error" not in policy
    assert policy["policy_id"] == "POL-12345"
    assert policy["coverage_type"] == "Gold Plan"
    assert "deductible" in policy


def test_get_policy_info_invalid():
    """Test getting invalid policy info."""
    policy = get_policy_info("INVALID-ID")

    assert "error" in policy
    assert "not found" in policy["message"].lower()


def test_get_policy_info_no_id():
    """Test getting policy info with no ID."""
    policy = get_policy_info(None)

    assert "error" in policy
    assert "no policy id" in policy["message"].lower()


def test_search_policy_coverage():
    """Test searching for specific coverage."""
    result = search_policy_coverage("POL-12345", "emergency")

    assert "details" in result or "message" in result


# Provider DB Tests
def test_search_providers_by_specialty():
    """Test searching providers by specialty."""
    providers = search_providers(specialty="cardiologist")

    assert len(providers) > 0
    assert all("cardiologist" in p["specialty"].lower() for p in providers)


def test_search_providers_by_location():
    """Test searching providers by location."""
    providers = search_providers(location="Boston")

    assert len(providers) > 0
    assert all("boston" in p["location"]["city"].lower() for p in providers)


def test_search_providers_by_network():
    """Test searching providers by network."""
    providers = search_providers(network="Premier Network")

    assert len(providers) > 0
    assert all("premier" in p["network"].lower() for p in providers)


def test_search_providers_accepting_patients():
    """Test searching providers accepting new patients."""
    providers = search_providers(accepting_new_patients=True)

    assert len(providers) > 0
    assert all(p["accepting_new_patients"] is True for p in providers)


def test_get_provider_details():
    """Test getting provider details."""
    provider = get_provider_details("PRV-001")

    assert provider is not None
    assert provider["provider_id"] == "PRV-001"
    assert "name" in provider


def test_get_provider_details_invalid():
    """Test getting invalid provider details."""
    provider = get_provider_details("INVALID-ID")

    assert provider is None


# Calendar Tests
def test_get_available_slots():
    """Test getting available appointment slots."""
    slots = get_available_slots(days_ahead=7)

    assert len(slots) > 0
    assert all("slot_id" in slot for slot in slots)
    assert all("date" in slot for slot in slots)
    assert all("time" in slot for slot in slots)


def test_schedule_appointment_valid():
    """Test scheduling an appointment with valid slot."""
    slots = get_available_slots(days_ahead=7)
    slot_id = slots[0]["slot_id"]

    result = schedule_appointment(
        slot_id=slot_id,
        contact_method="phone",
        contact_value="617-555-1234",
        issue_summary="Need help with claim",
        user_context={"policy_id": "POL-12345"},
    )

    assert "error" not in result
    assert "confirmation_number" in result
    assert result["contact_method"] == "phone"


def test_schedule_appointment_invalid_slot():
    """Test scheduling with invalid slot."""
    result = schedule_appointment(
        slot_id="INVALID-SLOT",
        contact_method="phone",
        contact_value="617-555-1234",
        issue_summary="Need help",
    )

    assert "error" in result
