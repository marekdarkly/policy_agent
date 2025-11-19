#!/usr/bin/env python3
"""
Simulate LaunchDarkly experiments for policy_agent and provider_agent
with specific posterior means and curve characteristics.

Based on numeric_experiment_runner approach:
- Pre-generate numpy normal distributions
- Fat curves = large spread (StdDev ~25% of mean)
- Tight curves = small spread (StdDev ~8% of mean)
"""

import os
import sys
import time
from uuid import uuid4
from dotenv import load_dotenv
import numpy as np
import random

load_dotenv()

# Suppress noisy logs
import logging
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("ldclient").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

# Initialize LaunchDarkly
from src.utils.observability import initialize_observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

import ldclient
from ldclient import Context

# Configuration
ITERATIONS = int(os.getenv("ITERATIONS", "200"))

# PROVIDER AGENT SPECIFICATIONS
PROVIDER_SPECS = {
    "SONNET": {
        "accuracy": {"center": 0.93, "spread": 0.07},     # Tight (8% of mean)
        "duration": {"center": 4237, "spread": 400},      # Normal
        "cost": {"center": 4.45, "spread": 1.20},         # Fat (27% of mean) - MORE EXPENSIVE
    },
    "NOVA": {
        "accuracy": {"center": 0.73, "spread": 0.20},     # Fat (27% of mean)
        "duration": {"center": 3238, "spread": 350},      # Normal
        "cost": {"center": 3.86, "spread": 0.50},         # Less flat - reduced spread
    },
    "LLAMA": {
        "accuracy": {"center": 0.89, "spread": 0.07},     # Tight (8% of mean)
        "duration": {"center": 2944, "spread": 300},      # Normal
        "cost": {"center": 2.80, "spread": 0.25},         # Tight (9% of mean)
    },
    "HAIKU": {
        "accuracy": {"center": 0.84, "spread": 0.22},     # Fat (26% of mean)
        "duration": {"center": 3312, "spread": 350},      # Normal
        "cost": {"center": 3.73, "spread": 0.25},         # Tighter - reduced spread
    },
}

# POLICY AGENT SPECIFICATIONS
POLICY_SPECS = {
    "SONNET": {
        "accuracy": {"center": 0.91, "spread": 0.07},     # Tight (8% of mean)
        "duration": {"center": 4319, "spread": 400},      # Normal
        "cost": {"center": 4.35, "spread": 0.40},         # Normal - MORE EXPENSIVE (almost as much as Nova)
    },
    "NOVA": {
        "accuracy": {"center": 0.84, "spread": 0.08},     # Tight - WORSE accuracy than Llama
        "duration": {"center": 4100, "spread": 400},      # Normal - SLOWER than Llama
        "cost": {"center": 3.50, "spread": 0.35},         # Closer to Llama
    },
    "LLAMA": {
        "accuracy": {"center": 0.92, "spread": 0.07},     # Tight (8% of mean) - BEST accuracy
        "duration": {"center": 3362, "spread": 350},      # Normal - FASTEST
        "cost": {"center": 3.19, "spread": 0.30},         # Normal - CHEAPEST
    },
    "HAIKU": {
        "accuracy": {"center": 0.83, "spread": 0.22},     # Fat (27% of mean)
        "duration": {"center": 3625, "spread": 380},      # Normal
        "cost": {"center": 3.40, "spread": 0.35},         # Closer to Llama
    },
}

def pre_generate_distributions(specs, iterations):
    """Pre-generate numpy normal distributions for all metrics."""
    distributions = {}
    
    for model, metrics in specs.items():
        distributions[model] = {}
        for metric_name, params in metrics.items():
            # Generate normal distribution
            values = np.random.default_rng().normal(
                params["center"], 
                params["spread"], 
                iterations * 2  # Extra buffer
            )
            
            # Clamp values to reasonable ranges
            if metric_name == "accuracy":
                values = np.clip(values, 0.5, 1.0)  # Accuracy between 0.5-1.0
            elif metric_name == "cost":
                values = np.maximum(values, 0.1)  # Cost minimum 0.1¢
            elif metric_name == "duration":
                values = np.maximum(values, 100)  # Duration minimum 100ms
            
            distributions[model][metric_name] = values.tolist()
    
    return distributions

# Pre-generate distributions for both agents
print(f"\n{'='*100}")
print(f"🎲 PRE-GENERATING DISTRIBUTIONS")
print(f"{'='*100}\n")

