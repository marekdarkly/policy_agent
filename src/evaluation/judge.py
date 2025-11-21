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
                error_msg = str(accuracy_data)
                print(f"⚠️  Accuracy evaluation failed: {error_msg}")
                
                # Check for AWS credential errors
                if any(pattern in error_msg for pattern in [
                    "KeyError", "JSONDecodeError", "Extra data",
                    "token", "credentials", "sso"
                ]):
                    reason = "AWS authentication failed - session expired. Re-run: aws sso login --profile marek"
                else:
                    reason = error_msg
                
                accuracy_result = {"score": 0.0, "passed": False, "reason": reason}
                accuracy_model = "unknown"
                accuracy_tokens = {"input": 0, "output": 0}
            else:
                accuracy_result, accuracy_model, accuracy_tokens = accuracy_data
            
            if isinstance(coherence_data, Exception):
                error_msg = str(coherence_data)
                print(f"⚠️  Coherence evaluation failed: {error_msg}")
                
                # Check for AWS credential errors
                if any(pattern in error_msg for pattern in [
                    "KeyError", "JSONDecodeError", "Extra data",
                    "token", "credentials", "sso"
                ]):
                    reason = "AWS authentication failed - session expired. Re-run: aws sso login --profile marek"
                else:
                    reason = error_msg
                
                coherence_result = {"score": 0.0, "passed": False, "reason": reason}
                coherence_model = "unknown"
                coherence_tokens = {"input": 0, "output": 0}
            else:
                coherence_result, coherence_model, coherence_tokens = coherence_data
            
            # Send judgment metrics to LaunchDarkly using user context and tracker
            self._send_judgment_to_ld(user_context, accuracy_result, coherence_result, brand_tracker)
            
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
        # Skip span annotation for judges since they run in background threads
        model_invoker, judge_config = get_model_invoker(
            config_key="ai-judge-accuracy",
            context=user_context,
            default_temperature=0.0,  # Deterministic for evaluation
            skip_span_annotation=True  # Background thread - don't try to annotate closed request spans
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
        # Skip span annotation for judges since they run in background threads
        model_invoker, judge_config = get_model_invoker(
            config_key="ai-judge-coherence",
            context=user_context,
            default_temperature=0.0,
            skip_span_annotation=True  # Background thread - don't try to annotate closed request spans
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
        user_context: Dict[str, Any],
        accuracy_result: Dict[str, Any],
        coherence_result: Dict[str, Any],
        brand_tracker: Any
    ):
        """
        Send judgment metrics to LaunchDarkly using the brand_tracker.
        
        Uses the brand_tracker (which has AI config metadata) to associate
        metrics with the brand_agent AI config, not the judge AI configs.
        
        Sends three metrics:
        - "$ld:ai:hallucinations": Accuracy score (higher = fewer hallucinations)
        - "$ld:ai:judge:accuracy": Accuracy score (duplicate for judge-specific tracking)
        - "$ld:ai:coherence": Coherence score
        
        Args:
            user_context: User context dict with user_key, name, etc.
            accuracy_result: Dict with "score" key (0.0-1.0)
            coherence_result: Dict with "score" key (0.0-1.0)
            brand_tracker: Tracker from brand_agent AI config (contains metadata)
        """
        if brand_tracker is None:
            print(f"⚠️  Cannot send metrics: brand_tracker is None")
            print(f"   Metrics will NOT be correlated to brand_agent AI Config!")
            return
        
        try:
            # Use brand_tracker to send metrics with AI config metadata
            # This ensures metrics show up on the brand_agent's monitoring page
            
            # Get the raw LaunchDarkly client for sending numeric metrics
            import ldclient
            raw_ld_client = ldclient.get()
            
            # Get the context from the brand_tracker (ModelInvoker stores it as user_context)
            # This context has the AI Config metadata that associates metrics with the brand_agent config
            ld_context = brand_tracker.user_context
            
            # 1. Hallucinations metric (accuracy score: higher = fewer hallucinations)
            hallucinations_score = float(accuracy_result["score"])
            raw_ld_client.track(
                event_name="$ld:ai:hallucinations",
                context=ld_context,
                metric_value=hallucinations_score
            )
            
            # 1b. Also send to judge-specific accuracy metric (duplicate)
            raw_ld_client.track(
                event_name="$ld:ai:judge:accuracy",
                context=ld_context,
                metric_value=hallucinations_score
            )
            
            # 2. Coherence metric
            coherence_score = float(coherence_result["score"])
            raw_ld_client.track(
                event_name="$ld:ai:coherence",
                context=ld_context,
                metric_value=coherence_score
            )
            
            print(f"📊 Sent judgment metrics to brand_agent AI config:")
            print(f"   - $ld:ai:hallucinations: {hallucinations_score:.2f}")
            print(f"   - $ld:ai:judge:accuracy: {hallucinations_score:.2f}")
            print(f"   - $ld:ai:coherence: {coherence_score:.2f}")
            
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
            print(f"   brand_tracker type: {type(brand_tracker)}")
            print(f"   brand_tracker: {brand_tracker}")
            import traceback
            traceback.print_exc()


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

