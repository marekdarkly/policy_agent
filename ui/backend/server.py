"""
FastAPI server for ToggleHealth Multi-Agent Chatbot UI
"""
import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    Main chat endpoint for multi-agent system.
    """
    try:
        logger.info(f"Chat request: {request.userInput[:100]}...")
        
        # Create user context
        user_context = create_user_profile(
            name=request.userName,
            location=request.location,
            policy_id=request.policyId,
            coverage_type=request.coverageType
        )
        
        # Run workflow
        result = await asyncio.to_thread(
            run_workflow,
            user_message=request.userInput,
            user_context=user_context
        )
        
        # Extract response
        final_response = result.get("final_response", "I'm sorry, I couldn't process your request.")
        
        # Build agent flow for UI
        agent_flow = []
        query_type = result.get("query_type", "UNKNOWN")
        agent_data = result.get("agent_data", {})
        confidence = result.get("confidence", 0)
        
        # Triage
        agent_flow.append({
            "agent": "triage_router",
            "name": "Triage Router",
            "status": "complete",
            "confidence": float(confidence) if confidence else 0.0,
            "icon": "🔍"
        })
        
        # Specialist
        if "policy_specialist" in agent_data:
            rag_docs = agent_data["policy_specialist"].get("rag_documents_retrieved", 0)
            agent_flow.append({
                "agent": "policy_specialist",
                "name": "Policy Specialist",
                "status": "complete",
                "rag_docs": rag_docs,
                "icon": "📋"
            })
        elif "provider_specialist" in agent_data:
            rag_docs = agent_data["provider_specialist"].get("rag_documents_retrieved", 0)
            agent_flow.append({
                "agent": "provider_specialist",
                "name": "Provider Specialist",
                "status": "complete",
                "rag_docs": rag_docs,
                "icon": "🏥"
            })
        elif "scheduler_specialist" in agent_data:
            agent_flow.append({
                "agent": "scheduler_specialist",
                "name": "Scheduler Specialist",
                "status": "complete",
                "icon": "📅"
            })
        
        # Brand voice
        if "brand_voice" in agent_data:
            agent_flow.append({
                "agent": "brand_voice",
                "name": "Brand Voice",
                "status": "complete",
                "icon": "✨"
            })
        
        # Build metrics
        metrics = {
            "query_type": str(query_type),
            "confidence": float(confidence) if confidence else 0.0,
            "agent_count": len(agent_flow),
            "rag_enabled": any(a.get("rag_docs", 0) > 0 for a in agent_flow)
        }
        
        request_id = str(uuid4())
        
        logger.info(f"Response generated: {len(final_response)} chars, {len(agent_flow)} agents")
        
        return ChatResponse(
            response=final_response,
            requestId=request_id,
            agentFlow=agent_flow,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return ChatResponse(
            response="I'm sorry, an error occurred while processing your request. Please try again.",
            requestId=str(uuid4()),
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
    ╚══════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(app, host="0.0.0.0", port=8000)

