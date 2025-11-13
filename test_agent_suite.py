"""
Comprehensive Agent Test Suite

Runs full agent circuits (initialize → route → answer → evaluate → terminate)
for automated testing and performance benchmarking.

This script:
1. Loads Q&A dataset (100 questions)
2. Runs N iterations with random questions
3. Each iteration is a complete circuit (matching backend server exactly)
4. Includes all metrics, observability, and evaluation
5. Outputs results in CSV format for LaunchDarkly analysis
"""

import os
import sys
import json
import random
import time
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
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
DATASET_PATH = "test_data/qa_dataset.json"
RESULTS_DIR = "test_results"

# Ensure results directory exists
Path(RESULTS_DIR).mkdir(exist_ok=True)

class AgentTestRunner:
    """Runs automated agent tests with full metrics and evaluation."""
    
    def __init__(self, dataset_path: str):
        """Initialize test runner with Q&A dataset."""
        self.dataset = self._load_dataset(dataset_path)
        self.results = []
        self.evaluation_results_store = {}  # Shared store for evaluations
        self.brand_trackers_store = {}  # Shared store for brand trackers
        
    def _load_dataset(self, path: str) -> Dict:
        """Load Q&A dataset from JSON file."""
        with open(path, 'r') as f:
            return json.load(f)
    
    def get_random_question(self) -> Dict:
        """Get a random question from the dataset."""
        return random.choice(self.dataset['questions'])
    
    def create_test_user(self, question_data: Dict, iteration: int) -> Dict:
        """Create user profile based on question context.
        
        Randomizes user name/key to ensure varied split test distribution.
        Uses UUID for user_key to maximize entropy for LaunchDarkly bucketing.
        """
        # Vary user profiles based on question tags
        tags = question_data.get('tags', [])
        
        # Determine location based on question tags
        city_tags = {
            'san_francisco': ('San Francisco', 'CA'),
            'boston': ('Boston', 'MA'),
            'seattle': ('Seattle', 'WA'),
            'portland': ('Portland', 'OR'),
            'new_york': ('New York', 'NY'),
            'los_angeles': ('Los Angeles', 'CA'),
            'chicago': ('Chicago', 'IL'),
            'miami': ('Miami', 'FL'),
            'denver': ('Denver', 'CO'),
            'atlanta': ('Atlanta', 'GA'),
            'houston': ('Houston', 'TX'),
            'dallas': ('Dallas', 'TX'),
            'austin': ('Austin', 'TX'),
            'phoenix': ('Phoenix', 'AZ'),
            'philadelphia': ('Philadelphia', 'PA'),
            'san_diego': ('San Diego', 'CA'),
            'detroit': ('Detroit', 'MI'),
            'minneapolis': ('Minneapolis', 'MN'),
            'charlotte': ('Charlotte', 'NC'),
            'washington_dc': ('Washington', 'DC'),
        }
        
        location = "San Francisco, CA"  # Default
        for tag, (city, state) in city_tags.items():
            if tag in tags:
                location = f"{city}, {state}"
                break
        
        # Randomize user name to get varied split test distribution
        first_names = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Quinn", "Avery", "Parker", "Cameron"]
        last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        
        random_name = f"{random.choice(first_names)} {random.choice(last_names)} {iteration}"
        
        # Create profile with random name (will auto-generate user_key from name)
        profile = create_user_profile(
            name=random_name,
            location=location,
            policy_id="TH-HMO-GOLD-2024",
            coverage_type="Gold HMO"
        )
        
        # OVERRIDE user_key with UUID for maximum entropy in LaunchDarkly bucketing
        # This ensures truly random distribution across split test variations
        profile["user_key"] = f"test-user-{uuid4()}"
        
        return profile
    
    async def run_single_test(self, iteration: int, question_data: Dict) -> Dict:
        """Run a single test iteration (full circuit).
        
        This mirrors the backend server's /api/chat endpoint exactly.
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
        print(f"🎯 Expected Route: {expected_route}")
        print(f"👤 User: {user_context.get('name')} (key: {user_context.get('user_key')})")
        
        try:
            
            # Run workflow (EXACTLY like backend server /api/chat endpoint)
            result = await asyncio.to_thread(
                run_workflow,
                user_message=question_text,
                user_context=user_context,
                request_id=request_id,
                evaluation_results_store=self.evaluation_results_store,
                brand_trackers_store=self.brand_trackers_store
            )
            
            total_duration = int((time.time() - start_time) * 1000)  # ms
            
            # Extract metrics (SAME as backend server)
            final_response = result.get("final_response", "")
            query_type = result.get("query_type", "UNKNOWN")
            agent_data = result.get("agent_data", {})
            confidence = result.get("confidence_score", 0)
            
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
            
            # Run single test (full circuit)
            result = await self.run_single_test(i, question_data)
            
            # Store result
            self.results.append(result)
            
            # Show running statistics every 10 iterations
            if i % 10 == 0 and i > 0:
                successful = [r for r in self.results if r['status'] == 'success']
                if successful:
                    avg_accuracy = sum(r['accuracy_score'] for r in successful) / len(successful)
                    avg_coherence = sum(r['coherence_score'] for r in successful) / len(successful)
                    route_matches = [r for r in successful if r['route_match']]
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
        
        successful = [r for r in self.results if r['status'] == 'success']
        failed = [r for r in self.results if r['status'] == 'error']
        
        print(f"✅ Successful: {len(successful)}/{len(self.results)}")
        print(f"❌ Failed: {len(failed)}/{len(self.results)}")
        
        if successful:
            # Routing accuracy
            route_matches = [r for r in successful if r['route_match']]
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
        
        # Define CSV columns
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
    
    # Initialize test runner
    runner = AgentTestRunner(DATASET_PATH)
    
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
    # Run async main
    asyncio.run(main())

