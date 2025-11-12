#!/usr/bin/env python3
"""
experiment_runner_noguard.py

Alternative CLI utility that runs the same ToggleBank chat experiment **without**:
  • AWS Bedrock Guardrails
  • LLM-as-Judge factual-accuracy evaluation

It still:
  • Retrieves LaunchDarkly AI config & user context
  • Performs RAG retrieval from the knowledge base
  • Sends the question to the generator model only
  • Tracks usage & synthetic user feedback
  • Sends manual cost metric (in cents) to LaunchDarkly

Example:
    python backend/experiment_runner_noguard.py --runs 3 --delay 1
"""

import argparse
import json
import logging
import os
import random
import sys
from typing import Dict, Any, Tuple
from pathlib import Path

import dotenv
import ldclient
from ldclient.config import Config
from ldclient import Context
from ldai.client import LDAIClient, AIConfig, ModelConfig
from ldai.tracker import FeedbackKind

from script import (
    initialize_aws_clients,
    get_kb_passages,
    map_messages,
    extract_system_messages,
)
from user_service import get_current_user_context

# ── env & logging ───────────────────────────────────────────────────────────

# Load .env from project root (one level up from backend/)
project_root = Path(__file__).parent.parent
dotenv.load_dotenv(project_root / ".env")
LD_SDK = os.getenv("LAUNCHDARKLY_SDK_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Hardcoded AI config keys
AI_CONFIG_KEY = "toggle-rag"
LD_JUDGE_KEY = "llm-as-judge"

if not LD_SDK:
    sys.exit("✖  Missing LaunchDarkly env vars – check .env")

ldclient.set_config(Config(LD_SDK))
ld = ldclient.get()
ai_client = LDAIClient(ld)

bedrock, bedrock_agent = initialize_aws_clients()

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("exp_runner_noguard")

# ── Simple pricing table -----------------------------------------------------
_PRICE_MAP = {
    "sonnet-4": (0.003, 0.015),
    "claude-sonnet-4": (0.003, 0.015),
    "sonnet": (0.003, 0.015),
    "haiku": (0.0008, 0.004),
    "nova": (0.0008, 0.0002),
}

def _estimate_cost(model_id: str, inp: int, out: int) -> float:
    lid = model_id.lower()
    for key, (r_in, r_out) in _PRICE_MAP.items():
        if key in lid:
            return (inp / 1000) * r_in + (out / 1000) * r_out
    # fallback pricing
    r_in, r_out = _PRICE_MAP["sonnet-4"]
    return (inp / 1000) * r_in + (out / 1000) * r_out

# ── per-session routine ------------------------------------------------------

def run_session(question: str) -> Tuple[str, Dict[str, Any]]:
    context: Context = get_current_user_context()

    default_cfg = AIConfig(enabled=True, model=ModelConfig(name="us.anthropic.claude-3-5-sonnet-20241022-v2:0"), messages=[])

    cfg, tracker = ai_client.config(AI_CONFIG_KEY, context, default_cfg, {"userInput": question})

    # custom params
    try:
        kb_id = cfg.model.get_custom("kb_id")
    except Exception:
        kb_id = cfg.to_dict().get("model", {}).get("custom", {}).get("kb_id")
    if not kb_id:
        raise RuntimeError("kb_id missing in LD AI config")

    # RAG retrieval (same heuristics as main script)
    ctx_dict = context.to_dict()
    tier = ctx_dict.get("tier", "")
    user_name = context.name
    enhanced_q = f"{user_name} {tier} tier {question}" if any(w in question.lower() for w in ["my", "i", "me", "mine"]) else f"{tier} tier {question}"

    passages = get_kb_passages(enhanced_q, kb_id, bedrock_agent, context)
    if "No relevant passages" in passages:
        passages = get_kb_passages(question, kb_id, bedrock_agent, context)

    # Build Bedrock messages (no guardContent wrapper)
    convo_msgs = map_messages(cfg.messages or []) + [{
        "role": "user",
        "content": [{"text": f"Context:\n{passages}\n\nQuestion: {question}"}]
    }]
    sys_msgs = extract_system_messages(cfg.messages or [])

    params = {
        "modelId": cfg.model.name,
        "messages": convo_msgs,
    }
    if sys_msgs:
        params["system"] = sys_msgs

    raw = bedrock.converse(**params)
    tracker.track_bedrock_converse_metrics(raw)

    reply = raw["output"]["message"]["content"][0]["text"]

    usage = raw.get("usage", {})
    inp_tokens = usage.get("inputTokens", 0)
    out_tokens = usage.get("outputTokens", 0)

    cost_usd = _estimate_cost(cfg.model.name, inp_tokens, out_tokens)
    cost_cents = round(cost_usd * 100, 4)

    # LaunchDarkly metrics ----------------------------------------------------
    ld.track("$ld:ai:tokens:costmanual", context, metric_value=cost_cents)

    # synthetic satisfaction
    if random.random() < 0.95:
        tracker.track_feedback({"kind": FeedbackKind.Positive})
    else:
        tracker.track_feedback({"kind": FeedbackKind.Negative})

    ld.flush()

    metrics = {
        "model_used": cfg.model.name,
        "input_tokens": inp_tokens,
        "output_tokens": out_tokens,
        "cost_usd": round(cost_usd, 6),
        "cost_cents": cost_cents,
    }
    return reply, metrics

# ── CLI ----------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Run chat experiments without guardrails or LLM-as-judge.")
    p.add_argument("--runs", type=int, default=2)
    p.add_argument("--delay", type=float, default=2.0)
    p.add_argument("--question", type=str, default="What is my average account balance?")
    args = p.parse_args()

    import time
    for i in range(1, args.runs + 1):
        logger.info("Session %d/%d", i, args.runs)
        try:
            ans, mets = run_session(args.question)
            print(json.dumps({"session": i, "answer": ans, "metrics": mets}, indent=2))
        except Exception as e:
            logger.error("Run failed: %s", e, exc_info=True)
        time.sleep(args.delay)

if __name__ == "__main__":
    main() 