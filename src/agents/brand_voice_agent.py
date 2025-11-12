"""Brand voice synthesis agent for customer-facing responses."""

import asyncio
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from ..graph.state import AgentState
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client
from ..evaluation.judge import evaluate_brand_voice_async


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

    response = model_invoker.invoke(langchain_messages)

    # Extract token usage if available
    tokens = {"input": 0, "output": 0}
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = {
            "input": response.usage_metadata.get("input_tokens", 0),
            "output": response.usage_metadata.get("output_tokens", 0)
        }

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
        "original_specialist_response": specialist_response[:500] + "..." if len(specialist_response) > 500 else specialist_response,
        "final_customer_response": final_response[:500] + "..." if len(final_response) > 500 else final_response,
        "brand_voice_applied": True,
        "tokens": tokens,
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
