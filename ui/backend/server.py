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

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global store for evaluation results (populated by evaluation module)
EVALUATION_RESULTS: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="ToggleHealth Multi-Agent Assistant")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        
        # Track agent start times for duration calculation
        agent_timings = {}
        current_agent_start = time.time()
        
        # Run workflow
        result = await asyncio.to_thread(
            run_workflow,
            user_message=request.userInput,
            user_context=user_context
        )
        
        total_duration = int((time.time() - start_time) * 1000)  # ms
        
        # Extract response
        final_response = result.get("final_response", "I'm sorry, I couldn't process your request.")
        
        # Build agent flow for UI with timing data
        agent_flow = []
        query_type = result.get("query_type", "UNKNOWN")
        agent_data = result.get("agent_data", {})
        confidence = result.get("confidence_score", 0)
        
        # Triage - estimate duration and get tokens
        triage_duration = int(total_duration * 0.1)  # ~10% of time
        triage_tokens = agent_data.get("triage_router", {}).get("tokens", {"input": 0, "output": 0})
        agent_flow.append({
            "agent": "triage_router",
            "name": "Triage Router",
            "status": "complete",
            "confidence": float(confidence) if confidence else 0.0,
            "icon": "🔍",
            "duration": triage_duration,
            "tokens": triage_tokens
        })
        
        # Specialist
        specialist_duration = int(total_duration * 0.6)  # ~60% of time
        if "policy_specialist" in agent_data:
            policy_data = agent_data["policy_specialist"]
            rag_docs = policy_data.get("rag_documents_retrieved", 0)
            tokens = policy_data.get("tokens", {"input": 0, "output": 0})
            agent_flow.append({
                "agent": "policy_specialist",
                "name": "Policy Specialist",
                "status": "complete",
                "rag_docs": rag_docs,
                "icon": "📋",
                "duration": specialist_duration,
                "tokens": tokens
            })
        elif "provider_specialist" in agent_data:
            provider_data = agent_data["provider_specialist"]
            rag_docs = provider_data.get("rag_documents_retrieved", 0)
            tokens = provider_data.get("tokens", {"input": 0, "output": 0})
            agent_flow.append({
                "agent": "provider_specialist",
                "name": "Provider Specialist",
                "status": "complete",
                "rag_docs": rag_docs,
                "icon": "🏥",
                "duration": specialist_duration,
                "tokens": tokens
            })
        elif "scheduler_specialist" in agent_data:
            agent_flow.append({
                "agent": "scheduler_specialist",
                "name": "Scheduler Specialist",
                "status": "complete",
                "icon": "📅",
                "duration": specialist_duration,
                "tokens": {"input": 0, "output": 0}
            })
        
        # Brand voice - estimate duration and get tokens
        brand_duration = int(total_duration * 0.3)  # ~30% of time
        if "brand_voice" in agent_data:
            brand_tokens = agent_data["brand_voice"].get("tokens", {"input": 0, "output": 0})
            agent_flow.append({
                "agent": "brand_voice",
                "name": "Brand Voice",
                "status": "complete",
                "icon": "✨",
                "duration": brand_duration,
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
