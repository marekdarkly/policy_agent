"""
Shared infrastructure for synthetic traffic handlers.

Contains user pool, question pool, beta tester profile generation,
observability initialization, and trace helpers used by both the
LangGraph handler and the Agent Graph handler.
"""

import logging
import os
import time
from datetime import datetime, timezone
from uuid import uuid4

import boto3

logger = logging.getLogger(__name__)

ITERATIONS = 10
POSITIVE_FEEDBACK_RATE = 0.99

BETA_TESTER_USERS = [
    {"name": "Alice Chen", "location": "San Francisco, CA", "policy_id": "TH-HMO-GOLD-2024-001", "coverage_type": "Gold HMO"},
    {"name": "Bob Martinez", "location": "Los Angeles, CA", "policy_id": "TH-PPO-PLAT-2024-002", "coverage_type": "Platinum PPO"},
    {"name": "Carol Washington", "location": "Boston, MA", "policy_id": "TH-EPO-SILV-2024-003", "coverage_type": "Silver EPO"},
    {"name": "David Kim", "location": "Seattle, WA", "policy_id": "TH-HMO-GOLD-2024-004", "coverage_type": "Gold HMO"},
    {"name": "Elena Rodriguez", "location": "Austin, TX", "policy_id": "TH-HDHP-BRNZ-2024-005", "coverage_type": "Bronze HDHP"},
    {"name": "Frank O'Brien", "location": "Chicago, IL", "policy_id": "TH-PPO-PLAT-2024-006", "coverage_type": "Platinum PPO"},
    {"name": "Grace Nakamura", "location": "Portland, OR", "policy_id": "TH-HMO-GOLD-2024-007", "coverage_type": "Gold HMO"},
    {"name": "Henry Patel", "location": "New York, NY", "policy_id": "TH-EPO-SILV-2024-008", "coverage_type": "Silver EPO"},
    {"name": "Isabel Santos", "location": "Miami, FL", "policy_id": "TH-HMO-GOLD-2024-009", "coverage_type": "Gold HMO"},
    {"name": "James Thompson", "location": "Denver, CO", "policy_id": "TH-PPO-PLAT-2024-010", "coverage_type": "Platinum PPO"},
    {"name": "Karen Liu", "location": "San Jose, CA", "policy_id": "TH-HDHP-BRNZ-2024-011", "coverage_type": "Bronze HDHP"},
    {"name": "Leo Rossi", "location": "Philadelphia, PA", "policy_id": "TH-HMO-GOLD-2024-012", "coverage_type": "Gold HMO"},
    {"name": "Maya Johnson", "location": "Atlanta, GA", "policy_id": "TH-EPO-SILV-2024-013", "coverage_type": "Silver EPO"},
    {"name": "Nathan Park", "location": "Houston, TX", "policy_id": "TH-PPO-PLAT-2024-014", "coverage_type": "Platinum PPO"},
    {"name": "Olivia Brown", "location": "Phoenix, AZ", "policy_id": "TH-HMO-GOLD-2024-015", "coverage_type": "Gold HMO"},
    {"name": "Peter Nguyen", "location": "Minneapolis, MN", "policy_id": "TH-HDHP-BRNZ-2024-016", "coverage_type": "Bronze HDHP"},
    {"name": "Quinn Davis", "location": "San Diego, CA", "policy_id": "TH-EPO-SILV-2024-017", "coverage_type": "Silver EPO"},
    {"name": "Rachel Green", "location": "Dallas, TX", "policy_id": "TH-HMO-GOLD-2024-018", "coverage_type": "Gold HMO"},
    {"name": "Sam Wilson", "location": "Detroit, MI", "policy_id": "TH-PPO-PLAT-2024-019", "coverage_type": "Platinum PPO"},
    {"name": "Tanya Sharma", "location": "Charlotte, NC", "policy_id": "TH-HMO-GOLD-2024-020", "coverage_type": "Gold HMO"},
    {"name": "Uri Cohen", "location": "Washington, DC", "policy_id": "TH-EPO-SILV-2024-021", "coverage_type": "Silver EPO"},
    {"name": "Vanessa Torres", "location": "Sacramento, CA", "policy_id": "TH-HDHP-BRNZ-2024-022", "coverage_type": "Bronze HDHP"},
    {"name": "William Chang", "location": "Nashville, TN", "policy_id": "TH-HMO-GOLD-2024-023", "coverage_type": "Gold HMO"},
    {"name": "Xena Papadopoulos", "location": "Raleigh, NC", "policy_id": "TH-PPO-PLAT-2024-024", "coverage_type": "Platinum PPO"},
    {"name": "Yosef Ali", "location": "Salt Lake City, UT", "policy_id": "TH-HMO-GOLD-2024-025", "coverage_type": "Gold HMO"},
    {"name": "Zoe Campbell", "location": "Kansas City, MO", "policy_id": "TH-EPO-SILV-2024-026", "coverage_type": "Silver EPO"},
    {"name": "Aaron Wright", "location": "Columbus, OH", "policy_id": "TH-HDHP-BRNZ-2024-027", "coverage_type": "Bronze HDHP"},
    {"name": "Bella Fernandez", "location": "San Antonio, TX", "policy_id": "TH-HMO-GOLD-2024-028", "coverage_type": "Gold HMO"},
    {"name": "Carlos Delgado", "location": "Jacksonville, FL", "policy_id": "TH-PPO-PLAT-2024-029", "coverage_type": "Platinum PPO"},
    {"name": "Diana Okafor", "location": "Indianapolis, IN", "policy_id": "TH-HMO-GOLD-2024-030", "coverage_type": "Gold HMO"},
    {"name": "Ethan Brooks", "location": "Pittsburgh, PA", "policy_id": "TH-EPO-SILV-2024-031", "coverage_type": "Silver EPO"},
    {"name": "Fatima Hassan", "location": "Las Vegas, NV", "policy_id": "TH-HDHP-BRNZ-2024-032", "coverage_type": "Bronze HDHP"},
]

