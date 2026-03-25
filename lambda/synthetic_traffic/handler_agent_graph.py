#!/usr/bin/env python3
"""
Synthetic traffic handler using LaunchDarkly Agent Graph.

Uses the LD Agent Graph SDK to traverse the graph structure defined in
LaunchDarkly, resolving each agent's AI Config at runtime. This is an
alternative to the LangGraph-based handler that demonstrates LD-native
multi-agent orchestration.

Graph structure (defined in LaunchDarkly):
    triage_agent
    ├── policy_agent
    │   └── brand_agent
    ├── provider_agent
    │   └── brand_agent
    └── scheduler_agent
        └── brand_agent
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone
from uuid import uuid4

from common import (
    BETA_TESTER_USERS,
    ITERATIONS,
    POSITIVE_FEEDBACK_RATE,
    QUESTION_POOL,
    build_ld_context,
    create_beta_tester_profile,
    ensure_initialized,
    flush_traces,
    get_tracer,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AGENT_GRAPH_KEY = "policy-agent"


def _patch_tracker_for_graph(tracker, graph_key):
    """Add graphKey to a node tracker's event data so the Agent Graph UI
    can associate per-node latency/token metrics with the graph."""
    if tracker is None:
        return
    original = tracker._LDAIConfigTracker__get_track_data

    def patched():
        data = original()
        data["graphKey"] = graph_key
        return data

    tracker._LDAIConfigTracker__get_track_data = patched


def _simulate_tool_calls(node, graph_tracker):
    """Simulate tool invocations for a node so they register in the Agent Graph UI.

    Produces varied tool usage: ~20% chance of no tools, otherwise 1 to all tools
    with a bias toward using fewer tools (weighted random).
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


def _invoke_model(agent_config, messages_list):
    """Invoke a Bedrock model using an AIAgentConfig from the graph.

    Args:
        agent_config: AIAgentConfig from node.get_config()
        messages_list: List of LangChain BaseMessage objects

    Returns:
        Tuple of (response_text, tokens_dict, duration_ms)
    """
    from src.utils.bedrock_llm import BedrockConverseLLM, get_bedrock_model_id
    from langchain_core.messages import SystemMessage, HumanMessage

    model_name = agent_config.model.name if agent_config.model else "us.anthropic.claude-haiku-4-5-20251001-v1:0"
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

    start = time.time()

    if agent_config.tracker:
        result = agent_config.tracker.track_duration_of(lambda: llm.invoke(messages_list))
        agent_config.tracker.track_success()
    else:
        result = llm.invoke(messages_list)

    duration_ms = int((time.time() - start) * 1000)

    tokens = {"input": 0, "output": 0}
    if hasattr(result, "usage_metadata") and result.usage_metadata:
        tokens["input"] = result.usage_metadata.get("input_tokens", 0)
        tokens["output"] = result.usage_metadata.get("output_tokens", 0)

    if agent_config.tracker and tokens["input"] + tokens["output"] > 0:
        from ldai.tracker import TokenUsage
        agent_config.tracker.track_tokens(TokenUsage(
            input=tokens["input"],
            output=tokens["output"],
            total=tokens["input"] + tokens["output"],
        ))

    return result.content, tokens, duration_ms


def _build_messages(instructions, **context_vars):
    """Build LangChain messages from agent instructions and context variables."""
    from langchain_core.messages import SystemMessage, HumanMessage
    import chevron

    rendered = chevron.render(instructions, context_vars) if instructions else ""
    return [SystemMessage(content=rendered)]


def _run_triage(triage_node, question, user_context, graph_tracker):
    """Execute the triage agent to determine routing."""
    from opentelemetry.trace import StatusCode
    from langchain_core.messages import HumanMessage

    tracer = get_tracer("togglehealth.agent-graph")
    config = triage_node.get_config()

    with tracer.start_as_current_span(
        "agent-graph.triage",
        attributes={
            "agent.name": triage_node.get_key(),
            "agent.model": config.model.name if config.model else "",
        },
    ) as span:
        messages = _build_messages(config.instructions, query=question, **user_context)
        messages.append(HumanMessage(content=question))

        response_text, tokens, duration_ms = _invoke_model(config, messages)

        graph_tracker.track_node_invocation(triage_node.get_key())
        tools_called = _simulate_tool_calls(triage_node, graph_tracker)

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
            f"  Triage: {query_type} (confidence: {result.get('confidence_score', 0):.2f}), "
            f"{duration_ms}ms, tools: {tools_called}"
        )

        return query_type, result, tokens