PROVIDER_DISTRIBUTIONS = pre_generate_distributions(PROVIDER_SPECS, ITERATIONS)
print("✅ Provider agent distributions generated:")
for model, specs in PROVIDER_SPECS.items():
    print(f"   {model:8s}: acc={specs['accuracy']['center']:.2f}±{specs['accuracy']['spread']:.2f}, "
          f"dur={specs['duration']['center']:,}±{specs['duration']['spread']}, "
          f"cost={specs['cost']['center']:.2f}±{specs['cost']['spread']:.2f}")

print()
POLICY_DISTRIBUTIONS = pre_generate_distributions(POLICY_SPECS, ITERATIONS)
print("✅ Policy agent distributions generated:")
for model, specs in POLICY_SPECS.items():
    print(f"   {model:8s}: acc={specs['accuracy']['center']:.2f}±{specs['accuracy']['spread']:.2f}, "
          f"dur={specs['duration']['center']:,}±{specs['duration']['spread']}, "
          f"cost={specs['cost']['center']:.2f}±{specs['cost']['spread']:.2f}")

def create_unique_user():
    """Create a unique user context."""
    return {
        "user_key": f"usr-{uuid4()}",
        "name": "Test User",
        "location": "San Francisco, CA",
        "policy_id": "TH-HMO-GOLD-2024",
        "coverage_type": "Gold HMO"
    }

def send_metrics_for_agent(agent_name: str, distributions: dict, specs: dict, iteration: int):
    """Send all metrics (accuracy, duration, cost) for an agent."""
    
    try:
        # Get AI config from LaunchDarkly
        from src.utils.launchdarkly_config import get_ld_client
        ld_client = get_ld_client()
        
        user_context = create_unique_user()
        config, tracker, ld_context = ld_client.get_ai_config(agent_name, user_context)
        
        # Call variation() to create exposure event
        raw_ld_client = ldclient.get()
        variation_result = raw_ld_client.variation(agent_name, ld_context, False)
        
        # DEBUG: Verify variation is being called
        if iteration <= 3:
            variation_key = variation_result.get("_ldMeta", {}).get("variationKey", "unknown") if isinstance(variation_result, dict) else "unknown"
            print(f"   🎯 Exposure created: {agent_name} → {variation_key} for user {user_context['user_key'][:20]}...")
        
        # Extract model info from config
        model_id = config.get("model", {}).get("name", "unknown")
        model_id_lower = model_id.lower()
        
        # Determine model type
        if "llama" in model_id_lower:
            model_type = "LLAMA"
        elif "sonnet" in model_id_lower:
            model_type = "SONNET"
        elif "haiku" in model_id_lower:
            model_type = "HAIKU"
        elif "nova" in model_id_lower:
            model_type = "NOVA"
        else:
            model_type = "SONNET"  # Default
        
        # Pick random values from pre-generated distributions
        accuracy = float(random.choice(distributions[model_type]["accuracy"]))
        duration_ms = int(random.choice(distributions[model_type]["duration"]))
        cost_cents = float(random.choice(distributions[model_type]["cost"]))
        
        # Derive total tokens from cost (reverse engineering typical pricing)
        # Typical pricing: ~$0.003 per 1K input, ~$0.015 per 1K output (60/40 split)
        # Average: ~$0.0078 per 1K tokens → ~1,282 tokens per cent
        total_tokens = int(cost_cents * 1280)
        
        # 1. Send accuracy metric ($ld:ai:hallucinations)
        raw_ld_client.track(
            event_name="$ld:ai:hallucinations",
            context=ld_context,
            metric_value=accuracy
        )
        
        # 2. Send duration metric ($ld:ai:duration:total)
        raw_ld_client.track(
            event_name="$ld:ai:duration:total",
            context=ld_context,
            metric_value=float(duration_ms)
        )
        
        # 3. Send tokens metric ($ld:ai:tokens:total)
        raw_ld_client.track(
            event_name="$ld:ai:tokens:total",
            context=ld_context,
            metric_value=float(total_tokens)
        )
        
        # 4. Send cost metric ($ld:ai:tokens:costmanual)
        raw_ld_client.track(
            event_name="$ld:ai:tokens:costmanual",
            context=ld_context,
            metric_value=cost_cents
        )
        
        # Flush immediately
        ldclient.get().flush()
        
        print(f"✅ {iteration:3d} | {agent_name:15s} | {model_type:8s} | acc={accuracy:.2f} | dur={duration_ms:5d}ms | cost={cost_cents:4.2f}¢")
        return True
        
    except Exception as e:
        print(f"❌ {iteration:3d} | {agent_name:15s} | ERROR: {str(e)[:80]}")
        return False

