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
        Dict with accuracy result
    """
    try:
        # Get agent-specific evaluator config from LaunchDarkly
        evaluator_config_key = f"agent-evaluator-{agent_name.replace('_agent', '')}"
        
        # Prepare evaluation prompt
        # Combine RAG documents for evaluation
        rag_context = "\n\n---\n\n".join([
            f"Document {i+1}:\n{doc.get('content', '')}"
            for i, doc in enumerate(rag_documents)
        ])
        
        # Build evaluation prompt
        evaluation_prompt = f"""You are evaluating the accuracy of a {agent_name}'s output.

USER QUERY: {original_query}

AGENT OUTPUT TO EVALUATE:
{agent_output}

RAG DOCUMENTS (Source of Truth):
{rag_context}

Evaluate the agent's output for factual accuracy against the RAG documents.
Score from 0.0 to 1.0 where:
- 1.0 = Perfectly accurate, all facts match RAG documents
- 0.8-0.9 = Mostly accurate with minor omissions
- 0.6-0.7 = Some inaccuracies or significant omissions  
- 0.4-0.5 = Multiple inaccuracies
- 0.0-0.3 = Major inaccuracies or hallucinations

Return JSON:
{{
  "score": <float 0.0-1.0>,
  "passed": <boolean>,
  "reason": "<brief explanation>",
  "issues": ["<issue 1>", "<issue 2>"]
}}"""

        # Get model invoker for evaluation (using LaunchDarkly config)
        model_invoker, eval_config = get_model_invoker(
            config_key=evaluator_config_key,
            user_context=user_context
        )
        
        # Run evaluation
        from langchain_core.messages import HumanMessage
        messages = [HumanMessage(content=evaluation_prompt)]
        
        response = model_invoker.llm.invoke(messages)
        response_text = response.content
        
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
        
        # Send metric to LaunchDarkly
        try:
            ld_client = ldclient.get()
            user_key = user_context.get("user_key", "anonymous")
            
            context_builder = Context.builder(user_key).kind("user")
            if user_context.get("name"):
                context_builder.set("name", user_context["name"])
            if user_context.get("location"):
                context_builder.set("location", user_context["location"])
            if user_context.get("policy_id"):
                context_builder.set("policy_id", user_context["policy_id"])
            ld_context = context_builder.build()
            
            # Send agent-specific accuracy metric
            agent_short_name = agent_name.replace("_agent", "")
            ld_client.track(
                event_name=f"$ld:ai:hallucinations:{agent_short_name}",
                context=ld_context,
                metric_value=float(result["score"])
            )
            
            print(f"📊 Sent {agent_name} accuracy metric: {result['score']:.2f}")
            
        except Exception as e:
            print(f"⚠️  Failed to send {agent_name} metric to LaunchDarkly: {e}")
        
        return result
        
    except Exception as e:
        print(f"❌ Agent evaluation error: {e}")
        return {
            "score": 0.0,
            "passed": False,
            "reason": f"Evaluation error: {e}",
            "issues": []
        }