def _find_specialist_node(graph, triage_node, query_type):
    """Find the specialist node matching the triage routing decision."""
    agent_map = {
        "policy_question": "policy_agent",
        "provider_lookup": "provider_agent",
        "schedule_agent": "scheduler_agent",
    }
    target_key = agent_map.get(query_type, "scheduler_agent")

    for edge in triage_node.get_edges():
        if edge.target_config == target_key:
            return graph.get_node(target_key), edge

    # Fallback: try first edge
    edges = triage_node.get_edges()
    if edges:
        fallback_key = edges[0].target_config
        return graph.get_node(fallback_key), edges[0]

    return None, None


def _run_specialist(specialist_node, question, user_context, query_type, graph_tracker, triage_key):
    """Execute a specialist agent with RAG retrieval."""
    from opentelemetry.trace import StatusCode
    from langchain_core.messages import HumanMessage

    tracer = get_tracer("togglehealth.agent-graph")
    config = specialist_node.get_config()
    node_key = specialist_node.get_key()

    with tracer.start_as_current_span(
        f"agent-graph.{node_key}",
        attributes={
            "agent.name": node_key,
            "agent.model": config.model.name if config.model else "",
            "agent.query_type": query_type,
        },
    ) as span:
        rag_documents = []
        policy_id = user_context.get("policy_id")
        location = user_context.get("location", "")
        coverage_type = user_context.get("coverage_type", "Unknown")

        ld_config = None
        if config.model:
            ld_config = {"model": {"custom": config.model._custom or {}}}

        if query_type == "policy_question":
            from src.tools.bedrock_rag import retrieve_policy_documents
            rag_documents = retrieve_policy_documents(question, policy_id, ld_config=ld_config)
        elif query_type == "provider_lookup":
            from src.tools.bedrock_rag import retrieve_provider_documents
            rag_documents = retrieve_provider_documents(question, location=location, ld_config=ld_config)

        rag_text = ""
        if rag_documents:
            rag_text = "\n\n=== RETRIEVED DOCUMENTS ===\n"
            for i, doc in enumerate(rag_documents, 1):
                rag_text += f"\n[Document {i} - Relevance: {doc.get('score', 0):.2f}]\n{doc.get('content', '')}\n"
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
        messages = _build_messages(config.instructions, **context_vars)
        messages.append(HumanMessage(content=question))

        response_text, tokens, duration_ms = _invoke_model(config, messages)

        graph_tracker.track_node_invocation(node_key)
        graph_tracker.track_handoff_success(triage_key, node_key)
        tools_called = _simulate_tool_calls(specialist_node, graph_tracker)

        span.set_attribute("agent.tokens.input", tokens["input"])
        span.set_attribute("agent.tokens.output", tokens["output"])
        span.set_attribute("agent.duration_ms", duration_ms)
        span.set_attribute("agent.response_length", len(response_text))
        if tools_called:
            span.set_attribute("agent.tools_called", ", ".join(tools_called))
        span.set_status(StatusCode.OK)

        logger.info(
            f"  Specialist ({node_key}): {len(response_text)} chars, {duration_ms}ms, tools: {tools_called}"
        )

        return response_text, tokens, duration_ms


def _run_brand_voice(brand_node, specialist_response, question, user_context,
                     graph_tracker, specialist_key):
    """Execute the brand voice agent to transform the response."""
    from opentelemetry.trace import StatusCode
    from langchain_core.messages import HumanMessage

    tracer = get_tracer("togglehealth.agent-graph")
    config = brand_node.get_config()
    node_key = brand_node.get_key()

    with tracer.start_as_current_span(
        f"agent-graph.{node_key}",
        attributes={
            "agent.name": node_key,
            "agent.model": config.model.name if config.model else "",
        },
    ) as span:
        customer_name = user_context.get("name", "there")

        context_vars = {
            **user_context,
            "customer_name": customer_name,
            "original_query": question,
            "query_type": user_context.get("_query_type", "unknown"),
            "specialist_response": specialist_response,
        }
        messages = _build_messages(config.instructions, **context_vars)
        messages.append(HumanMessage(content=(
            f"Transform this specialist response into a warm, customer-friendly message "
            f"for {customer_name}:\n\n{specialist_response}"
        )))

        response_text, tokens, duration_ms = _invoke_model(config, messages)

        graph_tracker.track_node_invocation(node_key)
        graph_tracker.track_handoff_success(specialist_key, node_key)
        tools_called = _simulate_tool_calls(brand_node, graph_tracker)

        span.set_attribute("agent.tokens.input", tokens["input"])
        span.set_attribute("agent.tokens.output", tokens["output"])
        span.set_attribute("agent.duration_ms", duration_ms)
        span.set_attribute("agent.response_length", len(response_text))
        if tools_called:
            span.set_attribute("agent.tools_called", ", ".join(tools_called))
        span.set_status(StatusCode.OK)

        logger.info(
            f"  Brand voice ({node_key}): {len(response_text)} chars, {duration_ms}ms"
        )

        return response_text, tokens, duration_ms


