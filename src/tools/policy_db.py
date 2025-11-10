"""Policy database tools (simulated)."""

from typing import Any


# Simulated policy database
POLICY_DATABASE = {
    "POL-12345": {
        "policy_id": "POL-12345",
        "policy_holder": "John Doe",
        "coverage_type": "Gold Plan",
        "network": "Premier Network",
        "deductible": "$1,500",
        "deductible_met": "$800",
        "out_of_pocket_max": "$6,000",
        "copay_primary_care": "$25",
        "copay_specialist": "$50",
        "coinsurance": "20%",
        "prescription_coverage": "Tier 1: $10, Tier 2: $30, Tier 3: $60",
        "coverage_details": {
            "preventive_care": "100% covered",
            "emergency_room": "$250 copay",
            "urgent_care": "$75 copay",
            "hospitalization": "20% coinsurance after deductible",
            "mental_health": "Covered same as medical",
            "physical_therapy": "$50 copay, 30 visits per year",
        },
    },
    "POL-67890": {
        "policy_id": "POL-67890",
        "policy_holder": "Jane Smith",
        "coverage_type": "Silver Plan",
        "network": "Standard Network",
        "deductible": "$3,000",
        "deductible_met": "$0",
        "out_of_pocket_max": "$8,000",
        "copay_primary_care": "$35",
        "copay_specialist": "$70",
        "coinsurance": "30%",
        "prescription_coverage": "Tier 1: $15, Tier 2: $40, Tier 3: $80",
        "coverage_details": {
            "preventive_care": "100% covered",
            "emergency_room": "$350 copay",
            "urgent_care": "$100 copay",
            "hospitalization": "30% coinsurance after deductible",
            "mental_health": "Covered same as medical",
            "physical_therapy": "$70 copay, 20 visits per year",
        },
    },
}


def get_policy_info(policy_id: str | None) -> dict[str, Any]:
    """Retrieve policy information from the database.

    Args:
        policy_id: The policy ID to look up

    Returns:
        Policy information dictionary
    """
    if not policy_id:
        return {
            "error": "No policy ID provided",
            "message": "Please provide your policy ID to retrieve coverage information.",
        }

    policy = POLICY_DATABASE.get(policy_id)

    if not policy:
        return {
            "error": "Policy not found",
            "message": f"Policy ID {policy_id} not found in our system. "
            "Please verify the policy ID or contact support.",
        }

    return policy


def search_policy_coverage(policy_id: str, coverage_type: str) -> dict[str, Any]:
    """Search for specific coverage information.

    Args:
        policy_id: The policy ID
        coverage_type: Type of coverage to search for (e.g., "dental", "vision")

    Returns:
        Coverage information
    """
    policy = get_policy_info(policy_id)

    if "error" in policy:
        return policy

    # Search in coverage details
    coverage_details = policy.get("coverage_details", {})

    matching_coverage = {}
    for key, value in coverage_details.items():
        if coverage_type.lower() in key.lower():
            matching_coverage[key] = value

    if not matching_coverage:
        return {
            "message": f"No specific information found for '{coverage_type}'. "
            f"Please contact support for detailed coverage information."
        }

    return {
        "policy_id": policy_id,
        "coverage_type": coverage_type,
        "details": matching_coverage,
    }
