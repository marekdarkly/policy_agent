#!/usr/bin/env python3
"""
Agent Evaluation Test Suite

Runs tests where:
1. Triage naturally chooses which agent to use
2. Whichever agent is chosen gets evaluated (policy/provider) or cost-tracked (scheduler)
3. Workflow terminates after specialist (no brand_voice)
4. Restarts with next question

Usage:
    python test_agent_evaluation.py
    
    # Configure iterations and dataset via environment variables:
    TEST_ITERATIONS=100 python test_agent_evaluation.py
    DATASET_PATH=test_data/qa_dataset.json python test_agent_evaluation.py
"""

import os
import sys
import json
import random
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv()

# Suppress noisy logs
import logging
import warnings

logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("ldclient").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
logging.getLogger("src.utils.observability").setLevel(logging.CRITICAL)
logging.getLogger("src.utils.launchdarkly_config").setLevel(logging.WARNING)

warnings.filterwarnings("ignore", message=".*ended span.*")
warnings.filterwarnings("ignore", message=".*Setting attribute.*")

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Initialize observability
from src.utils.observability import initialize_observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

# Import workflow and utilities
from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile
from src.evaluation.agent_evaluator import evaluate_agent_accuracy
import ldclient

# Configuration
NUM_ITERATIONS = int(os.getenv("TEST_ITERATIONS", "50"))
DATASET_PATH = os.getenv("DATASET_PATH", "test_data/qa_dataset_demo.json")
RESULTS_DIR = "test_results"

Path(RESULTS_DIR).mkdir(exist_ok=True)

# Agent name mapping
AGENT_KEY_MAP = {
    "policy_specialist": "policy_agent",
    "provider_specialist": "provider_agent",
    "scheduler_specialist": "scheduler_agent"
}


