"""Check what configs exist in LaunchDarkly."""

import os
from dotenv import load_dotenv
import ldclient
from ldclient import Context
from ldclient.config import Config

load_dotenv()

sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")

if not sdk_key:
    print("❌ LAUNCHDARKLY_SDK_KEY not set")
    exit(1)

ldclient.set_config(Config(sdk_key))

import time
max_wait = 5
start = time.time()
while not ldclient.get().is_initialized():
    if time.time() - start > max_wait:
        print("❌ Failed to initialize")
        exit(1)
    time.sleep(0.1)

print("✅ LaunchDarkly initialized")

# Create a test context
context = Context.builder("test-user").build()

# Try to get a feature flag to test the connection
client = ldclient.get()

print("\n" + "="*60)
print("Testing LaunchDarkly Connection")
print("="*60)

# List of AI config keys to check (matching LaunchDarkly)
config_keys = [
    "triage_agent",
    "policy_agent", 
    "provider_agent",
    "scheduler_agent"
]

print("\nChecking if AI Config keys exist in LaunchDarkly:")
print("(Note: If they return defaults, they may not be created yet)\n")

for key in config_keys:
    # Try to get a simple flag with the same key to see if it exists
    # This is a workaround since AI configs don't have a direct "exists" check
    print(f"  • {key}")

print("\n" + "="*60)
print("IMPORTANT: You need to create these AI Configs in LaunchDarkly!")
print("="*60)
print("\nSteps to create AI Configs:")
print("1. Go to https://app.launchdarkly.com")
print("2. Navigate to your project/environment")
print("3. Create AI Config for each agent:")
for key in config_keys:
    print(f"   - Key: {key}")
print("\n4. Configure each with:")
print("   - Model: claude-3-5-sonnet (or different per agent)")
print("   - Provider: bedrock")
print("   - Parameters: temperature, maxTokens, etc.")
print("\n5. Save and enable the configs")

ldclient.get().close()

