# Medical Insurance Multi-Agent System

Multi-agent system for medical insurance customer support using LangGraph, LaunchDarkly AI Configs, AWS Bedrock, and RAG.

## Quick Start

### Terminal Interface
```bash
# Setup
make setup

# Run chatbot
make run
```

### Web Interface
```bash
# Start backend + frontend
cd ui && ./start.sh

# Or manually:
# Backend:  cd ui/backend && python server.py
# Frontend: cd ui/frontend && npm install && npm run dev
```

Open `http://localhost:3000` in your browser.

See [ui/README.md](ui/README.md) for full UI documentation.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER QUERY                                 │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   TRIAGE ROUTER        │
                    │  (triage_agent)        │
                    │  Classifies intent     │
                    └────────┬───────────────┘
                             │
                ┌────────────┼────────────┐
                │            │            │
                ▼            ▼            ▼
         ┌──────────┐ ┌──────────┐ ┌──────────┐
         │ POLICY   │ │ PROVIDER │ │SCHEDULER │
         │SPECIALIST│ │SPECIALIST│ │SPECIALIST│
         │          │ │          │ │          │
         │ RAG ✓    │ │ RAG ✓    │ │          │
         └────┬─────┘ └────┬─────┘ └────┬─────┘
              │            │            │
              └────────────┼────────────┘
                           │
                           ▼
                  ┌────────────────┐
                  │  BRAND VOICE   │
                  │  (brand_agent) │
                  │  Transform &   │
                  │  Personalize   │
                  └───────┬────────┘
                          │
                          ▼
              ┌───────────────────────┐
              │   EVALUATION JUDGE    │
              │   (G-Eval)            │
              │   • Accuracy          │
              │   • Coherence         │
              │   → LaunchDarkly      │
              └───────────┬───────────┘
                          │
                          ▼
                ┌──────────────────┐
                │ FINAL RESPONSE   │
                └──────────────────┘
```

## Agents

| Agent | LD Key | RAG | Purpose |
|-------|--------|-----|---------|
| Triage Router | `triage_agent` | No | Classify query intent |
| Policy Specialist | `policy_agent` | Yes | Coverage, benefits, claims |
| Provider Specialist | `provider_agent` | Yes | Find doctors, check network |
| Scheduler Specialist | `scheduler_agent` | No | Schedule callbacks |
| Brand Voice | `brand_agent` | No | Apply brand voice to response |

## Evaluation System

The system includes **online evaluation** using G-Eval methodology:

| Judge | LD Key | Metric | Threshold |
|-------|--------|--------|-----------|
| Accuracy Judge | `ai-judge-accuracy` | Global system accuracy vs RAG docs | 0.8 |
| Coherence Judge | `ai-judge-coherence` | Response clarity & professionalism | 0.7 |

**Metrics sent to LaunchDarkly:**
- `$ld:ai:judge:accuracy` - Factual accuracy against RAG documents
- `$ld:ai:judge:coherence` - Response quality and readability

Evaluation runs asynchronously (non-blocking) on every brand voice output.

## Configuration

### Required: LaunchDarkly AI Configs

Create these AI Configs in LaunchDarkly:

**Agents:**
- `triage_agent` - Agent-based config
- `policy_agent` - Agent-based config (add `awskbid` custom param)
- `provider_agent` - Agent-based config (add `awskbid` custom param)
- `scheduler_agent` - Agent-based config
- `brand_agent` - Completion-based config

**Judges:**
- `ai-judge-accuracy` - Agent-based config
- `ai-judge-coherence` - Agent-based config

See [EVALUATION_PROMPTS.md](EVALUATION_PROMPTS.md) for judge prompts.

### Environment Variables

```bash
# .env file
LAUNCHDARKLY_ENABLED=true
LAUNCHDARKLY_SDK_KEY=api-your-key-here

AWS_PROFILE=your-profile
AWS_REGION=us-east-1
```

### AWS Bedrock Knowledge Bases (Optional)

If using RAG, add KB IDs as custom parameters in LaunchDarkly AI Configs:

```
policy_agent → Custom Parameters → awskbid: YOUR-POLICY-KB-ID
provider_agent → Custom Parameters → awskbid: YOUR-PROVIDER-KB-ID
```

## Usage

### Interactive Chatbot

```bash
make run
```

### Example Queries

```
What's my copay for seeing a specialist?
Find me a cardiologist in San Francisco
Does my plan cover physical therapy?
I need to schedule a callback
```

### Programmatic

```python
from src.graph.workflow import run_workflow

result = run_workflow(
    user_message="What is my copay?",
    user_context={
        "policy_id": "TH-HMO-GOLD-2024",
        "coverage_type": "Gold HMO",
        "location": "San Francisco, CA"
    }
)

