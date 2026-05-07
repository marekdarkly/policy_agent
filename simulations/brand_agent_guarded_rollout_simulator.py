#!/usr/bin/env python3
"""
BRAND AGENT GUARDED ROLLOUT SIMULATOR (Sonnet -> Haiku, accuracy regression)
============================================================================

Drives synthetic enterprise traffic against the `brand_agent` AI Config so a
guarded rollout from `sonnet-4-simple-prompt` (control) to
`nova-pro-simple-prompt` / Haiku 3.5 (treatment) auto-rolls back on accuracy.

Cost and duration metrics improve under Haiku (as expected for a smaller model);
only the accuracy metric degrades, and it degrades on a time-decay curve so the
guarded rollout's regression detector eventually fires.

Pre-reqs (handled by `setup_brand_guarded_rollout.py`):
    1. Segment `insurancebot-enterprise-customers` matches `customer_tier=enterprise`.
    2. A guarded rollout exists on the `Enterprise Segment` rule of `brand_agent`
       with the `accuracy` metric attached and automatic rollback enabled.

Usage:
    python simulations/brand_agent_guarded_rollout_simulator.py
    python simulations/brand_agent_guarded_rollout_simulator.py --speed 10
"""

from __future__ import annotations

import argparse
import os
import random
import sys
import time
import uuid
from datetime import datetime
from typing import Any

from dotenv import load_dotenv

import ldclient
from ldclient import Context
from ldclient.config import Config


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIG_KEY = "brand_agent"

CONTROL_VARIATION = "sonnet-4-simple-prompt"           # Sonnet 4, baseline accuracy
TREATMENT_VARIATION = "nova-pro-simple-prompt"          # Haiku 3.5, regressing accuracy

# Metric event keys (must match the metrics already configured in LD)
METRIC_HALLUCINATIONS = "$ld:ai:hallucinations"        # bound to `accuracy` metric
METRIC_JUDGE_ACCURACY = "$ld:ai:judge:accuracy"        # bound to ld_autogen judge accuracy
METRIC_COST = "$ld:ai:tokens:costmanual"               # bound to `cost-manual` metric
METRIC_DURATION = "$ld:ai:duration:total"              # bound to `duration` metric
METRIC_TOKENS = "$ld:ai:tokens:total"                  # bound to ld_autogen total tokens

# Performance characteristics
CONTROL_ACCURACY_CENTER = 0.97
CONTROL_ACCURACY_SPREAD = 0.02
CONTROL_COST_CENTER = 0.30          # cents per call
CONTROL_COST_SPREAD = 0.05
CONTROL_DURATION_CENTER = 3500       # ms
CONTROL_DURATION_SPREAD = 500
CONTROL_TOKENS_CENTER = 2100
CONTROL_TOKENS_SPREAD = 250

TREATMENT_COST_CENTER = 0.06         # cents per call (~5x cheaper)
TREATMENT_COST_SPREAD = 0.015
TREATMENT_DURATION_CENTER = 1300     # ms (~2.7x faster)
TREATMENT_DURATION_SPREAD = 250
TREATMENT_TOKENS_CENTER = 1900       # haiku tends to be slightly tighter
TREATMENT_TOKENS_SPREAD = 250

# Time-decay accuracy curve for the treatment (Haiku).
# Two presets: default (~5 min decay arc, looks like a real rollout) and --fast
# (~45s decay arc, for when you just want LD's regression detector to trip ASAP).
DEFAULT_PHASES = {
    "phase_1_end_sec": 60,
    "phase_2_end_sec": 180,
    "phase_1_acc": 0.92,
    "phase_2_end_acc": 0.70,
    "phase_3_acc": 0.45,
}
FAST_PHASES = {
    "phase_1_end_sec": 15,
    "phase_2_end_sec": 45,
    "phase_1_acc": 0.85,
    "phase_2_end_acc": 0.50,
    "phase_3_acc": 0.30,
}

TREATMENT_ACC_SPREAD = 0.04

EVALUATIONS_PER_SECOND = 8
EVALUATIONS_PER_SECOND_FAST = 30
STATS_INTERVAL_SEC = 30


# =============================================================================
# CONTEXT BUILDING
# =============================================================================

_FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery",
                "Quinn", "Dakota", "Sage", "Emerson", "Hayden", "Reese", "Skyler"]
_LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
               "Miller", "Davis", "Rodriguez", "Martinez", "Anderson", "Wilson"]
_LOCATIONS = [
    ("San Francisco", "CA"), ("New York", "NY"), ("Boston", "MA"),
    ("Austin", "TX"), ("Seattle", "WA"), ("Chicago", "IL"),
    ("Denver", "CO"), ("Portland", "OR"), ("Atlanta", "GA"),
]


