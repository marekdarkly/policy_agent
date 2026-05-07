"""
User Profile Management for LaunchDarkly Context

This module creates rich, segmented user profiles following LaunchDarkly best practices
for targeting and personalization.
"""

from datetime import datetime
from typing import Any
import random


def create_user_profile(
    name: str = "Marek Poliks",
    location: str = "San Francisco, CA",
    policy_id: str = "POL-12345",
    coverage_type: str = "Gold Plan",
    domain: str = "togglehealth",
    user_key: str | None = None,
    user_type: str | None = None,
    role: str | None = None,
    plan_override: str | None = None,
) -> dict[str, Any]:
    """Create a comprehensive user profile for LaunchDarkly context.
    
    This follows LaunchDarkly's best practices for rich context attributes,
    enabling targeted feature flags, A/B testing, and personalized experiences.
    
    The profile adapts to the domain (togglehealth, togglecell, togglebank) so
    that context fields are coherent with the brand the customer is interacting
    with. This prevents the coherence judge from flagging domain mismatches
    (e.g. health-insurance fields on a banking customer).
    
    Args:
        name: User's full name
        location: City and state
        policy_id: Insurance policy identifier (health) or account ID (bank/cell)
        coverage_type: Type of coverage plan (health) or account type (bank/cell)
        domain: Brand domain — ``togglehealth``, ``togglecell``, or ``togglebank``
        
    Returns:
        Dictionary of user attributes for LaunchDarkly context
    """
    # Parse location
    city, state = location.split(", ") if ", " in location else (location, "CA")
    
    # User key: explicit override wins (used by the demo "login switcher" so we
    # can target by user key directly in LaunchDarkly), otherwise derive from name.
    if not user_key:
        user_key = name.lower().replace(" ", "-")
    
    # Determine timezone from location
    timezone_map = {
        "MA": "America/New_York",
        "NY": "America/New_York",
        "CA": "America/Los_Angeles",
        "WA": "America/Los_Angeles",
        "TX": "America/Chicago",
        "IL": "America/Chicago",
    }
    timezone = timezone_map.get(state, "America/Los_Angeles")

    # Normalise domain for comparison
    domain = (domain or "togglehealth").lower()

    email_domain = {
        "togglehealth": "togglehealth.com",
        "togglecell": "togglecell.com",
        "togglebank": "togglebank.com",
    }.get(domain, "togglehealth.com")

    # ── shared base ──────────────────────────────────────────────────────
    profile: dict[str, Any] = {
        # Core Identity
        "user_key": user_key,
        "name": name,
        "email": f"{user_key}@{email_domain}",

        # Location & Time — always US-based
        "location": location,
        "city": city,
        "state": state,
        "zip_code": "94102",
        "timezone": timezone,
        "country": "US",

        # Demographics (for segmentation)
        "age_range": "35-44",
        "family_size": 1,
        "has_dependents": False,
        "employment_status": "employed",

        # Preferences & Behavior
        "preferred_language": "en",
        "communication_preference": "email",
        "notification_enabled": True,
        "paperless_billing": True,

        # Segmentation Attributes (for targeting)
        "engagement_level": "high",
        "lifetime_value": "high",

        # Feature Flags Context
        "beta_tester": False,
        "early_access": True,

        # Session Metadata
        "session_id": f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "last_login": datetime.now().isoformat(),
        "device_type": "web",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",

        # Domain tag (consumed by judges, triage, brand voice)
        "domain": domain,
    }

    # Optional identity overrides used by the demo "login switcher".
    # These let us target by user key / role / user_type in LaunchDarkly without
    # having to mutate the rest of the profile shape.
    if user_type:
        profile["user_type"] = user_type
    if role:
        profile["role"] = role

    # ── domain-specific fields ───────────────────────────────────────────
    if domain == "togglebank":
        # Tier labels must include "Gold" so the default server value
        # ("Gold HMO") resolves correctly and the LD segment rules
        # (plan=gold, customer_tier=gold) continue to match.
        account_tier_map = {
            "Basic": 1, "Standard": 2, "Gold": 3,
            "Premium": 3, "Private": 4, "Platinum": 4,
        }
        account_tier = next(
            (t for label, t in account_tier_map.items() if label in coverage_type),
            3,
        )
        tier_label = {1: "bronze", 2: "silver", 3: "gold", 4: "platinum"}.get(
            account_tier, "gold"
        )
        profile.update({
            "account_id": policy_id,
            "account_type": coverage_type,
            "account_tier": account_tier,
            "plan": tier_label,
            "customer_segment": f"{tier_label}_member",
            "customer_tier": tier_label,
            "member_since": "2023-01-15",
            "account_status": "active",
            "currency": "USD",

            "billing_status": "current",
            "payment_method": "auto_pay",
            "autopay_enabled": True,

            "risk_profile": "low",

            "search_context": {
                "primary_location": f"{city}, {state}",
                "account_type_filter": coverage_type,
                "account_tier": account_tier,
            },
        })

    elif domain == "togglecell":
        plan_tier_map = {
            "Basic": 1, "Standard": 2, "Gold": 3,
            "Plus": 3, "Unlimited": 4,
        }
        plan_tier = next(
            (t for label, t in plan_tier_map.items() if label in coverage_type),
            3,
        )
        tier_label = {1: "bronze", 2: "silver", 3: "gold", 4: "platinum"}.get(
            plan_tier, "gold"
        )
        profile.update({
            "account_id": policy_id,
            "plan_name": coverage_type,
            "plan_tier": plan_tier,
            "plan": tier_label,
            "customer_segment": f"{tier_label}_member",
            "customer_tier": tier_label,
            "member_since": "2023-01-15",
            "account_status": "active",

            "billing_status": "current",
            "payment_method": "auto_pay",
            "monthly_amount": 75.00,
            "billing_cycle": "monthly",
            "autopay_enabled": True,

            "search_context": {
                "primary_location": f"{city}, {state}",
                "plan_type_filter": coverage_type,
                "plan_tier": plan_tier,
            },
        })

    else:
        # togglehealth (default)
        plan_tier_map = {"Bronze": 1, "Silver": 2, "Gold": 3, "Platinum": 4}
        plan_tier = next(
            (t for label, t in plan_tier_map.items() if label in coverage_type),
            3,
        )
        tier_label = {1: "bronze", 2: "silver", 3: "gold", 4: "platinum"}.get(
            plan_tier, "gold"
        )
        network = "Premier Network"
        if "HMO" in coverage_type:
            network = "HMO Network"
        elif "PPO" in coverage_type:
            network = "PPO Network"
        elif "EPO" in coverage_type:
            network = "EPO Network"

        profile.update({
            "policy_id": policy_id,
            "coverage_type": coverage_type,
            "plan_tier": plan_tier,
            "plan": tier_label,
            "network": network,
            "network_type": "Premier",
            "member_since": "2023-01-15",
            "policy_status": "active",
            "renewal_date": "2025-01-15",

            "billing_status": "current",
            "payment_method": "auto_pay",
            "premium_amount": 650.00,
            "billing_cycle": "monthly",
            "autopay_enabled": True,

            "customer_segment": f"{tier_label}_member",
            "customer_tier": tier_label,
            "risk_profile": "low",

            "primary_care_assigned": True,
            "has_chronic_conditions": False,
            "recent_claims_count": 3,
            "last_claim_date": "2024-10-15",
            "preferred_providers": ["SPEC-MA-001", "PCP-MA-002"],

            "search_context": {
                "primary_location": f"{city}, {state}",
                "network_filter": network,
                "plan_type_filter": coverage_type,
                "coverage_tier": plan_tier,
            },
        })

    # Plan override: forces both `plan` and `customer_tier` to a non-gold label
    # (e.g. "internal") so the internal-dev user doesn't accidentally satisfy
    # commercial segment plan-based rules.
    if plan_override:
        profile["plan"] = plan_override
        profile["customer_tier"] = plan_override
        profile["customer_segment"] = f"{plan_override}_member"

    return profile


