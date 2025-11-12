#!/usr/bin/env python3
"""
FastAPI server for the multi-agent medical insurance support system.
Provides REST API endpoints for the ToggleHealth UI.
"""
import os
import sys
import asyncio
import json
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Import your workflow
from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile

# Load environment
load_dotenv()

app = FastAPI(title="ToggleHealth Multi-Agent API")

# Enable CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class ChatRequest(BaseModel):
    aiConfigKey: str
    userInput: str
    bypassResponse: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    modelName: str
    enabled: bool
    requestId: str
    metrics: Optional[Dict[str, Any]] = None
    pendingMetrics: bool = False
    error: Optional[str] = None
    agentFlow: Optional[list] = None  # Track agent execution flow

class FeedbackRequest(BaseModel):
    feedback: str
    aiConfigKey: str

# Global storage for status updates
AGENT_STATUS: Dict[str, Dict[str, Any]] = {}
EVAL_RESULTS: Dict[str, Dict[str, Any]] = {}


def create_togglehealth_context(user_input: str) -> dict:
    """
    Create user context for ToggleHealth chatbot.
    Uses the rich user profile from your user_profile.py
    """
    # Create comprehensive user profile
    profile = create_user_profile(
        name="Marek Poliks",
        location="San Francisco, CA",
        policy_id="TH-HMO-GOLD-2024",
        coverage_type="Gold HMO"
    )
    
    # Add session ID
    profile["session_id"] = f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    profile["user_key"] = f"marek-poliks-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    return profile


async def track_agent_progress(request_id: str, agent_name: str, status: str, details: Optional[dict] = None):
    """Track which agent is currently working"""
    if request_id not in AGENT_STATUS:
        AGENT_STATUS[request_id] = {"flow": [], "current": None}
    
    AGENT_STATUS[request_id]["flow"].append({
        "agent": agent_name,
        "status": status,
        "timestamp": datetime.now().isoformat(),
        "details": details or {}
    })
    
    if status == "working":
        AGENT_STATUS[request_id]["current"] = agent_name
    elif status == "completed":
        AGENT_STATUS[request_id]["current"] = None


