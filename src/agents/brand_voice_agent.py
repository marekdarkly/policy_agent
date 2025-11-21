"""Brand voice synthesis agent for customer-facing responses."""

import asyncio
from typing import Any
import ldclient

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from ldai.client import AIConfig, ModelConfig, ProviderConfig, LDMessage

from ..graph.state import AgentState
from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client
from ..evaluation.judge import evaluate_brand_voice_async


# Default AI Config fallback for brand_agent
# This is used if LaunchDarkly is unavailable or the flag doesn't exist
DEFAULT_BRAND_VOICE_SYSTEM_PROMPT = """You are ToggleHealth's Brand Voice Agent. Transform the specialist's technical response into a warm, friendly, and personalized customer response.

**Brand Voice Guidelines:**
- **Friendly & Warm**: Use a conversational tone that makes customers feel valued
- **Empathetic**: Acknowledge customer concerns and emotions
- **Clear & Simple**: Avoid jargon; explain complex terms in plain language
- **Helpful**: Provide actionable next steps when appropriate
- **Professional**: Maintain trust while being approachable

**Context Variables:**
- Customer Name: {customer_name}
- Original Query: {original_query}
- Query Type: {query_type}
- Specialist Response: {specialist_response}

**Your Task:**
Transform the specialist's response into a customer-facing message that:
1. Addresses the customer by name (if appropriate)
2. Directly answers their question
3. Uses ToggleHealth's warm, friendly tone
4. Ends with a helpful closing (e.g., "Is there anything else I can help you with?")

Provide ONLY the final customer-facing response. Do not include meta-commentary."""

