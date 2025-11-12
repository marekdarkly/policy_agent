"""
FastAPI server for ToggleHealth Multi-Agent Chatbot UI with full metrics support
"""
import os
import sys
import asyncio
import logging
import time
from typing import Dict, Any, Optional
from pathlib import Path
from uuid import uuid4

# Add project root to path FIRST
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# CRITICAL: Initialize observability BEFORE any LLM imports
# This must happen before importing workflow, agents, or any LLM-related modules
from src.utils.observability import initialize_observability
# Environment must match LaunchDarkly environment for proper correlation
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

# Now safe to import FastAPI and other modules
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import uvicorn
import queue
import json
from datetime import datetime

# Import LLM-related modules AFTER observability setup
from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile
from ldai.tracker import FeedbackKind

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global store for evaluation results (populated by evaluation module)
EVALUATION_RESULTS: Dict[str, Dict[str, Any]] = {}

# Track which evaluations we've logged polling for (to reduce noise)
POLLING_LOGGED: set = set()

# Store brand voice trackers for feedback (keyed by request_id)
# Trackers are needed to send feedback to LaunchDarkly
BRAND_TRACKERS: Dict[str, Any] = {}

# Global log broadcaster for SSE
LOG_QUEUES: list[queue.Queue] = []

def should_broadcast_log(message: str, level: str) -> bool:
    """Filter logs to only broadcast important events to the UI terminal.
    
    SHOW:
    - RAG operations (retrieval, results)
    - Agent lifecycle (starting, completion)
    - User queries and responses
    - Errors and warnings
    - Evaluation results
    
    HIDE:
    - AWS token loading/caching
    - Model caching
    - LaunchDarkly config retrieval (routine)
    - Instrumentation setup
    - HTTP request logging
    """
    # Always show errors and warnings
    if level in ["ERROR", "WARNING", "CRITICAL"]:
        return True
    
    message_lower = message.lower()
    
    # HIDE: Noise we don't want
    hide_patterns = [
        "loading cached sso token",
        "bedrock client cached",
        "aws credentials valid",
        "retrieved ai config",
        "✅ set ld.ai_config.key",
        "✅ added feature_flag event",
        "✅ triggered ld variation",
        "instrumentation",
        "http request:",
        "waiting for application",
        "started server process",
        "application startup complete",
    ]
    
    for pattern in hide_patterns:
        if pattern in message_lower:
            return False
    
    # SHOW: Important events
    show_patterns = [
        "🔍",  # RAG retrieval
        "📚",  # RAG documents
        "📄",  # Document results
        "retrieved",  # RAG retrieval
        "rag documents",
        "retrieving",
        "chat request:",
        "response generated:",
        "policy specialist:",
        "provider specialist:",
        "scheduler specialist:",
        "triage",
        "brand voice",
        "evaluation",
        "accuracy:",
        "coherence:",
        "g-eval",
    ]
    
    for pattern in show_patterns:
        if pattern in message_lower:
            return True
    
    # Default: hide routine INFO logs, show everything else
    return level != "INFO"

def broadcast_log(log_entry: Dict[str, Any]):
    """Broadcast a log entry to all connected SSE clients (with filtering)."""
    # Filter logs before broadcasting
    if not should_broadcast_log(log_entry.get("message", ""), log_entry.get("level", "")):
        return
    
    # Remove disconnected queues
    disconnected = []
    for q in LOG_QUEUES:
        try:
            q.put_nowait(log_entry)
        except queue.Full:
            disconnected.append(q)
    
    for q in disconnected:
        LOG_QUEUES.remove(q)

# Custom logging handler to capture logs for SSE
class SSELogHandler(logging.Handler):
    """Custom handler that broadcasts logs to SSE clients."""
    
    def emit(self, record):
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": record.levelname,
                "message": self.format(record),
                "name": record.name
            }
            broadcast_log(log_entry)
        except Exception:
            pass  # Don't let logging errors break the app

# Add SSE handler to root logger
sse_handler = SSELogHandler()
sse_handler.setLevel(logging.INFO)
sse_handler.setFormatter(logging.Formatter('%(message)s'))
logging.getLogger().addHandler(sse_handler)

