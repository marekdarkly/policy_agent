"""
LD Agent Graph traversal engine.

Provides a reusable ``run_agent_graph()`` entry-point that resolves the
LaunchDarkly Agent Graph, walks its nodes (triage → specialist → brand voice),
and records per-node and graph-level metrics via the LD AI SDK trackers.

Graph structure (defined in LaunchDarkly):
    triage_agent
    ├── policy_agent   → brand_agent
    ├── provider_agent → brand_agent
    └── scheduler_agent → brand_agent
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import time
from dataclasses import dataclass, field
from typing import Any, Optional

import chevron
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AgentGraphResult:
    """Outcome of a single agent-graph traversal."""

    final_response: str
    query_type: str
    execution_path: list[str]
    duration_ms: int
    tokens: dict[str, int] = field(default_factory=lambda: {"input": 0, "output": 0})
    node_durations: dict[str, int] = field(default_factory=dict)
    judge_results: dict[str, Any] = field(default_factory=dict)
    triage_result: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Tracker helpers
# ---------------------------------------------------------------------------

def patch_tracker_for_graph(tracker, graph_key: str) -> None:
    """Add *graphKey* to a node tracker's event data so the Agent Graph UI
    can associate per-node latency / token metrics with the graph."""
    if tracker is None:
        return
    original = tracker._LDAIConfigTracker__get_track_data

    def patched():
        data = original()
        data["graphKey"] = graph_key
        return data

    tracker._LDAIConfigTracker__get_track_data = patched


def simulate_tool_calls(node, graph_tracker) -> list[str]:
    """Report simulated tool invocations for *node*.

    Produces varied tool usage: ~20 % chance of no tools, otherwise 1-to-all
    tools with a bias toward fewer calls (weighted random).
    """
    config = node.get_config()
    params = config.model._parameters if config.model else {}
    tools = params.get("tools", [])
    if not tools:
        return []

    if random.random() < 0.2:
        return []

    weights = list(range(len(tools), 0, -1))
    num_calls = random.choices(range(1, len(tools) + 1), weights=weights, k=1)[0]
    selected = random.sample(tools, num_calls)
    called = []
    for tool in selected:
        tool_key = tool.get("name", "unknown")
        graph_tracker.track_tool_call(node.get_key(), tool_key)
        called.append(tool_key)
    return called


# ---------------------------------------------------------------------------
# Model invocation
# ---------------------------------------------------------------------------

def invoke_model(agent_config, messages: list) -> tuple[str, dict[str, int]]:
    """Invoke a Bedrock model using an ``AIAgentConfig``.

    Returns ``(response_text, {"input": …, "output": …})``.
    """
    from src.utils.bedrock_llm import BedrockConverseLLM, get_bedrock_model_id
    from ldai.tracker import TokenUsage

    model_name = (
        agent_config.model.name
        if agent_config.model
        else "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    )
    model_id = get_bedrock_model_id(model_name)

    model_obj = agent_config.model
    if model_obj:
        temp_val = model_obj.get_parameter("temperature")
        temperature = float(temp_val) if temp_val is not None else 0.7
        max_val = model_obj.get_parameter("max_tokens") or model_obj.get_parameter("maxTokens")
        max_tokens = int(max_val) if max_val is not None else 2000
    else:
        temperature = 0.7
        max_tokens = 2000

    region = os.getenv("AWS_REGION", "us-east-1")
    profile = os.getenv("AWS_PROFILE")

    llm = BedrockConverseLLM(
        model_id=model_id,
        temperature=temperature,
        max_tokens=max_tokens,
        region=region,
        profile_name=profile,
    )

    result = llm.invoke(messages)

    tokens: dict[str, int] = {"input": 0, "output": 0}
    if hasattr(result, "usage_metadata") and result.usage_metadata:
        tokens["input"] = result.usage_metadata.get("input_tokens", 0)
        tokens["output"] = result.usage_metadata.get("output_tokens", 0)

    if agent_config.tracker and tokens["input"] + tokens["output"] > 0:
        agent_config.tracker.track_tokens(TokenUsage(
            input=tokens["input"],
            output=tokens["output"],
            total=tokens["input"] + tokens["output"],
        ))

    return result.content, tokens


def build_messages(instructions: str | None, **context_vars) -> list:
    """Render agent instructions with mustache and return as a message list."""
    rendered = chevron.render(instructions, context_vars) if instructions else ""
    return [SystemMessage(content=rendered)]


# ---------------------------------------------------------------------------
# Per-node runners
# ---------------------------------------------------------------------------

def _get_tracer():
    from opentelemetry import trace
    return trace.get_tracer("togglehealth.agent-graph")


def run_triage(triage_node, question: str, user_context: dict,
               graph_tracker, graph_key: str):
    """Execute the triage agent and return ``(query_type, parsed_result, tokens)``."""
    from opentelemetry.trace import StatusCode

    tracer = _get_tracer()
    config = triage_node.get_config()
    patch_tracker_for_graph(config.tracker, graph_key)

    with tracer.start_as_current_span(
        "agent-graph.triage",
        attributes={
            "agent.name": triage_node.get_key(),
            "agent.model": config.model.name if config.model else "",
        },
    ) as span:
        node_start = time.time()

        messages = build_messages(config.instructions, query=question, **user_context)
        messages.append(HumanMessage(content=question))

        response_text, tokens = invoke_model(config, messages)

        duration_ms = int((time.time() - node_start) * 1000)

        if config.tracker:
            config.tracker.track_duration(duration_ms)
            config.tracker.track_success()

        graph_tracker.track_node_invocation(triage_node.get_key())
        tools_called = simulate_tool_calls(triage_node, graph_tracker)

        span.set_attribute("agent.tokens.input", tokens["input"])
        span.set_attribute("agent.tokens.output", tokens["output"])
        span.set_attribute("agent.duration_ms", duration_ms)
        if tools_called:
            span.set_attribute("agent.tools_called", ", ".join(tools_called))

        try:
            result = json.loads(response_text)
        except json.JSONDecodeError:
            result = {"query_type": "schedule_agent", "confidence_score": 0.5}

        query_type = result.get("query_type", "schedule_agent")
        span.set_attribute("agent.query_type", query_type)
        span.set_status(StatusCode.OK)

        logger.info(
            "  Triage: %s (confidence: %.2f), %dms, tools: %s",
            query_type, result.get("confidence_score", 0), duration_ms, tools_called,
        )

        return query_type, result, tokens, duration_ms


def find_specialist_node(graph, triage_node, query_type: str):
    """Resolve the specialist node matching the triage routing decision.

    Returns ``(node, edge)`` or ``(None, None)``.
    """
    agent_map = {
        "policy_question": "policy_agent",
        "provider_lookup": "provider_agent",
        "schedule_agent": "scheduler_agent",
    }
    target_key = agent_map.get(query_type, "scheduler_agent")

    for edge in triage_node.get_edges():
        if edge.target_config == target_key:
            return graph.get_node(target_key), edge

    edges = triage_node.get_edges()
    if edges:
        fallback_key = edges[0].target_config
        return graph.get_node(fallback_key), edges[0]

    return None, None


def run_specialist(specialist_node, question: str, user_context: dict,
                   query_type: str, graph_tracker, triage_key: str,
                   graph_key: str):
    """Execute a specialist agent (with RAG retrieval).

    Returns ``(response_text, tokens, duration_ms)``.
    """
    from opentelemetry.trace import StatusCode

    tracer = _get_tracer()
    config = specialist_node.get_config()
    patch_tracker_for_graph(config.tracker, graph_key)
    node_key = specialist_node.get_key()

    with tracer.start_as_current_span(
        f"agent-graph.{node_key}",
        attributes={
            "agent.name": node_key,
            "agent.model": config.model.name if config.model else "",
            "agent.query_type": query_type,
        },
    ) as span:
        node_start = time.time()

        rag_documents: list = []
        policy_id = user_context.get("policy_id")
        location = user_context.get("location", "")
        coverage_type = user_context.get("coverage_type", "Unknown")

        ld_config = None
        if config.model:
            ld_config = {"model": {"custom": config.model._custom or {}}}

        if query_type == "policy_question":
            from src.tools.bedrock_rag import retrieve_policy_documents
            rag_documents = retrieve_policy_documents(
                question, policy_id, ld_config=ld_config,
            )
        elif query_type == "provider_lookup":
            from src.tools.bedrock_rag import retrieve_provider_documents
            rag_documents = retrieve_provider_documents(
                question, location=location, ld_config=ld_config,
            )

        rag_text = ""
        if rag_documents:
            rag_text = "\n\n=== RETRIEVED DOCUMENTS ===\n"
            for i, doc in enumerate(rag_documents, 1):
                rag_text += (
                    f"\n[Document {i} - Relevance: {doc.get('score', 0):.2f}]\n"
                    f"{doc.get('content', '')}\n"
                )
            span.set_attribute("agent.rag_documents", len(rag_documents))

        context_vars = {
            **user_context,
            "query": question,
            "policy_id": policy_id or "Not provided",
            "coverage_type": coverage_type,
            "location": location or "Not specified",
            "policy_info": rag_text,
            "provider_info": rag_text,
        }
        messages = build_messages(config.instructions, **context_vars)
        messages.append(HumanMessage(content=question))

        response_text, tokens = invoke_model(config, messages)

        duration_ms = int((time.time() - node_start) * 1000)

        if config.tracker:
            config.tracker.track_duration(duration_ms)
            config.tracker.track_success()

        graph_tracker.track_node_invocation(node_key)
        graph_tracker.track_handoff_success(triage_key, node_key)
        tools_called = simulate_tool_calls(specialist_node, graph_tracker)

        span.set_attribute("agent.tokens.input", tokens["input"])
        span.set_attribute("agent.tokens.output", tokens["output"])
        span.set_attribute("agent.duration_ms", duration_ms)
        span.set_attribute("agent.response_length", len(response_text))
        if tools_called:
            span.set_attribute("agent.tools_called", ", ".join(tools_called))
        span.set_status(StatusCode.OK)

        logger.info(
            "  Specialist (%s): %d chars, %dms, tools: %s",
            node_key, len(response_text), duration_ms, tools_called,
        )

        return response_text, tokens, duration_ms


def run_brand_voice(brand_node, specialist_response: str, question: str,
                    user_context: dict, graph_tracker, specialist_key: str,
                    graph_key: str):
    """Execute the brand-voice agent.

    Returns ``(response_text, tokens, duration_ms)``.
    """
    from opentelemetry.trace import StatusCode

    tracer = _get_tracer()
    config = brand_node.get_config()
    patch_tracker_for_graph(config.tracker, graph_key)
    node_key = brand_node.get_key()

    with tracer.start_as_current_span(
        f"agent-graph.{node_key}",
        attributes={
            "agent.name": node_key,
            "agent.model": config.model.name if config.model else "",
        },
    ) as span:
        node_start = time.time()

        customer_name = user_context.get("name", "there")

        context_vars = {
            **user_context,
            "customer_name": customer_name,
            "original_query": question,
            "query_type": user_context.get("_query_type", "unknown"),
            "specialist_response": specialist_response,
        }
        messages = build_messages(config.instructions, **context_vars)
        messages.append(HumanMessage(content=(
            f"Transform this specialist response into a warm, customer-friendly "
            f"message for {customer_name}:\n\n{specialist_response}"
        )))

        response_text, tokens = invoke_model(config, messages)

        duration_ms = int((time.time() - node_start) * 1000)

        if config.tracker:
            config.tracker.track_duration(duration_ms)
            config.tracker.track_success()

        graph_tracker.track_node_invocation(node_key)
        graph_tracker.track_handoff_success(specialist_key, node_key)
        tools_called = simulate_tool_calls(brand_node, graph_tracker)

        span.set_attribute("agent.tokens.input", tokens["input"])
        span.set_attribute("agent.tokens.output", tokens["output"])
        span.set_attribute("agent.duration_ms", duration_ms)
        span.set_attribute("agent.response_length", len(response_text))
        if tools_called:
            span.set_attribute("agent.tools_called", ", ".join(tools_called))
        span.set_status(StatusCode.OK)

        logger.info(
            "  Brand voice (%s): %d chars, %dms",
            node_key, len(response_text), duration_ms,
        )

        return response_text, tokens, duration_ms


def run_judges(agent_graph, final_response: str, question: str,
               query_type: str, graph_tracker, graph_key: str) -> dict:
    """Run AI judge evaluations on the final response."""
    from ldai.providers.types import JudgeResponse, EvalScore

    judge_keys = ["ai-judge-accuracy", "ai-judge-coherence"]
    results: dict[str, Any] = {}

    for judge_key in judge_keys:
        judge_node = agent_graph.get_node(judge_key)
        if not judge_node:
            continue

        config = judge_node.get_config()
        patch_tracker_for_graph(config.tracker, graph_key)

        messages = [SystemMessage(content=config.instructions or "")]
        messages.append(HumanMessage(content=(
            f"original_query: {question}\n\n"
            f"rag_context: The response below was generated using retrieved policy "
            f"documents. Evaluate its quality based on the final output alone.\n\n"
            f"final_output: {final_response}"
        )))

        try:
            judge_start = time.time()
            response_text, tokens = invoke_model(config, messages)
            duration_ms = int((time.time() - judge_start) * 1000)

            if config.tracker:
                config.tracker.track_duration(duration_ms)
                config.tracker.track_success()

            graph_tracker.track_node_invocation(judge_key)

            score = 0.0
            reasoning = response_text[:200]
            try:
                parsed = json.loads(response_text)
                score = float(parsed.get("score", parsed.get("overall_score", 0.0)))
                reasoning = parsed.get("reasoning", parsed.get("explanation", reasoning))
            except (json.JSONDecodeError, ValueError):
                numbers = re.findall(r"\b([0-9]*\.?[0-9]+)\b", response_text[:100])
                for n in numbers:
                    val = float(n)
                    if 0 <= val <= 1:
                        score = val
                        break
                    elif 1 < val <= 10:
                        score = val / 10.0
                        break

            score = max(0.0, min(1.0, score))

            metric_name = (
                "$ld:ai:judge:accuracy" if "accuracy" in judge_key
                else "$ld:ai:judge:coherence"
            )
            judge_response = JudgeResponse(
                evals={metric_name: EvalScore(score=score, reasoning=reasoning)},
                success=True,
                judge_config_key=judge_key,
            )
            graph_tracker.track_judge_response(judge_response)

            results[judge_key] = {"score": score, "duration_ms": duration_ms}
            logger.info("  Judge (%s): score=%.2f, %dms", judge_key, score, duration_ms)

        except Exception as e:
            logger.warning("  Judge (%s) failed: %s", judge_key, e)
            results[judge_key] = {"error": str(e)}

    return results


# ---------------------------------------------------------------------------
# High-level entry-point
# ---------------------------------------------------------------------------

def run_agent_graph(
    graph_key: str,
    ld_context,
    question: str,
    user_context: dict,
    *,
    judge_probability: float = 0.10,
    feedback: Optional[str] = None,
) -> AgentGraphResult:
    """Execute a full agent-graph traversal and return an :class:`AgentGraphResult`.

    Parameters
    ----------
    graph_key:
        The LaunchDarkly Agent Graph key (e.g. ``"policy-agent"``).
    ld_context:
        An ``ldclient.Context`` for flag evaluation.
    question:
        The end-user question to process.
    user_context:
        Dict of user profile fields used to render prompt templates.
    judge_probability:
        Probability (0–1) of running judge evaluations.
    feedback:
        ``"positive"`` or ``"negative"``; omit to skip feedback tracking.
    """
    import ldclient
    from ldai.client import LDAIClient
    from ldai.tracker import FeedbackKind, TokenUsage

    start_time = time.time()

    ai_client = LDAIClient(ldclient.get())
    agent_graph = ai_client.agent_graph(graph_key, ld_context)

    if not agent_graph.is_enabled():
        raise RuntimeError(
            f"Agent graph '{graph_key}' is disabled — check that all nodes "
            f"are reachable and enabled in LaunchDarkly"
        )

    graph_tracker = agent_graph.get_tracker()
    root_node = agent_graph.root()

    if root_node is None:
        raise RuntimeError(f"Agent graph '{graph_key}' has no root node")

    # --- Step 1: Triage ---
    query_type, triage_result, triage_tokens, triage_dur = run_triage(
        root_node, question, user_context, graph_tracker, graph_key,
    )

    # --- Step 2: Specialist ---
    specialist_node, specialist_edge = find_specialist_node(
        agent_graph, root_node, query_type,
    )
    if specialist_node is None:
        raise RuntimeError(f"No specialist node found for query_type={query_type}")

    user_context["_query_type"] = query_type
    specialist_response, spec_tokens, spec_dur = run_specialist(
        specialist_node, question, user_context, query_type,
        graph_tracker, root_node.get_key(), graph_key,
    )

    # --- Step 3: Brand voice ---
    brand_node = None
    for edge in specialist_node.get_edges():
        brand_node = agent_graph.get_node(edge.target_config)
        if brand_node:
            break

    brand_tokens: dict[str, int] = {"input": 0, "output": 0}
    brand_dur = 0
    if brand_node is None:
        final_response = specialist_response
        execution_path = [root_node.get_key(), specialist_node.get_key()]
    else:
        final_response, brand_tokens, brand_dur = run_brand_voice(
            brand_node, specialist_response, question, user_context,
            graph_tracker, specialist_node.get_key(), graph_key,
        )
        execution_path = [
            root_node.get_key(),
            specialist_node.get_key(),
            brand_node.get_key(),
        ]

    duration_ms = int((time.time() - start_time) * 1000)

    # --- Graph-level metrics ---
    total_in = triage_tokens["input"] + spec_tokens["input"] + brand_tokens["input"]
    total_out = triage_tokens["output"] + spec_tokens["output"] + brand_tokens["output"]
    graph_tracker.track_total_tokens(TokenUsage(
        input=total_in, output=total_out, total=total_in + total_out,
    ))
    graph_tracker.track_invocation_success()
    graph_tracker.track_latency(duration_ms)
    graph_tracker.track_path(execution_path)

    # --- Judges ---
    judge_results: dict[str, Any] = {}
    if random.random() < judge_probability:
        judge_results = run_judges(
            agent_graph, final_response, question, query_type,
            graph_tracker, graph_key,
        )

    # --- Feedback ---
    if feedback and brand_node:
        brand_tracker = brand_node.get_config().tracker
        if brand_tracker:
            patch_tracker_for_graph(brand_tracker, graph_key)
            kind = FeedbackKind.Positive if feedback == "positive" else FeedbackKind.Negative
            brand_tracker.track_feedback({"kind": kind})

    ldclient.get().flush()

    return AgentGraphResult(
        final_response=final_response,
        query_type=query_type,
        execution_path=execution_path,
        duration_ms=duration_ms,
        tokens={"input": total_in, "output": total_out},
        node_durations={
            root_node.get_key(): triage_dur,
            specialist_node.get_key(): spec_dur,
            **(
                {brand_node.get_key(): brand_dur}
                if brand_node else {}
            ),
        },
        judge_results=judge_results,
        triage_result=triage_result,
    )
