"""
G-Eval based online evaluation using LaunchDarkly AI Configs.

This module implements async evaluation that runs after agent responses
without blocking the user experience. Evaluation results are sent to
LaunchDarkly using special metric keys for real-time monitoring.
"""

import asyncio
import json
from typing import Any, Optional, Dict, List
from dataclasses import dataclass

from langchain_core.messages import SystemMessage, HumanMessage

from ..utils.llm_config import get_model_invoker
from ..utils.launchdarkly_config import get_ld_client


@dataclass
class GEvalMetric:
    """G-Eval metric definition."""
    
    name: str
    evaluation_steps: List[str]
    threshold: float = 0.7


class BrandVoiceEvaluator:
    """Evaluates brand voice agent output using G-Eval."""
    
    def __init__(self):
        """Initialize evaluator with LaunchDarkly."""
        self.ld_client = get_ld_client()
    
    async def evaluate_async(
        self,
        original_query: str,
        rag_documents: List[Dict[str, Any]],
        brand_voice_output: str,
        user_context: Dict[str, Any],
        brand_tracker: Any
    ) -> Dict[str, Any]:
        """
        Evaluate brand voice output asynchronously.
        
        Args:
            original_query: The user's original question
            rag_documents: Retrieved RAG documents (source of truth for accuracy)
            brand_voice_output: Final output from brand voice agent (full system output)
            user_context: User context for LaunchDarkly targeting
            brand_tracker: The tracker from brand_agent for sending judgment metrics
            
        Returns:
            Dict with evaluation results
        """
        try:
            # Note: We don't need to pre-fetch config here since each metric
            # will get its own config (brand_eval_judge_accuracy, brand_eval_judge_coherence)
            
            # Run accuracy and coherence evaluations in parallel
            accuracy_task = self._evaluate_accuracy(
                original_query,
                rag_documents,
                brand_voice_output,
                user_context
            )
            
            coherence_task = self._evaluate_coherence(
                brand_voice_output,
                user_context
            )
            
            results = await asyncio.gather(
                accuracy_task,
                coherence_task,
                return_exceptions=True
            )
            
            # Unpack results
            accuracy_data = results[0]
            coherence_data = results[1]
            
            # Handle any exceptions and extract data
            if isinstance(accuracy_data, Exception):
                print(f"⚠️  Accuracy evaluation failed: {accuracy_data}")
                accuracy_result = {"score": 0.0, "passed": False, "reason": str(accuracy_data)}
                accuracy_model = "unknown"
                accuracy_tokens = {"input": 0, "output": 0}
            else:
                accuracy_result, accuracy_model, accuracy_tokens = accuracy_data
            
            if isinstance(coherence_data, Exception):
                print(f"⚠️  Coherence evaluation failed: {coherence_data}")
                coherence_result = {"score": 0.0, "passed": False, "reason": str(coherence_data)}
                coherence_model = "unknown"
                coherence_tokens = {"input": 0, "output": 0}
            else:
                coherence_result, coherence_model, coherence_tokens = coherence_data
            
            # Send judgment metrics to LaunchDarkly using brand_tracker
            self._send_judgment_to_ld(brand_tracker, accuracy_result, coherence_result)
            
            print(f"✅ Evaluation completed: Accuracy={accuracy_result['score']:.2f}, Coherence={coherence_result['score']:.2f}")
            
            # Calculate total tokens from both judges
            total_input_tokens = accuracy_tokens["input"] + coherence_tokens["input"]
            total_output_tokens = accuracy_tokens["output"] + coherence_tokens["output"]
            
            # Use accuracy model as primary (they should be the same)
            judge_model_name = accuracy_model if accuracy_model != "unknown" else coherence_model
            
            # Return flattened structure that matches frontend expectations
            return {
                "accuracy": accuracy_result,
                "coherence": coherence_result,
                "overall_passed": accuracy_result["passed"] and coherence_result["passed"],
                "judge_model_name": judge_model_name,
                "judge_input_tokens": total_input_tokens,
                "judge_output_tokens": total_output_tokens,
            }
            
        except Exception as e:
            print(f"❌ Evaluation error: {e}")
            return {
                "accuracy": {"score": 0.0, "passed": False, "reason": str(e)},
                "coherence": {"score": 0.0, "passed": False, "reason": str(e)},
                "overall_passed": False
            }
    
    async def _evaluate_accuracy(
        self,
        original_query: str,
        rag_documents: List[Dict[str, Any]],
        brand_voice_output: str,
        user_context: Dict[str, Any]
    ) -> tuple[Dict[str, Any], str, Dict[str, int]]:
        """
        Evaluate global system accuracy: Is the final output factually accurate against RAG documents?
        
        This evaluates the ENTIRE system (specialist + brand voice) against the source of truth (RAG docs).
        Uses G-Eval methodology with evaluation steps from LaunchDarkly.
        
        Returns:
            Tuple of (result_dict, model_name, tokens_dict)
        """
        # Get the judge LLM and config (with prompts from LaunchDarkly)
        model_invoker, judge_config = get_model_invoker(
            config_key="ai-judge-accuracy",
            context=user_context,
            default_temperature=0.0  # Deterministic for evaluation
        )
        
        # Extract model name from config
        model_name = judge_config.get("model", {}).get("name", "unknown") if isinstance(judge_config, dict) else "unknown"
        
        # Format RAG documents as context
        rag_context = self._format_rag_context(rag_documents)
        
        # Build messages from LaunchDarkly config with accuracy evaluation context
        context_vars = {
            **user_context,
            "original_query": original_query,
            "rag_context": rag_context,
            "final_output": brand_voice_output,
            "evaluation_type": "accuracy"
        }
        
        langchain_messages = self.ld_client.build_langchain_messages(judge_config, context_vars)
        
        # Run evaluation
        response = model_invoker.invoke(langchain_messages)
        
        # Extract tokens from response
        tokens = {"input": 0, "output": 0}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = {
                "input": response.usage_metadata.get("input_tokens", 0),
                "output": response.usage_metadata.get("output_tokens", 0)
            }
        
        # Parse result
        result = self._parse_eval_response(response.content, threshold=0.8)
        return result, model_name, tokens
    
    async def _evaluate_coherence(
        self,
        brand_voice_output: str,
        user_context: Dict[str, Any]
    ) -> tuple[Dict[str, Any], str, Dict[str, int]]:
        """
        Evaluate coherence: Is the output clear, well-structured, professional?
        
        Uses G-Eval methodology with evaluation steps from LaunchDarkly.
        
        Returns:
            Tuple of (result_dict, model_name, tokens_dict)
        """
        # Get the judge LLM and config (with prompts from LaunchDarkly)
        model_invoker, judge_config = get_model_invoker(
            config_key="ai-judge-coherence",
            context=user_context,
            default_temperature=0.0
        )
        
        # Extract model name from config
        model_name = judge_config.get("model", {}).get("name", "unknown") if isinstance(judge_config, dict) else "unknown"
        
        # Build messages from LaunchDarkly config with coherence evaluation context
        context_vars = {
            **user_context,
            "brand_voice_output": brand_voice_output,
            "evaluation_type": "coherence"
        }
        
        langchain_messages = self.ld_client.build_langchain_messages(judge_config, context_vars)
        
        # Run evaluation
        response = model_invoker.invoke(langchain_messages)
        
        # Extract tokens from response
        tokens = {"input": 0, "output": 0}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            tokens = {
                "input": response.usage_metadata.get("input_tokens", 0),
                "output": response.usage_metadata.get("output_tokens", 0)
            }
        
        # Parse result
        result = self._parse_eval_response(response.content, threshold=0.7)
        return result, model_name, tokens
    
    
    def _format_rag_context(self, rag_documents: List[Dict[str, Any]]) -> str:
        """Format RAG documents into a readable context string."""
        if not rag_documents:
            return "No RAG documents available"
        
        formatted = "=== RETRIEVED KNOWLEDGE BASE DOCUMENTS (Source of Truth) ===\n\n"
        for i, doc in enumerate(rag_documents, 1):
            score = doc.get("score", 0.0)
            content = doc.get("content", "")
            formatted += f"[Document {i} - Relevance Score: {score:.2f}]\n{content}\n\n"
        
        return formatted
    
    def _parse_eval_response(self, response: str, threshold: float) -> Dict[str, Any]:
        """Parse evaluation response from judge LLM."""
        try:
            # Extract JSON from response
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            result = json.loads(response)
            score = float(result.get("score", 0.0))
            
            return {
                "score": score,
                "passed": score >= threshold,
                "reason": result.get("reasoning", ""),
                "issues": result.get("issues", [])
            }
        except Exception as e:
            print(f"⚠️  Failed to parse evaluation response: {e}")
            return {
                "score": 0.0,
                "passed": False,
                "reason": f"Parse error: {e}",
                "issues": []
            }
    
    def _send_judgment_to_ld(
        self,
        brand_tracker: Any,
        accuracy_result: Dict[str, Any],
        coherence_result: Dict[str, Any]
    ):
        """
        Send judgment metrics to LaunchDarkly using special metric keys.
        
        These metrics will appear in the same tracker stream as the brand_agent.
        """
        try:
            # Send accuracy judgment
            # The tracker should support custom metric names
            if hasattr(brand_tracker, 'track_metric'):
                brand_tracker.track_metric(
                    "$ld:ai:judge:accuracy",
                    accuracy_result["score"]
                )
                brand_tracker.track_metric(
                    "$ld:ai:judge:coherence",
                    coherence_result["score"]
                )
            else:
                # Fallback: log as metadata if direct metric tracking not available
                print(f"📊 Judgment Metrics: accuracy={accuracy_result['score']:.2f}, coherence={coherence_result['score']:.2f}")
            
            # Display evaluation results with reasoning
            print("\n" + "="*80)
            print("🔍 G-EVAL JUDGMENT RESULTS")
            print("="*80)
            
            # Accuracy
            acc_pass = "✅ PASS" if accuracy_result.get("passed") else "❌ FAIL"
            print(f"\n📊 Accuracy: {accuracy_result.get('score', 0.0):.2f} {acc_pass}")
            print(f"   Reasoning: {accuracy_result.get('reason', 'No reasoning provided')}")
            if accuracy_result.get("issues"):
                print(f"   Issues:")
                for issue in accuracy_result.get("issues", []):
                    print(f"     - {issue}")
            
            # Coherence
            coh_pass = "✅ PASS" if coherence_result.get("passed") else "❌ FAIL"
            print(f"\n📊 Coherence: {coherence_result.get('score', 0.0):.2f} {coh_pass}")
            print(f"   Reasoning: {coherence_result.get('reason', 'No reasoning provided')}")
            if coherence_result.get("issues"):
                print(f"   Issues:")
                for issue in coherence_result.get("issues", []):
                    print(f"     - {issue}")
            
            print("="*80 + "\n")
                
        except Exception as e:
            print(f"⚠️  Failed to send judgment to LaunchDarkly: {e}")