def get_targeted_search_context(user_profile: dict[str, Any]) -> dict[str, str]:
    """Extract search-optimized context from user profile.
    
    This creates a focused context dict specifically for RAG queries,
    enabling highly targeted retrieval.  Adapts to the domain stored in
    the profile so only relevant fields are included.
    
    Args:
        user_profile: Full user profile dictionary
        
    Returns:
        Focused context for RAG searches
    """
    domain = user_profile.get("domain", "togglehealth")
    base = {
        "user_name": user_profile.get("name", ""),
        "location": user_profile.get("location", ""),
        "city": user_profile.get("city", ""),
        "state": user_profile.get("state", ""),
        "member_since": user_profile.get("member_since", ""),
    }

    if domain == "togglebank":
        base.update({
            "account_id": user_profile.get("account_id", ""),
            "account_type": user_profile.get("account_type", ""),
            "account_tier": str(user_profile.get("account_tier", "")),
            "currency": user_profile.get("currency", "USD"),
        })
    elif domain == "togglecell":
        base.update({
            "account_id": user_profile.get("account_id", ""),
            "plan_name": user_profile.get("plan_name", ""),
            "plan_tier": str(user_profile.get("plan_tier", "")),
        })
    else:
        base.update({
            "network": user_profile.get("network", ""),
            "network_type": user_profile.get("network_type", ""),
            "coverage_type": user_profile.get("coverage_type", ""),
            "plan_tier": str(user_profile.get("plan_tier", "")),
            "policy_id": user_profile.get("policy_id", ""),
            "has_chronic_conditions": str(user_profile.get("has_chronic_conditions", False)),
        })

    return base


