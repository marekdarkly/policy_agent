"""Per-agent evaluator for A/B testing individual agents.

This evaluator allows testing accuracy of individual agents (policy, provider, scheduler)
without running the full end-to-end system. Useful for LaunchDarkly experiments
on individual agent prompts/models.
"""

import asyncio
import ldclient
from ldclient import Context
from typing import Any, Dict, List

from ..utils.llm_config import get_model_invoker


async def evaluate_agent_accuracy(
    agent_name: str,
    original_query: str,
    rag_documents: List[Dict[str, Any]],
    agent_output: str,
    user_context: Dict[str, Any]
) -> Dict[str, Any]:
    """Evaluate a specific agent's accuracy.
    
    Args:
        agent_name: Name of the agent (policy_agent, provider_agent, scheduler_agent)
        original_query: The user's original question
        rag_documents: Retrieved RAG documents (source of truth for accuracy)
        agent_output: The agent's raw output before brand voice
        user_context: User context for LaunchDarkly targeting
    
    Returns:
        Dict with accuracy result (evaluator only sends accuracy metrics)
    """
    try:
        # Get agent evaluator config from LaunchDarkly
        evaluator_config_key = "agent-judge-accuracy"
        
        # Format RAG documents for template variable
        rag_context = "\n\n---\n\n".join([
            f"Document {i+1}:\n{doc.get('content', '')}"
            for i, doc in enumerate(rag_documents)
        ])
        
        # Get model invoker for evaluation (using LaunchDarkly config)
        model_invoker, eval_config = get_model_invoker(
            config_key=evaluator_config_key,
            context=user_context
        )
        
        # Get the prompt template from LaunchDarkly config
        # Agent-based configs have prompt in '_instructions'
        prompt_template = eval_config.get("_instructions", "")
        
        if not prompt_template:
            # Fallback if no prompt in config
            raise ValueError(f"No prompt found in LaunchDarkly config '{evaluator_config_key}'")
        
        # Debug: Show template before substitution
        print(f"🔍 DEBUG: Prompt template (first 300 chars): {prompt_template[:300]}...")
        print(f"🔍 DEBUG: Variables to substitute:")
        print(f"   - agent_name: {agent_name}")
        print(f"   - user_query length: {len(original_query)} chars")
        print(f"   - agent_output length: {len(agent_output)} chars")
        print(f"   - rag_documents length: {len(rag_context)} chars")
        
        # Substitute template variables
        # The LaunchDarkly prompt has sections like "**User Query:**\n\n**Agent Output..."
        # We need to inject content after each header
        evaluation_prompt = prompt_template.replace(
            "**User Query:**", 
            f"**User Query:**\n{original_query}"
        )
        evaluation_prompt = evaluation_prompt.replace(
            "**Agent Output to Evaluate:**",
            f"**Agent Output to Evaluate:**\n{agent_output}"
        )
        evaluation_prompt = evaluation_prompt.replace(
            "**RAG Documents (Source of Truth):**",
            f"**RAG Documents (Source of Truth):**\n{rag_context}"
        )
        
        print(f"🔍 DEBUG: After substitution (first 300 chars): {evaluation_prompt[:300]}...")
        
        # Run evaluation with substituted prompt
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=evaluation_prompt)]
        
        response = model_invoker.model.invoke(messages)
        response_text = response.content
        
        # Debug: Print response to help diagnose JSON parsing issues
        print(f"🔍 DEBUG: Agent evaluator response (first 500 chars):")
        print(f"{response_text[:500]}...")
        
        # Extract token usage
        tokens = {
            "input": response.usage_metadata.get("input_tokens", 0) if hasattr(response, 'usage_metadata') else 0,
            "output": response.usage_metadata.get("output_tokens", 0) if hasattr(response, 'usage_metadata') else 0
        }
        
        # Calculate cost for this evaluation
        eval_model_id = eval_config.get("model", {}).get("name", "unknown")
        
        # Import cost calculation function from brand_voice_agent
        from ..agents.brand_voice_agent import calculate_model_cost
        
        eval_cost_usd = calculate_model_cost(
            model_id=eval_model_id,
            input_tokens=tokens["input"],
            output_tokens=tokens["output"]
        )
        eval_cost_cents = round(eval_cost_usd * 100.0, 2)
        
        # Parse JSON response
        import json
        import re
        
        # Extract JSON from markdown code blocks if present
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON object directly
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in response")
        
        result = json.loads(json_str)
        
        # Ensure required fields
        if "score" not in result:
            result["score"] = 0.0
        if "passed" not in result:
            result["passed"] = result["score"] >= 0.8
        if "reason" not in result:
            result["reason"] = "No reason provided"
        if "issues" not in result:
            result["issues"] = []
        
        # Add cost and token info to result
        result["eval_tokens_input"] = tokens["input"]
        result["eval_tokens_output"] = tokens["output"]
        result["eval_cost_cents"] = eval_cost_cents
        result["eval_cost_usd"] = eval_cost_usd
        result["eval_model"] = eval_model_id
        
        # Send accuracy metrics to LaunchDarkly (associated with the agent's config key)
        try:
            from ..utils.launchdarkly_config import get_ld_client
            ld_full_client = get_ld_client()
            
            # Get the agent's tracker to associate metrics with the correct config
            # Map agent_name to config_key
            config_key_map = {
                "policy_agent": "policy_agent",
                "provider_agent": "provider_agent",
                "scheduler_agent": "scheduler_agent"
            }
            config_key = config_key_map.get(agent_name, agent_name)
            
            # Get the agent's config and tracker (this ensures metrics go to the right place)
            _, agent_tracker, ld_context = ld_full_client.get_ai_config(config_key, user_context)
            
            # Send accuracy metric using track method directly on full LaunchDarkly client
            # This ensures it's associated with the agent's config via context
            try:
                # Use the raw ldclient to send events with proper context
                raw_ld_client = ldclient.get()
                
                # Send as generation feedback event tied to the config
                raw_ld_client.track(
                    event_name="$ld:ai:generation:feedback",
                    context=ld_context,
                    data={
                        "config_key": config_key,
                        "accuracy": float(result["score"]),
                        "passed": result["passed"]
                    },
                    metric_value=float(result["score"])
                )
            except Exception as track_err:
                print(f"⚠️  Failed to send accuracy metric: {track_err}")
            
            # Also send as hallucination metric with config context
            try:
                raw_ld_client.track(
                    event_name="$ld:ai:hallucinations",
                    context=ld_context,
                    data={"config_key": config_key},
                    metric_value=float(result["score"])
                )
            except Exception as track_err:
                print(f"⚠️  Failed to send hallucination metric: {track_err}")
            
            print(f"📊 Sent {agent_name} accuracy metric: {result['score']:.2f} (config: {config_key})")
            print(f"💰 Evaluation cost: {eval_cost_cents:.2f}¢ (${eval_cost_usd:.6f}) [in={tokens['input']}, out={tokens['output']}, model={eval_model_id}]")
            
        except Exception as e:
            print(f"⚠️  Failed to send {agent_name} metrics to LaunchDarkly: {e}")
        
        return result
        
    except Exception as e:
        print(f"❌ Agent evaluation error: {e}")
        return {
            "score": 0.0,
            "passed": False,
            "reason": f"Evaluation error: {e}",
            "issues": []
        }

