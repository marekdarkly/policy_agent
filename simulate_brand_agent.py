#!/usr/bin/env python3
"""
Brand Agent AI Config Simulator

Simulates brand_agent flag evaluations with realistic metrics WITHOUT making actual model calls.
Generates metrics based on variation served and sends to LaunchDarkly for experimentation.

Usage:
    python simulate_brand_agent.py --iterations 100
    python simulate_brand_agent.py  # Run indefinitely
"""

import os
import sys
import time
import random
import argparse
import numpy as np
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.utils.launchdarkly_config import get_ld_client
from src.utils.user_profile import create_user_profile
import ldclient
from ldclient import Context

# Configuration
CONFIG_KEY = "brand_agent"

# Variation specifications with realistic metrics
VARIATION_SPECS = {
    "llama-4-simple-prompt": {
        # High accuracy, good coherence
        "accuracy": {"center": 0.97, "spread": 0.02},      # 95-99% accuracy
        "coherence": {"center": 0.90, "spread": 0.05},     # 85-95% coherence
        "duration": {"center": 3200, "spread": 400},       # ~3200ms duration
        "tokens": {"center": 2100, "spread": 300},         # ~2100 tokens
        "cost": {"center": 0.28, "spread": 0.05},          # ~0.28 cents
    },
    "llama-4-cost-cutting-prompt": {
        # Lower accuracy, lower coherence, faster/cheaper
        "accuracy": {"center": 0.70, "spread": 0.10},      # 60-80% accuracy
        "coherence": {"center": 0.77, "spread": 0.08},     # 70-85% coherence
        "duration": {"center": 2400, "spread": 350},       # ~2400ms (faster)
        "tokens": {"center": 1600, "spread": 250},         # ~1600 tokens (less)
        "cost": {"center": 0.18, "spread": 0.04},          # ~0.18 cents (cheaper)
    },
}


def create_random_gold_user() -> dict:
    """Create a random Gold plan user for testing."""
    # Random names for variety
    first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn", "Dakota", "Sage"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
    
    # Random locations
    locations = [
        "San Francisco, CA",
        "New York, NY", 
        "Boston, MA",
        "Austin, TX",
        "Seattle, WA",
        "Chicago, IL",
        "Denver, CO",
        "Portland, OR"
    ]
    
    # Generate random user
    random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
    random_location = random.choice(locations)
    
    profile = create_user_profile(
        name=random_name,
        location=random_location,
        policy_id="TH-HMO-GOLD-2024",
        coverage_type="Gold HMO"  # KEEP GOLD for segment matching
    )
    
    # OVERRIDE user_key with UUID for LaunchDarkly split test bucketing
    profile["user_key"] = f"brand-test-{uuid4()}"
    
    # Ensure Gold plan attributes are set for segment matching
    profile["plan_tier"] = 3  # Gold = 3
    profile["customer_tier"] = "gold"
    profile["customer_segment"] = "gold_member"
    
    return profile


def generate_distributions(iterations: int) -> dict:
    """Pre-generate metric distributions for all variations."""
    distributions = {}
    
    for variation_name, specs in VARIATION_SPECS.items():
        distributions[variation_name] = {
            "accuracy": np.random.normal(
                specs["accuracy"]["center"],
                specs["accuracy"]["spread"],
                iterations
            ),
            "coherence": np.random.normal(
                specs["coherence"]["center"],
                specs["coherence"]["spread"],
                iterations
            ),
            "duration": np.random.normal(
                specs["duration"]["center"],
                specs["duration"]["spread"],
                iterations
            ).astype(int),
            "tokens": np.random.normal(
                specs["tokens"]["center"],
                specs["tokens"]["spread"],
                iterations
            ).astype(int),
            "cost": np.random.normal(
                specs["cost"]["center"],
                specs["cost"]["spread"],
                iterations
            ),
        }
        
        # Clamp values to realistic ranges
        distributions[variation_name]["accuracy"] = np.clip(
            distributions[variation_name]["accuracy"], 0.0, 1.0
        )
        distributions[variation_name]["coherence"] = np.clip(
            distributions[variation_name]["coherence"], 0.0, 1.0
        )
        distributions[variation_name]["duration"] = np.maximum(
            distributions[variation_name]["duration"], 500
        )
        distributions[variation_name]["tokens"] = np.maximum(
            distributions[variation_name]["tokens"], 200
        )
        distributions[variation_name]["cost"] = np.maximum(
            distributions[variation_name]["cost"], 0.01
        )
    
    return distributions


