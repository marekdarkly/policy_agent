# Quick Start Guide

Get up and running in 2 minutes!

## 1. Initial Setup

```bash
# Clone the repo
git clone https://github.com/marekdarkly/policy_agent.git
cd policy_agent

# Complete setup (installs everything and verifies)
make setup
```

## 2. Configure

Edit `.env` with your LaunchDarkly SDK key:

```bash
LAUNCHDARKLY_SDK_KEY=api-your-key-here
```

## 3. Run

```bash
make run
```

That's it! 🎉

## What Happens

When you run `make run`:

1. ✅ **Checks AWS credentials** - Auto-refreshes if expired
2. ✅ **Initializes LaunchDarkly** - Loads AI configs
3. ✅ **Starts chatbot** - Interactive terminal UI

## Example Session

```
$ make run

🔐 Checking AWS credentials...
✅ AWS credentials valid for profile: marek

🚀 Starting Medical Insurance Support Chatbot...

================================================================================
🏥  Medical Insurance Support Chatbot
     Multi-Agent System with LaunchDarkly AI Configs
================================================================================

👤 You: What is my copay for seeing a specialist?

🔍 POLICY SPECIALIST: Retrieving policy information
📚 Retrieving policy documents via RAG...
  ℹ️  No RAG documents retrieved, using database only
  
🤖 Assistant: Based on your Gold Plan policy POL-12345, your copay for 
seeing a specialist is $50 per visit...
```

## Common Commands

```bash
make run          # Start chatbot
make chat         # Same as make run
make check        # Verify all configs
make info         # Show system status
make verify       # Run all tests
make help         # Show all commands
```

## Troubleshooting

### AWS Token Expired

```bash
make aws-login    # Force re-authentication
```

### LaunchDarkly Not Working

```bash
make verify-ld    # Check LaunchDarkly configs
```

### Want RAG?

See [RAG_SETUP_GUIDE.md](RAG_SETUP_GUIDE.md) - Takes ~10 minutes to set up Bedrock KB.

## What's Next?

- **Create LaunchDarkly AI Configs** - See [LAUNCHDARKLY.md](LAUNCHDARKLY.md)
- **Enable RAG** (optional) - See [RAG_SETUP_GUIDE.md](RAG_SETUP_GUIDE.md)
- **Customize agents** - See [SDD.md](SDD.md)

## Support

- 📚 Run `make docs` to see all documentation
- 🔍 Run `make info` to check system status
- ❓ Run `make help` for all commands

---

**TL;DR**: Run `make setup` then `make run`. Done! 🚀

