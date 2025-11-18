#!/usr/bin/env python3
"""
Simulate LaunchDarkly experiment for policy_agent prompt variations.

Tests 4 Llama 4 prompt variations with specific performance characteristics.
Uses unique users per iteration to enable CUPED.

Usage:
    ITERATIONS=200 python simulate_policy_prompts.py
"""

import os
import sys
import time
import random
import numpy as np
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

# Suppress noisy logs
import logging
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("ldclient").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

# Add project root
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

import ldclient
from ldclient import Context

# Configuration
ITERATIONS = int(os.getenv("ITERATIONS", "200"))
CONFIG_KEY = "policy_agent"

# PROMPT VARIATION SPECIFICATIONS
# Each variation has different performance characteristics
PROMPT_SPECS = {
    "llama-4-simple-prompt": {
        "accuracy": {"center": 0.90, "spread": 0.08},      # Control: Good accuracy, generous curve
        "duration": {"center": 4210, "spread": 350},       # Narrower curve
        "cost": {"center": 0.134, "spread": 0.02},         # Cost in cents (13.4 cents)
        "resolution_rate": 0.68,                           # 68% resolution rate (binary)
        "negative_feedback_rate": 0.068,                   # 6.8% negative feedback rate
    },
    "llama-4-systematic-prompt": {
        "accuracy": {"center": 0.83, "spread": 0.09},      # Lower accuracy, generous curve
        "duration": {"center": 4081, "spread": 340},       # Slightly faster, narrower curve
        "cost": {"center": 0.18, "spread": 0.025},         # More expensive (18 cents)
        "resolution_rate": 0.63,                           # 63% resolution rate
        "negative_feedback_rate": 0.1229,                  # 12.29% negative feedback rate
    },
    "llama-4-concise-prompt": {
        "accuracy": {"center": 0.9593, "spread": 0.07},    # BEST accuracy, generous curve
        "duration": {"center": 3452, "spread": 290},       # FASTEST, narrower curve
        "cost": {"center": 0.14, "spread": 0.02},          # Low cost (14 cents)
        "resolution_rate": 0.84,                           # BEST resolution (84%)
        "negative_feedback_rate": 0.021,                   # LOWEST negative feedback (2.1%)
    },
    "llama-4-reasoning-prompt": {
        "accuracy": {"center": 0.92, "spread": 0.08},      # Good accuracy, generous curve
        "duration": {"center": 4630, "spread": 380},       # SLOWEST (more reasoning), narrower curve
        "cost": {"center": 0.21, "spread": 0.03},          # MOST EXPENSIVE (21 cents)
        "resolution_rate": 0.74,                           # 74% resolution rate
        "negative_feedback_rate": 0.112,                   # 11.2% negative feedback rate
    },
}


def create_unique_user(iteration: int) -> dict:
    """Create a unique user for this iteration (enables CUPED)."""
    user_key = f"policy-prompt-test-{uuid4()}"
    return {
        "user_key": user_key,
        "name": f"Test User {iteration}",
        "policy_id": "TH-HMO-GOLD-2024",
        "coverage_type": "Gold HMO"
    }


def pre_generate_distributions(specs: dict, iterations: int) -> dict:
    """Pre-generate numpy normal distributions for all metrics."""
    distributions = {}
    
    for variation_name, variation_specs in specs.items():
        distributions[variation_name] = {
            # Continuous metrics use normal distribution
            "accuracy": np.random.normal(
                variation_specs["accuracy"]["center"],
                variation_specs["accuracy"]["spread"],
                iterations
            ),
            "duration": np.random.normal(
                variation_specs["duration"]["center"],
                variation_specs["duration"]["spread"],
                iterations
            ).astype(int),
            "cost": np.random.normal(
                variation_specs["cost"]["center"],
                variation_specs["cost"]["spread"],
                iterations
            ),
            # Binary metrics: generate random values and compare to rate
            "resolution": np.random.random(iterations) < variation_specs["resolution_rate"],
            "negative_feedback": np.random.random(iterations) < variation_specs["negative_feedback_rate"],
        }
        
        # Clamp accuracy to [0, 1] range
        distributions[variation_name]["accuracy"] = np.clip(
            distributions[variation_name]["accuracy"], 0.0, 1.0
        )
        
        # Ensure duration is positive
        distributions[variation_name]["duration"] = np.maximum(
            distributions[variation_name]["duration"], 100
        )
        
        # Ensure cost is positive
        distributions[variation_name]["cost"] = np.maximum(
            distributions[variation_name]["cost"], 0.01
        )
    
    return distributions