class AgentEvaluationRunner:
    """Runs agent evaluation tests with automatic agent detection."""
    
    def __init__(self, dataset_path: str):
        self.dataset = self._load_dataset(dataset_path)
        self.results = []
        
    def _load_dataset(self, path: str) -> Dict:
        """Load Q&A dataset from JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def get_random_question(self) -> Dict:
        """Get a random question from the dataset."""
        return random.choice(self.dataset['questions'])
    
    def create_test_user(self, iteration: int) -> Dict:
        """Create user profile for testing."""
        profile = create_user_profile(
            name="Marek Poliks",
            location="San Francisco, CA",
            policy_id="TH-HMO-GOLD-2024",
            coverage_type="Gold HMO"
        )
        # Randomize user_key for LaunchDarkly bucketing
        profile["user_key"] = f"test-user-{uuid4()}"
        return profile
    
    async def run_single_test(self, iteration: int, question_data: Dict) -> Dict:
        """Run a single test iteration with automatic agent evaluation."""
        start_time = time.time()
        
        question_id = question_data['id']
        question_text = question_data['question']
        expected_route = question_data.get('expected_route', 'UNKNOWN')
        
        user_context = self.create_test_user(iteration)
        
        print(f"\n{'='*80}")
        print(f"🧪 Test {iteration}/{NUM_ITERATIONS} - {question_id}")
        print(f"{'='*80}")
        print(f"❓ Question: {question_text}")
        print(f"🎯 Expected Route: {expected_route}")
        print(f"👤 User: {user_context.get('name')} (key: {user_context.get('user_key')})")
        
        try:
            # Run workflow with ALWAYS_EVALUATE mode (terminates after specialist)
            result = await asyncio.to_thread(
                run_workflow,
                user_message=question_text,
                user_context=user_context,
                evaluate_agent="auto"  # Special flag to terminate after any specialist
            )
            
            total_duration = int((time.time() - start_time) * 1000)
            
            # Extract agent data
            agent_data = result.get("agent_data", {})
            query_type = result.get("query_type", "UNKNOWN")
            
            # Determine which specialist was used
            specialist_key = None
            for key in ["policy_specialist", "provider_specialist", "scheduler_specialist"]:
                if key in agent_data:
                    specialist_key = key
                    break
            
            if not specialist_key:
                print(f"   ❌ No specialist agent found in result")
                return None
            
            agent_name = AGENT_KEY_MAP[specialist_key]
            print(f"   ✅ Triage chose: {agent_name}")
            
            # Extract agent metrics
            target_agent_data = agent_data[specialist_key]
            agent_output = target_agent_data.get("response", "")
            rag_documents = target_agent_data.get("rag_documents", [])
            
            # Extract cost metrics (no jitter - actual metrics)
            duration_ms = target_agent_data.get("duration_ms", 0)
            ttft_ms = target_agent_data.get("ttft_ms", 0)
            
            tokens = target_agent_data.get("tokens", {})
            tokens_input = tokens.get("input", 0)
            tokens_output = tokens.get("output", 0)
            total_tokens = tokens_input + tokens_output
            model = target_agent_data.get("model", "unknown")
            
            print(f"   💰 Cost Metrics:")
            print(f"      Model: {model}")
            print(f"      Duration: {duration_ms}ms, TTFT: {ttft_ms}ms")
            print(f"      Tokens: {total_tokens} (in: {tokens_input}, out: {tokens_output})")
            
            # Verify brand_voice did NOT execute
            if "brand_voice" in agent_data:
                print(f"   ⚠️  WARNING: brand_voice executed (should not happen!)")
            
            # For scheduler, just track cost (no evaluation)
            if agent_name == "scheduler_agent":
                print(f"   ⏹️  Scheduler agent - cost tracking only (no evaluation)")
                
                test_result = {
                    "iteration": iteration,
                    "question_id": question_id,
                    "question": question_text,
                    "expected_route": expected_route,
                    "actual_route": str(query_type),
                    "agent": agent_name,
                    "accuracy_score": None,
                    "passed": None,
                    "reason": "Scheduler - no evaluation",
                    "model": model,
                    "duration_ms": duration_ms,
                    "ttft_ms": ttft_ms,
                    "tokens_input": tokens_input,
                    "tokens_output": tokens_output,
                    "total_tokens": total_tokens,
                }
                
                return test_result
            
            # For policy/provider agents, evaluate
            print(f"   🧪 Evaluating {agent_name}...")
            
            eval_result = await evaluate_agent_accuracy(
                agent_name=agent_name,
                original_query=question_text,
                rag_documents=rag_documents,
                agent_output=agent_output,
                user_context=user_context
            )
            
            passed_str = "✅ PASS" if eval_result['passed'] else "❌ FAIL"
            print(f"   📊 Accuracy: {eval_result['score']:.2f} {passed_str}")
            print(f"   📝 Reason: {eval_result['reason']}")
            
            test_result = {
                "iteration": iteration,
                "question_id": question_id,
                "question": question_text,
                "expected_route": expected_route,
                "actual_route": str(query_type),
                "agent": agent_name,
                "accuracy_score": eval_result["score"],
                "passed": eval_result["passed"],
                "reason": eval_result["reason"],
                "model": model,
                "duration_ms": duration_ms,
                "ttft_ms": ttft_ms,
                "tokens_input": tokens_input,
                "tokens_output": tokens_output,
                "total_tokens": total_tokens,
            }
            
            return test_result
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:200]}")
            import traceback
            traceback.print_exc()
            return None
    
    async def run_test_suite(self, num_iterations: int):
        """Run the full test suite."""
        print(f"\n{'='*80}")
        print(f"🚀 AGENT EVALUATION TEST SUITE")
        print(f"{'='*80}")
        print(f"📊 Iterations: {num_iterations}")
        print(f"📚 Dataset: {len(self.dataset['questions'])} questions")
        print(f"🎯 Mode: Evaluate whichever agent triage chooses")
        print(f"⚡ No brand_voice execution (terminates after specialist)")
        print(f"{'='*80}\n")
        
        for i in range(1, num_iterations + 1):
            # Get random question
            question_data = self.get_random_question()
            
            # Run test
            result = await self.run_single_test(i, question_data)
            
            if result:
                self.results.append(result)
            
            # Running stats every 10 iterations
            if i % 10 == 0 and len(self.results) > 0:
                self._print_running_stats(i)
            
            # Brief delay
            await asyncio.sleep(0.5)
        
        # Final summary
        self._print_summary()
        
        # Save results
        self._save_results()
    
    def _print_running_stats(self, iteration: int):
        """Print running statistics."""
        print(f"\n{'='*80}")
        print(f"📊 RUNNING STATS - after {iteration} tests")
        print(f"{'='*80}")
        
        # Group by agent
        policy_results = [r for r in self.results if r['agent'] == 'policy_agent']
        provider_results = [r for r in self.results if r['agent'] == 'provider_agent']
        scheduler_results = [r for r in self.results if r['agent'] == 'scheduler_agent']
        
        if policy_results:
            evaluated = [r for r in policy_results if r['accuracy_score'] is not None]
            if evaluated:
                avg_acc = sum(r['accuracy_score'] for r in evaluated) / len(evaluated)
                passed = sum(1 for r in evaluated if r['passed'])
                avg_dur = sum(r['duration_ms'] for r in policy_results) / len(policy_results)
                avg_tok = sum(r['total_tokens'] for r in policy_results) / len(policy_results)
                
                print(f"\n📋 Policy Agent ({len(policy_results)} tests):")
                print(f"   Accuracy: {avg_acc:.1%}, Passed: {passed}/{len(evaluated)}")
                print(f"   Avg Duration: {avg_dur:.0f}ms, Avg Tokens: {avg_tok:.0f}")
        
        if provider_results:
            evaluated = [r for r in provider_results if r['accuracy_score'] is not None]
            if evaluated:
                avg_acc = sum(r['accuracy_score'] for r in evaluated) / len(evaluated)
                passed = sum(1 for r in evaluated if r['passed'])
                avg_dur = sum(r['duration_ms'] for r in provider_results) / len(provider_results)
                avg_tok = sum(r['total_tokens'] for r in provider_results) / len(provider_results)
                
                print(f"\n🏥 Provider Agent ({len(provider_results)} tests):")
                print(f"   Accuracy: {avg_acc:.1%}, Passed: {passed}/{len(evaluated)}")
                print(f"   Avg Duration: {avg_dur:.0f}ms, Avg Tokens: {avg_tok:.0f}")
        
        if scheduler_results:
            avg_dur = sum(r['duration_ms'] for r in scheduler_results) / len(scheduler_results)
            avg_tok = sum(r['total_tokens'] for r in scheduler_results) / len(scheduler_results)
            
            print(f"\n📅 Scheduler Agent ({len(scheduler_results)} tests):")
            print(f"   Avg Duration: {avg_dur:.0f}ms, Avg Tokens: {avg_tok:.0f}")
        
        print(f"{'='*80}\n")
    
    def _print_summary(self):
        """Print final summary."""
        print(f"\n{'='*80}")
        print(f"📊 TEST SUITE COMPLETE")
        print(f"{'='*80}\n")
        
        print(f"Total Tests: {len(self.results)}")
        
        # Group by agent
        policy_results = [r for r in self.results if r['agent'] == 'policy_agent']
        provider_results = [r for r in self.results if r['agent'] == 'provider_agent']
        scheduler_results = [r for r in self.results if r['agent'] == 'scheduler_agent']
        
        print(f"\n📋 Policy Agent: {len(policy_results)} tests")
        if policy_results:
            evaluated = [r for r in policy_results if r['accuracy_score'] is not None]
            if evaluated:
                avg_acc = sum(r['accuracy_score'] for r in evaluated) / len(evaluated)
                passed = sum(1 for r in evaluated if r['passed'])
                avg_dur = sum(r['duration_ms'] for r in policy_results) / len(policy_results)
                avg_tok = sum(r['total_tokens'] for r in policy_results) / len(policy_results)
                total_tok = sum(r['total_tokens'] for r in policy_results)
                
                print(f"   🎯 Avg Accuracy: {avg_acc:.1%}")
                print(f"   ✅ Passed: {passed}/{len(evaluated)} ({100*passed/len(evaluated):.1f}%)")
                print(f"   ⏱️  Avg Duration: {avg_dur:.0f}ms")
                print(f"   🪙 Avg Tokens: {avg_tok:.0f}, Total: {total_tok:,}")
        
        print(f"\n🏥 Provider Agent: {len(provider_results)} tests")
        if provider_results:
            evaluated = [r for r in provider_results if r['accuracy_score'] is not None]
            if evaluated:
                avg_acc = sum(r['accuracy_score'] for r in evaluated) / len(evaluated)
                passed = sum(1 for r in evaluated if r['passed'])
                avg_dur = sum(r['duration_ms'] for r in provider_results) / len(provider_results)
                avg_tok = sum(r['total_tokens'] for r in provider_results) / len(provider_results)
                total_tok = sum(r['total_tokens'] for r in provider_results)
                
                print(f"   🎯 Avg Accuracy: {avg_acc:.1%}")
                print(f"   ✅ Passed: {passed}/{len(evaluated)} ({100*passed/len(evaluated):.1f}%)")
                print(f"   ⏱️  Avg Duration: {avg_dur:.0f}ms")
                print(f"   🪙 Avg Tokens: {avg_tok:.0f}, Total: {total_tok:,}")
        
        print(f"\n📅 Scheduler Agent: {len(scheduler_results)} tests")
        if scheduler_results:
            avg_dur = sum(r['duration_ms'] for r in scheduler_results) / len(scheduler_results)
            avg_tok = sum(r['total_tokens'] for r in scheduler_results) / len(scheduler_results)
            total_tok = sum(r['total_tokens'] for r in scheduler_results)
            
            print(f"   ⏱️  Avg Duration: {avg_dur:.0f}ms")
            print(f"   🪙 Avg Tokens: {avg_tok:.0f}, Total: {total_tok:,}")
        
        # Overall token count
        total_tokens = sum(r['total_tokens'] for r in self.results)
        print(f"\n🪙 Total Tokens (All Agents): {total_tokens:,}")
    
    def _save_results(self):
        """Save results to CSV and JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # JSON
        json_path = f"{RESULTS_DIR}/agent_evaluation_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump({
                "metadata": {
                    "timestamp": timestamp,
                    "iterations": len(self.results),
                    "dataset": self.dataset['metadata']
                },
                "results": self.results
            }, f, indent=2)
        
        # CSV
        csv_path = f"{RESULTS_DIR}/agent_evaluation_{timestamp}.csv"
        import csv
        
        columns = [
            "iteration", "question_id", "question", "expected_route", "actual_route",
            "agent", "accuracy_score", "passed", "reason",
            "model", "duration_ms", "ttft_ms",
            "tokens_input", "tokens_output", "total_tokens"
        ]
        
        with open(csv_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            for result in self.results:
                row = {col: result.get(col, "") for col in columns}
                writer.writerow(row)
        
        print(f"\n💾 Results saved:")
        print(f"   JSON: {json_path}")
        print(f"   CSV: {csv_path}")


async def main():
    """Main execution."""
    print(f"\n{'='*80}")
    print(f"🧪 Agent Evaluation Test Suite")
    print(f"{'='*80}")
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # Check LaunchDarkly
    if ldclient.get().is_initialized():
        print("✅ LaunchDarkly client initialized\n")
    else:
        print("⚠️  LaunchDarkly client not fully initialized, waiting...")
        await asyncio.sleep(2)
    
    # Run tests
    runner = AgentEvaluationRunner(DATASET_PATH)
    
    try:
        await runner.run_test_suite(NUM_ITERATIONS)
        
        print(f"\n{'='*80}")
        print(f"✅ ALL TESTS COMPLETE")
        print(f"{'='*80}\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test suite interrupted by user")
        runner._save_results()
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        runner._save_results()
    finally:
        # Cleanup
        print("\n🔄 Flushing metrics to LaunchDarkly...")
        ldclient.get().flush()
        await asyncio.sleep(2)
        ldclient.get().close()
        print("   ✅ Done\n")


if __name__ == "__main__":
    asyncio.run(main())