print(result["final_response"])
```

## Makefile Commands

### Basic

```bash
make setup       # Install dependencies, check AWS & LaunchDarkly
make run         # Run chatbot
make verify      # Verify all configs loaded
make help        # Show all commands
```

### AWS

```bash
make aws-check   # Check credentials (auto-refresh if expired)
make aws-login   # Force SSO login
```

### Development

```bash
make format      # Format with black
make lint        # Lint with ruff
make clean       # Remove cache files
```

## Data Flow

### RAG Pipeline (Policy & Provider Agents)

```
1. User Query → "What's my copay?"

2. Triage → Routes to Policy Specialist

3. Policy Specialist:
   - Enhances query with user context (policy_id, plan)
   - Retrieves from Bedrock KB (5 documents)
   - Generates response using RAG documents only

4. Brand Voice:
   - Receives specialist response
   - Applies personalization & brand voice
   - Preserves all factual information

5. Evaluation Judge (async):
   - Receives: Original query + RAG docs + Final output
   - Evaluates accuracy (against RAG docs)
   - Evaluates coherence (response quality)
   - Sends metrics to LaunchDarkly

6. Final Response → User
```

### Error Handling

The system uses **CATASTROPHIC** error handling:
- Missing LaunchDarkly config → Hard fail
- No RAG documents retrieved → Hard fail
- Missing KB ID in config → Hard fail
- No prompts in AI config → Hard fail

**No silent fallbacks.** This ensures data quality issues are caught immediately.

## Key Features

### 1. Dynamic Prompt Management
All prompts managed in LaunchDarkly AI Configs:
- Agent-based configs use "Goal or task" field
- Completion-based configs use "Prompt" messages
- No hardcoded prompts in code

### 2. RAG-Only Specialists
Policy and Provider specialists use **only** Bedrock KB retrieval:
- No structured database fallback
- No hardcoded data
- All responses grounded in RAG documents

### 3. Online Evaluation
G-Eval judges run on every response:
- Non-blocking (async)
- Evaluates global system accuracy
- Sends metrics to LaunchDarkly for monitoring

### 4. AWS Token Management
Makefile auto-refreshes AWS SSO tokens:
- Checks expiry before running
- Auto-runs `aws sso login` if needed
- No manual token management

## Project Structure

```
policy_agent/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── triage_router.py
│   │   ├── policy_specialist.py
│   │   ├── provider_specialist.py
│   │   ├── scheduler_specialist.py
│   │   └── brand_voice_agent.py
│   ├── evaluation/          # G-Eval judges
│   │   └── judge.py
│   ├── graph/               # LangGraph workflow
│   │   ├── workflow.py
│   │   └── state.py
│   ├── tools/               # RAG & utilities
│   │   └── bedrock_rag.py
│   └── utils/               # Config & helpers
│       ├── launchdarkly_config.py
│       ├── llm_config.py
│       └── user_profile.py
├── data/                    # Sample data for RAG
│   ├── markdown/            # Policy documents
│   └── togglehealth_*.json  # Sample structured data
├── interactive_chatbot.py   # Main chatbot entry
├── Makefile                 # Commands
├── EVALUATION_PROMPTS.md    # Judge prompt templates
└── LAUNCHDARKLY.md          # LaunchDarkly setup guide
```

## Documentation

- [LAUNCHDARKLY.md](LAUNCHDARKLY.md) - LaunchDarkly AI Config setup
- [EVALUATION_PROMPTS.md](EVALUATION_PROMPTS.md) - G-Eval judge prompts
- [SDD.md](SDD.md) - System Design Document

## Requirements

- Python 3.11+
- AWS CLI with SSO configured
- LaunchDarkly account
- AWS Bedrock access (optional, for RAG)

## Installation

```bash
# Clone
git clone https://github.com/marekdarkly/policy_agent.git
cd policy_agent

# Setup
make setup

# Run
make run
```

## Troubleshooting

### AWS Credentials Expired
```bash
make aws-login
```

### LaunchDarkly Config Not Found
Check that all configs exist:
```bash
make verify
```

Expected configs:
- `triage_agent`, `policy_agent`, `provider_agent`, `scheduler_agent`, `brand_agent`
- `ai-judge-accuracy`, `ai-judge-coherence`

### No RAG Documents Retrieved
1. Check KB IDs are set in LaunchDarkly custom params (`awskbid`)
2. Verify AWS Bedrock access
3. Check KB actually has documents indexed

### Evaluation Scores Low
- **Accuracy 0.0-0.3**: Hallucinations or RAG retrieval issues
- **Accuracy 0.3-0.7**: Missing information or incomplete responses
- **Accuracy 0.7-1.0**: Good grounding in RAG documents
- **Coherence 0.7+**: Response quality is acceptable

Low accuracy usually indicates:
- RAG retrieved wrong documents
- Knowledge base missing relevant data
- Agent hallucinating when no matches found

## License

MIT
