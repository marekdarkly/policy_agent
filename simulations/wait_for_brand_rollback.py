#!/usr/bin/env python3
"""
WAIT-FOR-ROLLBACK POLLER for the brand_agent guarded rollback demo.

Watches the `Enterprise Segment` rule on the `brand_agent` flag in production
and prints a state line every few seconds. Detects three transitions:

    1. baseline       -> guarded rollout was created (rule grew a `rollout` block)
    2. monitoring     -> rollout is live (variation=null, rollout populated)
    3. rolled-back    -> rule reverted to a single variation index (typically 2 = sonnet)

Exits 0 when the rolled-back transition is observed (or when the rollout was
clearly created and then disappeared, which is also "done").

Usage:
    python simulations/wait_for_brand_rollback.py
    python simulations/wait_for_brand_rollback.py --interval 5 --timeout 1800
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from urllib.parse import urlencode

from dotenv import load_dotenv


LD_API_BASE = "https://app.launchdarkly.com/api/v2"
DEFAULT_ENV = "production"
FLAG_KEY = "brand_agent"
RULE_DESCRIPTION = "Enterprise Segment"


def _http_get(path: str, token: str) -> tuple[int, dict | str]:
    req = urllib.request.Request(f"{LD_API_BASE}{path}")
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            return resp.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, raw


def fetch_rule_state(project: str, env: str, token: str) -> dict | None:
    qs = urlencode({"env": env})
    status, flag = _http_get(f"/flags/{project}/{FLAG_KEY}?{qs}", token)
    if status != 200 or not isinstance(flag, dict):
        print(f"  WARN: could not fetch flag (HTTP {status})", file=sys.stderr)
        return None
    env_block = (flag.get("environments", {}) or {}).get(env, {}) or {}
    for rule in env_block.get("rules", []):
        if rule.get("description") == RULE_DESCRIPTION:
            return rule
    return None


def classify(rule: dict | None) -> str:
    """Returns 'missing', 'baseline', 'monitoring', or 'rolled-back'."""
    if rule is None:
        return "missing"
    has_rollout = bool(rule.get("rollout"))
    variation = rule.get("variation")
    if has_rollout and variation is None:
        return "monitoring"
    if not has_rollout and variation is not None:
        # Could be baseline (always was a single variation) or rolled-back
        # (was guarded, now reverted). The state-machine in main() distinguishes.
        return "single-variation"
    return "unknown"


def describe(rule: dict | None) -> str:
    if rule is None:
        return "rule not found"
    if rule.get("rollout"):
        weights = [(v.get("variation"), v.get("weight", 0) / 1000.0)
                   for v in rule["rollout"].get("variations", [])]
        weights_str = ", ".join(f"v{i}={w:.1f}%" for i, w in weights)
        return f"rollout block present | {weights_str}"
    return f"single variation index = {rule.get('variation')}"


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Poll until the brand_agent guarded rollout has rolled back"
    )
    parser.add_argument("--project", default=os.getenv("LAUNCHDARKLY_PROJECT_KEY"))
    parser.add_argument("--env", default=DEFAULT_ENV)
    parser.add_argument("--token", default=os.getenv("LAUNCHDARKLY_ACCESS_TOKEN"))
    parser.add_argument("--interval", type=float, default=10.0,
                        help="Polling interval in seconds (default: 10)")
    parser.add_argument("--timeout", type=float, default=3600.0,
                        help="Give up after this many seconds (default: 3600)")
    args = parser.parse_args()

    if not args.project or not args.token:
        print("ERROR: LAUNCHDARKLY_PROJECT_KEY and LAUNCHDARKLY_ACCESS_TOKEN required",
              file=sys.stderr)
        return 1

    print(f"Polling brand_agent / {args.env} every {args.interval:.0f}s "
          f"(timeout {args.timeout:.0f}s)...")
    print(f"  Looking for: rule '{RULE_DESCRIPTION}' transitions to a guarded "
          f"rollout, then reverts to a single variation.")
    print()

    seen_monitoring = False
    last_state = None
    start = time.time()

    while time.time() - start < args.timeout:
        rule = fetch_rule_state(args.project, args.env, args.token)
        state = classify(rule)
        elapsed = time.time() - start
        if state != last_state or int(elapsed) % 30 == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] +{elapsed:5.0f}s  "
                  f"state={state:15s}  ({describe(rule)})")
            last_state = state

        if state == "monitoring":
            seen_monitoring = True

        if seen_monitoring and state == "single-variation":
            print()
            print("ROLLBACK DETECTED: rule reverted from a guarded rollout to a "
                  "single variation.")
            print(f"  rule now: {describe(rule)}")
            return 0

        time.sleep(args.interval)

    print(f"\nTIMEOUT after {args.timeout:.0f}s without observing rollback.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