def build_enterprise_context() -> Context:
    """Build a unique LD user context that the segment rule
    (customer_tier=enterprise) will match.
    """
    user_key = f"brand-grr-{uuid.uuid4()}"
    name = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
    city, state = random.choice(_LOCATIONS)

    builder = Context.builder(user_key).kind("user")
    builder.set("name", name)
    builder.set("email", f"{user_key}@enterprise.example.com")

    # Attributes used by the seeded segment rule.
    builder.set("customer_tier", "enterprise")
    builder.set("customer_segment", "enterprise_member")
    builder.set("plan_tier", 5)
    builder.set("plan", "enterprise")

    # Bunch of plausible enterprise attributes so the context is realistic.
    builder.set("policy_id", "TH-ENT-PLATINUM-2024")
    builder.set("coverage_type", "Enterprise Platinum")
    builder.set("location", f"{city}, {state}")
    builder.set("city", city)
    builder.set("state", state)
    builder.set("country", "US")
    builder.set("domain", "togglehealth")
    builder.set("engagement_level", "high")
    builder.set("lifetime_value", "high")

    return builder.build()


# =============================================================================
# METRIC GENERATION
# =============================================================================

def control_accuracy() -> float:
    return _clamp(random.gauss(CONTROL_ACCURACY_CENTER, CONTROL_ACCURACY_SPREAD), 0.0, 1.0)


def treatment_accuracy(elapsed_seconds: float, phases: dict) -> float:
    """Time-decay accuracy curve for the haiku variation."""
    p1_end = phases["phase_1_end_sec"]
    p2_end = phases["phase_2_end_sec"]
    if elapsed_seconds < p1_end:
        center = phases["phase_1_acc"]
    elif elapsed_seconds < p2_end:
        progress = (elapsed_seconds - p1_end) / (p2_end - p1_end)
        center = phases["phase_1_acc"] + (phases["phase_2_end_acc"] - phases["phase_1_acc"]) * progress
    else:
        center = phases["phase_3_acc"]
    return _clamp(random.gauss(center, TREATMENT_ACC_SPREAD), 0.0, 1.0)


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def is_treatment(variation_key: str) -> bool:
    return TREATMENT_VARIATION in variation_key or "haiku" in variation_key.lower()


def is_control(variation_key: str) -> bool:
    return CONTROL_VARIATION in variation_key or "sonnet" in variation_key.lower()


# =============================================================================
# STATS TRACKING
# =============================================================================

class StatsTracker:
    def __init__(self):
        self.counts: dict[str, int] = {}
        self.acc_sums: dict[str, float] = {}
        self.cost_sums: dict[str, float] = {}
        self.dur_sums: dict[str, float] = {}
        self.last_print = time.time()
        self.total = 0

    def record(self, variation_key: str, accuracy: float, cost: float, duration: float) -> None:
        self.total += 1
        self.counts[variation_key] = self.counts.get(variation_key, 0) + 1
        self.acc_sums[variation_key] = self.acc_sums.get(variation_key, 0.0) + accuracy
        self.cost_sums[variation_key] = self.cost_sums.get(variation_key, 0.0) + cost
        self.dur_sums[variation_key] = self.dur_sums.get(variation_key, 0.0) + duration

    def should_print(self) -> bool:
        return (time.time() - self.last_print) >= STATS_INTERVAL_SEC

    def print_stats(self, elapsed_sec: float) -> None:
        bar = "=" * 88
        print(f"\n{bar}")
        print(f"STATS @ {datetime.now().strftime('%H:%M:%S')} | elapsed {elapsed_sec:6.1f}s | total {self.total}")
        print(bar)
        for variation_key in sorted(self.counts.keys()):
            n = self.counts[variation_key]
            avg_acc = self.acc_sums[variation_key] / n
            avg_cost = self.cost_sums[variation_key] / n
            avg_dur = self.dur_sums[variation_key] / n
            role = "control  " if is_control(variation_key) else (
                   "treatment" if is_treatment(variation_key) else "other    ")
            warn = ""
            if is_treatment(variation_key) and avg_acc < 0.85:
                warn = "  <- below 0.85, regression detector should be tripping"
            print(f"  {role} {variation_key:35s} n={n:5d}  acc={avg_acc:.3f}  cost={avg_cost:.3f}c  dur={avg_dur:6.0f}ms{warn}")
        print(bar + "\n")
        self.last_print = time.time()


# =============================================================================
# MAIN LOOP
# =============================================================================

