# Interactive Medical Insurance Chatbot

An interactive terminal-based chatbot that demonstrates the multi-agent system with LaunchDarkly AI Configs.

## Features

- 🤖 **Multi-Agent Architecture**: Triage Router → Specialist Agents
- 🎯 **LaunchDarkly AI Configs**: Each agent uses its own configuration
- 🔍 **Extensive Debug Logging**: See exactly how the system works
- 💬 **Interactive Terminal UI**: Beautiful colored output
- 📊 **Real-time Metrics**: View confidence scores, routing decisions, and more

## Quick Start

### Run the Chatbot

```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Run the interactive chatbot
python interactive_chatbot.py
```

### Test Mode

Run a single query to test the system:

```bash
python interactive_chatbot.py test
```

## How It Works

### Agent Flow

1. **Triage Router** - Analyzes your query
   - Determines query type (policy, provider, or scheduling)
   - Calculates confidence score
   - Routes to appropriate specialist

2. **Specialist Agents** - Handle specific domains
   - **Policy Specialist**: Coverage, benefits, deductibles
   - **Provider Specialist**: Find doctors, check network
   - **Scheduler Specialist**: Schedule callbacks, escalate complex issues

3. **LaunchDarkly Integration**
   - Each agent retrieves its AI config from LaunchDarkly
   - Configs specify model, provider, temperature, etc.
   - Metrics tracked automatically

### What You'll See

The chatbot provides detailed logging:

- 🔍 **Configuration checks** - Verify LaunchDarkly, AWS, and LLM settings
- 📋 **User context** - Policy ID, coverage type, location, etc.
- 🎯 **Routing decisions** - Which agent handles your query
- 💯 **Confidence scores** - How certain the system is
- 🤖 **Agent responses** - Full conversation flow
- 📊 **Performance metrics** - Token usage, duration, etc.

## Example Interactions

### Policy Questions

```
You: What is my copay for seeing a specialist?
```

The system will:
- Route to Policy Specialist
- Retrieve your policy details
- Look up specialist copay information
- Provide a detailed answer

### Provider Lookup

```
You: I need to find a cardiologist in Boston
```

The system will:
- Route to Provider Specialist  
- Search the provider database
- Filter by specialty, location, and network
- Return matching providers

### Scheduling

```
You: I need to speak with someone urgently
```

The system will:
- Route to Scheduler Specialist
- Recognize escalation need
- Provide available callback slots
- Schedule with a human agent

## Commands

While chatting:

- `help` - Show example queries
- `context` - View current user context
- `quit`, `exit`, `q` - Exit the chatbot

## Debug Output

The chatbot shows:

```
🔍 Debug Information - Internal system state
ℹ️  Info Messages - What's happening now
✅ Success Messages - Completed actions
⚠️  Warnings - Important notices
❌ Errors - Problems encountered
🤖 Agent Messages - Responses from agents
👤 User Messages - Your input
```

## Configuration

The chatbot uses your `.env` configuration:

```bash
LAUNCHDARKLY_ENABLED=true
LAUNCHDARKLY_SDK_KEY=your-key-here
LLM_PROVIDER=bedrock
LLM_MODEL=claude-3-5-sonnet
AWS_REGION=us-east-1
AWS_PROFILE=default
```

## Troubleshooting

### "LaunchDarkly SDK key not found"

Make sure your `.env` file has:
```bash
LAUNCHDARKLY_SDK_KEY=api-your-key-here
```

### "Unsupported LLM provider"

Check that your LaunchDarkly AI Configs use supported providers:
- `bedrock` (or `Bedrock:Anthropic`, `Bedrock:Nova`)
- `openai`
- `anthropic`

### Slow responses

- First query initializes the LaunchDarkly SDK (a few seconds)
- AWS Bedrock may take 2-5 seconds per agent invocation
- Check your AWS SSO session is active

## Architecture

```
User Input
    ↓
Triage Router (LaunchDarkly: triage_agent)
    ↓
[Routing Decision]
    ↓
    ├─→ Policy Specialist (LaunchDarkly: policy_agent)
    ├─→ Provider Specialist (LaunchDarkly: provider_agent)  
    └─→ Scheduler Specialist (LaunchDarkly: scheduler_agent)
         ↓
    Final Response
```

## Tips

1. **Be specific**: "Find a cardiologist in Boston" works better than "Find a doctor"
2. **Ask follow-ups**: The system maintains context across the conversation
3. **Try different queries**: Test routing by asking different types of questions
4. **Watch the logs**: See how LaunchDarkly configs affect each agent's behavior
5. **Experiment**: Change configs in LaunchDarkly and see immediate effects

## Next Steps

- Try modifying agent configs in LaunchDarkly
- Test different models for different agents
- A/B test configuration changes
- Monitor metrics in LaunchDarkly dashboard

Enjoy exploring the multi-agent system! 🚀