@app.post("/api/chat-multiagent", response_model=ChatResponse)
async def chat_multiagent(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Multi-agent healthcare support chatbot endpoint.
    
    Flow: Triage → Specialist (+ RAG) → Brand Voice → Evaluation
    """
    request_id = str(uuid4())
    
    try:
        # Create user context
        user_context = create_togglehealth_context(request.userInput)
        
        # Track that we're starting triage
        await track_agent_progress(request_id, "triage", "working")
        
        # Run the multi-agent workflow
        result = run_workflow(
            user_message=request.userInput,
            user_context=user_context
        )
        
        # Extract agent flow for UI
        agent_flow = []
        
        # Triage completed
        agent_flow.append({
            "agent": "triage",
            "status": "completed",
            "details": {
                "routed_to": str(result.get("query_type", "unknown")),
                "confidence": result.get("confidence", 0.0)
            }
        })
        
        # Specialist agent
        agent_data = result.get("agent_data", {})
        specialist_name = None
        rag_docs_count = 0
        
        for agent_key in ["policy_specialist", "provider_specialist", "scheduler_specialist"]:
            if agent_key in agent_data:
                specialist_name = agent_key
                rag_docs_count = agent_data[agent_key].get("rag_documents_retrieved", 0)
                agent_flow.append({
                    "agent": specialist_name,
                    "status": "completed",
                    "details": {
                        "rag_documents": rag_docs_count
                    }
                })
                break
        
        # Brand voice agent
        if "brand_voice" in agent_data:
            agent_flow.append({
                "agent": "brand_voice",
                "status": "completed",
                "details": {}
            })
        
        # Start evaluation in background
        if specialist_name and rag_docs_count > 0:
            rag_documents = agent_data.get(specialist_name, {}).get("rag_documents", [])
            background_tasks.add_task(
                run_evaluation_async,
                request_id=request_id,
                original_query=request.userInput,
                rag_documents=rag_documents,
                final_output=result.get("final_response", ""),
                user_context=user_context
            )
        
        # Extract metrics from result (if available)
        metrics = {
            "query_type": str(result.get("query_type", "")),
            "confidence": result.get("confidence", 0.0),
            "rag_documents_retrieved": rag_docs_count,
            "agents_invoked": len(agent_flow)
        }
        
        # Determine model name (extract from agent configs if available)
        model_name = "Multi-Agent System"
        
        return ChatResponse(
            response=result.get("final_response", "I apologize, but I couldn't process your request."),
            modelName=model_name,
            enabled=True,
            requestId=request_id,
            metrics=metrics,
            pendingMetrics=rag_docs_count > 0,  # Evaluation pending if RAG was used
            agentFlow=agent_flow
        )
        
    except Exception as e:
        print(f"Error in chat_multiagent: {e}")
        import traceback
        traceback.print_exc()
        
        return ChatResponse(
            response="I apologize, but an error occurred processing your request. Please try again.",
            modelName="Error",
            enabled=True,
            requestId=request_id,
            error=str(e)
        )


async def run_evaluation_async(
    request_id: str,
    original_query: str,
    rag_documents: list,
    final_output: str,
    user_context: dict
):
    """Run G-Eval evaluation in background"""
    try:
        # Import evaluation here to avoid circular imports
        from src.evaluation.judge import Judge
        from src.utils.launchdarkly_config import get_ld_client
        
        # Get LaunchDarkly client for evaluation
        ld_client = get_ld_client()
        
        # Create judge
        judge = Judge()
        
        # Run evaluation (no tracker since this is API-only)
        # The judge will call LaunchDarkly internally
        eval_result = await judge.evaluate_async(
            original_query=original_query,
            rag_documents=rag_documents,
            brand_voice_output=final_output,
            user_context=user_context,
            brand_tracker=None  # No tracker for API-only mode
        )
        
        # Store results
        EVAL_RESULTS[request_id] = {
            "accuracy": eval_result.get("accuracy", {}),
            "coherence": eval_result.get("coherence", {}),
            "overall_passed": eval_result.get("overall_passed", False)
        }
        
        print(f"Evaluation completed for request {request_id}")
        
    except Exception as e:
        print(f"Evaluation error for request {request_id}: {e}")
        import traceback
        traceback.print_exc()
        EVAL_RESULTS[request_id] = {"error": str(e)}


@app.get("/api/chat-metrics")
async def get_chat_metrics(request_id: str):
    """Get evaluation metrics for a chat request"""
    if request_id not in EVAL_RESULTS:
        return {"status": "unknown"}
    
    result = EVAL_RESULTS.get(request_id)
    if result is None:
        return {"status": "pending"}
    
    return {"status": "ready", "metrics": EVAL_RESULTS.pop(request_id)}


@app.get("/api/agent-status")
async def get_agent_status(request_id: str):
    """Get current agent status for real-time UI updates"""
    if request_id not in AGENT_STATUS:
        return {"status": "unknown"}
    
    return AGENT_STATUS[request_id]


@app.post("/api/chatbotfeedback")
async def feedback_endpoint(request: FeedbackRequest):
    """Feedback endpoint for thumbs up/down"""
    try:
        # TODO: Integrate with LaunchDarkly feedback tracking if needed
        print(f"Feedback received: {request.feedback} for {request.aiConfigKey}")
        return {"status": "success", "message": "Feedback received"}
    except Exception as e:
        return {"error": str(e)}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "ToggleHealth Multi-Agent API",
        "agents": ["triage", "policy", "provider", "scheduler", "brand_voice"],
        "evaluation": "G-Eval (accuracy + coherence)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)  # Different port from existing backend

