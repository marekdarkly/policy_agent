#!/usr/bin/env python3
"""
GUARDED RELEASE ACCURACY SIMULATOR
===================================

Simulates traffic for a guarded release demo with accuracy-based rollback.

Usage:
    python guarded_release_accuracy_simulator.py

How it works:
    1. Evaluates policy_agent AI Config for each user
    2. Tracks $ld:ai:hallucinations metric based on served variation
    3. Control (concise): High accuracy ~0.92-0.98 (good)
    4. Treatment (bad): Low accuracy ~0.30-0.60 (fails, will trigger rollback)
    5. Runs until stopped (Ctrl+C)

Demo Timeline:
    - 0-60s: Control gets most traffic (high accuracy)
    - 60-120s: Treatment ramps up (accuracy drops)
    - 120-180s: Rollback triggers (returns to control)
"""

import argparse
import ldclient
from ldclient import Context
from ldclient.config import Config
import os
import random
import sys
import time
from datetime import datetime
import uuid

# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_KEY = "policy_agent"
CONTROL_VARIATION = "llama-4-concise-prompt"       # Good, accurate
TREATMENT_VARIATION = "llama-4-bad-hallucinating-prompt"  # Bad, hallucinates
ACCURACY_METRIC = "$ld:ai:hallucinations"

# Performance characteristics for each variation
CONTROL_ACCURACY_RANGE = (0.92, 0.98)      # 92-98% pass rate (good!)
TREATMENT_ACCURACY_RANGE = (0.30, 0.60)    # 30-60% pass rate (terrible!)

EVALUATIONS_PER_SECOND = 10  # How fast to generate traffic
STATS_INTERVAL = 30          # Print stats every 30 seconds


# =============================================================================
# USER CONTEXT CREATION
# =============================================================================

def create_user_context() -> Context:
    """Create a unique user context for each evaluation."""
    user_key = f"gr-demo-user-{uuid.uuid4()}"
    
    context_builder = Context.builder(user_key)
    context_builder.kind("user")
    context_builder.set("policy_id", "TH-HMO-GOLD-2024")
    context_builder.set("coverage_type", random.choice(["Gold HMO", "Silver PPO", "Platinum HMO"]))
    
    return context_builder.build()


# =============================================================================
# STATS TRACKING
# =============================================================================

class StatsTracker:
    """Track statistics for control and treatment variations."""
    
    def __init__(self):
        self.control_count = 0
        self.control_accuracy_sum = 0.0
        self.treatment_count = 0
        self.treatment_accuracy_sum = 0.0
        self.last_print_time = time.time()
        self.total_evaluations = 0
    
    def record(self, variation: str, accuracy: float):
        """Record an accuracy value for a variation."""
        self.total_evaluations += 1
        
        if variation == CONTROL_VARIATION or "concise" in variation.lower():
            self.control_count += 1
            self.control_accuracy_sum += accuracy
        elif variation == TREATMENT_VARIATION or "bad" in variation.lower() or "hallucinating" in variation.lower():
            self.treatment_count += 1
            self.treatment_accuracy_sum += accuracy
    
    def should_print(self) -> bool:
        """Check if it's time to print stats."""
        return (time.time() - self.last_print_time) >= STATS_INTERVAL
    
    def print_stats(self):
        """Print current statistics."""
        print(f"\n{'='*80}")
        print(f"📊 STATS UPDATE - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*80}")
        
        if self.control_count > 0:
            control_avg = self.control_accuracy_sum / self.control_count
            control_status = "✅" if control_avg >= 0.95 else "⚠️"
            print(f"Control   ({CONTROL_VARIATION}):")
            print(f"  {control_status} Avg Accuracy: {control_avg:.3f} ({self.control_count} evals)")
        else:
            print(f"Control   ({CONTROL_VARIATION}): No data yet")
        
        if self.treatment_count > 0:
            treatment_avg = self.treatment_accuracy_sum / self.treatment_count
            treatment_status = "✅" if treatment_avg >= 0.95 else "🚨"
            print(f"Treatment ({TREATMENT_VARIATION}):")
            print(f"  {treatment_status} Avg Accuracy: {treatment_avg:.3f} ({self.treatment_count} evals)")
            if treatment_avg < 0.95:
                print(f"  ⚠️  BELOW THRESHOLD! Rollback should trigger soon...")
        else:
            print(f"Treatment ({TREATMENT_VARIATION}): No data yet")
        
        print(f"\nTotal Evaluations: {self.total_evaluations}")
        print(f"{'='*80}\n")
        
        self.last_print_time = time.time()


