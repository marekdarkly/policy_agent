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
        specialist_response: str,
        brand_voice_output: str,
        user_context: Dict[str, Any],
        brand_tracker: Any
    ) -> Dict[str, Any]:
        """
        Evaluate brand voice output asynchronously.
        
        Args:
            original_query: The user's original question
            specialist_response: Response from the specialist agent (policy/provider/scheduler)
            brand_voice_output: Final output from brand voice agent
            user_context: User context for LaunchDarkly targeting
            brand_tracker: The tracker from brand_agent for sending judgment metrics
            
        Returns:
            Dict with evaluation results
        """
        try:
            # Get evaluation config from LaunchDarkly
            eval_config, eval_tracker = self.ld_client.get_ai_config(
                "brand_eval_judge",
                user_context
            )
            
            # Run accuracy and coherence evaluations in parallel
            accuracy_task = self._evaluate_accuracy(
                original_query,
                specialist_response,
                brand_voice_output,
                user_context,
                eval_config
            )
            
            coherence_task = self._evaluate_coherence(
                brand_voice_output,
                user_context,
                eval_config
            )
            
            accuracy_result, coherence_result = await asyncio.gather(
                accuracy_task,
                coherence_task,
                return_exceptions=True
            )
            
            # Handle any exceptions
            if isinstance(accuracy_result, Exception):
                print(f"⚠️  Accuracy evaluation failed: {accuracy_result}")
                accuracy_result = {"score": 0.0, "passed": False, "reason": str(accuracy_result)}
            
            if isinstance(coherence_result, Exception):
                print(f"⚠️  Coherence evaluation failed: {coherence_result}")
                coherence_result = {"score": 0.0, "passed": False, "reason": str(coherence_result)}
            
            # Send judgment metrics to LaunchDarkly using brand_tracker
            self._send_judgment_to_ld(brand_tracker, accuracy_result, coherence_result)
            
            print(f"✅ Evaluation completed: Accuracy={accuracy_result['score']:.2f}, Coherence={coherence_result['score']:.2f}")
            
            return {
                "accuracy": accuracy_result,
                "coherence": coherence_result,
                "overall_passed": accuracy_result["passed"] and coherence_result["passed"]
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
        specialist_response: str,
        brand_voice_output: str,
        user_context: Dict[str, Any],
        eval_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate accuracy: Did brand voice preserve factual accuracy?
        
        Uses G-Eval methodology with evaluation steps from LaunchDarkly.
        """
        # Get the judge LLM
        model_invoker, _ = get_model_invoker(
            config_key="brand_eval_judge",
            context=user_context,
            default_temperature=0.0  # Deterministic for evaluation
        )
        
        # Build evaluation prompt using G-Eval methodology
        prompt = self._build_accuracy_prompt(
            original_query,
            specialist_response,
            brand_voice_output,
            eval_config
        )
        
        # Run evaluation
        response = model_invoker.invoke([
            SystemMessage(content="You are an expert evaluator assessing the accuracy of AI-generated responses."),
            HumanMessage(content=prompt)
        ])
        
        # Parse result
        return self._parse_eval_response(response.content, threshold=0.8)
    
    async def _evaluate_coherence(
        self,
        brand_voice_output: str,
        user_context: Dict[str, Any],
        eval_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evaluate coherence: Is the output clear, well-structured, professional?
        
        Uses G-Eval methodology with evaluation steps from LaunchDarkly.
        """
        # Get the judge LLM
        model_invoker, _ = get_model_invoker(
            config_key="brand_eval_judge",
            context=user_context,
            default_temperature=0.0
        )
        
        # Build evaluation prompt
        prompt = self._build_coherence_prompt(brand_voice_output, eval_config)
        
        # Run evaluation
        response = model_invoker.invoke([
            SystemMessage(content="You are an expert evaluator assessing the coherence and clarity of AI-generated responses."),
            HumanMessage(content=prompt)
        ])
        
        # Parse result
        return self._parse_eval_response(response.content, threshold=0.7)
    
    def _build_accuracy_prompt(
        self,
        original_query: str,
        specialist_response: str,
        brand_voice_output: str,
        eval_config: Dict[str, Any]
    ) -> str:
        """Build G-Eval prompt for accuracy evaluation."""
        
        # Extract evaluation steps from config or use defaults
        instructions = eval_config.get("_instructions", "")
        
        # Default evaluation steps if not in config
        default_steps = [
            "Compare the facts in the brand voice output against the specialist response",
            "Check if any medical/policy/provider facts were changed, omitted, or added",
            "Verify that numbers, dates, names, and specific details remain accurate",
            "Heavily penalize any hallucinations or factual errors",
            "Minor rephrasing for clarity is acceptable as long as facts are preserved"
        ]
        
        return f"""Evaluate the ACCURACY of the brand voice output by comparing it to the specialist response.

Original User Query:
{original_query}

Specialist Response (Source of Truth):
{specialist_response}

Brand Voice Output (To Evaluate):
{brand_voice_output}

Evaluation Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(default_steps))}

Rate the accuracy on a scale of 0.0 to 1.0, where:
- 1.0 = Perfect accuracy, all facts preserved
- 0.8-0.9 = Minor rephrasing but facts intact
- 0.6-0.7 = Some details lost but core facts correct
- 0.4-0.5 = Significant factual changes
- 0.0-0.3 = Major errors or hallucinations

Return your evaluation as JSON:
{{
    "score": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of score>",
    "issues": ["<list any factual discrepancies found>"]
}}

JSON:"""
    
    def _build_coherence_prompt(
        self,
        brand_voice_output: str,
        eval_config: Dict[str, Any]
    ) -> str:
        """Build G-Eval prompt for coherence evaluation."""
        
        default_steps = [
            "Evaluate whether the response uses clear and direct language",
            "Check if medical/insurance terminology is explained when used",
            "Assess whether the message is well-structured with logical flow",
            "Verify the tone is professional yet friendly and empathetic",
            "Identify any confusing, vague, or overly complex parts"
        ]
        
        return f"""Evaluate the COHERENCE of this customer-facing response.

Brand Voice Output:
{brand_voice_output}

Evaluation Steps:
{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(default_steps))}

Rate the coherence on a scale of 0.0 to 1.0, where:
- 1.0 = Exceptionally clear, professional, and easy to understand
- 0.8-0.9 = Clear and well-structured with minor room for improvement
- 0.6-0.7 = Understandable but has some confusing parts
- 0.4-0.5 = Somewhat unclear or poorly structured
- 0.0-0.3 = Confusing, unprofessional, or difficult to follow

Return your evaluation as JSON:
{{
    "score": <float between 0.0 and 1.0>,
    "reasoning": "<brief explanation of score>",
    "issues": ["<list any coherence issues found>"]
}}

JSON:"""
    
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
    specialist_response: str,
    brand_voice_output: str,
    user_context: Dict[str, Any],
    brand_tracker: Any
) -> None:
    """
    Evaluate brand voice output asynchronously without blocking.
    
    This is a fire-and-forget function that runs evaluation in the background.
    
    Args:
        original_query: The user's original question
        specialist_response: Response from specialist (before brand voice)
        brand_voice_output: Final output after brand voice transformation
        user_context: User context for LaunchDarkly
        brand_tracker: The tracker from brand_agent for sending metrics
    """
    evaluator = get_evaluator()
    
    try:
        # Run evaluation without awaiting (fire-and-forget)
        await evaluator.evaluate_async(
            original_query,
            specialist_response,
            brand_voice_output,
            user_context,
            brand_tracker
        )
    except Exception as e:
        # Never let evaluation errors crash the main flow
        print(f"⚠️  Background evaluation failed: {e}")