def run(sdk_key: str, speed: int, phases: dict) -> int:
    print("=" * 88)
    print("BRAND AGENT GUARDED ROLLOUT SIMULATOR")
    print("=" * 88)
    print(f"  Config:       {CONFIG_KEY}")
    print(f"  Control:      {CONTROL_VARIATION}  (Sonnet 4, ~0.97 accuracy)")
    print(f"  Treatment:    {TREATMENT_VARIATION}  (Haiku 3.5, regressing accuracy)")
    print(f"  Throughput:   {speed} evaluations/sec")
    print(f"  Regression:   accuracy {phases['phase_1_acc']:.2f} -> "
          f"{phases['phase_2_end_acc']:.2f} -> {phases['phase_3_acc']:.2f} "
          f"(phase ends @ {phases['phase_1_end_sec']}s, {phases['phase_2_end_sec']}s)")
    print(f"  Cost/latency: improve under treatment (cheaper, faster)")
    print("=" * 88)

    Config_ = Config(sdk_key, events_max_pending=10000, flush_interval=1.0)
    ldclient.set_config(Config_)
    client = ldclient.get()
    if not client.is_initialized():
        print("ERROR: LaunchDarkly client failed to initialize", file=sys.stderr)
        return 1
    print("LaunchDarkly client initialized. Streaming traffic... (Ctrl+C to stop)\n")

    stats = StatsTracker()
    sleep_time = 1.0 / max(1, speed)
    start = time.time()
    iteration = 0

    try:
        while True:
            iteration += 1
            elapsed = time.time() - start

            ctx = build_enterprise_context()

            detail = client.variation_detail(CONFIG_KEY, ctx, {})
            value: Any = detail.value
            if not isinstance(value, dict):
                if iteration % 50 == 0:
                    print(f"[{iteration:5d}] WARN: variation value is not a dict (got {type(value).__name__}) - skipping")
                time.sleep(sleep_time)
                continue

            ld_meta = value.get("_ldMeta", {}) or {}
            variation_key = ld_meta.get("variationKey") or "unknown"

            # Build attribution payload so events bin under brand_agent in Insights.
            model_obj = value.get("model") or {}
            provider_obj = value.get("provider") or {}
            attribution = {
                "configKey": CONFIG_KEY,
                "variationKey": variation_key,
                "version": int(ld_meta.get("version", 1)),
                "modelName": model_obj.get("name", ""),
                "providerName": provider_obj.get("name", ""),
            }

            # Generate metrics.
            if is_treatment(variation_key):
                accuracy = treatment_accuracy(elapsed, phases)
                cost = max(0.0, random.gauss(TREATMENT_COST_CENTER, TREATMENT_COST_SPREAD))
                duration = max(100.0, random.gauss(TREATMENT_DURATION_CENTER, TREATMENT_DURATION_SPREAD))
                tokens = max(200.0, random.gauss(TREATMENT_TOKENS_CENTER, TREATMENT_TOKENS_SPREAD))
            else:
                accuracy = control_accuracy()
                cost = max(0.0, random.gauss(CONTROL_COST_CENTER, CONTROL_COST_SPREAD))
                duration = max(100.0, random.gauss(CONTROL_DURATION_CENTER, CONTROL_DURATION_SPREAD))
                tokens = max(200.0, random.gauss(CONTROL_TOKENS_CENTER, CONTROL_TOKENS_SPREAD))

            # LaunchDarkly only accepts metric values with 2 decimal places of precision.
            cost_2dp = round(cost, 2)
            accuracy_4dp = round(accuracy, 4)

            client.track(METRIC_HALLUCINATIONS, ctx, data=attribution, metric_value=accuracy_4dp)
            client.track(METRIC_JUDGE_ACCURACY, ctx, data=attribution, metric_value=accuracy_4dp)
            client.track(METRIC_COST, ctx, data=attribution, metric_value=cost_2dp)
            client.track(METRIC_DURATION, ctx, data=attribution, metric_value=float(round(duration, 2)))
            client.track(METRIC_TOKENS, ctx, data=attribution, metric_value=float(round(tokens, 2)))

            stats.record(variation_key, accuracy, cost, duration)

            if iteration % 20 == 0:
                role = "control  " if is_control(variation_key) else (
                       "treatment" if is_treatment(variation_key) else "other    ")
                print(f"[{iteration:5d} t+{elapsed:5.0f}s] {role} {variation_key:34s} "
                      f"acc={accuracy:.3f} cost={cost:.3f}c dur={duration:5.0f}ms")

            if stats.should_print():
                stats.print_stats(elapsed)

            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopping (Ctrl+C)...")
        stats.print_stats(time.time() - start)
        print("Flushing remaining events...")
        client.flush()
        time.sleep(2)
        client.close()
        print("Done.")
        return 0


# =============================================================================
# CLI
# =============================================================================

def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Brand Agent Guarded Rollout Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--sdk-key",
        type=str,
        default=os.getenv("LAUNCHDARKLY_SDK_KEY"),
        help="LaunchDarkly SDK key (defaults to LAUNCHDARKLY_SDK_KEY env var)",
    )
    parser.add_argument(
        "--speed",
        type=int,
        default=None,
        help=f"Evaluations per second (default: {EVALUATIONS_PER_SECOND}, or "
             f"{EVALUATIONS_PER_SECOND_FAST} with --fast)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Compress the accuracy decay curve (~45s) and bump throughput so "
             "LD's regression detector trips ASAP",
    )
    args = parser.parse_args()

    if not args.sdk_key:
        print("ERROR: SDK key required. Set LAUNCHDARKLY_SDK_KEY or pass --sdk-key.", file=sys.stderr)
        return 1

    phases = FAST_PHASES if args.fast else DEFAULT_PHASES
    speed = args.speed if args.speed is not None else (
        EVALUATIONS_PER_SECOND_FAST if args.fast else EVALUATIONS_PER_SECOND
    )
    return run(args.sdk_key, speed, phases)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)
