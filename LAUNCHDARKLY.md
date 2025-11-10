# LaunchDarkly AI Config Integration Guide

This guide explains how to configure and use LaunchDarkly AI Configs to manage AI models for each specialist agent in the medical insurance support system.

## Overview

Each agent in the system retrieves its own AI configuration from LaunchDarkly, enabling you to:
- Use different models for different agents (e.g., GPT-4 for triage, GPT-3.5 for simple queries)
- A/B test different models and configurations
- Target specific users with different model configurations
- Update model configurations without code changes
- Track token usage and performance metrics per agent

## Agent AI Config Keys

The system uses the following AI Config keys in LaunchDarkly:

| Agent | Config Key | Purpose |
|-------|-----------|---------|
| Triage Router | `triage-router` | Classifies and routes customer queries |
| Policy Specialist | `policy-specialist` | Answers policy-related questions |
| Provider Specialist | `provider-specialist` | Helps find in-network providers |
| Scheduler Specialist | `scheduler-specialist` | Schedules live agent callbacks |

## Setup Instructions

### 1. Create LaunchDarkly Account

1. Sign up at [LaunchDarkly](https://launchdarkly.com/)
2. Create a new project for your medical insurance support system
3. Navigate to the SDK Keys section and copy your Server-side SDK key

### 2. Configure Environment Variables

Update your `.env` file:

```bash
# Enable LaunchDarkly AI Config
LAUNCHDARKLY_ENABLED=true
LAUNCHDARKLY_SDK_KEY=sdk-your-actual-key-here

# LLM API Keys (still required for model access)
OPENAI_API_KEY=your_openai_api_key_here
# or
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

### 3. Create AI Configs in LaunchDarkly

For each agent, create an AI Config in LaunchDarkly:

#### Example: Triage Router Config

**Config Key:** `triage-router`

**Default Configuration:**
```json
{
  "model": {
    "name": "gpt-4-turbo-preview",
    "parameters": {
      "temperature": 0.0,
      "maxTokens": 1000
    }
  },
  "provider": "openai",
  "enabled": true
}
```

#### Example: Policy Specialist Config

**Config Key:** `policy-specialist`

**Default Configuration:**
```json
{
  "model": {
    "name": "gpt-4-turbo-preview",
    "parameters": {
      "temperature": 0.7,
      "maxTokens": 2000
    }
  },
  "provider": "openai",
  "enabled": true
}
```

#### Example: Provider Specialist Config

**Config Key:** `provider-specialist`

**Default Configuration:**
```json
{
  "model": {
    "name": "gpt-3.5-turbo",
    "parameters": {
      "temperature": 0.7,
      "maxTokens": 1500
    }
  },
  "provider": "openai",
  "enabled": true
}
```

#### Example: Scheduler Specialist Config

**Config Key:** `scheduler-specialist`

**Default Configuration:**
```json
{
  "model": {
    "name": "gpt-3.5-turbo",
    "parameters": {
      "temperature": 0.7,
      "maxTokens": 1500
    }
  },
  "provider": "openai",
  "enabled": true
}
```

### 4. Using Anthropic Models

To use Anthropic's Claude models:

```json
{
  "model": {
    "name": "claude-3-5-sonnet-20241022",
    "parameters": {
      "temperature": 0.7,
      "maxTokens": 2000
    }
  },
  "provider": "anthropic",
  "enabled": true
}
```

## Advanced Configuration

### User Targeting

Target different models to different user segments using LaunchDarkly's targeting rules:

**Example:** Premium users get GPT-4, standard users get GPT-3.5

1. In LaunchDarkly, add targeting rules to your AI Config
2. Target by custom attributes like `tier`, `policy_type`, etc.
3. Pass user context when calling the agents:

```python
result = run_workflow(
    user_message="What is my copay?",
    user_context={
        "policy_id": "POL-12345",
        "tier": "premium",  # Used for targeting
        "policy_type": "Gold"
    }
)
```

### A/B Testing Models

Test different models with percentage rollouts:

1. Create a new variation in your AI Config
2. Set up percentage rollout (e.g., 10% GPT-4, 90% GPT-3.5)
3. Monitor metrics in LaunchDarkly
4. Gradually increase rollout based on performance

### Cost Optimization

Example strategy for cost-effective configuration:

```json
// Triage Router - High accuracy needed
{
  "model": {"name": "gpt-4-turbo-preview"},
  "provider": "openai"
}

// Policy Specialist - Complex reasoning
{
  "model": {"name": "gpt-4-turbo-preview"},
  "provider": "openai"
}

// Provider Specialist - Simpler task
{
  "model": {"name": "gpt-3.5-turbo"},
  "provider": "openai"
}

// Scheduler Specialist - Simpler task
{
  "model": {"name": "gpt-3.5-turbo"},
  "provider": "openai"
}
```

## Metrics Tracking

The system automatically tracks metrics for each agent when LaunchDarkly is enabled:

- **Duration:** Response time in seconds
- **Token Usage:** Input, output, and total tokens
- **Success/Error:** Success rate and error messages

View metrics in LaunchDarkly's AI Config dashboard.

## Testing

### Testing with LaunchDarkly Enabled

```bash
# Set up environment
export LAUNCHDARKLY_ENABLED=true
export LAUNCHDARKLY_SDK_KEY=your-key

# Run examples
python examples/run_example.py
```

### Testing without LaunchDarkly

```bash
# Use fallback configuration
export LAUNCHDARKLY_ENABLED=false

# Run examples
python examples/run_example.py
```

## Fallback Behavior

If LaunchDarkly is unavailable or disabled:
- System uses environment variable configuration (`LLM_PROVIDER`, `LLM_MODEL`)
- No metrics tracking
- All agents use the same model configuration

## Best Practices

1. **Start with Default Configs:** Use the same model for all agents initially
2. **Monitor Metrics:** Track token usage and response quality
3. **Optimize Gradually:** Move simpler tasks to cheaper models based on metrics
4. **Use Targeting:** Provide better models to premium users
5. **Test Changes:** Use percentage rollouts before full deployment
6. **Set Budget Limits:** Monitor costs in LaunchDarkly dashboard

## Troubleshooting

### SDK Not Initializing

```
⚠️  LaunchDarkly SDK failed to initialize
```

**Solution:** Check your SDK key is correct and you have internet connectivity.

### AI Config Not Found

```
⚠️  Error retrieving AI config 'triage-router'
```

**Solution:** Create the AI Config in LaunchDarkly with the exact key name.

### Model Not Supported

```
ValueError: Unsupported LLM provider: xyz
```

**Solution:** Ensure `provider` is either `openai` or `anthropic` in your AI Config.

### API Key Missing

```
ValueError: OPENAI_API_KEY not set in environment
```

**Solution:** Set the appropriate API key in your `.env` file.

## Example LaunchDarkly Dashboard Setup

1. **Create AI Configs** for each agent (4 total)
2. **Set Default Values** with model configurations
3. **Create User Segment** (e.g., "Premium Users")
4. **Add Targeting Rules** to serve better models to premium users
5. **Enable Metrics** to track token usage and performance
6. **Set Up Alerts** for high error rates or excessive token usage

## Further Reading

- [LaunchDarkly AI Config Documentation](https://docs.launchdarkly.com/home/ai-configs)
- [Python AI SDK Reference](https://docs.launchdarkly.com/sdk/ai/python)
- [AI Config Targeting Guide](https://docs.launchdarkly.com/guides/ai-configs/targeting-python)
