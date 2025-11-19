from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status, BackgroundTasks, Request, Response, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional, Set
import asyncio
import json
import os
import uuid

from app.models import LDConfig, SimulationStatus, SessionRequest, LogsResponse
from app.simulation import (
    start_simulation, stop_simulation, get_simulation_status,
    register_websocket, unregister_websocket, send_status_to_clients, send_log_to_clients
)
from app.api import router as ld_api_router

# Initialize FastAPI app
app = FastAPI(
    title="LaunchDarkly Guarded Rollout Runner",
    description="A web application to simulate and send metric events to LaunchDarkly flags for Guarded Rollouts.",
    version="1.0.0"
)

# Add CORS middleware with maximum permissiveness
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
)

# Add a global OPTIONS route handler that returns a 200 response
@app.options("/{path:path}")
async def options_route(path: str):
    response = Response(status_code=200)
    # Manually add CORS headers to ensure they're correct
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Include the LaunchDarkly API proxy router
app.include_router(ld_api_router)

@app.get("/", tags=["Health"])
async def health_check():
    """Check if the API is running"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/session", tags=["Session"], response_model=Dict[str, str])
async def create_session():
    """Create a new session ID for the client"""
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

@app.post("/simulation/start", tags=["Simulation"], response_model=SimulationStatus)
async def api_start_simulation(config: LDConfig):
    """Start the simulation with the provided configuration"""
    # The session_id is now passed as part of the config
    await start_simulation(config.session_id, config)
    return get_simulation_status(config.session_id)

@app.post("/simulation/stop", tags=["Simulation"], response_model=SimulationStatus)
async def api_stop_simulation(request: SessionRequest):
    """Stop the simulation"""
    await stop_simulation(request.session_id)
    return get_simulation_status(request.session_id)

@app.get("/simulation/status", tags=["Simulation"], response_model=SimulationStatus)
async def api_get_status(session_id: str = Query(..., description="Session ID to get status for")):
    """Get the current simulation status"""
    return get_simulation_status(session_id)

@app.get("/simulation/logs", tags=["Simulation"], response_model=LogsResponse)
async def api_get_logs(
    session_id: str = Query(..., description="Session ID to get logs for"),
    limit: int = Query(100, description="Maximum number of logs to return", ge=1, le=1000),
    skip: int = Query(0, description="Number of logs to skip for pagination", ge=0)
):
    """Get stored logs for a specific session with pagination
    
    Args:
        session_id: The session ID to get logs for
        limit: Maximum number of logs to return (1-1000)
        skip: Number of logs to skip for pagination
        
    Returns:
        LogsResponse containing the logs, total count, and whether there are more logs
    """
    status = get_simulation_status(session_id)
    
    # Get total count of logs
    total_logs = status.total_logs_generated
    
    # Get stored logs with pagination
    stored_logs = status.stored_logs
    
    # Apply pagination
    paginated_logs = stored_logs[skip:skip+limit] if skip < len(stored_logs) else []
    
    # Convert logs to dictionaries
    log_dicts = [log.to_dict() for log in paginated_logs]
    
    # Check if there are more logs
    has_more = (skip + limit) < len(stored_logs)
    
    return LogsResponse(
        logs=log_dicts,
        total_count=total_logs,
        has_more=has_more
    )

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time updates for a specific session"""
    await websocket.accept()
    register_websocket(session_id, websocket)
    
    try:
        # Send current status when a client connects
        current_status = get_simulation_status(session_id)
        await websocket.send_text(json.dumps({
            "type": "status", 
            "data": current_status.model_dump()
        }))
        
        # Keep connection alive
        while True:
            # Wait for any message from client (can be used as a ping)
            await websocket.receive_text()
    except WebSocketDisconnect:
        # Client disconnected
        pass
    finally:
        unregister_websocket(session_id, websocket)