def send_metrics_for_variation(
    variation_name: str,
    iteration_idx: int,
    distributions: dict,
    user_context: dict,
    ld_client: any
) -> dict:
    """Send all metrics for a specific variation and iteration."""
    
    # Get pre-generated values for this iteration
    accuracy = float(distributions[variation_name]["accuracy"][iteration_idx])
    duration = int(distributions[variation_name]["duration"][iteration_idx])
    cost = float(distributions[variation_name]["cost"][iteration_idx])
    resolution = bool(distributions[variation_name]["resolution"][iteration_idx])
    negative_feedback = bool(distributions[variation_name]["negative_feedback"][iteration_idx])
    
    # Build LaunchDarkly context
    context_builder = Context.builder(user_context["user_key"])
    context_builder.kind("user")
    context_builder.set("policy_id", user_context.get("policy_id", ""))
    context_builder.set("coverage_type", user_context.get("coverage_type", ""))
    ld_context = context_builder.build()
    
    try:
        # Call variation() to generate exposure event
        variation_detail = ld_client.variation_detail(CONFIG_KEY, ld_context, "llama-4-simple-prompt")
        actual_variation = variation_detail.value
        
        # Track accuracy (hallucinations metric)
        ld_client.track(
            event_name="$ld:ai:hallucinations",
            context=ld_context,
            metric_value=accuracy
        )
        
        # Track duration
        ld_client.track(
            event_name="$ld:ai:duration:total",
            context=ld_context,
            metric_value=float(duration)
        )
        
        # Track cost (in cents)
        ld_client.track(
            event_name="$ld:ai:tokens:costmanual",
            context=ld_context,
            metric_value=cost
        )
        
        # Track resolution (binary: 0.0 or 1.0)
        ld_client.track(
            event_name="$ld:customer:resolution",
            context=ld_context,
            metric_value=1.0 if resolution else 0.0
        )
        
        # Track negative feedback (only send if true)
        if negative_feedback:
            ld_client.track(
                event_name="$ld:ai:feedback:user:negative",
                context=ld_context,
                metric_value=1.0
            )
        
        # Flush after every metric set
        ld_client.flush()
        
        return {
            "success": True,
            "variation": actual_variation,
            "accuracy": accuracy,
            "duration": duration,
            "cost": cost,
            "resolution": resolution,
            "negative_feedback": negative_feedback,
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """Run the simulation."""
    print(f"\n{'='*100}")
    print(f"🧪 POLICY AGENT PROMPT VARIATION EXPERIMENT SIMULATOR")
    print(f"{'='*100}")
    print(f"Config: {CONFIG_KEY}")
    print(f"Iterations: {ITERATIONS}")
    print(f"Variations: {len(PROMPT_SPECS)}")
    print()
    
    # Show expected performance characteristics
    print("Expected Performance Characteristics:")
    print()
    for variation_name, specs in PROMPT_SPECS.items():
        print(f"📋 {variation_name}:")
        print(f"   Accuracy:         {specs['accuracy']['center']:.4f} (spread: {specs['accuracy']['spread']:.2f}) [generous curve]")
        print(f"   Duration:         {specs['duration']['center']:,}ms (spread: {specs['duration']['spread']}) [narrower curve]")
        print(f"   Cost:             {specs['cost']['center']:.3f}¢ (spread: {specs['cost']['spread']:.3f})")
        print(f"   Resolution Rate:  {specs['resolution_rate']*100:.1f}% (binary 0/1)")
        print(f"   Negative FB Rate: {specs['negative_feedback_rate']*100:.2f}% (binary)")
        print()
    
    print(f"{'='*100}")
    print()
    
    # Initialize LaunchDarkly
    sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
    if not sdk_key:
        print("❌ LAUNCHDARKLY_SDK_KEY not set")
        return 1
    
    ldclient.set_config(ldclient.Config(sdk_key))
    ld_client = ldclient.get()
    
    # Wait for initialization
    if not ld_client.is_initialized():
        print("⏳ Waiting for LaunchDarkly to initialize...")
        time.sleep(2)
    
    if ld_client.is_initialized():
        print("✅ LaunchDarkly client initialized\n")
    else:
        print("⚠️  LaunchDarkly client not initialized, but continuing...\n")
    
    # Pre-generate all distributions
    print("🎲 Pre-generating distributions...")
    distributions = pre_generate_distributions(PROMPT_SPECS, ITERATIONS)
    print("✅ Distributions ready\n")
    
    # Track results
    results = {variation: {"success": 0, "failed": 0} for variation in PROMPT_SPECS.keys()}
    total_metrics_sent = 0
    start_time = time.time()
    
    # Run iterations
    for i in range(ITERATIONS):
        # Create unique user for this iteration
        user_context = create_unique_user(i + 1)
        
        # Randomly select a variation to simulate natural bucketing
        # (In reality, LaunchDarkly does this, but we simulate all variations equally)
        variation_name = random.choice(list(PROMPT_SPECS.keys()))
        
        # Send metrics for this variation
        result = send_metrics_for_variation(
            variation_name=variation_name,
            iteration_idx=i,
            distributions=distributions,
            user_context=user_context,
            ld_client=ld_client
        )
        
        if result["success"]:
            results[variation_name]["success"] += 1
            total_metrics_sent += 5  # accuracy, duration, cost, resolution, negative_feedback (conditional)
            
            # Progress indicator every 20 iterations
            if (i + 1) % 20 == 0:
                print(f"✅ {i + 1:3d} | {variation_name:30s} | "
                      f"acc={result['accuracy']:.2f} | dur={result['duration']:4d}ms | "
                      f"cost={result['cost']:.3f}¢ | res={int(result['resolution'])} | "
                      f"neg={int(result['negative_feedback'])}")
        else:
            results[variation_name]["failed"] += 1
            print(f"❌ {i + 1:3d} | {variation_name:30s} | Error: {result.get('error', 'Unknown')}")
        
        # Small delay to avoid rate limiting
        time.sleep(0.05)
    
    duration_secs = time.time() - start_time
    
    # Final summary
    print(f"\n{'='*100}")
    print(f"📊 SUMMARY")
    print(f"{'='*100}")
    
    total_success = sum(r["success"] for r in results.values())
    total_failed = sum(r["failed"] for r in results.values())
    
    print(f"✅ Success: {total_success}/{ITERATIONS} ({100*total_success/ITERATIONS:.1f}%)")
    
    if total_failed > 0:
        print(f"❌ Failed: {total_failed}/{ITERATIONS}")
    
    print(f"⏱️  Duration: {duration_secs:.1f}s ({ITERATIONS/duration_secs:.1f} iterations/sec)")
    print(f"🎯 Total metrics sent: ~{total_metrics_sent}")
    print(f"{'='*100}")
    print()
    
    print("Per-variation results:")
    for variation_name, result in results.items():
        print(f"  {variation_name:30s}: {result['success']} success, {result['failed']} failed")
    print()
    
    # Final flush
    print("🔄 Final flush to LaunchDarkly...")
    ld_client.flush()
    print("   ⏳ Waiting 10 seconds for all events to be sent...")
    time.sleep(10)
    print("   ✅ Done!")
    print()
    print("   ⚠️  Note: LaunchDarkly may take 3-5 minutes to process all events.")
    print("   ⚠️  Check your experiment dashboard and refresh if needed.")
    print()
    
    # Show what to expect
    print("📈 Metrics sent:")
    print("   - $ld:ai:hallucinations (accuracy: 0.0-1.0)")
    print("   - $ld:ai:duration:total (duration in ms)")
    print("   - $ld:ai:tokens:costmanual (cost in cents)")
    print("   - $ld:customer:resolution (binary: 0.0 or 1.0)")
    print("   - $ld:ai:feedback:user:negative (binary, only when true)")
    print()
    
    print("🏆 Expected Winners:")
    print("   - BEST Accuracy: llama-4-concise-prompt (0.9593)")
    print("   - FASTEST: llama-4-concise-prompt (3,452ms)")
    print("   - CHEAPEST: llama-4-simple-prompt (0.134¢)")
    print("   - BEST Resolution: llama-4-concise-prompt (84%)")
    print("   - LOWEST Negative Feedback: llama-4-concise-prompt (2.1%)")
    print()
    print("📊 Overall Winner: llama-4-concise-prompt (best on 4/5 metrics!)")
    print()
    
    ld_client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

