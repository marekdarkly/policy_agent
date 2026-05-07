#!/usr/bin/env python3
"""
SETUP HELPER for the Brand Agent Guarded Rollback demo.

Idempotently primes LaunchDarkly so the companion simulator
(`brand_agent_guarded_rollout_simulator.py`) drives a Sonnet -> Haiku
guarded rollout to auto-rollback on accuracy.

What this does:
    1. Patches segment `insurancebot-enterprise-customers` to add a single
       targeting rule clause (`customer_tier in ["enterprise"]`) so the
       simulator's synthetic users are routed through the guarded rule.
    2. Attempts to create a guarded rollout via the LaunchDarkly REST API
       (release-pipelines beta endpoint). This is best-effort: if the
       endpoint is not enabled for this account/project, it falls through.
    3. Prints precise UI fallback instructions for the operator regardless
       of API outcome (with rule/variation/metric IDs and a deep link).

Cleanup:
    --cleanup    Removes the added segment rule and (if the API path
                 succeeded) attempts to stop the rollout.

Usage:
    python simulations/setup_brand_guarded_rollout.py
    python simulations/setup_brand_guarded_rollout.py --cleanup
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any
from urllib.parse import urlencode

import urllib.request
import urllib.error

from dotenv import load_dotenv


# =============================================================================
# CONFIGURATION
# =============================================================================

LD_API_BASE = "https://app.launchdarkly.com/api/v2"
DEFAULT_ENV = "production"
SEGMENT_KEY = "insurancebot-enterprise-customers"
FLAG_KEY = "brand_agent"
RULE_DESCRIPTION = "Enterprise Segment"

# Rule clause we add to the segment to match simulator-generated users.
CLAUSE_ATTRIBUTE = "customer_tier"
CLAUSE_OP = "in"
CLAUSE_VALUES = ["enterprise"]
CLAUSE_CONTEXT_KIND = "user"

# Guarded rollout settings (used both for the API attempt and the UI fallback).
CONTROL_VARIATION_KEY = "sonnet-4-simple-prompt"
TREATMENT_VARIATION_KEY = "nova-pro-simple-prompt"
ROLLOUT_METRIC_KEY = "accuracy"
ROLLOUT_RANDOMIZATION_UNIT = "user"
ROLLOUT_MONITORING_WINDOW_MS = 5 * 60 * 1000   # 5 minutes
ROLLOUT_TARGET_WEIGHT = 100                     # ramp to 100% of the rule's audience


# =============================================================================
# HTTP HELPERS
# =============================================================================

def _request(method: str, path: str, token: str, *, body: Any = None,
             content_type: str = "application/json",
             beta: bool = False) -> tuple[int, dict | str]:
    url = f"{LD_API_BASE}{path}"
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", token)
    req.add_header("Content-Type", content_type)
    if beta:
        req.add_header("LD-API-Version", "beta")
    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                return resp.status, raw
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, raw


def _get(path: str, token: str) -> tuple[int, dict | str]:
    return _request("GET", path, token)


def _patch(path: str, token: str, body: Any, *, semantic: bool = False) -> tuple[int, dict | str]:
    ct = "application/json; domain-model=launchdarkly.semanticpatch" if semantic else "application/json"
    return _request("PATCH", path, token, body=body, content_type=ct)


def _put(path: str, token: str, body: Any, *, beta: bool = False) -> tuple[int, dict | str]:
    return _request("PUT", path, token, body=body, beta=beta)


# =============================================================================
# SEGMENT RULE MANAGEMENT
# =============================================================================

def _matches_seeded_clause(clause: dict) -> bool:
    return (
        clause.get("attribute") == CLAUSE_ATTRIBUTE
        and clause.get("op") == CLAUSE_OP
        and CLAUSE_VALUES[0] in (clause.get("values") or [])
    )


def find_seeded_rule_id(segment: dict) -> str | None:
    """Returns the rule _id of an existing seeded rule, or None."""
    for rule in segment.get("rules", []):
        clauses = rule.get("clauses", []) or []
        # Single-clause rule we own: exactly one clause that matches our seed.
        if len(clauses) == 1 and _matches_seeded_clause(clauses[0]):
            return rule.get("_id")
    return None


def ensure_segment_rule(project: str, env: str, token: str) -> str:
    """Ensure the segment has a rule that matches `customer_tier=enterprise`.

    Returns "exists" or "added".
    """
    path = f"/segments/{project}/{env}/{SEGMENT_KEY}"
    status, segment = _get(path, token)
    if status != 200 or not isinstance(segment, dict):
        raise RuntimeError(f"Could not fetch segment {SEGMENT_KEY}: {status} {segment}")

    if find_seeded_rule_id(segment) is not None:
        print(f"  segment '{SEGMENT_KEY}': seeded rule already present, skipping")
        return "exists"

    body = [
        {
            "op": "add",
            "path": "/rules/-",
            "value": {
                "clauses": [
                    {
                        "attribute": CLAUSE_ATTRIBUTE,
                        "op": CLAUSE_OP,
                        "values": CLAUSE_VALUES,
                        "negate": False,
                        "contextKind": CLAUSE_CONTEXT_KIND,
                    }
                ],
            },
        }
    ]
    status, resp = _patch(path, token, body)
    if status >= 300:
        raise RuntimeError(f"Failed to add segment rule (HTTP {status}): {resp}")
    print(f"  segment '{SEGMENT_KEY}': added rule customer_tier in [\"enterprise\"]")
    return "added"


def remove_segment_rule(project: str, env: str, token: str) -> str:
    path = f"/segments/{project}/{env}/{SEGMENT_KEY}"
    status, segment = _get(path, token)
    if status != 200 or not isinstance(segment, dict):
        raise RuntimeError(f"Could not fetch segment {SEGMENT_KEY}: {status} {segment}")

    rule_id = find_seeded_rule_id(segment)
    if rule_id is None:
        print(f"  segment '{SEGMENT_KEY}': no seeded rule found, nothing to remove")
        return "absent"

    # Find the index of the rule we own (JSON Patch needs an index).
    rule_index = None
    for idx, rule in enumerate(segment.get("rules", [])):
        if rule.get("_id") == rule_id:
            rule_index = idx
            break
    if rule_index is None:
        print(f"  segment '{SEGMENT_KEY}': could not locate seeded rule index, skipping")
        return "absent"

    body = [{"op": "remove", "path": f"/rules/{rule_index}"}]
    status, resp = _patch(path, token, body)
    if status >= 300:
        raise RuntimeError(f"Failed to remove segment rule (HTTP {status}): {resp}")
    print(f"  segment '{SEGMENT_KEY}': removed seeded rule")
    return "removed"


# =============================================================================
# FLAG INTROSPECTION
# =============================================================================

def fetch_flag_summary(project: str, env: str, token: str) -> dict:
    """Returns a dict with rule_id, control_variation_id, treatment_variation_id,
    plus links for the UI fallback message.
    """
    qs = urlencode({"env": env})
    status, flag = _get(f"/flags/{project}/{FLAG_KEY}?{qs}", token)
    if status != 200 or not isinstance(flag, dict):
        raise RuntimeError(f"Could not fetch flag {FLAG_KEY}: {status} {flag}")

    variations = flag.get("variations", [])
    control_id = treatment_id = None
    control_index = treatment_index = None
    for idx, v in enumerate(variations):
        meta = (v.get("value") or {}).get("_ldMeta") or {}
        key = meta.get("variationKey")
        if key == CONTROL_VARIATION_KEY:
            control_id = v.get("_id")
            control_index = idx
        elif key == TREATMENT_VARIATION_KEY:
            treatment_id = v.get("_id")
            treatment_index = idx

    env_block = (flag.get("environments", {}) or {}).get(env, {}) or {}
    rule_id = None
    for rule in env_block.get("rules", []):
        if rule.get("description") == RULE_DESCRIPTION:
            rule_id = rule.get("_id")
            break

    return {
        "control_variation_id": control_id,
        "control_variation_index": control_index,
        "treatment_variation_id": treatment_id,
        "treatment_variation_index": treatment_index,
        "rule_id": rule_id,
        "ui_url": f"https://app.launchdarkly.com/{project}/{env}/features/{FLAG_KEY}/targeting",
    }


# =============================================================================
# GUARDED ROLLOUT (API ATTEMPT)
# =============================================================================

def attempt_api_guarded_rollout(project: str, env: str, token: str, summary: dict) -> bool:
    """Best-effort POST to the release-pipelines beta endpoint to start a guarded
    rollout for brand_agent. Returns True on success, False otherwise.
    """
    if not (summary.get("control_variation_id") and summary.get("treatment_variation_id")):
        print("  api: missing variation ids, skipping API attempt")
        return False

    body = {
        "environmentKey": env,
        "ruleId": summary["rule_id"],
        "originalVariationId": summary["control_variation_id"],
        "newVariationId": summary["treatment_variation_id"],
        "releaseGuardianConfiguration": {
            "monitoringWindowMilliseconds": ROLLOUT_MONITORING_WINDOW_MS,
            "rolloutWeight": ROLLOUT_TARGET_WEIGHT,
            "rollbackOnRegression": True,
            "randomizationUnit": ROLLOUT_RANDOMIZATION_UNIT,
        },
        "metrics": [{"key": ROLLOUT_METRIC_KEY}],
    }

    status, resp = _put(f"/projects/{project}/flags/{FLAG_KEY}/release", token, body, beta=True)
    if 200 <= status < 300:
        print(f"  api: created guarded rollout via release-pipelines beta (HTTP {status})")
        return True
    print(f"  api: release-pipelines beta endpoint did not accept the request (HTTP {status})")
    if isinstance(resp, dict) and resp.get("message"):
        print(f"        message: {resp['message']}")
    print("  api: this is expected on accounts that don't have release pipelines enabled")
    return False


def attempt_api_stop_release(project: str, token: str) -> None:
    """Best-effort: ask LD to abandon any in-flight release for brand_agent."""
    status, resp = _request("DELETE", f"/projects/{project}/flags/{FLAG_KEY}/release", token)
    if 200 <= status < 300:
        print(f"  api: abandoned in-flight release (HTTP {status})")
    else:
        print(f"  api: no release to abandon or endpoint unavailable (HTTP {status})")


# =============================================================================
# UI FALLBACK INSTRUCTIONS
# =============================================================================

def print_ui_instructions(summary: dict) -> None:
    bar = "=" * 88
    print(f"\n{bar}")
    print("UI FALLBACK: create the guarded rollout in LaunchDarkly")
    print(bar)
    print(f"  Open:  {summary['ui_url']}")
    print(f"  Edit the rule: '{RULE_DESCRIPTION}'  (matches segment '{SEGMENT_KEY}')")
    print(f"  Rule _id (for reference): {summary.get('rule_id') or '(not found)'}")
    print()
    print("  In the rule's Serve menu, choose 'Guarded rollout', then:")
    print(f"    Original variation : {CONTROL_VARIATION_KEY}    "
          f"(index {summary.get('control_variation_index')})")
    print(f"    Target variation   : {TREATMENT_VARIATION_KEY}  "
          f"(index {summary.get('treatment_variation_index')}, Haiku 3.5)")
    print(f"    Metric             : {ROLLOUT_METRIC_KEY}  (event $ld:ai:hallucinations, HigherThanBaseline)")
    print(f"    Automatic rollback : ON")
    print(f"    Randomization unit : {ROLLOUT_RANDOMIZATION_UNIT}")
    print(f"    Rollout duration   : default (or short, e.g. 30 minutes, for a faster demo)")
    print()
    print(f"  The simulator generates contexts with customer_tier=enterprise,")
    print(f"  which the seeded segment rule routes into '{RULE_DESCRIPTION}'.")
    print(bar + "\n")


# =============================================================================
# MAIN
# =============================================================================

def setup(project: str, env: str, token: str) -> int:
    print(f"Project:     {project}")
    print(f"Environment: {env}")
    print(f"Flag:        {FLAG_KEY}")
    print(f"Segment:     {SEGMENT_KEY}")
    print()

    print("[1/3] Ensuring segment rule for customer_tier=enterprise")
    try:
        ensure_segment_rule(project, env, token)
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR: {exc}", file=sys.stderr)
        return 1

    print("\n[2/3] Inspecting brand_agent flag for rule + variation IDs")
    try:
        summary = fetch_flag_summary(project, env, token)
        print(f"  rule_id:               {summary.get('rule_id')}")
        print(f"  control_variation_id:  {summary.get('control_variation_id')} "
              f"(index {summary.get('control_variation_index')}, key {CONTROL_VARIATION_KEY})")
        print(f"  treatment_variation_id:{summary.get('treatment_variation_id')} "
              f"(index {summary.get('treatment_variation_index')}, key {TREATMENT_VARIATION_KEY})")
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR: {exc}", file=sys.stderr)
        return 1

    print("\n[3/3] Attempting guarded rollout via REST API (release-pipelines beta)")
    api_ok = attempt_api_guarded_rollout(project, env, token, summary)

    if not api_ok:
        print_ui_instructions(summary)
    else:
        print("\nGuarded rollout created via API. You can monitor it on the targeting page:")
        print(f"  {summary['ui_url']}")

    print("Next: run `python simulations/brand_agent_guarded_rollout_simulator.py`")
    return 0


def cleanup(project: str, env: str, token: str) -> int:
    print(f"Cleaning up demo state in project '{project}', env '{env}'")
    print()
    print("[1/2] Removing seeded segment rule")
    try:
        remove_segment_rule(project, env, token)
    except Exception as exc:  # noqa: BLE001
        print(f"  ERROR: {exc}", file=sys.stderr)
        return 1

    print("\n[2/2] Asking LD to abandon any in-flight release for brand_agent (best-effort)")
    attempt_api_stop_release(project, token)

    print("\nNote: if you started the guarded rollout via the LD UI, stop it from the UI:")
    print(f"  https://app.launchdarkly.com/{project}/{env}/features/{FLAG_KEY}/targeting")
    return 0


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(
        description="Setup helper for the Brand Agent Guarded Rollback demo",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--project", default=os.getenv("LAUNCHDARKLY_PROJECT_KEY"),
                        help="LaunchDarkly project key (default: LAUNCHDARKLY_PROJECT_KEY env)")
    parser.add_argument("--env", default=DEFAULT_ENV,
                        help=f"LaunchDarkly environment key (default: {DEFAULT_ENV})")
    parser.add_argument("--token", default=os.getenv("LAUNCHDARKLY_ACCESS_TOKEN"),
                        help="LD API access token (default: LAUNCHDARKLY_ACCESS_TOKEN env)")
    parser.add_argument("--cleanup", action="store_true",
                        help="Reverse the changes made by this script")
    args = parser.parse_args()

    if not args.project:
        print("ERROR: project required (set LAUNCHDARKLY_PROJECT_KEY or pass --project)", file=sys.stderr)
        return 1
    if not args.token:
        print("ERROR: token required (set LAUNCHDARKLY_ACCESS_TOKEN or pass --token)", file=sys.stderr)
        return 1

    if args.cleanup:
        return cleanup(args.project, args.env, args.token)
    return setup(args.project, args.env, args.token)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"\nFATAL: {exc}", file=sys.stderr)
        sys.exit(1)