# Global evaluator instance
_evaluator = None


def get_evaluator() -> BrandVoiceEvaluator:
    """Get or create the global evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = BrandVoiceEvaluator()
    return _evaluator


async def evaluate_brand_voice_async(
    original_query: str,
    rag_documents: List[Dict[str, Any]],
    brand_voice_output: str,
    user_context: Dict[str, Any],
    brand_tracker: Any,
    request_id: Optional[str] = None,
    results_store: Optional[Dict[str, Any]] = None
) -> None:
    """
    Evaluate system output asynchronously without blocking.
    
    This is a fire-and-forget function that runs evaluation in the background.
    Evaluates GLOBAL SYSTEM ACCURACY against RAG documents (source of truth).
    
    Args:
        original_query: The user's original question
        rag_documents: Retrieved RAG documents (source of truth)
        brand_voice_output: Final system output to evaluate
        user_context: User context for LaunchDarkly
        brand_tracker: The tracker from brand_agent for sending metrics
        request_id: Optional request ID to store results for later retrieval
    """
    evaluator = get_evaluator()
    
    try:
        # Run evaluation
        results = await evaluator.evaluate_async(
            original_query,
            rag_documents,
            brand_voice_output,
            user_context,
            brand_tracker
        )
        
        # Store results in global store if request_id provided
        if request_id and results and results_store is not None:
            print(f"📊 Evaluation complete! Storing results for request_id={request_id}")
            print(f"   Accuracy: {results.get('accuracy', {}).get('score', 'N/A')}")
            print(f"   Coherence: {results.get('coherence', {}).get('score', 'N/A')}")
            
            try:
                results_store[request_id] = results
                print(f"✅ EVALUATION STORED for request_id={request_id}")
                print(f"   Keys in results_store: {list(results_store.keys())}")
            except Exception as e:
                # Show full error for debugging
                import traceback
                print(f"❌ Failed to store evaluation: {e}")
                print(f"   Traceback: {traceback.format_exc()}")
        else:
            print(f"⚠️  Cannot store evaluation:")
            print(f"   request_id: {request_id}")
            print(f"   results: {'present' if results else 'None'}")
            print(f"   results_store: {'present' if results_store is not None else 'None'}")
        
    except Exception as e:
        # Never let evaluation errors crash the main flow
        print(f"⚠️  Background evaluation failed: {e}")

