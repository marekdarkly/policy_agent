"""Brand voice synthesis agent for customer-facing responses."""

import asyncio
from typing import Any
import ldclient

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..graph.state import AgentState
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client
from ..evaluation.judge import evaluate_brand_voice_async


def calculate_model_cost(model_id: str, input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for a model based on token usage.
    
    Args:
        model_id: The model identifier (e.g., 'us.anthropic.claude-haiku-4-5-20251001-v1:0')
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        Total cost in dollars
    """
    # Pricing per 1000 tokens
    pricing = {
        "haiku": {"input": 0.001, "output": 0.005},
        "sonnet-4": {"input": 0.003, "output": 0.015},
        "llama4-maverick": {"input": 0.00024, "output": 0.00097},
        "nova-pro": {"input": 0.0008, "output": 0.0002},
    }
    
    # Determine model type from model_id
    model_lower = model_id.lower()
    if "haiku" in model_lower:
        rates = pricing["haiku"]
    elif "sonnet-4" in model_lower or "sonnet4" in model_lower:
        rates = pricing["sonnet-4"]
    elif "llama4" in model_lower or "maverick" in model_lower:
        rates = pricing["llama4-maverick"]
    elif "nova-pro" in model_lower:
        rates = pricing["nova-pro"]
    else:
        # Unknown model, return 0
        print(f"⚠️  Unknown model for cost calculation: {model_id}")
        return 0.0
    
    # Calculate cost (pricing is per 1000 tokens)
    input_cost = (input_tokens / 1000.0) * rates["input"]
    output_cost = (output_tokens / 1000.0) * rates["output"]
    total_cost = input_cost + output_cost
    
    return total_cost


def brand_voice_node(state: AgentState) -> dict[str, Any]:
    """Brand voice synthesis agent node.

    Takes the specialist's response and transforms it to match ToggleHealth's
    brand voice - friendly, empathetic, clear, and helpful.
    Uses prompts from LaunchDarkly AI Config.

    Args:
        state: Current agent state with specialist response

    Returns:
        Updated state with brand-voiced customer response
    """
    # Get the specialist's raw response (last message)
    messages = state["messages"]
    specialist_response = messages[-1].content if messages else ""

    # Get user context for personalization
    user_context = state.get("user_context", {})
    customer_name = user_context.get("name", "there")
    query_type = state.get("query_type", "unknown")
    
    # Get original customer query (first human message)
    original_query = ""
    for msg in messages:
        if isinstance(msg, HumanMessage):
            original_query = msg.content
            break

    # Get LLM and messages from LaunchDarkly AI Config
    model_invoker, ld_config = get_model_invoker(
        config_key="brand_agent",
        context=user_context,
        default_temperature=0.7,  # Slightly creative for natural language
    )
    
    # Log the variation being used
    variation_name = ld_config.get("_variation", "unknown")
    print(f"🎯 Brand Voice Agent using variation: '{variation_name}'")
    
    # Extract model ID from config for tracking
    model_id = ld_config.get("model", {}).get("name", "unknown")

    # Build LangChain messages from LaunchDarkly config (supports both agent-based and completion-based)
    ld_client = get_ld_client()
    context_vars = {
        **user_context,
        "customer_name": customer_name,
        "original_query": original_query,
        "query_type": str(query_type),
        "specialist_response": specialist_response,
    }
    langchain_messages = ld_client.build_langchain_messages(ld_config, context_vars)

    # Track start time for duration measurement
    import time
    start_time = time.time()
    
    response = model_invoker.invoke(langchain_messages)
    
    # Calculate duration
    duration_ms = int((time.time() - start_time) * 1000)

    # Extract token usage and TTFT if available
    tokens = {"input": 0, "output": 0}
    ttft_ms = None
    
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = {
            "input": response.usage_metadata.get("input_tokens", 0),
            "output": response.usage_metadata.get("output_tokens", 0)
        }
    
    # Extract Time to First Token (TTFT) from response metadata
    if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
        ttft_ms = response.response_metadata.get("ttft_ms")

    # Store the brand-voiced response
    final_response = response.content
    
    # Start async evaluation without blocking (fire-and-forget)
    # This evaluates GLOBAL SYSTEM ACCURACY against RAG documents
    try:
        # Get RAG documents from agent_data (stored by specialist)
        agent_data = state.get("agent_data", {})
        rag_documents = []
        
        # Extract RAG docs from whichever specialist ran
        for specialist in ["policy_specialist", "provider_specialist"]:
            if specialist in agent_data:
                rag_docs = agent_data[specialist].get("rag_documents", [])
                if rag_docs:
                    rag_documents = rag_docs
                    break
        
        # Get request_id and results_store from state for evaluation tracking
        request_id = state.get("request_id")
        results_store = state.get("evaluation_results_store")
        
        # Store the brand voice tracker for feedback tracking (if request_id available)
        trackers_store = state.get("brand_trackers_store")
        if request_id and trackers_store is not None:
            trackers_store[request_id] = model_invoker.tracker
            print(f"✅ Stored brand voice tracker for request {request_id[:8]}...")
        
        # Calculate and send cost metric for brand agent
        brand_cost_usd = calculate_model_cost(
            model_id=model_id,
            input_tokens=tokens["input"],
            output_tokens=tokens["output"]
        )
        
        # Convert to cents for better precision in LaunchDarkly metrics
        # Round to 2 decimal places (LaunchDarkly only accepts 2 decimal places)
        brand_cost_cents = round(brand_cost_usd * 100.0, 2)
        
        # Send cost metric to LaunchDarkly (in cents, rounded to 2 decimal places)
        try:
            from ldclient import Context
            ld_client = ldclient.get()
            
            # Build context from user_context
            user_key = user_context.get("user_key", "anonymous")
            context_builder = Context.builder(user_key).kind("user")
            if user_context.get("name"):
                context_builder.set("name", user_context["name"])
            ld_context = context_builder.build()
            
            # Send cost metric in cents (rounded to 2 decimal places)
            ld_client.track(
                event_name="$ld:ai:tokens:costmanual",
                context=ld_context,
                metric_value=float(brand_cost_cents)
            )
            
            print(f"💰 Brand agent cost: {brand_cost_cents:.2f}¢ (${brand_cost_usd:.6f}) [in={tokens['input']}, out={tokens['output']}, model={model_id.split(':')[0].split('.')[-1]}]")
        except Exception as e:
            print(f"⚠️  Failed to send cost metric: {e}")
        
        # Handle both sync and async contexts
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we have a running loop, use create_task
            asyncio.create_task(
                evaluate_brand_voice_async(
                    original_query=original_query,
                    rag_documents=rag_documents,
                    brand_voice_output=final_response,
                    user_context=user_context,
                    brand_tracker=model_invoker.tracker,
                    request_id=request_id,
                    results_store=results_store
                )
            )
        except RuntimeError:
            # No running loop - we're in a sync context
            # Run evaluation in a background thread to avoid blocking
            import threading
            
            def run_eval_in_thread():
                asyncio.run(
                    evaluate_brand_voice_async(
                        original_query=original_query,
                        rag_documents=rag_documents,
                        brand_voice_output=final_response,
                        user_context=user_context,
                        brand_tracker=model_invoker.tracker,
                        request_id=request_id,
                        results_store=results_store
                    )
                )
            
            thread = threading.Thread(target=run_eval_in_thread, daemon=True)
            thread.start()
        
        print(f"🔍 Background evaluation started (evaluating against {len(rag_documents)} RAG documents) - request_id: {request_id[:8] if request_id else 'N/A'}...")
    except Exception as e:
        # Never let evaluation errors affect the main flow
        print(f"⚠️  Failed to start background evaluation: {e}")

    # Add debug info to agent_data (store full responses for hallucination debugging)
    brand_data = {
        "model": model_id,  # Track which model was used
        "original_specialist_response": specialist_response[:500] + "..." if len(specialist_response) > 500 else specialist_response,
        "final_customer_response": final_response[:500] + "..." if len(final_response) > 500 else final_response,
        "brand_voice_applied": True,
        "tokens": tokens,
        "cost_usd": brand_cost_usd,  # Manual cost calculation for this agent in USD
        "cost_cents": brand_cost_cents,  # Cost in cents (sent to LaunchDarkly)
        "ttft_ms": ttft_ms,  # Time to first token from Bedrock streaming
        "duration_ms": duration_ms,  # Total time to generate response
        "personalization": {
            "customer_name": customer_name,
            "query_type": str(query_type),
        }
    }

    # Update agent_data
    updated_agent_data = state.get("agent_data", {}).copy()
    updated_agent_data["brand_voice"] = brand_data

    # Create the final customer message
    final_message = AIMessage(content=final_response)

    return {
        "messages": [final_message],
        "final_response": final_response,  # CRITICAL: Set this so the customer sees the brand-voiced response!
        "agent_data": updated_agent_data,
        "next_agent": "END",
    }