def _run_single_iteration(iteration_num: int) -> dict:
    """Run a single iteration using the LD Agent Graph."""
    from opentelemetry.trace import StatusCode
    import ldclient
    from ldai.client import LDAIClient

    tracer = get_tracer("togglehealth.agent-graph")
    user_spec = random.choice(BETA_TESTER_USERS)
    question = random.choice(QUESTION_POOL)
    request_id = str(uuid4())

    user_context = create_beta_tester_profile(user_spec)
    is_positive = random.random() < POSITIVE_FEEDBACK_RATE

    with tracer.start_as_current_span(
        "synthetic-iteration",
        attributes={
            "synthetic.iteration": iteration_num,
            "synthetic.user.name": user_spec["name"],
            "synthetic.user.location": user_spec["location"],
            "synthetic.user.coverage_type": user_spec["coverage_type"],
            "synthetic.question": question,
            "synthetic.request_id": request_id,
            "synthetic.user_key": user_context["user_key"],
            "synthetic.handler": "agent-graph",
        },
    ) as span:
        logger.info(
            f"[Iteration {iteration_num}] User: {user_spec['name']}, "
            f"Question: {question[:60]}..."
        )

        start_time = time.time()

        try:
            ld_context = build_ld_context(user_context)
            ai_client = LDAIClient(ldclient.get())
            agent_graph = ai_client.agent_graph(AGENT_GRAPH_KEY, ld_context)

            if not agent_graph.is_enabled():
                raise RuntimeError(
                    f"Agent graph '{AGENT_GRAPH_KEY}' is disabled — check that all nodes "
                    f"are reachable and enabled in LaunchDarkly"
                )

            graph_tracker = agent_graph.get_tracker()
            root_node = agent_graph.root()

            if root_node is None:
                raise RuntimeError(f"Agent graph '{AGENT_GRAPH_KEY}' has no root node")

            # Patch root node tracker so its events include graphKey
            _patch_tracker_for_graph(root_node.get_config().tracker, AGENT_GRAPH_KEY)

            # Step 1: Triage
            query_type, triage_result, triage_tokens = _run_triage(
                root_node, question, user_context, graph_tracker
            )

            # Step 2: Find and run specialist
            specialist_node, specialist_edge = _find_specialist_node(
                agent_graph, root_node, query_type
            )
            if specialist_node is None:
                raise RuntimeError(f"No specialist node found for query_type={query_type}")

            _patch_tracker_for_graph(specialist_node.get_config().tracker, AGENT_GRAPH_KEY)

            user_context["_query_type"] = query_type
            specialist_response, spec_tokens, spec_duration = _run_specialist(
                specialist_node, question, user_context, query_type,
                graph_tracker, root_node.get_key()
            )

            # Step 3: Find and run brand voice (child of specialist)
            brand_node = None
            for edge in specialist_node.get_edges():
                brand_node = agent_graph.get_node(edge.target_config)
                if brand_node:
                    break

            if brand_node is not None:
                _patch_tracker_for_graph(brand_node.get_config().tracker, AGENT_GRAPH_KEY)

            if brand_node is None:
                final_response = specialist_response
                execution_path = [root_node.get_key(), specialist_node.get_key()]
                brand_tokens = {"input": 0, "output": 0}
            else:
                final_response, brand_tokens, brand_duration = _run_brand_voice(
                    brand_node, specialist_response, question, user_context,
                    graph_tracker, specialist_node.get_key()
                )
                execution_path = [
                    root_node.get_key(),
                    specialist_node.get_key(),
                    brand_node.get_key(),
                ]

            duration_ms = int((time.time() - start_time) * 1000)

            # Aggregate tokens across all nodes for graph-level tracking
            from ldai.tracker import TokenUsage as _TU
            total_input = triage_tokens["input"] + spec_tokens["input"] + brand_tokens["input"]
            total_output = triage_tokens["output"] + spec_tokens["output"] + brand_tokens["output"]
            graph_tracker.track_total_tokens(_TU(
                input=total_input, output=total_output,
                total=total_input + total_output,
            ))

            # Track graph-level metrics
            graph_tracker.track_invocation_success()
            graph_tracker.track_latency(duration_ms)
            graph_tracker.track_path(execution_path)

            # Submit feedback via brand voice tracker
            feedback_label = "positive" if is_positive else "negative"
            if brand_node and brand_node.get_config().tracker:
                from ldai.tracker import FeedbackKind
                brand_tracker = brand_node.get_config().tracker
                _patch_tracker_for_graph(brand_tracker, AGENT_GRAPH_KEY)
                feedback_kind = FeedbackKind.Positive if is_positive else FeedbackKind.Negative
                brand_tracker.track_feedback({"kind": feedback_kind})

            ldclient.get().flush()

            span.set_attribute("synthetic.response_length", len(final_response))
            span.set_attribute("synthetic.duration_ms", duration_ms)
            span.set_attribute("synthetic.query_type", query_type)
            span.set_attribute("synthetic.feedback", feedback_label)
            span.set_attribute("synthetic.execution_path", ",".join(execution_path))
            span.set_status(StatusCode.OK)

            logger.info(
                f"[Iteration {iteration_num}] Response: {len(final_response)} chars, "
                f"{duration_ms}ms, path: {' -> '.join(execution_path)}"
            )

            return {
                "iteration": iteration_num,
                "user": user_spec["name"],
                "question": question,
                "response_length": len(final_response),
                "duration_ms": duration_ms,
                "query_type": query_type,
                "execution_path": execution_path,
                "feedback": feedback_label,
                "success": True,
            }

        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.error(
                f"[Iteration {iteration_num}] Error: {e}", exc_info=True
            )
            span.set_status(StatusCode.ERROR, str(e))
            span.record_exception(e)
            span.set_attribute("synthetic.duration_ms", duration_ms)

            try:
                if "graph_tracker" in dir():
                    graph_tracker.track_invocation_failure()
            except Exception:
                pass

            return {
                "iteration": iteration_num,
                "user": user_spec["name"],
                "question": question,
                "error": str(e),
                "duration_ms": duration_ms,
                "success": False,
            }