# Intercept print statements to also broadcast them
_original_print = print
def custom_print(*args, **kwargs):
    """Custom print that also broadcasts to SSE clients."""
    # Call original print
    _original_print(*args, **kwargs)
    
    # Broadcast to SSE (only if clients are connected)
    if LOG_QUEUES:  # Only broadcast if there are listeners
        message = ' '.join(str(arg) for arg in args)
        if message.strip():  # Only broadcast non-empty messages
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "level": "PRINT",
                "message": message,
                "name": "system"
            }
            broadcast_log(log_entry)

# Replace built-in print
import builtins
builtins.print = custom_print

app = FastAPI(title="ToggleHealth Multi-Agent Assistant")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instrument FastAPI for observability (CRITICAL: Ensures FastAPI/ASGI request spans exist as parents for LLM spans)
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor().instrument_app(app)
    logger.info("✅ FastAPI instrumented for observability (parent spans for LLM correlation)")
except Exception as e:
    logger.warning(f"⚠️  Failed to instrument FastAPI: {e}")


# Pydantic models
class ChatRequest(BaseModel):
    userInput: str
    userName: Optional[str] = "Marek Poliks"
    location: Optional[str] = "San Francisco, CA"
    policyId: Optional[str] = "TH-HMO-GOLD-2024"
    coverageType: Optional[str] = "Gold HMO"


