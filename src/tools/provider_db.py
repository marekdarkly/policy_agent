"""Provider database tools (simulated)."""

from typing import Any


# Simulated provider database
PROVIDER_DATABASE = [
    {
        "provider_id": "PRV-001",
        "name": "Dr. Sarah Johnson",
        "specialty": "Primary Care Physician",
        "network": "Premier Network",
        "location": {
            "address": "123 Medical Plaza, Suite 200",
            "city": "Boston",
            "state": "MA",
            "zip": "02108",
        },
        "phone": "(617) 555-0123",
        "accepting_new_patients": True,
        "languages": ["English", "Spanish"],
    },
    {
        "provider_id": "PRV-002",
        "name": "Dr. Michael Chen",
        "specialty": "Cardiologist",
        "network": "Premier Network",
        "location": {
            "address": "456 Heart Center Drive",
            "city": "Boston",
            "state": "MA",
            "zip": "02109",
        },
        "phone": "(617) 555-0234",
        "accepting_new_patients": True,
        "languages": ["English", "Mandarin"],
    },
    {
        "provider_id": "PRV-003",
        "name": "Dr. Emily Rodriguez",
        "specialty": "Dermatologist",
        "network": "Premier Network",
        "location": {
            "address": "789 Skin Care Lane",
            "city": "Cambridge",
            "state": "MA",
            "zip": "02139",
        },
        "phone": "(617) 555-0345",
        "accepting_new_patients": False,
        "languages": ["English", "Spanish"],
    },
    {
        "provider_id": "PRV-004",
        "name": "Dr. James Wilson",
        "specialty": "Orthopedic Surgeon",
        "network": "Standard Network",
        "location": {
            "address": "321 Bone & Joint Center",
            "city": "Boston",
            "state": "MA",
            "zip": "02110",
        },
        "phone": "(617) 555-0456",
        "accepting_new_patients": True,
        "languages": ["English"],
    },
    {
        "provider_id": "PRV-005",
        "name": "Dr. Lisa Park",
        "specialty": "Primary Care Physician",
        "network": "Standard Network",
        "location": {
            "address": "555 Family Health Road",
            "city": "Somerville",
            "state": "MA",
            "zip": "02143",
        },
        "phone": "(617) 555-0567",
        "accepting_new_patients": True,
        "languages": ["English", "Korean"],
    },
]


def search_providers(
    specialty: str | None = None,
    location: str | None = None,
    network: str | None = None,
    accepting_new_patients: bool | None = None,
) -> list[dict[str, Any]]:
    """Search for healthcare providers.

    Args:
        specialty: Provider specialty to filter by
        location: City or zip code to search in
        network: Insurance network (e.g., "Premier Network")
        accepting_new_patients: Filter by whether accepting new patients

    Returns:
        List of matching providers
    """
    results = PROVIDER_DATABASE.copy()

    # Filter by specialty
    if specialty:
        specialty_lower = specialty.lower()
        results = [
            p
            for p in results
            if specialty_lower in p["specialty"].lower()
        ]

    # Filter by location
    if location:
        location_lower = location.lower()
        results = [
            p
            for p in results
            if (
                location_lower in p["location"]["city"].lower()
                or location_lower in p["location"]["zip"]
                or location_lower in p["location"]["state"].lower()
            )
        ]

    # Filter by network
    if network:
        network_lower = network.lower()
        results = [
            p for p in results if network_lower in p["network"].lower()
        ]

    # Filter by accepting new patients
    if accepting_new_patients is not None:
        results = [
            p
            for p in results
            if p["accepting_new_patients"] == accepting_new_patients
        ]

    return results


def get_provider_details(provider_id: str) -> dict[str, Any] | None:
    """Get detailed information about a specific provider.

    Args:
        provider_id: The provider ID

    Returns:
        Provider details or None if not found
    """
    for provider in PROVIDER_DATABASE:
        if provider["provider_id"] == provider_id:
            return provider
    return None