DEFAULT_BRAND_AGENT_CONFIG = AIConfig(
    enabled=True,
    model=ModelConfig(
        name="us.anthropic.claude-haiku-4-5-20251001-v1:0",
        parameters={"temperature": 0.7, "maxTokens": 2000}
    ),
    provider=ProviderConfig(name="bedrock"),
    messages=[LDMessage(role="system", content=DEFAULT_BRAND_VOICE_SYSTEM_PROMPT)]
)


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

    # Check if guardrail is enabled from state (UI toggle)
    guardrail_enabled = state.get("guardrail_enabled", True)
    
    # Get request_id from state for tracking
    request_id = state.get("request_id")
    
    # Get LLM and messages from LaunchDarkly AI Config (with fallback)
    print(f"\n{'─'*80}")
    print(f"🔍 BRAND VOICE AGENT: Crafting response")
    model_invoker, ld_config = get_model_invoker(
        config_key="brand_agent",
        context=user_context,
        default_temperature=0.7,  # Slightly creative for natural language
        default_config=DEFAULT_BRAND_AGENT_CONFIG,  # Fallback if LaunchDarkly unavailable
        override_guardrail_enabled=guardrail_enabled,  # Pass UI toggle
    )
    variation_name = ld_config.get("_variation", "unknown")
    print(f"   📌 Variation: {variation_name}")
    
    # Check if this is the toxic variation that should trigger simulated guardrail
    should_simulate_guardrail = (variation_name == "llama-4-toxic-prompt")
    
    # Extract guardrail ID from custom parameters (if present)
    custom_params = ld_config.get("_custom", {}) or ld_config.get("model", {}).get("custom", {})
    guardrail_id = custom_params.get("guardrail_id", "gr-healthinsure-safety-v2")
    
    print(f"{'─'*80}")
    
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
    guardrail_action = None
    guardrail_trace = None
    
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        tokens = {
            "input": response.usage_metadata.get("input_tokens", 0),
            "output": response.usage_metadata.get("output_tokens", 0)
        }
    
    # Extract Time to First Token (TTFT) from response metadata
    if hasattr(response, "response_metadata") and isinstance(response.response_metadata, dict):
        ttft_ms = response.response_metadata.get("ttft_ms")
    
    # Simulate guardrail intervention if toxic variation is served AND guardrail enabled
    guardrail_action = None
    guardrail_trace = None
    
    if should_simulate_guardrail and guardrail_enabled:
        # SIMULATED AWS BEDROCK GUARDRAIL: Block the response
        print(f"\n{'─'*80}")
        print(f"🛡️  AWS BEDROCK GUARDRAIL INTERVENED")
        print(f"   🆔 Guardrail ID: {guardrail_id}")
        print(f"   ⚠️  Response blocked due to policy violation")
        print(f"")
        print(f"   📝 Model's attempted response (first 200 chars):")
        print(f"      '{response.content[:200]}{'...' if len(response.content) > 200 else ''}'")
        print(f"")
        print(f"   🚨 Violation Details:")
        print(f"      • Policy Type: Content Policy")
        print(f"      • Filter Type: MISCONDUCT")
        print(f"      • Confidence: HIGH")
        print(f"      • Action: BLOCKED")
        print(f"")
        print(f"   💡 The model generated content that violates health safety guidelines")
        print(f"{'─'*80}\n")
        guardrail_action = "GUARDRAIL_INTERVENED"
        guardrail_trace = {
            "guardrail_id": guardrail_id,
            "action": "BLOCKED",
            "original_response": response.content[:500]
        }
    
    # No additional display needed - already shown above when simulated
    
    # Self-healing: If guardrail intervened, retry with modified context
    if guardrail_action == "GUARDRAIL_INTERVENED":
        print(f"\n{'='*80}")
        print(f"🔄 SELF-HEALING: Guardrail intervention detected")
        print(f"{'='*80}")
        print(f"   ❌ Blocked: Toxic variation '{variation_name}' violated safety policy")
        print(f"   🎯 Strategy: Modify user context to trigger fallback targeting")
        print(f"{'='*80}\n")
        
        try:
            # Strategy 1: Context Attribute Override - Modify context with fallback flag
            print(f"   📍 Strategy: LaunchDarkly Context Attribute Override")
            
            # Create modified context with fallback attribute
            fallback_context = {
                **user_context,  # Keep all original attributes
                "is_fallback": True,  # Add fallback marker
                "fallback_reason": "guardrail_intervention",
                "blocked_variation": variation_name,
                "original_request_id": request_id,
            }
            
            print(f"   🔧 Modified context attributes:")
            print(f"      • is_fallback: True")
            print(f"      • fallback_reason: guardrail_intervention")
            print(f"      • blocked_variation: {variation_name}")
            print(f"")
            print(f"   📡 Re-evaluating AI Config with fallback context...")
            
            # Pull the SAME AI Config with modified context
            fallback_model_invoker, fallback_ld_config = get_model_invoker(
                config_key="brand_agent",  # Same flag!
                context=fallback_context,   # Modified context
                default_config=DEFAULT_BRAND_AGENT_CONFIG,
                override_guardrail_enabled=False,  # Never apply guardrail to fallback
            )
            
            fallback_variation = fallback_ld_config.get("_variation", "unknown")
            
            # Safety check: Ensure we didn't get the toxic variation again
            if fallback_variation == "llama-4-toxic-prompt":
                raise ValueError(
                    f"Fallback targeting failed: Still received toxic variation '{fallback_variation}'. "
                    f"Check LaunchDarkly targeting rules - 'is_fallback' rule must be FIRST."
                )
            
            print(f"   ✅ LaunchDarkly returned variation: '{fallback_variation}'")
            print(f"   🛡️  Verified: Safe variation (not toxic)")
            print(f"")
            
            # Build messages from fallback config
            ld_client = get_ld_client()
            fallback_messages = ld_client.build_langchain_messages(fallback_ld_config, context_vars)
            
            # Generate safe response
            print(f"   🔄 Generating response with fallback variation...")
            fallback_start = time.time()
            fallback_response = fallback_model_invoker.invoke(fallback_messages)
            fallback_duration = int((time.time() - fallback_start) * 1000)
            
            # Success! Use fallback response from LaunchDarkly
            final_response = fallback_response.content
            print(f"   ✅ Self-healing succeeded!")
            print(f"   📦 Used LaunchDarkly variation: '{fallback_variation}'")
            print(f"   💬 Safe response (first 150 chars):")
            print(f"      '{final_response[:150]}{'...' if len(final_response) > 150 else ''}'")
            print(f"   ⏱️  Fallback duration: {fallback_duration}ms")
            print(f"   🎯 Customer receives safe response via LaunchDarkly fallback targeting")
            
            # Update tokens and duration for the fallback
            if hasattr(fallback_response, "usage_metadata") and fallback_response.usage_metadata:
                tokens = {
                    "input": fallback_response.usage_metadata.get("input_tokens", 0),
                    "output": fallback_response.usage_metadata.get("output_tokens", 0)
                }
            duration_ms = fallback_duration
            
            if hasattr(fallback_response, "response_metadata") and isinstance(fallback_response.response_metadata, dict):
                ttft_ms = fallback_response.response_metadata.get("ttft_ms")
            
            # Store fallback metadata in agent_data for observability
            agent_data["guardrail_intervention"] = True
            agent_data["fallback_variation"] = fallback_variation
            agent_data["blocked_variation"] = variation_name
            
            print(f"{'='*80}\n")
            
        except Exception as e:
            # If LaunchDarkly fallback fails, use hardcoded default as last resort
            print(f"   ❌ LaunchDarkly fallback strategy failed: {e}")
            print(f"   📋 Possible causes:")
            print(f"      • LaunchDarkly unavailable")
            print(f"      • 'is_fallback' targeting rule not configured")
            print(f"      • 'is_fallback' rule not first in targeting order")
            print(f"")
            print(f"   🆘 Falling back to hardcoded safe default as last resort...")
            print(f"{'='*80}\n")
            
            try:
                from ..utils.bedrock_llm import BedrockConverseLLM, get_bedrock_model_id
                import os
                
                # Use safe hardcoded defaults
                default_model = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
                default_temp = 0.7
                default_max_tokens = 2000
                
                # Create Bedrock LLM with default settings
                model_id = get_bedrock_model_id(default_model)
                region = os.getenv("AWS_REGION", "us-east-1")
                profile = os.getenv("AWS_PROFILE")
                
                fallback_llm = BedrockConverseLLM(
                    model_id=model_id,
                    temperature=default_temp,
                    max_tokens=default_max_tokens,
                    region=region,
                    profile_name=profile,
                )
                
                # Build messages from hardcoded default config
                fallback_messages = []
                for msg in DEFAULT_BRAND_AGENT_CONFIG.messages:
                    content = msg.content
                    # Replace template variables
                    for key, value in context_vars.items():
                        content = content.replace(f"{{{key}}}", str(value))
                    
                    if msg.role == "system":
                        fallback_messages.append(SystemMessage(content=content))
                    else:
                        fallback_messages.append(HumanMessage(content=content))
                
                # Invoke with hardcoded default
                fallback_start = time.time()
                fallback_response = fallback_llm.invoke(fallback_messages)
                fallback_duration = int((time.time() - fallback_start) * 1000)
                
                final_response = fallback_response.content
                print(f"   ✅ Hardcoded fallback succeeded")
                print(f"   ⏱️  Duration: {fallback_duration}ms")
                
                # Update tokens and duration
                if hasattr(fallback_response, "usage_metadata") and fallback_response.usage_metadata:
                    tokens = {
                        "input": fallback_response.usage_metadata.get("input_tokens", 0),
                        "output": fallback_response.usage_metadata.get("output_tokens", 0)
                    }
                duration_ms = fallback_duration
                
                if hasattr(fallback_response, "response_metadata") and isinstance(fallback_response.response_metadata, dict):
                    ttft_ms = fallback_response.response_metadata.get("ttft_ms")
                
                print(f"{'='*80}\n")
                
            except Exception as e2:
                print(f"   ❌ Hardcoded fallback also failed: {e2}")
                print(f"   🆘 Using generic safe message")
                print(f"{'='*80}\n")
                final_response = "I apologize, but I'm unable to provide a response at this time. Please contact our support team for assistance."
    else:
        # No guardrail intervention, use original response
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
        },
        "guardrail": {
            "action": guardrail_action,
            "intervened": guardrail_action == "GUARDRAIL_INTERVENED",
            "trace": guardrail_trace,
        } if guardrail_action else None,
        "self_healing": {
            "triggered": guardrail_action == "GUARDRAIL_INTERVENED",
            "used_fallback": guardrail_action == "GUARDRAIL_INTERVENED",
            "fallback_config": "DEFAULT_BRAND_AGENT_CONFIG",
        } if guardrail_action == "GUARDRAIL_INTERVENED" else None,
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
