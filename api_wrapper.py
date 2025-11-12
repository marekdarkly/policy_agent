"""
FastAPI wrapper for the multi-agent policy system.
Integrates with ToggleHealth UI frontend.
"""
import os
import sys
import asyncio
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from pydantic import BaseModel

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Pydantic models for API
class MultiAgentChatRequest(BaseModel):
    """Request model for multi-agent chat."""
    userInput: str
    aiConfigKey: str = "policy_multiagent"


class MultiAgentChatResponse(BaseModel):
    """Response model for multi-agent chat."""
    response: str
    modelName: str
    enabled: bool
    requestId: str
    agentFlow: list[Dict[str, str]] = []  # Track which agents ran
    metrics: Optional[Dict[str, Any]] = None
    pendingMetrics: bool = False
    error: Optional[str] = None


class AgentStatusUpdate(BaseModel):
    """Real-time status update during agent execution."""
    status: str  # "routing", "specialist", "brand_voice", "complete"
    agent: Optional[str] = None  # Which agent is running
    message: str  # User-friendly status message


def create_user_context_from_profile(user_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create user context for LaunchDarkly and workflow.
    Uses the existing user_profile.py create_user_profile function.
    
    Args:
        user_data: Optional user data from frontend (name, location, etc.)
    
    Returns:
        Dictionary of user context attributes
    """
    # Extract user data if provided, otherwise use defaults
    name = user_data.get("name", "Marek Poliks") if user_data else "Marek Poliks"
    location = user_data.get("location", "San Francisco, CA") if user_data else "San Francisco, CA"
    policy_id = user_data.get("policy_id", "TH-HMO-GOLD-2024") if user_data else "TH-HMO-GOLD-2024"
    coverage_type = user_data.get("coverage_type", "Gold HMO") if user_data else "Gold HMO"
    
    # Use the existing create_user_profile function
    profile = create_user_profile(
        name=name,
        location=location,
        policy_id=policy_id,
        coverage_type=coverage_type
    )
    
    return profile


async def run_workflow_with_status_updates(
    user_message: str,
    user_context: Dict[str, Any],
    status_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Run the multi-agent workflow with status updates.
    
    Args:
        user_message: User's query
        user_context: User context for personalization
        status_callback: Optional callback for status updates
    
    Returns:
        Workflow result dictionary
    """
    try:
        # Status: Routing
        if status_callback:
            await status_callback(AgentStatusUpdate(
                status="routing",
                agent="triage_router",
                message="Analyzing your question..."
            ))
        
        # Run the workflow (this is synchronous, so wrap in asyncio.to_thread)
        result = await asyncio.to_thread(
            run_workflow,
            user_message=user_message,
            user_context=user_context
        )
        
        # Extract which specialist ran from result
        query_type = result.get("query_type", "UNKNOWN")
        agent_data = result.get("agent_data", {})
        
        # Status: Specialist running
        if status_callback:
            specialist_name = None
            if "policy_specialist" in agent_data:
                specialist_name = "Policy Specialist"
            elif "provider_specialist" in agent_data:
                specialist_name = "Provider Specialist"
            elif "scheduler_specialist" in agent_data:
                specialist_name = "Scheduler Specialist"
            
            if specialist_name:
                await status_callback(AgentStatusUpdate(
                    status="specialist",
                    agent=specialist_name.lower().replace(" ", "_"),
                    message=f"Reaching out to {specialist_name}..."
                ))
        
        # Status: Brand voice
        if status_callback and "brand_voice" in agent_data:
            await status_callback(AgentStatusUpdate(
                status="brand_voice",
                agent="brand_voice",
                message="Putting an answer together..."
            ))
        
        # Status: Complete
        if status_callback:
            await status_callback(AgentStatusUpdate(
                status="complete",
                agent=None,
                message="Complete"
            ))
        
        return result
        
    except Exception as e:
        logger.error(f"Workflow error: {e}")
        raise


async def handle_multiagent_chat(request: MultiAgentChatRequest) -> MultiAgentChatResponse:
    """
    Handle multi-agent chat request.
    
    Args:
        request: Chat request with user input
    
    Returns:
        Chat response with agent flow and metrics
    """
    try:
        # Create user context from profile
        user_context = create_user_context_from_profile()
        
        # Run workflow (without status updates for initial implementation)
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
        
        # Triage
        agent_flow.append({
            "agent": "triage_router",
            "status": "complete",
            "confidence": str(result.get("confidence", 0))
        })
        
        # Specialist
        if "policy_specialist" in agent_data:
            agent_flow.append({
                "agent": "policy_specialist",
                "status": "complete",
                "rag_docs": str(agent_data["policy_specialist"].get("rag_documents_retrieved", 0))
            })
        elif "provider_specialist" in agent_data:
            agent_flow.append({
                "agent": "provider_specialist",
                "status": "complete",
                "rag_docs": str(agent_data["provider_specialist"].get("rag_documents_retrieved", 0))
            })
        elif "scheduler_specialist" in agent_data:
            agent_flow.append({
                "agent": "scheduler_specialist",
                "status": "complete"
            })
        
        # Brand voice
        if "brand_voice" in agent_data:
            agent_flow.append({
                "agent": "brand_voice",
                "status": "complete"
            })
        
        # Extract evaluation metrics if available
        metrics = {}
        # Note: Evaluation metrics will be added after judge runs
        # For now, we'll include basic info
        metrics["agent_flow"] = agent_flow
        metrics["query_type"] = str(query_type)
        
        # Determine model name (extract from agent data if available)
        model_name = "Multi-Agent System"
        
        request_id = str(uuid4())
        
        return MultiAgentChatResponse(
            response=final_response,
            modelName=model_name,
            enabled=True,
            requestId=request_id,
            agentFlow=agent_flow,
            metrics=metrics,
            pendingMetrics=False  # Set to True if we implement async evaluation
        )
        
    except Exception as e:
        logger.error(f"Error in multi-agent chat: {e}")
        return MultiAgentChatResponse(
            response="I'm sorry, an error occurred while processing your request.",
            modelName="",
            enabled=False,
            requestId=str(uuid4()),
            error=str(e)
        )


# Export for use in FastAPI app
__all__ = [
    "MultiAgentChatRequest",
    "MultiAgentChatResponse",
    "AgentStatusUpdate",
    "handle_multiagent_chat",
    "create_user_context_from_profile"
]

