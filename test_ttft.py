"""Quick test to verify TTFT (Time to First Token) tracking works."""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Initialize observability BEFORE any LLM imports
from src.utils.observability import initialize_observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

from src.utils.llm_config import get_model_invoker
from src.utils.user_profile import create_user_profile
from langchain_core.messages import HumanMessage

print("=" * 80)
print("Testing TTFT (Time to First Token) Tracking")
print("=" * 80)

# Create test user context
user_context = create_user_profile(
    name="Test User",
    location="Seattle, WA"
)

# Test with triage agent (simple, fast response)
print("\n🧪 Testing triage_agent...")
try:
    model_invoker, config = get_model_invoker(
        config_key="triage_agent",
        context=user_context,
        default_temperature=0.0
    )
    
    test_message = HumanMessage(content="What's my copay for a doctor visit?")
    
    print("   Invoking model...")
    result = model_invoker.invoke([test_message])
    
    # Check if TTFT was tracked
    if hasattr(result, 'response_metadata'):
        ttft = result.response_metadata.get('ttft_ms')
        if ttft:
            print(f"   ✅ TTFT tracked: {ttft}ms")
        else:
            print("   ❌ TTFT not found in response_metadata")
    else:
        print("   ❌ No response_metadata")
    
    # Check token usage
    if hasattr(result, 'usage_metadata'):
        usage = result.usage_metadata
        print(f"   ✅ Tokens: {usage.get('input_tokens', 0)} input, {usage.get('output_tokens', 0)} output")
    
    print(f"   Response: {result.content[:100]}...")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
print("\n📊 Next steps:")
print("   1. Check LaunchDarkly AI Config Monitoring tab for 'triage_agent'")
print("   2. Look for 'Time to First Token' metric")
print("   3. Verify it shows the tracked TTFT value")
print("\n💡 If metrics don't appear immediately, wait a few seconds and refresh.")