def format_profile_summary(user_profile: dict[str, Any]) -> str:
    """Format user profile as a readable summary.
    
    Args:
        user_profile: User profile dictionary
        
    Returns:
        Formatted string summary
    """
    domain = user_profile.get("domain", "togglehealth")

    lines = [
        "=" * 80,
        "USER PROFILE",
        "=" * 80,
        "",
        "Identity:",
        f"  • Name: {user_profile.get('name')}",
        f"  • Email: {user_profile.get('email')}",
        f"  • User Key: {user_profile.get('user_key')}",
        "",
        "Location:",
        f"  • Location: {user_profile.get('location')}",
        f"  • Timezone: {user_profile.get('timezone')}",
        f"  • Zip Code: {user_profile.get('zip_code')}",
        "",
    ]

    if domain == "togglebank":
        lines += [
            "Banking Details:",
            f"  • Account ID: {user_profile.get('account_id')}",
            f"  • Account Type: {user_profile.get('account_type')}",
            f"  • Member Since: {user_profile.get('member_since')}",
            f"  • Status: {user_profile.get('account_status', 'active').upper()}",
            f"  • Currency: {user_profile.get('currency', 'USD')}",
        ]
    elif domain == "togglecell":
        lines += [
            "Plan Details:",
            f"  • Account ID: {user_profile.get('account_id')}",
            f"  • Plan: {user_profile.get('plan_name')}",
            f"  • Member Since: {user_profile.get('member_since')}",
            f"  • Status: {user_profile.get('account_status', 'active').upper()}",
        ]
    else:
        lines += [
            "Insurance Coverage:",
            f"  • Policy ID: {user_profile.get('policy_id')}",
            f"  • Plan: {user_profile.get('coverage_type')}",
            f"  • Network: {user_profile.get('network')}",
            f"  • Member Since: {user_profile.get('member_since')}",
            f"  • Status: {user_profile.get('policy_status', 'active').upper()}",
        ]

    lines += [
        "",
        "Billing:",
        f"  • Status: {user_profile.get('billing_status', 'current').upper()}",
        f"  • Auto-Pay: {'Enabled' if user_profile.get('autopay_enabled') else 'Disabled'}",
        "",
        "Segmentation:",
        f"  • Customer Segment: {user_profile.get('customer_segment', 'standard').upper()}",
        f"  • Engagement Level: {user_profile.get('engagement_level', 'medium').upper()}",
        f"  • Lifetime Value: {user_profile.get('lifetime_value', 'medium').upper()}",
        "",
        "Preferences:",
        f"  • Language: {user_profile.get('preferred_language', 'en').upper()}",
        f"  • Communication: {user_profile.get('communication_preference', 'email').upper()}",
        f"  • Paperless Billing: {'Yes' if user_profile.get('paperless_billing') else 'No'}",
        "",
        "=" * 80,
    ]
    return "\n".join(lines)


# Default profile for demo purposes
DEFAULT_PROFILE = create_user_profile(
    name="Marek Poliks",
    location="San Francisco, CA",
    policy_id="TH-HMO-GOLD-2024",
    coverage_type="Gold HMO",
    domain="togglehealth",
)