def main():
    """Main execution."""
    print(f"\n{'='*100}")
    print(f"🎯 EXPERIMENT SIMULATOR - PROVIDER & POLICY AGENTS")
    print(f"{'='*100}")
    print(f"📊 Iterations per agent: {ITERATIONS}")
    print(f"📈 Total metrics: {ITERATIONS * 2 * 4} (2 agents × 4 metrics × {ITERATIONS} iterations)")
    print(f"{'='*100}\n")
    
    # Wait for LaunchDarkly to initialize
    if ldclient.get().is_initialized():
        print("✅ LaunchDarkly client initialized\n")
    else:
        print("⏳ Waiting for LaunchDarkly client to initialize...")
        time.sleep(2)
    
    print(f"{'Iter':<5} | {'Agent':<15} | {'Model':<8} | {'Accuracy':<11} | {'Duration':<11} | {'Cost'}")
    print("-" * 100)
    
    success_count = 0
    start_time = time.time()
    
    for i in range(1, ITERATIONS + 1):
        # Send for provider_agent
        if send_metrics_for_agent("provider_agent", PROVIDER_DISTRIBUTIONS, PROVIDER_SPECS, i):
            success_count += 1
        
        # Send for policy_agent
        if send_metrics_for_agent("policy_agent", POLICY_DISTRIBUTIONS, POLICY_SPECS, i):
            success_count += 1
        
        # Progress indicator
        if i % 50 == 0:
            print(f"\n⏸️  Progress: {i}/{ITERATIONS} iterations ({i * 2} total metrics sent)\n")
            time.sleep(0.1)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*100}")
    print(f"📊 SUMMARY")
    print(f"{'='*100}")
    print(f"✅ Success: {success_count}/{ITERATIONS * 2} ({100.0 * success_count / (ITERATIONS * 2):.1f}%)")
    print(f"⏱️  Duration: {elapsed_time:.1f}s ({success_count / elapsed_time:.1f} metrics/sec)")
    print(f"🎯 Total metrics sent: {success_count * 4} (4 metrics per iteration)")
    print(f"{'='*100}\n")
    
    # Final flush
    print("🔄 Final flush to LaunchDarkly...")
    ldclient.get().flush()
    print("   ⏳ Waiting 10 seconds for all events to be sent...")
    time.sleep(10)
    print("   ✅ Done!")
    print("   ⚠️  Note: LaunchDarkly may take 3-5 minutes to process all events.")
    print("   ⚠️  Check your experiment dashboard and refresh if needed.\n")
    
    print("📈 Metrics sent:")
    print("   - $ld:ai:hallucinations (accuracy)")
    print("   - $ld:ai:duration:total (duration in ms)")
    print("   - $ld:ai:tokens:total (derived from cost)")
    print("   - $ld:ai:tokens:costmanual (cost in ¢)")
    print()
    print("Expected posterior means:")
    print()
    print("PROVIDER AGENT:")
    print("  Sonnet 4:  acc=0.93 (tight), dur=4,237ms, cost=4.45¢ (fat)")
    print("  Nova Pro:  acc=0.73 (fat),   dur=3,238ms, cost=3.86¢ (tighter)")
    print("  Llama 4:   acc=0.89 (tight), dur=2,944ms, cost=2.80¢ (tight)")
    print("  Haiku 4.5: acc=0.84 (fat),   dur=3,312ms, cost=3.73¢ (tighter)")
    print()
    print("POLICY AGENT (Llama WINS on accuracy + duration):")
    print("  Sonnet 4:  acc=0.91 (tight), dur=4,319ms (slowest), cost=4.35¢ (expensive) ← MOST EXPENSIVE")
    print("  Nova Pro:  acc=0.84 (tight), dur=4,100ms (slow),    cost=3.50¢ (mid)       ← WORSE than Llama")
    print("  Llama 4:   acc=0.92 (tight), dur=3,362ms (WINNER),  cost=3.19¢ (cheap)     ← BEST PERFORMER")
    print("  Haiku 4.5: acc=0.83 (fat),   dur=3,625ms,          cost=3.40¢ (mid)       ← Closer to Llama")
    print()

if __name__ == "__main__":
    main()

