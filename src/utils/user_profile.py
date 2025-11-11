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
    coverage_type: str = "Gold Plan"
) -> dict[str, Any]:
    """Create a comprehensive user profile for LaunchDarkly context.
    
    This follows LaunchDarkly's best practices for rich context attributes,
    enabling targeted feature flags, A/B testing, and personalized experiences.
    
    Args:
        name: User's full name
        location: City and state
        policy_id: Insurance policy identifier
        coverage_type: Type of coverage plan
        
    Returns:
        Dictionary of user attributes for LaunchDarkly context
    """
    # Parse location
    city, state = location.split(", ") if ", " in location else (location, "CA")
    
    # Generate user key from name
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
    
    # Map plan type to tier
    plan_tier_map = {
        "Bronze": 1,
        "Silver": 2,
        "Gold": 3,
        "Platinum": 4
    }
    plan_tier = None
    for tier_name, tier_num in plan_tier_map.items():
        if tier_name in coverage_type:
            plan_tier = tier_num
            break
    
    # Determine network type
    network = "Premier Network"  # Could be derived from policy data
    if "HMO" in coverage_type:
        network = "HMO Network"
    elif "PPO" in coverage_type:
        network = "PPO Network"
    elif "EPO" in coverage_type:
        network = "EPO Network"
    
    return {
        # Core Identity
        "user_key": user_key,
        "name": name,
        "email": f"{user_key}@togglehealth.com",
        
        # Location & Time
        "location": location,
        "city": city,
        "state": state,
        "zip_code": "94102",  # Downtown San Francisco
        "timezone": timezone,
        "country": "US",
        
        # Insurance Policy Details
        "policy_id": policy_id,
        "coverage_type": coverage_type,
        "plan_tier": plan_tier or 3,  # 1=Bronze, 2=Silver, 3=Gold, 4=Platinum
        "network": network,
        "network_type": "Premier",
        "member_since": "2023-01-15",
        "policy_status": "active",
        "renewal_date": "2025-01-15",
        
        # Billing & Payment
        "billing_status": "current",  # current, past_due, suspended
        "payment_method": "auto_pay",
        "premium_amount": 650.00,
        "billing_cycle": "monthly",
        "autopay_enabled": True,
        
        # Demographics (for segmentation)
        "age_range": "35-44",  # Age ranges for privacy
        "family_size": 1,
        "has_dependents": False,
        "employment_status": "employed",
        
        # Healthcare Profile
        "primary_care_assigned": True,
        "has_chronic_conditions": False,
        "recent_claims_count": 3,
        "last_claim_date": "2024-10-15",
        "preferred_providers": ["SPEC-MA-001", "PCP-MA-002"],
        
        # Preferences & Behavior
        "preferred_language": "en",
        "communication_preference": "email",  # email, sms, phone, app
        "notification_enabled": True,
        "paperless_billing": True,
        
        # Segmentation Attributes (for targeting)
        "customer_segment": "gold_member",  # bronze_member, silver_member, gold_member, platinum_member
        "engagement_level": "high",  # low, medium, high
        "risk_profile": "low",  # low, medium, high (for underwriting)
        "lifetime_value": "high",  # low, medium, high
        
        # RAG Enhancement Attributes
        "search_context": {
            "primary_location": f"{city}, {state}",
            "network_filter": network,
            "plan_type_filter": coverage_type,
            "coverage_tier": plan_tier or 3,
        },
        
        # Feature Flags Context
        "beta_tester": False,
        "early_access": True,
        "customer_tier": "gold",
        
        # Session Metadata
        "session_id": f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "last_login": datetime.now().isoformat(),
        "device_type": "web",
        "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    }


def get_targeted_search_context(user_profile: dict[str, Any]) -> dict[str, str]:
    """Extract search-optimized context from user profile.
    
    This creates a focused context dict specifically for RAG queries,
    enabling highly targeted retrieval.
    
    Args:
        user_profile: Full user profile dictionary
        
    Returns:
        Focused context for RAG searches
    """
    return {
        "user_name": user_profile.get("name", ""),
        "location": user_profile.get("location", ""),
        "city": user_profile.get("city", ""),
        "state": user_profile.get("state", ""),
        "network": user_profile.get("network", ""),
        "network_type": user_profile.get("network_type", ""),
        "coverage_type": user_profile.get("coverage_type", ""),
        "plan_tier": str(user_profile.get("plan_tier", "")),
        "policy_id": user_profile.get("policy_id", ""),
        "member_since": user_profile.get("member_since", ""),
        "has_chronic_conditions": str(user_profile.get("has_chronic_conditions", False)),
    }


def format_profile_summary(user_profile: dict[str, Any]) -> str:
    """Format user profile as a readable summary.
    
    Args:
        user_profile: User profile dictionary
        
    Returns:
        Formatted string summary
    """
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
        "Insurance Coverage:",
        f"  • Policy ID: {user_profile.get('policy_id')}",
        f"  • Plan: {user_profile.get('coverage_type')}",
        f"  • Network: {user_profile.get('network')}",
        f"  • Member Since: {user_profile.get('member_since')}",
        f"  • Status: {user_profile.get('policy_status', 'active').upper()}",
        "",
        "Billing:",
        f"  • Status: {user_profile.get('billing_status', 'current').upper()}",
        f"  • Premium: ${user_profile.get('premium_amount', 0):.2f}/{user_profile.get('billing_cycle', 'monthly')}",
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
    policy_id="POL-12345",
    coverage_type="Gold Plan"
)

