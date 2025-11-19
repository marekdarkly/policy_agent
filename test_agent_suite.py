"""
Comprehensive Agent Test Suite

Runs full agent circuits (initialize → route → answer → evaluate → terminate)
for automated testing and performance benchmarking.

This script:
1. Loads Q&A dataset (50 demo-optimized questions by default)
2. Runs N iterations with random questions
3. Each iteration is a complete circuit (matching backend server exactly)
4. Includes all metrics, observability, and evaluation
5. Outputs results in CSV format for LaunchDarkly analysis
6. Supports per-agent evaluation (--evaluate policy_agent|provider_agent|brand_agent) for A/B testing
"""

import os
import sys
import json
import random
import time
import asyncio
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

# Suppress noisy logs for test suite
import logging
import warnings

# Suppress all botocore, boto3, ldclient, httpx, and observability logs
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("ldclient").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
logging.getLogger("src.utils.observability").setLevel(logging.CRITICAL)
logging.getLogger("src.utils.launchdarkly_config").setLevel(logging.WARNING)

# Suppress span-related warnings
warnings.filterwarnings("ignore", message=".*ended span.*")
warnings.filterwarnings("ignore", message=".*Setting attribute.*")

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Initialize observability BEFORE any LLM imports (but suppress its logs)
from src.utils.observability import initialize_observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

# Import workflow and utilities (SAME as backend server)
from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile
import ldclient

# Test configuration
NUM_ITERATIONS = int(os.getenv("TEST_ITERATIONS", "50"))  # Number of test runs (configurable)
DATASET_PATH = os.getenv("DATASET_PATH", "test_data/qa_dataset_demo.json")  # Use demo dataset by default
RESULTS_DIR = "test_results"

# Ensure results directory exists
Path(RESULTS_DIR).mkdir(exist_ok=True)

# Global variable for per-agent evaluation mode (set by CLI args)
EVALUATE_AGENT: Optional[str] = None

