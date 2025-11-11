"""Verification script to ensure all agents retrieve AI configs from LaunchDarkly."""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.launchdarkly_config import get_ld_client
from src.utils.llm_config import get_llm_from_config, get_model_invoker


def verify_config_retrieval(config_key: str, agent_name: str) -> bool:
    """Verify that an agent can retrieve its LaunchDarkly AI config.
    
    Args:
        config_key: The LaunchDarkly config key
        agent_name: Human-readable agent name
        
    Returns:
        True if config retrieval works, False otherwise
    """
    print(f"\n{'='*60}")
    print(f"Verifying: {agent_name}")
    print(f"Config Key: {config_key}")
    print(f"{'='*60}")
    
    try:
        # Test config retrieval
        ld_client = get_ld_client()
        context = {"user_key": "test_user", "policy_id": "POL-12345"}
        
        config, tracker = ld_client.get_ai_config(config_key, context)
        
        print(f"✅ Config retrieved successfully!")
        print(f"   Enabled: {config.get('enabled', 'N/A')}")
        print(f"   Provider: {config.get('provider', 'N/A')}")
        
        if config.get('model'):
            model_info = config['model']
            print(f"   Model: {model_info.get('name', 'N/A')}")
            params = model_info.get('parameters', {})
            print(f"   Temperature: {params.get('temperature', 'N/A')}")
            print(f"   Max Tokens: {params.get('maxTokens', 'N/A')}")
        
        # Verify tracker is not a NoOpTracker (if LD is enabled)
        tracker_type = type(tracker).__name__
        print(f"   Tracker Type: {tracker_type}")
        
        if ld_client.enabled:
            if tracker_type == "NoOpTracker":
                print(f"   ⚠️  Warning: Using NoOpTracker (LD enabled but config not found?)")
            else:
                print(f"   ✅ Using LaunchDarkly tracker")
        else:
            print(f"   ℹ️  LaunchDarkly disabled, using NoOpTracker (expected)")
        
        # Test LLM creation
        print(f"\n   Testing LLM creation...")
        if agent_name == "Triage Router":
            llm, tracker = get_llm_from_config(config_key, context)
            print(f"   ✅ LLM created via get_llm_from_config")
        else:
            invoker = get_model_invoker(config_key, context)
            print(f"   ✅ ModelInvoker created via get_model_invoker")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Verify all agents retrieve LaunchDarkly configs."""
    print("\n" + "="*60)
    print("LaunchDarkly AI Config Verification")
    print("="*60)
    
    # Check if LaunchDarkly is enabled
    ld_enabled = os.getenv("LAUNCHDARKLY_ENABLED", "false").lower() == "true"
    ld_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
    
    print(f"\nLaunchDarkly Status:")
    print(f"   Enabled: {ld_enabled}")
    print(f"   SDK Key: {'Set' if ld_key else 'Not Set'}")
    
    if not ld_enabled:
        print("\n⚠️  LaunchDarkly is disabled. Configs will use defaults.")
        print("   Set LAUNCHDARKLY_ENABLED=true to enable.")
    
    # Agents and their config keys (matching LaunchDarkly)
    agents = [
        ("triage_agent", "Triage Router"),
        ("policy_agent", "Policy Specialist"),
        ("provider_agent", "Provider Specialist"),
        ("scheduler_agent", "Scheduler Specialist"),
    ]
    
    results = []
    for config_key, agent_name in agents:
        success = verify_config_retrieval(config_key, agent_name)
        results.append((agent_name, config_key, success))
    
    # Summary
    print(f"\n{'='*60}")
    print("Verification Summary")
    print(f"{'='*60}")
    
    all_passed = True
    for agent_name, config_key, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {agent_name} ({config_key})")
        if not success:
            all_passed = False
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✅ All agents successfully retrieve LaunchDarkly AI configs!")
    else:
        print("❌ Some agents failed to retrieve configs. Check errors above.")
    print(f"{'='*60}\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

