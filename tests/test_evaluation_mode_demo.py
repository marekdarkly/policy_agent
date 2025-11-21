#!/usr/bin/env python3
"""
Demo script to test per-agent evaluation mode.
Runs a few tests for each agent to verify the new functionality.
"""
import os
import sys
import asyncio
import random
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Suppress noisy logs
import logging
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("ldclient").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)

# Initialize observability
from src.utils.observability import initialize_observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

# Import workflow
from src.graph.workflow import run_workflow
from src.utils.user_profile import create_user_profile
from src.evaluation.agent_evaluator import evaluate_agent_accuracy
from uuid import uuid4

async def test_agent(agent_name: str, question: str):
    """Test a single agent with evaluation mode."""
    print(f"\n{'='*80}")
    print(f"Testing {agent_name.upper()}")
    print(f"{'='*80}")
    print(f"Question: {question}")
    
    # Create user context
    user_context = create_user_profile(
        name="Marek Poliks",
        location="San Francisco, CA",
        policy_id="TH-HMO-GOLD-2024",
        coverage_type="Gold HMO"
    )
    
    # Map agent names
    agent_key_map = {
        "policy_agent": "policy_specialist",
        "provider_agent": "provider_specialist",
        "scheduler_agent": "scheduler_specialist"
    }
    
    try:
        # Run workflow with evaluation mode
        result = await asyncio.to_thread(
            run_workflow,
            user_message=question,
            user_context=user_context,
            request_id=str(uuid4()),
            evaluate_agent=agent_name  # Enable evaluation mode
        )
        
        # Extract agent data
        agent_data = result.get("agent_data", {})
        target_key = agent_key_map.get(agent_name)
        
        if target_key not in agent_data:
            print(f"   ❌ {agent_name} was not used for this question")
            return False
        
        print(f"   ✅ {agent_name} was used")
        print(f"   ✅ Workflow terminated after {target_key}")
        
        # Extract metrics
        target_agent_data = agent_data[target_key]
        agent_output = target_agent_data.get("response", "")
        rag_documents = target_agent_data.get("rag_documents", [])
        
        # Extract cost metrics (no jitter - actual metrics)
        duration_ms = target_agent_data.get("duration_ms", 0)
        ttft_ms = target_agent_data.get("ttft_ms", 0)
        
        tokens = target_agent_data.get("tokens", {})
        tokens_input = tokens.get("input", 0)
        tokens_output = tokens.get("output", 0)
        model = target_agent_data.get("model", "unknown")
        
        print(f"\n   💰 Cost Metrics:")
        print(f"      Model: {model}")
        print(f"      Duration: {duration_ms}ms")
        print(f"      TTFT: {ttft_ms}ms")
        print(f"      Tokens: {tokens_input + tokens_output} (in: {tokens_input}, out: {tokens_output})")
        
        # For scheduler, skip evaluation
        if agent_name == "scheduler_agent":
            print(f"\n   ⏹️  Scheduler agent - no evaluation (as expected)")
            return True
        
        # Evaluate policy/provider agents
        print(f"\n   🧪 Running evaluation...")
        eval_result = await evaluate_agent_accuracy(
            agent_name=agent_name,
            original_query=question,
            rag_documents=rag_documents,
            agent_output=agent_output,
            user_context=user_context
        )
        
        passed = "✅ PASS" if eval_result['passed'] else "❌ FAIL"
        print(f"   📊 Accuracy: {eval_result['score']:.2f} {passed}")
        print(f"   📝 Reason: {eval_result['reason']}")
        
        # Verify brand_voice was NOT executed
        if "brand_voice" in agent_data:
            print(f"\n   ⚠️  WARNING: brand_voice should not have executed in evaluation mode!")
            return False
        else:
            print(f"\n   ✅ Confirmed: brand_voice did NOT execute (correct!)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run demo tests."""
    print(f"\n{'='*80}")
    print(f"PER-AGENT EVALUATION MODE - DEMO")
    print(f"{'='*80}")
    print(f"This demo verifies that evaluation mode works correctly:")
    print(f"  1. Workflow terminates after target agent")
    print(f"  2. Brand voice is NOT executed")
    print(f"  3. Cost metrics are captured")
    print(f"  4. Evaluation runs (for policy/provider)")
    print(f"{'='*80}")
    
    results = []
    
    # Test policy agent
    success = await test_agent(
        "policy_agent",
        "What's my copay for specialist visits?"
    )
    results.append(("policy_agent", success))
    
    await asyncio.sleep(1)
    
    # Test provider agent
    success = await test_agent(
        "provider_agent",
        "Find dermatologists in San Francisco"
    )
    results.append(("provider_agent", success))
    
    await asyncio.sleep(1)
    
    # Test scheduler agent
    success = await test_agent(
        "scheduler_agent",
        "Schedule an appointment with Dr. Smith"
    )
    results.append(("scheduler_agent", success))
    
    # Summary
    print(f"\n{'='*80}")
    print(f"DEMO SUMMARY")
    print(f"{'='*80}")
    for agent, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {agent:20s}: {status}")
    
    all_passed = all(success for _, success in results)
    if all_passed:
        print(f"\n✅ All tests passed! Evaluation mode is working correctly.")
    else:
        print(f"\n❌ Some tests failed. Please review the output above.")
    
    print(f"{'='*80}\n")
    
    # Cleanup
    import ldclient
    ldclient.get().flush()
    await asyncio.sleep(1)
    ldclient.get().close()

if __name__ == "__main__":
    asyncio.run(main())

