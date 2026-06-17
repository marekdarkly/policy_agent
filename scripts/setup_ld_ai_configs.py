#!/usr/bin/env python3
"""
Create the AI Configs this project needs in a LaunchDarkly project.

Reads the canonical definitions from ``scripts/ld_ai_configs/*.json`` and
creates each AI Config (plus its default variation) via the LaunchDarkly
REST API. A freshly-created AI Config is enabled with its first variation
served by default, so no extra targeting step is required.

The seven configs created:
  triage_agent        (agent)      - classify + route the query
  policy_agent        (agent)      - RAG over the policy KB (custom.awskbid)
  provider_agent      (agent)      - RAG over the provider KB (custom.awskbid)
  scheduler_agent     (agent)      - schedule callbacks
  brand_agent         (completion) - rewrite in brand voice
  ai-judge-accuracy   (agent)      - G-Eval accuracy judge
  ai-judge-coherence  (agent)      - G-Eval coherence judge

Usage:
  python scripts/setup_ld_ai_configs.py              # create into LAUNCHDARKLY_PROJECT_KEY
  python scripts/setup_ld_ai_configs.py --dry-run    # print what would happen
  python scripts/setup_ld_ai_configs.py --project my-proj
  LD_SETUP_MODEL=us.anthropic.claude-haiku-4-5-20251001-v1:0 \
      python scripts/setup_ld_ai_configs.py          # force one model for every config

Env vars (loaded from .env):
  LAUNCHDARKLY_ACCESS_TOKEN   API token with writeProject scope (api-...)
  LAUNCHDARKLY_PROJECT_KEY    target project key
  LD_SETUP_MODEL              optional: override every config's model id
"""

import argparse
import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

LD_API_KEY = (
    os.getenv("LAUNCHDARKLY_ACCESS_TOKEN")
    or os.getenv("LAUNCHDARKLY_API_KEY")
    or os.getenv("LD_API_KEY")
)
LD_PROJECT_KEY = os.getenv("LAUNCHDARKLY_PROJECT_KEY")
LD_BASE_URL = "https://app.launchdarkly.com/api/v2"
LD_API_VERSION = "beta"
MODEL_OVERRIDE = os.getenv("LD_SETUP_MODEL")

CONFIG_DIR = Path(__file__).parent / "ld_ai_configs"
# Created in this order so dependencies read naturally in the LD UI.
CONFIG_ORDER = [
    "triage_agent",
    "policy_agent",
    "provider_agent",
    "scheduler_agent",
    "brand_agent",
    "ai-judge-accuracy",
    "ai-judge-coherence",
]

GREEN, RED, YELLOW, BLUE, GREY, RESET = (
    "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[90m", "\033[0m",
)


def headers() -> dict:
    return {
        "Authorization": LD_API_KEY,
        "LD-API-Version": LD_API_VERSION,
        "Content-Type": "application/json",
    }


def validate() -> None:
    if not LD_API_KEY:
        print(f"{RED}❌ LAUNCHDARKLY_ACCESS_TOKEN not set (need an api-... token "
              f"with writeProject scope).{RESET}")
        sys.exit(1)
    if not LD_PROJECT_KEY:
        print(f"{RED}❌ LAUNCHDARKLY_PROJECT_KEY not set.{RESET}")
        sys.exit(1)
    print(f"{GREEN}✅ Token {LD_API_KEY[:8]}…{LD_API_KEY[-4:]}  →  project "
          f"{BLUE}{LD_PROJECT_KEY}{RESET}")
    if MODEL_OVERRIDE:
        print(f"{YELLOW}   Model override: every config will use {MODEL_OVERRIDE}{RESET}")


def load_definitions() -> list[dict]:
    defs = []
    for key in CONFIG_ORDER:
        path = CONFIG_DIR / f"{key}.json"
        if not path.exists():
            print(f"{RED}❌ Missing definition: {path}{RESET}")
            sys.exit(1)
        defs.append(json.loads(path.read_text()))
    return defs


def config_exists(project: str, key: str) -> bool:
    r = requests.get(f"{LD_BASE_URL}/projects/{project}/ai-configs/{key}",
                     headers=headers(), timeout=30)
    return r.status_code == 200


def create_config(project: str, d: dict) -> bool:
    body = {
        "key": d["key"],
        "name": d["name"],
        "mode": d["mode"],
        "description": d.get("description", ""),
        "tags": d.get("tags", []),
    }
    r = requests.post(f"{LD_BASE_URL}/projects/{project}/ai-configs",
                      headers=headers(), json=body, timeout=30)
    if r.status_code in (200, 201):
        return True
    print(f"{RED}   ✗ create config failed ({r.status_code}): {r.text[:200]}{RESET}")
    return False


def create_variation(project: str, d: dict) -> bool:
    v = d["variation"]
    model = {
        "modelName": MODEL_OVERRIDE or v.get("modelName", ""),
        "parameters": v.get("parameters", {}),
        "custom": v.get("custom", {}),
    }
    body = {"key": v.get("key", "default"), "name": v.get("name", "Default"), "model": model}
    if "messages" in v:
        body["messages"] = v["messages"]
    else:
        body["instructions"] = v.get("instructions", "")
    r = requests.post(
        f"{LD_BASE_URL}/projects/{project}/ai-configs/{d['key']}/variations",
        headers=headers(), json=body, timeout=30,
    )
    if r.status_code in (200, 201):
        return True
    print(f"{RED}   ✗ create variation failed ({r.status_code}): {r.text[:200]}{RESET}")
    return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Create policy_agent AI Configs in LaunchDarkly.")
    parser.add_argument("--project", help="Target project key (overrides LAUNCHDARKLY_PROJECT_KEY)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without calling the API")
    args = parser.parse_args()

    global LD_PROJECT_KEY
    if args.project:
        LD_PROJECT_KEY = args.project

    validate()
    defs = load_definitions()
    project = LD_PROJECT_KEY

    print(f"\n{BLUE}Creating {len(defs)} AI Configs in '{project}'…{RESET}\n")
    created = skipped = failed = 0

    for d in defs:
        key, mode = d["key"], d["mode"]
        model = MODEL_OVERRIDE or d["variation"].get("modelName", "")
        kb = d["variation"].get("custom", {}).get("awskbid")
        label = f"{key:20} {GREY}{mode:11} {model}{(' kb='+kb) if kb else ''}{RESET}"

        if args.dry_run:
            print(f"  {YELLOW}would create{RESET}  {label}")
            continue

        if config_exists(project, key):
            print(f"  {YELLOW}skip (exists){RESET} {label}")
            skipped += 1
            continue

        if create_config(project, d) and create_variation(project, d):
            print(f"  {GREEN}created{RESET}       {label}")
            created += 1
        else:
            failed += 1

    if not args.dry_run:
        print(f"\n{GREEN}Done.{RESET} created={created} skipped={skipped} failed={failed}")
        if failed:
            sys.exit(1)
        print(f"{BLUE}Next:{RESET} confirm the policy/provider KB IDs (custom.awskbid) match "
              f"your Bedrock Knowledge Bases, then run {BLUE}make togglebank{RESET}.")


if __name__ == "__main__":
    main()
