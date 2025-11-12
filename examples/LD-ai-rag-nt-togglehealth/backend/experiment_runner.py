#!/usr/bin/env python3
"""
experiment_runner.py

Standalone CLI tool to spin up repeated chat sessions against the ToggleBank
LLM-backend **without** running the FastAPI server or the React frontend.

For every run it will:
  1. Fetch LaunchDarkly AI config & the current demo-user context (same helper
     used by FastAPI & script.py).
  2. Build the enhanced RAG query, call Bedrock with guardrails enabled.
  3. Parse guardrail trace → metrics, immediately run the LLM-as-judge factual
     accuracy check, and push both sets of metrics to LaunchDarkly.
  4. Print a clean JSON summary to stdout.
  5. Pause for N seconds, then repeat.

Example:
    python backend/experiment_runner.py --runs 3 --delay 2
"""

import os
import sys
import json
import time
import random
import logging
import argparse
from typing import Dict, Any, Tuple

import dotenv
import os
from pathlib import Path

# ── Environment ────────────────────────────────────────────────────────────

# Load .env from project root (one level up from backend/)
project_root = Path(__file__).parent.parent
dotenv.load_dotenv(project_root / ".env")

LD_SDK = os.getenv("LAUNCHDARKLY_SDK_KEY")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Hardcoded AI config keys
AI_CONFIG_KEY = "toggle-rag"
LD_JUDGE_KEY = "llm-as-judge"

if not LD_SDK:
    sys.exit("✖  Missing required LaunchDarkly env vars – check your .env file")

# ── Third-party SDKs ────────────────────────────────────────────────────────

import ldclient
from ldclient.config import Config
from ldai.client import LDAIClient, AIConfig, ModelConfig
from ldclient import Context
from ldai.tracker import FeedbackKind

# Initialise LaunchDarkly
ldclient.set_config(Config(LD_SDK))
ld = ldclient.get()
ai_client = LDAIClient(ld)

# ── Local project imports (from existing backend modules) ──────────────────

from script import (
    initialize_aws_clients,
    get_kb_passages,
    build_guardrail_prompt,
    map_messages,
    extract_system_messages,
    check_factual_accuracy,
    validate_response_for_user,
)
from user_service import get_current_user_context

# ── AWS Bedrock clients ─────────────────────────────────────────────────────

bedrock, bedrock_agent = initialize_aws_clients()

# ── Logging setup ───────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("experiment_runner")

# ── Helper: parse guardrail trace into flat metrics -------------------------

def _extract_guardrail_metrics(raw: Dict[str, Any], *, model_id: str, kb_id: str, gr_id: str) -> Dict[str, Any]:
    """Flatten the Bedrock guardrail trace structure into simple key/values."""
    metrics: Dict[str, Any] = {}

    if "trace" in raw and "guardrail" in raw["trace"]:
        guardrail_trace = raw["trace"]["guardrail"]

        # Output assessments
        output_assessments = guardrail_trace.get("outputAssessments", {})
        for _gid, assessments in output_assessments.items():
            if not assessments:
                continue
            assessment = assessments[0]

            # Contextual grounding section
            cg_policy = assessment.get("contextualGroundingPolicy", {})
            for filt in cg_policy.get("filters", []):
                if filt.get("type") == "GROUNDING":
                    metrics["grounding_score"] = filt.get("score", 0)
                    metrics["grounding_threshold"] = filt.get("threshold", 0)
                elif filt.get("type") == "RELEVANCE":
                    metrics["relevance_score"] = filt.get("score", 0)
                    metrics["relevance_threshold"] = filt.get("threshold", 0)

            # Invocation / latency / usage
            inv = assessment.get("invocationMetrics", {})
            if inv:
                metrics["processing_latency_ms"] = inv.get("guardrailProcessingLatency")
                usage = inv.get("usage", {})
                metrics["contextual_grounding_units"] = usage.get("contextualGroundingPolicyUnits")
                coverage = inv.get("guardrailCoverage", {}).get("textCharacters", {})
                metrics["characters_guarded"] = coverage.get("guarded")
                metrics["total_characters"] = coverage.get("total")
            break  # analyse first assessment only – mirrors FastAPI code
    else:
        logger.debug("No guardrail trace found in Bedrock response")

    # Always stamp identifiers
    metrics.update({
        "model_used": model_id,
        "knowledge_base_id": kb_id,
        "guardrail_id": gr_id,
    })

    # token usage (top-level)
    usage = raw.get("usage", {})
    metrics["input_tokens"] = usage.get("inputTokens")
    metrics["output_tokens"] = usage.get("outputTokens")

    return metrics

