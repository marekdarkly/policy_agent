#!/usr/bin/env python3
"""Test script to verify LaunchDarkly AI Config integration."""

import os
from dotenv import load_dotenv
from src.utils.launchdarkly_config import get_ld_client

# Load environment variables
load_dotenv()

def main():
    """Test LaunchDarkly configuration retrieval."""
    print("=" * 60)
    print("LaunchDarkly AI Config Test")
    print("=" * 60)
    print()

    # Check environment variables
    print("Environment Configuration:")
    print(f"  LAUNCHDARKLY_ENABLED: {os.getenv('LAUNCHDARKLY_ENABLED')}")
    print(f"  LAUNCHDARKLY_SDK_KEY: {'***' + os.getenv('LAUNCHDARKLY_SDK_KEY', '')[-4:] if os.getenv('LAUNCHDARKLY_SDK_KEY') else 'Not set'}")
    print(f"  LLM_PROVIDER: {os.getenv('LLM_PROVIDER')}")
    print(f"  AWS_PROFILE: {os.getenv('AWS_PROFILE')}")
    print(f"  AWS_REGION: {os.getenv('AWS_REGION')}")
    print()

    # Initialize LaunchDarkly client
    print("Initializing LaunchDarkly client...")
    ld_client = get_ld_client()
    print()

    # Test config retrieval for each agent
    config_keys = [
        "triage_agent",
        "policy_agent",
        "provider_agent",
        "scheduling_agent"
    ]

    print("Testing AI Config retrieval:")
    print("-" * 60)

    for config_key in config_keys:
        print(f"\n📋 Config: {config_key}")
        print("-" * 60)

        try:
            # Get the AI config
            config, tracker = ld_client.get_ai_config(
                config_key=config_key,
                context={"user_key": "test-user", "environment": "development"}
            )

            print(f"✅ Successfully retrieved config")
            print(f"\nConfiguration:")
            print(f"  Provider: {config.get('provider', 'N/A')}")
            print(f"  Enabled: {config.get('enabled', 'N/A')}")

            model_config = config.get('model', {})
            print(f"\nModel Settings:")
            print(f"  Name: {model_config.get('name', 'N/A')}")

            params = model_config.get('parameters', {})
            print(f"  Temperature: {params.get('temperature', 'N/A')}")
            print(f"  Max Tokens: {params.get('maxTokens', 'N/A')}")

        except Exception as e:
            print(f"❌ Error retrieving config: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

    # Close the client
    ld_client.close()

if __name__ == "__main__":
    main()
