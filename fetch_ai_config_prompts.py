"""
Fetch all AI Config prompts/instructions from LaunchDarkly
to sync documentation with actual configurations
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# Initialize LaunchDarkly
from src.utils.observability import initialize_observability
initialize_observability(environment=os.getenv("LAUNCHDARKLY_ENVIRONMENT", "production"))

from src.utils.llm_config import get_model_invoker

# AI Config keys to fetch
config_keys = [
    "triage_agent",
    "policy_agent",
    "provider_agent",
    "scheduler_agent",
    "brand_agent",
    "ai-judge-accuracy",
    "ai-judge-coherence"
]

print("=" * 80)
print("FETCHING AI CONFIG PROMPTS FROM LAUNCHDARKLY")
print("=" * 80)
print()

results = {}

for config_key in config_keys:
    print(f"\n{'='*80}")
    print(f"📋 Config: {config_key}")
    print(f"{'='*80}")
    
    try:
        model_invoker, ld_config = get_model_invoker(
            config_key=config_key, 
            context={"user_key": "prompt-fetch-user", "name": "Prompt Fetch User"},
            default_temperature=0.7
        )
        
        config_type = None
        prompt_content = None
        model = ld_config.get("model", {}).get("name", "unknown")
        
        # Check if agent-based (has '_instructions' field from .agents())
        if "_instructions" in ld_config and ld_config["_instructions"]:
            config_type = "agent-based"
            prompt_content = ld_config["_instructions"]
            print(f"✅ Type: Agent-based (Goal or task)")
            print(f"📦 Model: {model}")
            print(f"📝 Instructions:")
            print("-" * 80)
            print(prompt_content)
            print("-" * 80)
        
        # Check if completion-based (has 'messages' array from .config())
        elif "messages" in ld_config and ld_config["messages"]:
            config_type = "completion-based"
            messages = ld_config["messages"]
            print(f"✅ Type: Completion-based (Prompt messages)")
            print(f"📦 Model: {model}")
            print(f"📝 Messages ({len(messages)} total):")
            print("-" * 80)
            for i, msg in enumerate(messages, 1):
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                print(f"\nMessage {i} [{role}]:")
                print(content)
                print()
            print("-" * 80)
            prompt_content = messages
        else:
            print(f"⚠️  No prompt content found")
            continue
        
        results[config_key] = {
            "type": config_type,
            "model": model,
            "prompt": prompt_content
        }
        
    except Exception as e:
        print(f"❌ Error fetching {config_key}: {e}")

# Save to JSON for documentation
output_path = "ai_config_prompts.json"
with open(output_path, 'w') as f:
    json.dump(results, f, indent=2)

print(f"\n{'='*80}")
print(f"✅ Saved all prompts to: {output_path}")
print(f"{'='*80}")