# ── Pricing table (USD per 1K tokens) ---------------------------------------
_PRICE_MAP = {
    # model_key: (input_rate, output_rate)
    "sonnet-4": (0.003, 0.015),
    "claude-sonnet-4": (0.003, 0.015),  # alt naming
    "sonnet": (0.003, 0.015),  # fallback for unnamed sonnet variants
    "haiku": (0.0008, 0.004),
    "nova": (0.0008, 0.0002),  # matches Nova Pro
}

def _estimate_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Return approximate USD cost for a model invocation."""
    lid = model_id.lower()
    for key, (in_rate, out_rate) in _PRICE_MAP.items():
        if key in lid:
            return (input_tokens / 1000.0) * in_rate + (output_tokens / 1000.0) * out_rate
    # Unknown model → assume Sonnet pricing as conservative default
    in_rate, out_rate = _PRICE_MAP["sonnet-4"]
    return (input_tokens / 1000.0) * in_rate + (output_tokens / 1000.0) * out_rate

# ── Core per-session routine ────────────────────────────────────────────────

def run_session(question: str) -> Tuple[str, Dict[str, Any]]:
    """Runs a complete ask-&-judge cycle and returns (answer, metrics_dict)."""

    # 1. LaunchDarkly context (demo user profile)
    context: Context = get_current_user_context()

    # 2. Seed config – same default used elsewhere
    default_cfg = AIConfig(
        enabled=True,
        model=ModelConfig(name="us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
        messages=[],
    )

    # Pass user question so LD can template it if needed
    cfg, tracker = ai_client.config(
        AI_CONFIG_KEY,
        context,
        default_cfg,
        {"userInput": question},
    )

    # 3. Extract custom parameters (kb_id, guardrail id…)
    try:
        kb_id = cfg.model.get_custom("kb_id")
        gr_id = cfg.model.get_custom("gr_id")
        gr_ver = str(cfg.model.get_custom("gr_version") or "1")
        eval_freq = cfg.model.get_custom("eval_freq") or "0.2"
    except Exception as err:
        # Fallback to dict method (older ldai version)
        cfg_dict = cfg.to_dict()
        custom = cfg_dict.get("model", {}).get("custom", {})
        kb_id = custom.get("kb_id")
        gr_id = custom.get("gr_id")
        gr_ver = str(custom.get("gr_version", "1"))
        eval_freq = custom.get("eval_freq", "0.2")
        logger.warning("get_custom failed (%s) – using fallback", err)

    if not kb_id or not gr_id:
        raise RuntimeError("kb_id or gr_id missing from LaunchDarkly AI config")

    custom_params = {
        "kb_id": kb_id,
        "gr_id": gr_id,
        "gr_version": gr_ver,
        "eval_freq": eval_freq,
    }

    # 4. Build RAG query (same heuristics as wrapper)
    context_dict = context.to_dict()
    user_tier = context_dict.get("tier", "")
    user_name = context.name

    if any(word in question.lower() for word in ["my", "me", "i", "mine"]):
        enhanced_query = f"{user_name} {user_tier} tier {question}"
    else:
        enhanced_query = f"{user_tier} tier {question}"

    passages = get_kb_passages(enhanced_query, kb_id, bedrock_agent, context)
    if "No relevant passages found" in passages:
        passages = get_kb_passages(question, kb_id, bedrock_agent, context)

    if "No relevant passages found" in passages:
        passages = (
            "I don't have specific information about that topic. Please contact "
            "ToggleSupport via chat or phone for personalized assistance."
        )

    # 5. Build Bedrock message payload --------------------------------------
    combined_grounding_text = f"QUESTION: {question}\n\n{passages}"

    user_content = [
        {
            "guardContent": {
                "text": {"text": combined_grounding_text, "qualifiers": ["grounding_source"]}
            }
        },
        {
            "guardContent": {"text": {"text": question, "qualifiers": ["query"]}}
        },
    ]

    convo_msgs = map_messages(cfg.messages or []) + [
        {"role": "user", "content": user_content}
    ]
    system_msgs = extract_system_messages(cfg.messages or [])

    converse_params = {
        "modelId": cfg.model.name,
        "messages": convo_msgs,
        "guardrailConfig": {
            "guardrailIdentifier": gr_id,
            "guardrailVersion": gr_ver,
            "trace": "enabled",
        },
    }
    if system_msgs:
        converse_params["system"] = system_msgs

    # 6. Call Bedrock --------------------------------------------------------
    raw = bedrock.converse(**converse_params)
    tracker.track_bedrock_converse_metrics(raw)  # push usage stats to LD

    # 7. Guardrail metrics extraction
    guard_metrics = _extract_guardrail_metrics(raw, model_id=cfg.model.name, kb_id=kb_id, gr_id=gr_id)

    # 8. Response text + user validation
    reply_txt = raw["output"]["message"]["content"][0]["text"]
    reply_txt = validate_response_for_user(reply_txt, context)

    # 9. Judge evaluation (may be skipped via eval_freq)
    judge_metrics = check_factual_accuracy(
        source_passages=passages,
        response_text=reply_txt,
        user_question=question,
        generator_model_id=cfg.model.name,
        custom_params=custom_params,
        context=context,
        ai_client=ai_client,
        bedrock=bedrock,
    ) or {}

    # 9b. Send hallucination/accuracy metric to LaunchDarkly ------------------
    if "accuracy_score" in judge_metrics and judge_metrics["accuracy_score"] is not None:
        acc_pct = judge_metrics["accuracy_score"] * 100  # 0-1 → percentage
        ld.track(
            "$ld:ai:hallucinations",
            context,
            data=None,
            metric_value=acc_pct,
        )

    # 10. Cost estimation for the **generator** model only --------------------
    total_cost_usd = round(
        _estimate_cost(
            cfg.model.name,
            guard_metrics.get("input_tokens", 0) or 0,
            guard_metrics.get("output_tokens", 0) or 0,
        ),
        6,
    )

    # Convert to cents for tracking
    total_cost_cents = round(total_cost_usd * 100, 4)

    # 11. Merge metrics (guardrail → judge → cost)
    combined_metrics = {
        **guard_metrics,
        **judge_metrics,
        "cost_usd": total_cost_usd,
        "cost_cents": total_cost_cents,
    }

    # Send manual cost metric to LaunchDarkly
    ld.track(
        "$ld:ai:tokens:costmanual",
        context,
        data=None,
        metric_value=total_cost_cents,
    )

    # 12. Simulate user feedback – 95% positive, 5% negative
    if tracker:
        if random.random() < 0.95:
            tracker.track_feedback({"kind": FeedbackKind.Positive})
        else:
            tracker.track_feedback({"kind": FeedbackKind.Negative})

    # 13. Flush LD events so they show up quickly in the dashboard
    ld.flush()

    # ── Send guardrail quality metrics to LaunchDarkly -----------------------
    if "grounding_score" in guard_metrics and guard_metrics["grounding_score"] is not None:
        ld.track(
            "$ld:ai:source-fidelity",
            context,
            data=None,
            metric_value=guard_metrics["grounding_score"] * 100,
        )

    if "relevance_score" in guard_metrics and guard_metrics["relevance_score"] is not None:
        ld.track(
            "$ld:ai:relevance",
            context,
            data=None,
            metric_value=guard_metrics["relevance_score"] * 100,
        )

    return reply_txt, combined_metrics

# ── CLI / main loop ─────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Run repeat chat experiments without the FastAPI layer.")
    parser.add_argument("--runs", type=int, default=2, help="Number of sessions to run (default: 2)")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds to wait between sessions (default: 2.0)")
    parser.add_argument(
        "--question",
        type=str,
        default="What is my average account balance?",
        help="Question to ask the chatbot each run.",
    )

    args = parser.parse_args()

    for i in range(1, args.runs + 1):
        logger.info("── Session %d/%d ──", i, args.runs)
        try:
            answer, metrics = run_session(args.question)
            summary = {
                "session": i,
                "question": args.question,
                "answer": answer,
                "metrics": metrics,
            }
            print(json.dumps(summary, indent=2))
        except Exception as exc:
            logger.error("Session %d failed: %s", i, exc, exc_info=True)
        time.sleep(args.delay)


if __name__ == "__main__":
    main() 