class AgentTestRunner:
    """Runs automated agent tests with full metrics and evaluation."""
    
    def __init__(self, dataset_path: str, evaluate_agent: Optional[str] = None):
        """Initialize test runner with Q&A dataset.
        
        Args:
            dataset_path: Path to Q&A dataset JSON
            evaluate_agent: Optional agent to evaluate (policy_agent, provider_agent, scheduler_agent, brand_agent)
                           If set, will evaluate only that agent and skip end-to-end testing
                           - policy_agent/provider_agent: Evaluates accuracy
                           - brand_agent: Evaluates coherence
                           - scheduler_agent: No evaluation (just metrics)
        """
        full_dataset = self._load_dataset(dataset_path)
        
        # Filter dataset based on agent being evaluated
        if evaluate_agent == "brand_agent":
            # Brand agent only processes policy questions
            self.dataset = {
                "metadata": full_dataset["metadata"],
                "questions": [q for q in full_dataset["questions"] if q.get("expected_route") == "POLICY_QUESTION"]
            }
            print(f"🔍 Filtered dataset to {len(self.dataset['questions'])} POLICY_QUESTION questions for brand_agent evaluation")
        else:
            self.dataset = full_dataset
        
        self.results = []
        self.evaluation_results_store = {}  # Shared store for evaluations
        self.brand_trackers_store = {}  # Shared store for brand trackers
        self.evaluate_agent = evaluate_agent
        
    def _load_dataset(self, path: str) -> Dict:
        """Load Q&A dataset from JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def get_random_question(self) -> Dict:
        """Get a random question from the dataset."""
        return random.choice(self.dataset['questions'])
    
    def create_test_user(self, question_data: Dict, iteration: int) -> Dict:
        """Create user profile for testing.
        
        Creates random unique users while maintaining Gold plan attributes for segment matching.
        """
        # Random names for variety
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn", "Dakota", "Sage"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        
        # Random locations (keeping US cities)
        locations = [
            "San Francisco, CA",
            "New York, NY", 
            "Boston, MA",
            "Austin, TX",
            "Seattle, WA",
            "Chicago, IL",
            "Denver, CO",
            "Portland, OR"
        ]
        
        # Generate random user
        random_name = f"{random.choice(first_names)} {random.choice(last_names)}"
        random_location = random.choice(locations)
        
        profile = create_user_profile(
            name=random_name,
            location=random_location,
            policy_id="TH-HMO-GOLD-2024",
            coverage_type="Gold HMO"  # KEEP GOLD for segment matching
        )
        
        # OVERRIDE user_key with UUID for LaunchDarkly split test bucketing
        profile["user_key"] = f"test-user-{uuid4()}"
        
        # Ensure Gold plan attributes are set for segment matching
        profile["plan_tier"] = 3  # Gold = 3
        profile["customer_tier"] = "gold"
        profile["customer_segment"] = "gold_member"
        
        return profile
    
    async def run_single_test(self, iteration: int, question_data: Dict) -> Dict:
        """Run a single test iteration (full circuit or per-agent).
        
        This mirrors the backend server's /api/chat endpoint exactly.
        If self.evaluate_agent is set, will evaluate only that agent.
        """
        request_id = str(uuid4())
        start_time = time.time()
        
        question_id = question_data['id']
        question_text = question_data['question']
        expected_route = question_data.get('expected_route', 'UNKNOWN')
        
        # Create user context (same as backend server)
        # Randomize user key for split test distribution
        user_context = self.create_test_user(question_data, iteration)
        
        print(f"\n{'='*80}")
        print(f"🧪 Test {iteration}/{NUM_ITERATIONS} - {question_id}")
        print(f"{'='*80}")
        print(f"❓ Question: {question_text}")
        if self.evaluate_agent:
            print(f"🎯 Evaluating: {self.evaluate_agent}")
        else:
            print(f"🎯 Expected Route: {expected_route}")
        print(f"👤 User: {user_context.get('name')} (key: {user_context.get('user_key')})")
        
        try:
            
            # Run workflow (with evaluation mode if set)
            result = await asyncio.to_thread(
                run_workflow,
                user_message=question_text,
                user_context=user_context,
                request_id=request_id,
                evaluation_results_store=self.evaluation_results_store,
                brand_trackers_store=self.brand_trackers_store,
                evaluate_agent=self.evaluate_agent  # Pass evaluation mode to workflow
            )
            
            total_duration = int((time.time() - start_time) * 1000)  # ms
            
            # Extract metrics (SAME as backend server)
            final_response = result.get("final_response", "")
            query_type = result.get("query_type", "UNKNOWN")
            agent_data = result.get("agent_data", {})
            confidence = result.get("confidence_score", 0)
            
            # PER-AGENT EVALUATION MODE
            if self.evaluate_agent:
                # Map agent names to keys in agent_data
                agent_key_map = {
                    "policy_agent": "policy_specialist",
                    "provider_agent": "provider_specialist",
                    "scheduler_agent": "scheduler_specialist",
                    "brand_agent": "brand_voice"
                }
                
                target_key = agent_key_map.get(self.evaluate_agent)
                
                # Check if this agent was used in this test
                if target_key not in agent_data:
                    print(f"   ⏭️  SKIPPED - {self.evaluate_agent} not used for this question")
                    return None  # Skip this test
                
                # Agent was used
                print(f"   ✅ {self.evaluate_agent} was used")
                
                target_agent_data = agent_data[target_key]
                agent_output = target_agent_data.get("response", "")
                rag_documents = target_agent_data.get("rag_documents", [])
                
                # Extract cost metrics (no jitter - actual metrics)
                agent_duration_ms = target_agent_data.get("duration_ms", 0)
                agent_ttft_ms = target_agent_data.get("ttft_ms", 0)
                
                tokens = target_agent_data.get("tokens", {})
                tokens_input = tokens.get("input", 0)
                tokens_output = tokens.get("output", 0)
                total_tokens = tokens_input + tokens_output
                agent_model = target_agent_data.get("model", "unknown")
                
                # For scheduler agent, just terminate without evaluation
                if self.evaluate_agent == "scheduler_agent":
                    print(f"   ⏹️  Scheduler agent - terminating without evaluation")
                    print(f"   💰 Cost Metrics:")
                    print(f"      Model: {agent_model}")
                    print(f"      Duration: {agent_duration_ms}ms")
                    print(f"      TTFT: {agent_ttft_ms}ms")
                    print(f"      Tokens: {total_tokens} (in: {tokens_input}, out: {tokens_output})")
                    
                    test_result = {
                        "iteration": iteration,
                        "question_id": question_id,
                        "agent": self.evaluate_agent,
                        "agent_used": True,
                        "accuracy_score": None,  # No evaluation for scheduler
                        "passed": None,
                        "reason": "Scheduler agent - no evaluation",
                        "model": agent_model,
                        "duration_ms": agent_duration_ms,
                        "ttft_ms": agent_ttft_ms,
                        "tokens_input": tokens_input,
                        "tokens_output": tokens_output,
                        "total_tokens": total_tokens,
                    }
                    
                    self.results.append(test_result)
                    return test_result
                
                # For brand agent, evaluate both accuracy and coherence
                if self.evaluate_agent == "brand_agent":
                    print(f"   🧪 Evaluating brand_agent (accuracy + coherence)...")
                    
                    # Get specialist response for context
                    specialist_response = ""
                    if "policy_specialist" in agent_data:
                        specialist_response = agent_data["policy_specialist"].get("response", "")
                    elif "provider_specialist" in agent_data:
                        specialist_response = agent_data["provider_specialist"].get("response", "")
                    elif "scheduler_specialist" in agent_data:
                        specialist_response = agent_data["scheduler_specialist"].get("response", "")
                    
                    # Get RAG documents from specialist for accuracy evaluation
                    rag_documents = []
                    if "policy_specialist" in agent_data:
                        rag_documents = agent_data["policy_specialist"].get("rag_documents", [])
                    elif "provider_specialist" in agent_data:
                        rag_documents = agent_data["provider_specialist"].get("rag_documents", [])
                    
                    # Run brand voice evaluation (both accuracy and coherence)
                    from src.evaluation.judge import evaluate_brand_voice_async
                    
                    eval_result = await evaluate_brand_voice_async(
                        original_query=question_text,
                        rag_documents=rag_documents,
                        brand_voice_output=agent_output,
                        user_context=user_context
                    )
                    
                    # Extract both metrics
                    accuracy_score = eval_result.get("accuracy", 0.0)
                    accuracy_passed = eval_result.get("accuracy_passed", False)
                    coherence_score = eval_result.get("coherence", 0.0)
                    coherence_passed = coherence_score >= 0.7  # 70% threshold
                    
                    print(f"   📊 Brand Accuracy: {accuracy_score:.2f} {'✅ PASS' if accuracy_passed else '❌ FAIL'}")
                    print(f"   Reason: {eval_result.get('accuracy_reasoning', 'N/A')}")
                    print(f"   📊 Brand Coherence: {coherence_score:.2f} {'✅ PASS' if coherence_passed else '❌ FAIL'}")
                    print(f"   Reason: {eval_result.get('coherence_reasoning', 'N/A')}")
                    print(f"   💰 Cost Metrics:")
                    print(f"      Model: {agent_model}")
                    print(f"      Duration: {agent_duration_ms}ms")
                    print(f"      TTFT: {agent_ttft_ms}ms")
                    print(f"      Tokens: {total_tokens} (in: {tokens_input}, out: {tokens_output})")
                    
                    # Send metrics to LaunchDarkly
                    try:
                        import ldclient
                        ld_client = ldclient.get()
                        
                        if ld_client and ld_client.is_initialized():
                            # Create LD context
                            from ldclient import Context
                            ld_context = Context.builder(user_context.get("user_key", "test-user")).build()
                            
                            # Track accuracy to TWO places (same value)
                            ld_client.track("$ld:ai:hallucinations", ld_context, accuracy_score)
                            ld_client.track("$ld:ai:judge:accuracy", ld_context, accuracy_score)
                            
                            # Track coherence
                            ld_client.track("$ld:ai:coherence", ld_context, coherence_score)
                            
                            ld_client.flush()
                            
                            print(f"   📊 Sent to LaunchDarkly:")
                            print(f"      $ld:ai:hallucinations: {accuracy_score:.2f}")
                            print(f"      $ld:ai:judge:accuracy: {accuracy_score:.2f}")
                            print(f"      $ld:ai:coherence: {coherence_score:.2f}")
                    except Exception as e:
                        print(f"   ⚠️  Failed to send metrics to LaunchDarkly: {e}")
                    
                    test_result = {
                        "iteration": iteration,
                        "question_id": question_id,
                        "agent": self.evaluate_agent,
                        "agent_used": True,
                        "accuracy_score": accuracy_score,
                        "accuracy_passed": accuracy_passed,
                        "accuracy_reason": eval_result.get('accuracy_reasoning', 'N/A'),
                        "coherence_score": coherence_score,
                        "coherence_passed": coherence_passed,
                        "coherence_reason": eval_result.get('coherence_reasoning', 'N/A'),
                        "passed": accuracy_passed and coherence_passed,  # Both must pass
                        "model": agent_model,
                        "duration_ms": agent_duration_ms,
                        "ttft_ms": agent_ttft_ms,
                        "tokens_input": tokens_input,
                        "tokens_output": tokens_output,
                        "total_tokens": total_tokens,
                    }
                    
                    self.results.append(test_result)
                    return test_result
                
                # For policy/provider agents, evaluate accuracy
                print(f"   🧪 Evaluating {self.evaluate_agent}...")
                
                # Run per-agent evaluation
                from src.evaluation.agent_evaluator import evaluate_agent_accuracy
                
                eval_result = await evaluate_agent_accuracy(
                    agent_name=self.evaluate_agent,
                    original_query=question_text,
                    rag_documents=rag_documents,
                    agent_output=agent_output,
                    user_context=user_context
                )
                
                print(f"   📊 Agent Accuracy: {eval_result['score']:.2f} {'✅ PASS' if eval_result['passed'] else '❌ FAIL'}")
                print(f"   Reason: {eval_result['reason']}")
                print(f"   💰 Cost Metrics:")
                print(f"      Model: {agent_model}")
                print(f"      Duration: {agent_duration_ms}ms")
                print(f"      TTFT: {agent_ttft_ms}ms")
                print(f"      Tokens: {total_tokens} (in: {tokens_input}, out: {tokens_output})")
                
                # Send two additional fabricated metrics to LaunchDarkly
                # These are for demo purposes and based on accuracy pass/fail
                resolution_value = 0.0
                negative_feedback = False
                
                try:
                    import ldclient
                    from ldclient import Context
                    
                    ld_client_raw = ldclient.get()
                    context_builder = Context.builder(user_context.get("user_key", "test-user"))
                    context_builder.kind("user")
                    ld_context = context_builder.build()
                    
                    # Calculate resolution metric based on accuracy
                    # If accuracy passes: 80% chance = 1.0, 20% chance = 0.0
                    # If accuracy fails: 30% chance = 1.0, 70% chance = 0.0
                    if eval_result['passed']:
                        resolution_value = 1.0 if random.random() < 0.80 else 0.0
                    else:
                        resolution_value = 1.0 if random.random() < 0.30 else 0.0
                    
                    # Calculate negative feedback metric based on accuracy
                    # If accuracy passes: 3% chance = true
                    # If accuracy fails: 40% chance = true
                    if eval_result['passed']:
                        negative_feedback = random.random() < 0.03
                    else:
                        negative_feedback = random.random() < 0.40
                    
                    # Send resolution metric
                    ld_client_raw.track(
                        event_name="$ld:customer:resolution",
                        context=ld_context,
                        metric_value=float(resolution_value)
                    )
                    
                    # Send negative feedback metric (boolean)
                    if negative_feedback:
                        ld_client_raw.track(
                            event_name="$ld:ai:feedback:user:negative",
                            context=ld_context,
                            metric_value=1.0  # LaunchDarkly numeric representation of boolean
                        )
                    
                    print(f"   📊 Demo Metrics Sent:")
                    print(f"      Resolution: {resolution_value}")
                    print(f"      Negative Feedback: {negative_feedback}")
                    
                except Exception as e:
                    print(f"   ⚠️  Failed to send demo metrics: {e}")
                
                # Result record with evaluation + cost metrics + demo metrics
                test_result = {
                    "iteration": iteration,
                    "question_id": question_id,
                    "agent": self.evaluate_agent,
                    "agent_used": True,
                    "accuracy_score": eval_result["score"],
                    "passed": eval_result["passed"],
                    "reason": eval_result["reason"],
                    "model": agent_model,
                    "duration_ms": agent_duration_ms,
                    "ttft_ms": agent_ttft_ms,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "total_tokens": total_tokens,
                    "resolution": resolution_value,
                    "negative_feedback": negative_feedback,
                }
                
                self.results.append(test_result)
                return test_result
            
            # FULL END-TO-END EVALUATION MODE (default)
            # Wait for evaluation to complete (background thread)
            # Poll for up to 30 seconds (same as UI frontend)
            print(f"   ⏳ Waiting for evaluation to complete...")
            eval_data = {}
            for attempt in range(60):  # 60 attempts * 0.5s = 30s max
                await asyncio.sleep(0.5)
                
                # Check if evaluation results are available
                if request_id in self.evaluation_results_store:
                    eval_data = self.evaluation_results_store[request_id]
                    print(f"   ✅ Evaluation complete after {(attempt + 1) * 0.5:.1f}s")
                    break
            
            if not eval_data:
                print(f"   ⚠️  Evaluation not completed within 30s timeout")
                eval_data = {}
            
            # Extract evaluation scores
            accuracy_score = eval_data.get("accuracy", {}).get("score", 0.0) if eval_data else 0.0
            coherence_score = eval_data.get("coherence", {}).get("score", 0.0) if eval_data else 0.0
            
            # Extract agent metrics
            triage_data = agent_data.get("triage_router", {})
            specialist_key = None
            specialist_data = {}
            specialist_response = ""
            
            if "policy_specialist" in agent_data:
                specialist_key = "policy_specialist"
                specialist_data = agent_data["policy_specialist"]
                specialist_response = specialist_data.get("response", "")
            elif "provider_specialist" in agent_data:
                specialist_key = "provider_specialist"
                specialist_data = agent_data["provider_specialist"]
                specialist_response = specialist_data.get("response", "")
            elif "scheduler_specialist" in agent_data:
                specialist_key = "scheduler_specialist"
                specialist_data = agent_data["scheduler_specialist"]
                specialist_response = specialist_data.get("response", "")
            
            brand_data = agent_data.get("brand_voice", {})
            
            # Extract model information from each agent
            triage_model = triage_data.get("model", "unknown")
            specialist_model = specialist_data.get("model", "unknown")
            brand_model = brand_data.get("model", "unknown")
            
            # Extract judge models from evaluation data
            accuracy_judge_model = eval_data.get("accuracy", {}).get("model", "unknown") if eval_data else "unknown"
            coherence_judge_model = eval_data.get("coherence", {}).get("model", "unknown") if eval_data else "unknown"
            
            # Build result record
            test_result = {
                "iteration": iteration,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "user_key": user_context.get("user_key", "unknown"),  # Track for split test analysis
                "user_name": user_context.get("name", "unknown"),
                "question_id": question_id,
                "question": question_text,
                "category": question_data.get("category", ""),
                "expected_route": expected_route,
                "actual_route": query_type.value if hasattr(query_type, 'value') else str(query_type),
                "route_match": (query_type.value if hasattr(query_type, 'value') else str(query_type)).upper() == expected_route.upper(),
                "confidence": float(confidence),
                "response_length": len(final_response),
                "total_duration_ms": total_duration,
                
                # Agent metrics
                "triage_model": triage_model,
                "triage_duration_ms": triage_data.get("duration_ms", 0),
                "triage_ttft_ms": triage_data.get("ttft_ms", 0),
                "triage_tokens_input": triage_data.get("tokens", {}).get("input", 0),
                "triage_tokens_output": triage_data.get("tokens", {}).get("output", 0),
                
                "specialist_type": specialist_key or "none",
                "specialist_model": specialist_model,
                "specialist_duration_ms": specialist_data.get("duration_ms", 0),
                "specialist_ttft_ms": specialist_data.get("ttft_ms", 0),
                "specialist_tokens_input": specialist_data.get("tokens", {}).get("input", 0),
                "specialist_tokens_output": specialist_data.get("tokens", {}).get("output", 0),
                "specialist_rag_docs": specialist_data.get("rag_documents_retrieved", 0),
                "specialist_response": specialist_response[:1000] if specialist_response else "",  # Truncate for CSV
                
                "brand_model": brand_model,
                "brand_duration_ms": brand_data.get("duration_ms", 0),
                "brand_ttft_ms": brand_data.get("ttft_ms", 0),
                "brand_tokens_input": brand_data.get("tokens", {}).get("input", 0),
                "brand_tokens_output": brand_data.get("tokens", {}).get("output", 0),
                "final_response": final_response[:1000] if final_response else "",  # Truncate for CSV
                
                # Evaluation metrics
                "accuracy_score": accuracy_score,
                "accuracy_judge_model": accuracy_judge_model,
                "coherence_score": coherence_score,
                "coherence_judge_model": coherence_judge_model,
                "accuracy_reasoning": eval_data.get("accuracy", {}).get("reasoning", "")[:200] if eval_data else "",  # Truncate
                
                # Status
                "status": "success",
                "error": None
            }
            
            # Print detailed summary including specialist outputs
            print(f"✅ SUCCESS")
            print(f"   Route: {query_type} {'✓' if test_result['route_match'] else '✗ Expected: ' + expected_route}")
            print(f"   Confidence: {confidence:.1f}%")
            print(f"   Duration: {total_duration}ms")
            print(f"   Models: Triage={triage_model}, Specialist={specialist_model}, Brand={brand_model}")
            print(f"   Judges: Accuracy={accuracy_judge_model}, Coherence={coherence_judge_model}")
            print(f"   Accuracy: {accuracy_score:.1f}%")
            print(f"   Coherence: {coherence_score:.1f}%")
            
            # Print specialist agent output for visibility (FULL output, no truncation)
            if specialist_response:
                print(f"\n   📋 SPECIALIST OUTPUT ({specialist_key}):")
                print(f"   {'-' * 76}")
                # Print FULL specialist output (user needs to see complete RAG-based responses)
                specialist_lines = specialist_response.split('\n')
                for line in specialist_lines:
                    print(f"   {line}")
                print(f"   {'-' * 76}")
            
            # Print final customer-facing response (FULL output, no truncation)
            print(f"\n   💬 FINAL RESPONSE (Brand Voice):")
            print(f"   {'-' * 76}")
            response_lines = final_response.split('\n')
            for line in response_lines:
                print(f"   {line}")
            print(f"   {'-' * 76}")
            
            return test_result
            
        except Exception as e:
            total_duration = int((time.time() - start_time) * 1000)
            
            print(f"❌ FAILED: {str(e)[:100]}")
            
            return {
                "iteration": iteration,
                "request_id": request_id,
                "timestamp": datetime.now().isoformat(),
                "question_id": question_id,
                "question": question_text,
                "category": question_data.get("category", ""),
                "expected_route": expected_route,
                "actual_route": "ERROR",
                "route_match": False,
                "confidence": 0.0,
                "total_duration_ms": total_duration,
                "status": "error",
                "error": str(e)[:500]
            }
    
    async def run_test_suite(self, num_iterations: int):
        """Run the full test suite."""
        print(f"\n{'='*80}")
        print(f"🚀 STARTING AGENT TEST SUITE")
        print(f"{'='*80}")
        print(f"📊 Iterations: {num_iterations}")
        print(f"📚 Dataset: {len(self.dataset['questions'])} questions")
        print(f"🎯 Categories: {', '.join(self.dataset['metadata']['categories'])}")
        print(f"{'='*80}\n")
        
        for i in range(1, num_iterations + 1):
            # Progress indicator at the start of each iteration
            print(f"\n{'='*80}")
            print(f"⏳ PROGRESS: {i}/{num_iterations} ({100*i/num_iterations:.1f}% complete)")
            print(f"{'='*80}")
            
            # Get random question
            question_data = self.get_random_question()
            
            # Run single test (full circuit or per-agent)
            result = await self.run_single_test(i, question_data)
            
            # Skip if result is None (agent not used in per-agent mode)
            if result is None:
                continue
            
            # Store result
            self.results.append(result)
            
            # Show running statistics every 10 iterations
            if i % 10 == 0 and i > 0:
                if self.evaluate_agent:
                    # Per-agent evaluation stats
                    evaluated = [r for r in self.results if r.get('agent_used')]
                    if evaluated:
                        # Accuracy stats (only for policy/provider agents)
                        evaluated_with_scores = [r for r in evaluated if r.get('accuracy_score') is not None]
                        if evaluated_with_scores:
                            avg_accuracy = sum(r['accuracy_score'] for r in evaluated_with_scores) / len(evaluated_with_scores)
                            passed = [r for r in evaluated_with_scores if r['passed']]
                            
                        # Cost stats (for all agents including scheduler)
                        avg_duration = sum(r.get('duration_ms', 0) for r in evaluated) / len(evaluated)
                        avg_tokens = sum(r.get('total_tokens', 0) for r in evaluated) / len(evaluated)
                        
                        print(f"\n📊 RUNNING STATS ({self.evaluate_agent}) - after {i} attempts:")
                        print(f"   Tests where agent used: {len(evaluated)}/{i}")
                        
                        if evaluated_with_scores:
                            print(f"   Avg Accuracy: {avg_accuracy:.1%}")
                            print(f"   Passed: {len(passed)}/{len(evaluated_with_scores)} ({100*len(passed)/len(evaluated_with_scores):.1f}%)")
                        
                        print(f"   Avg Duration: {avg_duration:.0f}ms")
                        print(f"   Avg Tokens: {avg_tokens:.0f}")
                        print()
                else:
                    # Full end-to-end stats
                    successful = [r for r in self.results if r.get('status') == 'success']
                    if successful:
                        avg_accuracy = sum(r['accuracy_score'] for r in successful) / len(successful)
                        avg_coherence = sum(r['coherence_score'] for r in successful) / len(successful)
                        route_matches = [r for r in successful if r.get('route_match')]
                        print(f"\n📊 RUNNING STATS (after {i} tests):")
                        print(f"   Avg Accuracy: {avg_accuracy:.1%}")
                        print(f"   Avg Coherence: {avg_coherence:.1%}")
                        print(f"   Routing Accuracy: {len(route_matches)}/{len(successful)} ({100*len(route_matches)/len(successful):.1f}%)")
                        print()
            
            # Small delay between iterations
            await asyncio.sleep(0.5)
        
        # Final summary
        self._print_summary()
        
        # Save results
        self._save_results()
    
    def _print_summary(self):
        """Print test suite summary."""
        print(f"\n{'='*80}")
        print(f"📊 TEST SUITE COMPLETE")
        print(f"{'='*80}\n")
        
        if self.evaluate_agent:
            # Per-agent evaluation summary
            evaluated = [r for r in self.results if r.get('agent_used')]
            
            print(f"Agent: {self.evaluate_agent}")
            print(f"✅ Tests where agent used: {len(evaluated)}")
            
            if evaluated:
                # Accuracy stats (only for policy/provider agents)
                evaluated_with_scores = [r for r in evaluated if r.get('accuracy_score') is not None]
                
                if evaluated_with_scores:
                    avg_accuracy = sum(r['accuracy_score'] for r in evaluated_with_scores) / len(evaluated_with_scores)
                    passed = [r for r in evaluated_with_scores if r['passed']]
                    
                    print(f"\n🎯 Avg Accuracy: {avg_accuracy:.1%}")
                    print(f"✅ Passed: {len(passed)}/{len(evaluated_with_scores)} ({100*len(passed)/len(evaluated_with_scores):.1f}%)")
                    print(f"❌ Failed: {len(evaluated_with_scores) - len(passed)}/{len(evaluated_with_scores)}")
                
                # Cost metrics (for all agents including scheduler)
                avg_duration = sum(r.get('duration_ms', 0) for r in evaluated) / len(evaluated)
                avg_tokens = sum(r.get('total_tokens', 0) for r in evaluated) / len(evaluated)
                avg_ttft = sum(r.get('ttft_ms', 0) for r in evaluated) / len(evaluated)
                total_tokens = sum(r.get('total_tokens', 0) for r in evaluated)
                
                print(f"\n💰 Cost Metrics:")
                print(f"   Avg Duration: {avg_duration:.0f}ms")
                print(f"   Avg TTFT: {avg_ttft:.0f}ms")
                print(f"   Avg Tokens/Test: {avg_tokens:.0f}")
                print(f"   Total Tokens: {total_tokens:,}")
            
            return  # Skip full stats for per-agent mode
        
        # Full end-to-end summary
        successful = [r for r in self.results if r.get('status') == 'success']
        failed = [r for r in self.results if r.get('status') == 'error']
        
        print(f"✅ Successful: {len(successful)}/{len(self.results)}")
        print(f"❌ Failed: {len(failed)}/{len(self.results)}")
        
        if successful:
            # Routing accuracy
            route_matches = [r for r in successful if r.get('route_match')]
            print(f"\n🎯 Routing Accuracy: {len(route_matches)}/{len(successful)} ({100*len(route_matches)/len(successful):.1f}%)")
            
            # Average confidence
            avg_confidence = sum(r['confidence'] for r in successful) / len(successful)
            print(f"📊 Avg Confidence: {avg_confidence:.1f}%")
            
            # Average duration
            avg_duration = sum(r['total_duration_ms'] for r in successful) / len(successful)
            print(f"⏱️  Avg Duration: {avg_duration:.0f}ms")
            
            # Evaluation scores
            accuracy_scores = [r['accuracy_score'] for r in successful if r.get('accuracy_score')]
            if accuracy_scores:
                avg_accuracy = sum(accuracy_scores) / len(accuracy_scores)
                print(f"🎯 Avg Accuracy: {avg_accuracy:.1f}%")
            
            coherence_scores = [r['coherence_score'] for r in successful if r.get('coherence_score')]
            if coherence_scores:
                avg_coherence = sum(coherence_scores) / len(coherence_scores)
                print(f"📝 Avg Coherence: {avg_coherence:.1f}%")
            
            # Token usage
            total_tokens = sum(
                r.get('triage_tokens_input', 0) + r.get('triage_tokens_output', 0) +
                r.get('specialist_tokens_input', 0) + r.get('specialist_tokens_output', 0) +
                r.get('brand_tokens_input', 0) + r.get('brand_tokens_output', 0)
                for r in successful
            )
            print(f"🪙 Total Tokens: {total_tokens:,}")
            
            # Time to First Token
            ttft_values = [
                r.get('triage_ttft_ms', 0) + 
                r.get('specialist_ttft_ms', 0) + 
                r.get('brand_ttft_ms', 0)
                for r in successful if r.get('triage_ttft_ms')
            ]
            if ttft_values:
                avg_ttft = sum(ttft_values) / len(ttft_values)
                print(f"⚡ Avg Total TTFT: {avg_ttft:.0f}ms")
        
        if failed:
            print(f"\n❌ Errors:")
            for r in failed[:5]:  # Show first 5 errors
                print(f"   - {r['question_id']}: {r['error'][:100]}")
    
    def _save_results(self):
        """Save results to CSV and JSON files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save as JSON (full detail)
        json_path = f"{RESULTS_DIR}/test_results_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                "metadata": {
                    "timestamp": timestamp,
                    "iterations": len(self.results),
                    "dataset": self.dataset['metadata']
                },
                "results": self.results
            }, f, indent=2)
        
        print(f"\n💾 Results saved:")
        print(f"   JSON: {json_path}")
        
        # Save as CSV (for analysis)
        csv_path = f"{RESULTS_DIR}/test_results_{timestamp}.csv"
        self._save_csv(csv_path)
        print(f"   CSV: {csv_path}")
    
    def _save_csv(self, path: str):
        """Save results as CSV file."""
        import csv
        
        if not self.results:
            return
        
        # Define CSV columns based on mode
        if self.evaluate_agent:
            # Per-agent evaluation columns
            if self.evaluate_agent == "brand_agent":
                # Brand agent uses both accuracy and coherence
                columns = [
                    "iteration", "question_id", "agent", "agent_used",
                    "accuracy_score", "accuracy_passed", "accuracy_reason",
                    "coherence_score", "coherence_passed", "coherence_reason",
                    "passed",
                    "model", "duration_ms", "ttft_ms",
                    "tokens_input", "tokens_output", "total_tokens"
                ]
            else:
                # Policy/Provider agents use accuracy
                columns = [
                    "iteration", "question_id", "agent", "agent_used",
                    "accuracy_score", "passed", "reason",
                    "model", "duration_ms", "ttft_ms",
                    "tokens_input", "tokens_output", "total_tokens",
                    "resolution", "negative_feedback"
                ]
        else:
            # Full end-to-end columns
            columns = [
                "iteration", "request_id", "timestamp", "user_key", "user_name",
                "question_id", "question",
                "category", "expected_route", "actual_route", "route_match",
                "confidence", "response_length", "total_duration_ms",
                "triage_model", "triage_duration_ms", "triage_ttft_ms", "triage_tokens_input", "triage_tokens_output",
                "specialist_type", "specialist_model", "specialist_duration_ms", "specialist_ttft_ms",
                "specialist_tokens_input", "specialist_tokens_output", "specialist_rag_docs", "specialist_response",
                "brand_model", "brand_duration_ms", "brand_ttft_ms", "brand_tokens_input", "brand_tokens_output", "final_response",
                "accuracy_score", "accuracy_judge_model", "coherence_score", "coherence_judge_model", "accuracy_reasoning",
                "status", "error"
            ]
        
        with open(path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for result in self.results:
                # Ensure all columns exist
                row = {col: result.get(col, "") for col in columns}
                writer.writerow(row)

async def main():
    """Main test execution."""
    print(f"\n{'='*80}")
    print(f"🧪 ToggleHealth Multi-Agent System - Automated Test Suite")
    print(f"{'='*80}")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if EVALUATE_AGENT:
        print(f"🎯 Mode: Per-Agent Evaluation (Agent: {EVALUATE_AGENT})")
        print(f"   - Will run tests up to {EVALUATE_AGENT}")
        print(f"   - Will evaluate only that agent's output")
        print(f"   - Will skip tests where agent is not used")
    else:
        print(f"🔬 Mode: Full Circuit (Initialize → Route → Answer → Evaluate → Terminate)")
    
    print(f"📡 Observability: Enabled (traces → LaunchDarkly)")
    print(f"🎯 Evaluation: Enabled (G-Eval judges)")
    print(f"{'='*80}\n")
    
    # Check LaunchDarkly client is initialized
    if ldclient.get().is_initialized():
        print("✅ LaunchDarkly client initialized")
    else:
        print("⚠️  LaunchDarkly client not fully initialized, waiting...")
        await asyncio.sleep(2)
    
    # Initialize test runner with evaluation mode
    runner = AgentTestRunner(DATASET_PATH, evaluate_agent=EVALUATE_AGENT)
    
    # Run test suite
    try:
        await runner.run_test_suite(NUM_ITERATIONS)
        
        print(f"\n{'='*80}")
        print(f"✅ ALL TESTS COMPLETE")
        print(f"{'='*80}\n")
        
        print("📊 Check LaunchDarkly for:")
        print("   - AI Config Monitoring tabs (metrics per agent)")
        print("   - Traces (observability data)")
        print("   - Experiments (if you set up A/B tests)")
        
        print("\n📈 Analyze results in:")
        print(f"   - {RESULTS_DIR}/test_results_*.csv (import to spreadsheet)")
        print(f"   - {RESULTS_DIR}/test_results_*.json (full details)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        runner._save_results()
        print("   Partial results saved")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        runner._save_results()
    finally:
        # Flush LaunchDarkly metrics
        print("\n🔄 Flushing metrics to LaunchDarkly...")
        ldclient.get().flush()
        await asyncio.sleep(2)
        print("   ✅ Flushed")
        
        # Close LaunchDarkly client
        ldclient.get().close()
        print("   ✅ Closed LaunchDarkly client")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="ToggleHealth Multi-Agent Test Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full end-to-end tests (default)
  python test_agent_suite.py

  # Evaluate only the policy agent
  python test_agent_suite.py --evaluate policy_agent

  # Evaluate only the provider agent  
  python test_agent_suite.py --evaluate provider_agent

  # Evaluate scheduler agent
  python test_agent_suite.py --evaluate scheduler_agent
  
  # Evaluate brand voice agent (accuracy + coherence)
  python test_agent_suite.py --evaluate brand_agent
        """
    )
    parser.add_argument(
        "--evaluate",
        choices=["policy_agent", "provider_agent", "scheduler_agent", "brand_agent"],
        help="Evaluate a specific agent only (stops after that agent executes)"
    )
    
    args = parser.parse_args()
    
    # Set global evaluation mode
    EVALUATE_AGENT = args.evaluate
    
    # Run async main
    asyncio.run(main())

