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
    "sonnet-4-simple-prompt": {
        "accuracy": {"center": 0.8973, "spread": 0.04},    # Sonnet accuracy from experiment
        "duration": {"center": 4300, "spread": 400},       # Sonnet duration from experiment
        "cost": {"center": 4.1731, "spread": 1.2},         # Cost in cents (4.17 cents)
        "resolution_rate": 0.68,                           # 68% resolution rate
        "negative_feedback_rate": 0.068,                   # 6.8% negative feedback rate
    },
    "llama-4-simple-prompt": {
        "accuracy": {"center": 0.9223, "spread": 0.03},    # Llama accuracy from experiment - WINNER
        "duration": {"center": 3359, "spread": 320},       # Llama duration from experiment - WINNER
        "cost": {"center": 3.1844, "spread": 0.9},         # Cost in cents (3.18 cents) - WINNER
        "resolution_rate": 0.68,                           # 68% resolution rate
        "negative_feedback_rate": 0.068,                   # 6.8% negative feedback rate
    },
    "haiku-4-5-simple-prompt": {
        "accuracy": {"center": 0.8225, "spread": 0.055},   # Haiku accuracy from experiment
        "duration": {"center": 3566, "spread": 350},       # Haiku duration from experiment
        "cost": {"center": 3.9739, "spread": 1.0},         # Cost in cents (3.97 cents)
        "resolution_rate": 0.68,                           # 68% resolution rate
        "negative_feedback_rate": 0.068,                   # 6.8% negative feedback rate
    },
}


def create_unique_user(iteration: int) -> dict:
    """Create a completely unique user for each iteration."""
    # Generate unique UUID for each user
    import uuid
    user_uuid = str(uuid.uuid4())
    user_key = f"policy-prompt-test-{user_uuid}"
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
    iteration_idx: int,
    distributions: dict,
    user_context: dict,
    ld_client: any
) -> dict:
    """Send all metrics for the variation served by LaunchDarkly."""
    
    # Build LaunchDarkly context
    context_builder = Context.builder(user_context["user_key"])
    context_builder.kind("user")
    context_builder.set("policy_id", user_context.get("policy_id", ""))
    context_builder.set("coverage_type", user_context.get("coverage_type", ""))
    ld_context = context_builder.build()
    
    try:
        # Call variation_detail() to get what variation LD serves and generate exposure event
        variation_detail = ld_client.variation_detail(CONFIG_KEY, ld_context, "llama-4-simple-prompt")
        
        # For AI Configs, the value is a dict with model config
        # Extract the variation key from the _ldMeta field
        actual_variation_key = None
        if isinstance(variation_detail.value, dict):
            actual_variation_key = variation_detail.value.get("_ldMeta", {}).get("variationKey")
        
        if not actual_variation_key or actual_variation_key not in distributions:
            return {
                "success": False,
                "error": f"Unknown variation from LD: {actual_variation_key}"
            }
        
        # Get pre-generated values for this iteration using the LD-served variation
        accuracy = float(distributions[actual_variation_key]["accuracy"][iteration_idx])
        duration = int(distributions[actual_variation_key]["duration"][iteration_idx])
        cost = float(distributions[actual_variation_key]["cost"][iteration_idx])
        resolution = bool(distributions[actual_variation_key]["resolution"][iteration_idx])
        negative_feedback = bool(distributions[actual_variation_key]["negative_feedback"][iteration_idx])
        
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
        
        return {
            "success": True,
            "variation": actual_variation_key,
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
        duration_pct = (specs['duration']['spread'] / specs['duration']['center'] * 100)
        print(f"   Duration:         {specs['duration']['center']:,}ms (spread: {specs['duration']['spread']}, {duration_pct:.1f}%)")
        print(f"   Cost:             {specs['cost']['center']:.2f}¢ (spread: {specs['cost']['spread']:.3f})")
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
        
        # Send metrics - LaunchDarkly will determine which variation to serve
        result = send_metrics_for_variation(
            iteration_idx=i,
            distributions=distributions,
            user_context=user_context,
            ld_client=ld_client
        )
        
        if result["success"]:
            variation_name = result["variation"]  # Use the variation LD actually served
            results[variation_name]["success"] += 1
            total_metrics_sent += 5  # accuracy, duration, cost, resolution, negative_feedback (conditional)
            
            # Progress indicator every 20 iterations
            if (i + 1) % 20 == 0:
                print(f"✅ {i + 1:3d} | {variation_name:30s} | "
                      f"acc={result['accuracy']:.2f} | dur={result['duration']:4d}ms | "
                      f"cost={result['cost']:.3f}¢ | res={int(result['resolution'])} | "
                      f"neg={int(result['negative_feedback'])}")
                # Flush every 20 events and wait
                print(f"   🔄 Flushing batch...")
                ld_client.flush()
                time.sleep(2)  # Wait for batch to send
        else:
            # Error occurred - try to get variation if available
            error_variation = result.get("variation", "unknown")
            if error_variation in results:
                results[error_variation]["failed"] += 1
            print(f"❌ {i + 1:3d} | Error: {result.get('error', 'Unknown')}")
    
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
    print("   ⏳ Waiting for events to send...")
    time.sleep(5)  # Give SDK time to transmit batched events
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
    print("   - BEST Accuracy: llama-4-concise-prompt (0.95)")
    print("   - FASTEST: llama-4-concise-prompt (1,852ms) ← DRAMATICALLY FASTER")
    print("   - CHEAPEST: llama-4-concise-prompt (0.14¢)")
    print("   - BEST Resolution: llama-4-concise-prompt & reasoning (84%)")
    print("   - LOWEST Negative Feedback: llama-4-concise-prompt (0.1%)")
    print()
    print("📊 Overall Winner: llama-4-concise-prompt (dominates all 5 metrics!)")
    print()
    
    ld_client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