def lambda_handler(event, context):
    """AWS Lambda entry point — Agent Graph workflow."""
    execution_start = datetime.now(timezone.utc)
    logger.info(
        f"[AgentGraph] Starting synthetic traffic at {execution_start.isoformat()}"
    )
    logger.info(f"Event: {json.dumps(event, default=str)}")

    ensure_initialized()

    tracer = get_tracer("togglehealth.agent-graph")

    with tracer.start_as_current_span(
        "synthetic-traffic-batch",
        attributes={
            "synthetic.total_iterations": ITERATIONS,
            "synthetic.positive_feedback_rate": POSITIVE_FEEDBACK_RATE,
            "synthetic.timestamp": execution_start.isoformat(),
            "synthetic.source": "lambda",
            "synthetic.handler": "agent-graph",
            "synthetic.graph_key": AGENT_GRAPH_KEY,
        },
    ) as batch_span:
        results = []
        for i in range(1, ITERATIONS + 1):
            result = _run_single_iteration(i)
            results.append(result)
            logger.info(f"Completed iteration {i}/{ITERATIONS}")

        success_count = sum(1 for r in results if r["success"])
        total_duration = int(
            (datetime.now(timezone.utc) - execution_start).total_seconds()
        )

        batch_span.set_attribute("synthetic.successful", success_count)
        batch_span.set_attribute("synthetic.failed", ITERATIONS - success_count)
        batch_span.set_attribute("synthetic.total_duration_seconds", total_duration)

        from opentelemetry.trace import StatusCode

        if success_count == ITERATIONS:
            batch_span.set_status(StatusCode.OK)
        else:
            batch_span.set_status(
                StatusCode.ERROR,
                f"{ITERATIONS - success_count}/{ITERATIONS} iterations failed",
            )

    try:
        import ldclient

        ldclient.get().flush()
    except Exception:
        pass

    flush_traces()
    time.sleep(1)

    summary = {
        "total_iterations": ITERATIONS,
        "successful": success_count,
        "failed": ITERATIONS - success_count,
        "total_duration_seconds": total_duration,
        "timestamp": execution_start.isoformat(),
        "handler": "agent-graph",
        "graph_key": AGENT_GRAPH_KEY,
        "results": results,
    }

    logger.info(
        f"[AgentGraph] Complete: {success_count}/{ITERATIONS} successful, "
        f"{total_duration}s total"
    )

    return {
        "statusCode": 200,
        "body": json.dumps(summary, default=str),
    }


if __name__ == "__main__":
    import pathlib

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

    from dotenv import load_dotenv

    load_dotenv()

    test_event = {}
    test_context = type(
        "Context",
        (),
        {
            "function_name": "synthetic-traffic-agent-graph-test",
            "remaining_time_in_millis": lambda: 900000,
        },
    )()

    result = lambda_handler(test_event, test_context)
    print(json.dumps(json.loads(result["body"]), indent=2))
