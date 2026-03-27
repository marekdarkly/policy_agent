#!/usr/bin/env python3
"""
Synthetic traffic handler using the LangGraph-based multi-agent workflow.

Runs 10 iterations per invocation, each exercising the full pipeline:
triage -> specialist -> brand voice, with feedback submission.
"""

import json
import logging
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
    create_beta_tester_profile,
    ensure_initialized,
    flush_traces,
    get_tracer,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def _run_single_iteration(iteration_num: int) -> dict:
    """Run a single iteration of the synthetic traffic flow."""
    from opentelemetry.trace import StatusCode
    from src.graph.workflow import run_workflow

    tracer = get_tracer()
    user_spec = random.choice(BETA_TESTER_USERS)
    question = random.choice(QUESTION_POOL)
    request_id = str(uuid4())

    user_context = create_beta_tester_profile(user_spec)
    brand_trackers: dict = {}
    eval_results: dict = {}
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
            "synthetic.handler": "langgraph",
        },
    ) as span:
        logger.info(
            f"[Iteration {iteration_num}] User: {user_spec['name']}, "
            f"Question: {question[:60]}..."
        )

        start_time = time.time()

        try:
            result = run_workflow(
                user_message=question,
                user_context=user_context,
                request_id=request_id,
                evaluation_results_store=eval_results,
                brand_trackers_store=brand_trackers,
                guardrail_enabled=True,
            )

            duration_ms = int((time.time() - start_time) * 1000)
            final_response = result.get("final_response", "No response")
            query_type = str(result.get("query_type", "unknown"))

            span.set_attribute("synthetic.response_length", len(final_response))
            span.set_attribute("synthetic.duration_ms", duration_ms)
            span.set_attribute("synthetic.query_type", query_type)

            logger.info(
                f"[Iteration {iteration_num}] Response: "
                f"{len(final_response)} chars, {duration_ms}ms"
            )

            feedback_label = "positive" if is_positive else "negative"
            span.set_attribute("synthetic.feedback", feedback_label)

            if request_id in brand_trackers:
                from ldai.tracker import FeedbackKind
                import ldclient

                model_invoker = brand_trackers[request_id]
                feedback_kind = (
                    FeedbackKind.Positive if is_positive else FeedbackKind.Negative
                )
                model_invoker.tracker.track_feedback({"kind": feedback_kind})
                ldclient.get().flush()
                logger.info(
                    f"[Iteration {iteration_num}] Feedback: {feedback_label}"
                )
            else:
                logger.warning(
                    f"[Iteration {iteration_num}] No tracker found for feedback"
                )

            span.set_status(StatusCode.OK)

            return {
                "iteration": iteration_num,
                "user": user_spec["name"],
                "question": question,
                "response_length": len(final_response),
                "duration_ms": duration_ms,
                "query_type": query_type,
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
            return {
                "iteration": iteration_num,
                "user": user_spec["name"],
                "question": question,
                "error": str(e),
                "duration_ms": duration_ms,
                "success": False,
            }


def lambda_handler(event, context):
    """AWS Lambda entry point — LangGraph workflow."""
    execution_start = datetime.now(timezone.utc)
    logger.info(
        f"[LangGraph] Starting synthetic traffic at {execution_start.isoformat()}"
    )
    logger.info(f"Event: {json.dumps(event, default=str)}")

    ensure_initialized()

    tracer = get_tracer()

    with tracer.start_as_current_span(
        "synthetic-traffic-batch",
        attributes={
            "synthetic.total_iterations": ITERATIONS,
            "synthetic.positive_feedback_rate": POSITIVE_FEEDBACK_RATE,
            "synthetic.timestamp": execution_start.isoformat(),
            "synthetic.source": "lambda",
            "synthetic.handler": "langgraph",
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
        "handler": "langgraph",
        "results": results,
    }

    logger.info(
        f"[LangGraph] Complete: {success_count}/{ITERATIONS} successful, "
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
            "function_name": "synthetic-traffic-test",
            "remaining_time_in_millis": lambda: 900000,
        },
    )()

    result = lambda_handler(test_event, test_context)
    print(json.dumps(json.loads(result["body"]), indent=2))
