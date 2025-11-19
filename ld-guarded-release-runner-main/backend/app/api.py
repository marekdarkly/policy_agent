from fastapi import APIRouter, Depends, HTTPException, Response, Request
from pydantic import BaseModel
import httpx
import logging
from typing import Dict, Any, Optional
import time

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ld-api-proxy", tags=["LaunchDarkly API Proxy"])

# Track API requests per session
session_request_counts: Dict[str, int] = {}
session_last_reset: Dict[str, float] = {}
REQUEST_LIMIT_PER_MINUTE = 60  # Limit API requests per session

class ProxyRequest(BaseModel):
    url: str
    method: str
    payload: dict
    api_key: str
    session_id: str  # Add session ID for identifying client sessions
    headers: dict = None

# Add specific OPTIONS handler for the proxy endpoint with manual CORS headers
@router.options("/proxy")
async def options_proxy(request: Request):
    logger.info("OPTIONS request received for /ld-api-proxy/proxy")
    response = Response(status_code=200)
    # Set CORS headers manually
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    logger.info(f"Returning OPTIONS response with headers: {dict(response.headers)}")
    return response

def check_rate_limit(session_id: str) -> bool:
    """Check if a session has exceeded its rate limit"""
    current_time = time.time()
    
    # Initialize tracking for new sessions
    if session_id not in session_request_counts:
        session_request_counts[session_id] = 0
        session_last_reset[session_id] = current_time
    
    # Reset counter if more than a minute has passed
    if current_time - session_last_reset[session_id] > 60:
        session_request_counts[session_id] = 0
        session_last_reset[session_id] = current_time
    
    # Check if limit is exceeded
    if session_request_counts[session_id] >= REQUEST_LIMIT_PER_MINUTE:
        return False
    
    # Increment the counter
    session_request_counts[session_id] += 1
    return True

@router.post("/proxy")
async def proxy_launchdarkly_request(request: ProxyRequest):
    """
    Proxy requests to LaunchDarkly API to avoid CORS issues
    """
    try:
        # Rate limit check
        if not check_rate_limit(request.session_id):
            raise HTTPException(
                status_code=429, 
                detail=f"Rate limit exceeded for session {request.session_id}. Max {REQUEST_LIMIT_PER_MINUTE} requests per minute."
            )
        
        # Create headers with the provided API key
        headers = {
            "Authorization": request.api_key,
            "Content-Type": "application/json"
        }
        
        # Add any custom headers provided in the request
        if request.headers:
            headers.update(request.headers)
        
        logger.info(f"Proxying request for session {request.session_id}: {request.method} {request.url}")
        
        # Make the request
        async with httpx.AsyncClient() as client:
            if request.method.lower() == "get":
                response = await client.get(
                    request.url,
                    headers=headers,
                    timeout=30.0
                )
            elif request.method.lower() == "post":
                response = await client.post(
                    request.url,
                    headers=headers,
                    json=request.payload,
                    timeout=30.0
                )
            elif request.method.lower() == "put":
                response = await client.put(
                    request.url,
                    headers=headers,
                    json=request.payload,
                    timeout=30.0
                )
            elif request.method.lower() == "delete":
                response = await client.delete(
                    request.url,
                    headers=headers,
                    timeout=30.0
                )
            else:
                raise HTTPException(status_code=400, detail=f"Unsupported method: {request.method}")
            
        # Return the response data
        response_data = {
            "status_code": response.status_code,
            "data": response.json() if response.text else None,
            "success": response.status_code < 400,
            "headers": dict(response.headers),
            "url": response.url
        }
        
        logger.info(f"Response status code for session {request.session_id}: {response.status_code}")
        
        return response_data
    except httpx.RequestError as e:
        logger.error(f"Request error for session {request.session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Request error: {str(e)}")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error for session {request.session_id}: {str(e)}")
        raise HTTPException(status_code=e.response.status_code, detail=f"HTTP error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error for session {request.session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}") 