def send_metrics_for_variation(
    iteration: int,
    distributions: dict,
    user_context: dict,
    ld_client_instance: any
) -> dict:
    """Pull flag variation and send corresponding metrics."""
    try:
        # Create LD context
        ld_context = Context.builder(user_context["user_key"])
        ld_context.kind("user")
        for key, value in user_context.items():
            if key != "user_key":
                ld_context.set(key, value)
        ld_context = ld_context.build()
        
        # Pull the brand_agent AI Config to get variation
        variation_detail = ld_client_instance.variation_detail(CONFIG_KEY, ld_context, {})
        
        # Extract variation key
        variation_key = None
        if isinstance(variation_detail.value, dict):
            variation_key = variation_detail.value.get("_ldMeta", {}).get("variationKey")
        
        if not variation_key or variation_key not in distributions:
            return {
                "success": False,
                "error": f"Unknown variation: {variation_key}"
            }
        
        # Get pre-generated metrics for this variation and iteration
        idx = iteration % len(distributions[variation_key]["accuracy"])
        
        accuracy = float(distributions[variation_key]["accuracy"][idx])
        coherence = float(distributions[variation_key]["coherence"][idx])
        duration = int(distributions[variation_key]["duration"][idx])
        tokens = int(distributions[variation_key]["tokens"][idx])
        cost = float(distributions[variation_key]["cost"][idx])
        
        # Send metrics to LaunchDarkly
        ld_client_instance.track("$ld:ai:hallucinations", ld_context, accuracy)
        ld_client_instance.track("$ld:ai:judge:accuracy", ld_context, accuracy)
        ld_client_instance.track("$ld:ai:coherence", ld_context, coherence)
        ld_client_instance.track("$ld:ai:duration:total", ld_context, float(duration))
        ld_client_instance.track("$ld:ai:tokens:total", ld_context, float(tokens))
        ld_client_instance.track("$ld:ai:tokens:costmanual", ld_context, cost)
        
        # Flush immediately
        ld_client_instance.flush()
        
        return {
            "success": True,
            "variation": variation_key,
            "accuracy": accuracy,
            "coherence": coherence,
            "duration": duration,
            "tokens": tokens,
            "cost": cost,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Run the brand agent simulation."""
    parser = argparse.ArgumentParser(
        description="Brand Agent AI Config Simulator - Generate metrics without model calls"
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=None,
        help="Number of iterations to run (default: infinite)"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("🎨 BRAND AGENT SIMULATOR")
    print("=" * 80)
    print(f"Config Key: {CONFIG_KEY}")
    print(f"Iterations: {'∞ (infinite)' if args.iterations is None else args.iterations}")
    print(f"Wait time: 1-15 seconds (random)")
    print()
    
    # Show variation specs
    print("📊 Variation Specifications:")
    for variation_name, specs in VARIATION_SPECS.items():
        print(f"\n  {variation_name}:")
        print(f"    Accuracy: {specs['accuracy']['center']:.2f} ± {specs['accuracy']['spread']:.2f}")
        print(f"    Coherence: {specs['coherence']['center']:.2f} ± {specs['coherence']['spread']:.2f}")
        print(f"    Duration: {specs['duration']['center']}ms ± {specs['duration']['spread']}ms")
        print(f"    Tokens: {specs['tokens']['center']} ± {specs['tokens']['spread']}")
        print(f"    Cost: {specs['cost']['center']:.2f}¢ ± {specs['cost']['spread']:.2f}¢")
    
    print("\n" + "=" * 80)
    
    # Initialize LaunchDarkly
    ld_client = get_ld_client()
    raw_ld_client = ldclient.get()
    
    if not raw_ld_client or not raw_ld_client.is_initialized():
        print("❌ LaunchDarkly client not initialized!")
        return
    
    print("✅ LaunchDarkly client initialized")
    
    # Pre-generate distributions
    max_iterations = args.iterations if args.iterations else 10000  # Large number for infinite mode
    print(f"📈 Pre-generating metric distributions for {max_iterations} iterations...")
    distributions = generate_distributions(max_iterations)
    print("✅ Distributions generated")
    
    print("\n" + "=" * 80)
    print("🚀 Starting simulation...\n")
    
    iteration = 0
    
    try:
        while True:
            iteration += 1
            
            # Check if we should stop
            if args.iterations and iteration > args.iterations:
                break
            
            # Create random Gold plan user
            user_context = create_random_gold_user()
            
            # Send metrics
            result = send_metrics_for_variation(
                iteration - 1,  # 0-indexed
                distributions,
                user_context,
                raw_ld_client
            )
            
            if result["success"]:
                variation = result["variation"]
                print(f"✅ {iteration:4d} | {variation:30s} | "
                      f"acc={result['accuracy']:.2f} | coh={result['coherence']:.2f} | "
                      f"dur={result['duration']:4d}ms | tok={result['tokens']:4d} | "
                      f"cost={result['cost']:.2f}¢")
            else:
                print(f"❌ {iteration:4d} | ERROR: {result.get('error', 'Unknown error')}")
            
            # Random wait between 1-15 seconds
            wait_time = random.uniform(1, 15)
            time.sleep(wait_time)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Simulation stopped by user")
    
    # Final stats
    print("\n" + "=" * 80)
    print(f"📊 SIMULATION COMPLETE")
    print(f"   Total iterations: {iteration}")
    print("=" * 80)
    
    # Close LD client
    raw_ld_client.close()


if __name__ == "__main__":
    main()