# =============================================================================
# MAIN SIMULATION
# =============================================================================

def run_simulation(sdk_key: str):
    """Run the guarded release simulation."""
    
    print("\n" + "="*80)
    print("🚀 GUARDED RELEASE ACCURACY SIMULATOR")
    print("="*80)
    print(f"Config:     {CONFIG_KEY}")
    print(f"Control:    {CONTROL_VARIATION} (high accuracy ✅)")
    print(f"Treatment:  {TREATMENT_VARIATION} (low accuracy ❌)")
    print(f"Metric:     {ACCURACY_METRIC}")
    print(f"Speed:      {EVALUATIONS_PER_SECOND} evaluations/second")
    print("="*80)
    print("\n⏳ Initializing LaunchDarkly client...")
    
    # Initialize LD client
    config = Config(
        sdk_key,
        events_max_pending=10000,
        flush_interval=1.0
    )
    ldclient.set_config(config)
    ld_client = ldclient.get()
    
    if not ld_client.is_initialized():
        print("❌ Failed to initialize LaunchDarkly client")
        return 1
    
    print("✅ LaunchDarkly client initialized")
    print("\n🎬 Starting simulation... (Press Ctrl+C to stop)\n")
    
    stats = StatsTracker()
    sleep_time = 1.0 / EVALUATIONS_PER_SECOND
    
    try:
        iteration = 0
        while True:
            iteration += 1
            
            # Create user context
            context = create_user_context()
            user_key = context.key
            
            # Evaluate AI Config
            variation_detail = ld_client.variation_detail(CONFIG_KEY, context, CONTROL_VARIATION)
            served_variation = variation_detail.value
            
            # Determine which variation was served
            # For AI Configs, the value is a dict with the config
            if isinstance(served_variation, dict):
                variation_key = served_variation.get("_ldMeta", {}).get("variationKey", CONTROL_VARIATION)
            else:
                variation_key = str(served_variation)
            
            # Generate accuracy based on variation
            if "bad" in variation_key.lower() or "hallucinating" in variation_key.lower():
                # Treatment: Low accuracy (will fail!)
                accuracy = random.uniform(*TREATMENT_ACCURACY_RANGE)
                status_icon = "❌"
                variation_display = "treatment"
            else:
                # Control: High accuracy (good!)
                accuracy = random.uniform(*CONTROL_ACCURACY_RANGE)
                status_icon = "✅"
                variation_display = "control  "
            
            # Track accuracy metric to LaunchDarkly
            ld_client.track(
                event_name=ACCURACY_METRIC,
                context=context,
                metric_value=accuracy
            )
            
            # Record stats
            stats.record(variation_key, accuracy)
            
            # Print every 10th evaluation
            if iteration % 10 == 0:
                pass_fail = "PASS" if accuracy >= 0.95 else "FAIL"
                print(f"{status_icon} {iteration:4d} | {variation_display} | {variation_key:35s} | accuracy: {accuracy:.3f} | {pass_fail}")
            
            # Print stats periodically
            if stats.should_print():
                stats.print_stats()
            
            # Sleep to maintain rate
            time.sleep(sleep_time)
    
    except KeyboardInterrupt:
        print("\n\n🛑 Simulation stopped by user")
        
        # Final stats
        print("\n📊 FINAL STATISTICS:")
        stats.print_stats()
        
        # Cleanup
        print("🔄 Flushing remaining events...")
        ld_client.flush()
        time.sleep(2)
        ld_client.close()
        print("✅ Cleanup complete")
        
        return 0


# =============================================================================
# COMMAND LINE INTERFACE
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Guarded Release Accuracy Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        "--sdk-key",
        type=str,
        default=os.getenv("LAUNCHDARKLY_SDK_KEY"),
        help="LaunchDarkly SDK key (or set LAUNCHDARKLY_SDK_KEY env var)"
    )
    
    parser.add_argument(
        "--speed",
        type=int,
        default=EVALUATIONS_PER_SECOND,
        help=f"Evaluations per second (default: {EVALUATIONS_PER_SECOND})"
    )
    
    args = parser.parse_args()
    
    if not args.sdk_key:
        print("❌ Error: SDK key required")
        print("   Provide via --sdk-key or LAUNCHDARKLY_SDK_KEY environment variable")
        return 1
    
    # Update speed if specified
    global EVALUATIONS_PER_SECOND
    EVALUATIONS_PER_SECOND = args.speed
    
    return run_simulation(args.sdk_key)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)