class ChatResponse(BaseModel):
    response: str
    requestId: str
    agentFlow: list[Dict[str, Any]] = []
    metrics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class FeedbackRequest(BaseModel):
    requestId: str
    feedback: str  # 'positive' or 'negative'


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """
    Main chat endpoint for multi-agent system with full metrics tracking.
    """
    request_id = str(uuid4())
    start_time = time.time()
    
    try:
        logger.info(f"[{request_id}] Chat request: {request.userInput[:100]}...")
        
        # Create user context
        user_context = create_user_profile(
            name=request.userName,
            location=request.location,
            policy_id=request.policyId,
            coverage_type=request.coverageType
        )
        
        # Span correlation now happens per-agent in ModelInvoker (see launchdarkly_config.py)
        # Each agent (triage, policy, provider, brand) sets its own ld.ai_config.key
        # This allows each config's spans to appear in its respective Monitoring tab
        
        # Track agent start times for duration calculation
        agent_timings = {}
        current_agent_start = time.time()
        request_id = str(uuid4())
        
        # Run workflow with request_id, evaluation store, and tracker store
        result = await asyncio.to_thread(
            run_workflow,
            user_message=request.userInput,
            user_context=user_context,
            request_id=request_id,
            evaluation_results_store=EVALUATION_RESULTS,
            brand_trackers_store=BRAND_TRACKERS
        )
        
        total_duration = int((time.time() - start_time) * 1000)  # ms
        
        # Extract response
        final_response = result.get("final_response", "I'm sorry, I couldn't process your request.")
        
        # Build agent flow for UI with timing data
        agent_flow = []
        query_type = result.get("query_type", "UNKNOWN")
        agent_data = result.get("agent_data", {})
        confidence = result.get("confidence_score", 0)
        
        # Triage - estimate duration and get tokens + TTFT
        triage_duration = int(total_duration * 0.1)  # ~10% of time
        triage_data = agent_data.get("triage_router", {})
        triage_tokens = triage_data.get("tokens", {"input": 0, "output": 0})
        triage_ttft = triage_data.get("ttft_ms")
        agent_flow.append({
            "agent": "triage_router",
            "name": "Triage Router",
            "status": "complete",
            "confidence": float(confidence) if confidence else 0.0,
            "icon": "🔍",
            "duration": triage_duration,
            "ttft_ms": triage_ttft,  # Time to first token from streaming
            "tokens": triage_tokens
        })
        
        # Specialist
        specialist_duration = int(total_duration * 0.6)  # ~60% of time
        if "policy_specialist" in agent_data:
            policy_data = agent_data["policy_specialist"]
            rag_docs = policy_data.get("rag_documents_retrieved", 0)
            tokens = policy_data.get("tokens", {"input": 0, "output": 0})
            ttft_ms = policy_data.get("ttft_ms")
            agent_flow.append({
                "agent": "policy_specialist",
                "name": "Policy Specialist",
                "status": "complete",
                "rag_docs": rag_docs,
                "icon": "📋",
                "duration": specialist_duration,
                "ttft_ms": ttft_ms,  # Time to first token from streaming
                "tokens": tokens
            })
        elif "provider_specialist" in agent_data:
            provider_data = agent_data["provider_specialist"]
            rag_docs = provider_data.get("rag_documents_retrieved", 0)
            tokens = provider_data.get("tokens", {"input": 0, "output": 0})
            ttft_ms = provider_data.get("ttft_ms")
            agent_flow.append({
                "agent": "provider_specialist",
                "name": "Provider Specialist",
                "status": "complete",
                "rag_docs": rag_docs,
                "icon": "🏥",
                "duration": specialist_duration,
                "ttft_ms": ttft_ms,  # Time to first token from streaming
                "tokens": tokens
            })
        elif "scheduler_specialist" in agent_data:
            scheduler_data = agent_data.get("scheduler_specialist", {})
            ttft_ms = scheduler_data.get("ttft_ms")
            agent_flow.append({
                "agent": "scheduler_specialist",
                "name": "Scheduler Specialist",
                "status": "complete",
                "icon": "📅",
                "duration": specialist_duration,
                "ttft_ms": ttft_ms,  # Time to first token from streaming
                "tokens": {"input": 0, "output": 0}
            })
        
        # Brand voice - estimate duration and get tokens + TTFT
        brand_duration = int(total_duration * 0.3)  # ~30% of time
        if "brand_voice" in agent_data:
            brand_data_info = agent_data["brand_voice"]
            brand_tokens = brand_data_info.get("tokens", {"input": 0, "output": 0})
            brand_ttft = brand_data_info.get("ttft_ms")
            agent_flow.append({
                "agent": "brand_voice",
                "name": "Brand Voice",
                "status": "complete",
                "icon": "✨",
                "duration": brand_duration,
                "ttft_ms": brand_ttft,  # Time to first token from streaming
                "tokens": brand_tokens
            })
        
        # Check for evaluation results from global store
        eval_data = agent_data.get("evaluation", {})
        
        # Build comprehensive metrics
        metrics = {
            "query_type": str(query_type),
            "confidence": float(confidence) if confidence else 0.0,
            "agent_count": len(agent_flow),
            "rag_enabled": any(a.get("rag_docs", 0) > 0 for a in agent_flow),
            "total_duration_ms": total_duration
        }
        
        # Add evaluation metrics if available
        if eval_data:
            metrics["accuracy_score"] = eval_data.get("accuracy_score")
            metrics["accuracy_reasoning"] = eval_data.get("accuracy_reasoning")
            metrics["accuracy_issues"] = eval_data.get("accuracy_issues", [])
            metrics["coherence_score"] = eval_data.get("coherence_score")
            metrics["coherence_reasoning"] = eval_data.get("coherence_reasoning")
            metrics["coherence_issues"] = eval_data.get("coherence_issues", [])
            metrics["judge_model_name"] = eval_data.get("judge_model_name")
            metrics["judge_input_tokens"] = eval_data.get("judge_input_tokens")
            metrics["judge_output_tokens"] = eval_data.get("judge_output_tokens")
        
        logger.info(f"[{request_id}] Response generated: {len(final_response)} chars, {len(agent_flow)} agents, {total_duration}ms")
        
        return ChatResponse(
            response=final_response,
            requestId=request_id,
            agentFlow=agent_flow,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"[{request_id}] Error in chat endpoint: {e}", exc_info=True)
        return ChatResponse(
            response="I'm sorry, an error occurred while processing your request. Please try again.",
            requestId=request_id,
            agentFlow=[],
            error=str(e)
        )


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ToggleHealth Multi-Agent Assistant"}