QUESTION_POOL = [
    "What is my copay for a primary care visit?",
    "Does my plan require referrals for specialist visits?",
    "What is my copay for generic medications?",
    "Tell me about the Diabetes Management Program for my plan.",
    "What is my emergency room copay?",
    "Does my plan cover out-of-network providers?",
    "What is my specialist visit copay?",
    "How many nutritionist visits do I get through the Diabetes Management Program?",
    "What is my urgent care copay?",
    "What are the key features of my health plan?",
    "What is the mail order copay for preferred brand drugs on my plan?",
    "Do I need to select a primary care physician?",
    "What is my specialty drug copay at retail?",
    "Which ToggleHealth plans are eligible for the Diabetes Management Program?",
    "Does the Diabetes Management Program cover glucose monitors for my plan?",
    "What prescription drug tiers does my plan have?",
    "Do copays apply before my deductible is met?",
    "What diabetes education services are covered at 100%?",
    "Are specialty medications available by mail order on my plan?",
    "How do I enroll in the Diabetes Management Program?",
    "What is my copay for non-preferred brand drugs at retail?",
    "Can you help me find a dermatologist in New York?",
    "I need a primary care doctor in San Francisco. What providers are available?",
    "Are there any mental health providers in Seattle who accept my plan?",
    "Can you find me a pharmacy in Portland, Oregon?",
    "I need to find a specialist in Texas. What's available?",
    "What networks does Dr. Kevin Patel participate in?",
    "Find me a primary care doctor in Boston.",
    "I'm looking for mental health services in Chicago.",
    "Show me dermatologists in California who accept my plan.",
    "Is Dr. Kevin Patel accepting new patients?",
    "Find me doctors in Florida who accept my plan.",
    "Show me specialists in North Carolina.",
    "I need to speak with someone about my claim denial.",
    "Can I schedule a call with an agent?",
    "I'm having a billing issue and need to talk to someone.",
    "I want to file a complaint about a recent experience.",
    "Can you transfer me to a human agent?",
]

_initialized = False


def ensure_initialized():
    """Load secrets from SSM and initialize observability (once per cold start)."""
    global _initialized
    if _initialized:
        return

    parameter_prefix = os.environ.get(
        "PARAMETER_PREFIX", "/togglehealth-synthetic/prod"
    )

    try:
        ssm = boto3.client("ssm")
        response = ssm.get_parameter(
            Name=f"{parameter_prefix}/launchdarkly/sdk-key", WithDecryption=True
        )
        os.environ["LAUNCHDARKLY_SDK_KEY"] = response["Parameter"]["Value"]
    except Exception as e:
        logger.warning(f"SSM lookup failed ({e}), falling back to env var")
        if not os.environ.get("LAUNCHDARKLY_SDK_KEY"):
            raise

    os.environ.setdefault("LAUNCHDARKLY_ENABLED", "true")
    os.environ.setdefault("LLM_PROVIDER", "bedrock")
    os.environ.setdefault("LLM_MODEL", "claude-3-5-sonnet")
    os.environ.setdefault("AWS_REGION", "us-east-1")

    from src.utils.observability import initialize_observability

    result = initialize_observability(environment="production")
    if not result:
        logger.error("Observability init failed — LD client may not be configured")

    import ldclient
    if not ldclient.get().is_initialized():
        logger.warning("LD client not initialized after observability setup, retrying...")
        import time
        for _ in range(20):
            if ldclient.get().is_initialized():
                break
            time.sleep(0.5)

    _initialized = True


def create_beta_tester_profile(user_spec: dict) -> dict:
    """Create a user profile for a beta tester."""
    from src.utils.user_profile import create_user_profile

    profile = create_user_profile(
        name=user_spec["name"],
        location=user_spec["location"],
        policy_id=user_spec["policy_id"],
        coverage_type=user_spec["coverage_type"],
    )

    profile["beta_tester"] = True
    profile["role"] = "Beta"
    profile["customer_tier"] = "beta"
    profile["plan"] = "beta"
    profile["user_key"] = f"synthetic-{profile['user_key']}"
    profile["session_id"] = (
        f"synthetic-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}"
        f"-{uuid4().hex[:6]}"
    )
    return profile


def get_tracer(name: str = "togglehealth.synthetic-traffic"):
    """Get an OpenTelemetry tracer for synthetic traffic spans."""
    from opentelemetry import trace

    return trace.get_tracer(name, "1.0.0")


def flush_traces(timeout_ms: int = 10000):
    """Flush all pending spans and LD client events."""
    try:
        from opentelemetry import trace

        provider = trace.get_tracer_provider()
        if hasattr(provider, "force_flush"):
            provider.force_flush(timeout_millis=timeout_ms)
            logger.info("Trace spans flushed to LaunchDarkly")
    except Exception as e:
        logger.warning(f"Failed to flush trace spans: {e}")

    try:
        import ldclient
        client = ldclient.get()
        if client and client.is_initialized():
            client.flush()
            logger.info("LD client events flushed")
    except Exception as e:
        logger.warning(f"Failed to flush LD client events: {e}")


def build_ld_context(user_context: dict):
    """Build a LaunchDarkly Context from a user profile dict."""
    from ldclient import Context

    user_key = user_context.get("user_key", "anonymous")
    builder = Context.builder(user_key).kind("user")
    for attr in ["name", "role", "beta_tester", "customer_tier",
                 "plan", "coverage_type", "location", "policy_id"]:
        val = user_context.get(attr)
        if val is not None:
            builder.set(attr, val)
    return builder.build()