@app.get("/api/evaluation/{request_id}")
async def get_evaluation(request_id: str):
    """
    Check if evaluation results are ready for a given request_id.
    Returns evaluation results if available, or status indicating still processing.
    """
    # Only log the first time we start polling for this request
    if request_id not in POLLING_LOGGED:
        logger.info(f"[{request_id}] ⏳ Starting to poll for evaluation results...")
        POLLING_LOGGED.add(request_id)
    
    if request_id in EVALUATION_RESULTS:
        eval_data = EVALUATION_RESULTS[request_id]
        logger.info(f"[{request_id}] ✅ Evaluation complete!")
        logger.info(f"[{request_id}]    Accuracy: {eval_data.get('accuracy', {}).get('score', 'N/A')}")
        logger.info(f"[{request_id}]    Coherence: {eval_data.get('coherence', {}).get('score', 'N/A')}")
        
        # Clean up
        del EVALUATION_RESULTS[request_id]
        POLLING_LOGGED.discard(request_id)
        
        return {
            "ready": True,
            "evaluation": eval_data
        }
    else:
        # Don't log every poll attempt, only the first one
        return {
            "ready": False,
            "message": "Evaluation still processing or not found"
        }


@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback (positive/negative) for a brand voice response.
    Sends the feedback to LaunchDarkly for tracking in the AI Config Monitoring tab.
    """
    request_id = request.requestId
    feedback_type = request.feedback
    
    logger.info(f"[{request_id}] 📝 Received feedback: {feedback_type}")
    
    # Retrieve the brand voice tracker for this request
    if request_id not in BRAND_TRACKERS:
        logger.warning(f"[{request_id}] ⚠️  No tracker found for request (may have expired)")
        raise HTTPException(status_code=404, detail="Request not found or expired")
    
    tracker = BRAND_TRACKERS[request_id]
    
    # Track feedback in LaunchDarkly
    try:
        feedback_kind = FeedbackKind.Positive if feedback_type == 'positive' else FeedbackKind.Negative
        tracker.track_feedback({'kind': feedback_kind})
        logger.info(f"[{request_id}] ✅ Feedback tracked in LaunchDarkly: {feedback_type}")
        
        # Flush to ensure immediate delivery
        from ldclient import get as get_ld_client
        get_ld_client().flush()
        
        # Clean up tracker after feedback is sent (optional)
        del BRAND_TRACKERS[request_id]
        
        return {
            "success": True,
            "message": f"Feedback ({feedback_type}) recorded successfully"
        }
    except Exception as e:
        logger.error(f"[{request_id}] ❌ Failed to track feedback: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to track feedback: {str(e)}")


@app.get("/api/logs/stream")
async def stream_logs():
    """
    Server-Sent Events endpoint for streaming logs to the frontend.
    Keeps connection open and sends log entries as they occur.
    """
    async def event_generator():
        # Create a queue for this client
        log_queue = queue.Queue(maxsize=1000)
        LOG_QUEUES.append(log_queue)
        
        try:
            # Send initial connection message
            init_message = {
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "🔌 Connected to log stream",
                "name": "sse"
            }
            yield f"data: {json.dumps(init_message)}\n\n"
            
            # Stream logs as they come in
            heartbeat_counter = 0
            while True:
                try:
                    # Non-blocking check for new logs
                    log_entry = log_queue.get_nowait()
                    yield f"data: {json.dumps(log_entry)}\n\n"
                    heartbeat_counter = 0  # Reset heartbeat counter
                except queue.Empty:
                    # No logs available, sleep briefly
                    await asyncio.sleep(0.1)
                    heartbeat_counter += 1
                    
                    # Send heartbeat every 30 seconds (300 * 0.1s)
                    if heartbeat_counter >= 300:
                        heartbeat = {
                            "timestamp": datetime.now().isoformat(),
                            "level": "HEARTBEAT",
                            "message": "",
                            "name": "sse"
                        }
                        yield f"data: {json.dumps(heartbeat)}\n\n"
                        heartbeat_counter = 0
        except asyncio.CancelledError:
            # Client disconnected
            if log_queue in LOG_QUEUES:
                LOG_QUEUES.remove(log_queue)
            raise
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║  ToggleHealth Multi-Agent Assistant API                      ║
    ║  Server starting on http://localhost:8000                    ║
    ║  API Docs: http://localhost:8000/docs                        ║
    ║  Features: Full metrics, timing, eval scores                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)
