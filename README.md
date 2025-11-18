# ToggleHealth Multi-Agent System

Multi-agent customer support system for medical insurance using **LangGraph**, **LaunchDarkly AI Configs**, **AWS Bedrock RAG**, and **G-Eval**.

## Quick Start

### Web Interface (Recommended)
```bash
cd ui && ./start.sh
# Open http://localhost:3000
```

### Terminal Interface
```bash
make setup  # First time only
make run
```

## System Architecture

```
                        ┌─────────────────┐
                        │   USER QUERY    │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ TRIAGE ROUTER   │
                        │ (triage_agent)  │
                        └────────┬────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
    │ POLICY AGENT   │  │ PROVIDER AGENT │  │ SCHEDULER AGENT│
    │ (policy_agent) │  │(provider_agent)│  │(scheduler_agent│
    │                │  │                │  │                │
    │ + RAG (Bedrock)│  │ + RAG (Bedrock)│  │                │
    └───────┬────────┘  └───────┬────────┘  └───────┬────────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                        ┌────────▼────────┐
                        │  BRAND VOICE    │
                        │  (brand_agent)  │
                        └────────┬────────┘
                                 │
                        ┌────────▼────────┐
                        │ EVALUATION      │
                        │ (G-Eval Judges) │
                        │ → LaunchDarkly  │
                        └─────────────────┘
```

## Agents & Judges

| Component | LD Config Key | RAG | Purpose |
|-----------|---------------|-----|---------|
| **Triage Router** | `triage_agent` | No | Classify query intent |
| **Policy Specialist** | `policy_agent` | Yes | Coverage, benefits, claims |
| **Provider Specialist** | `provider_agent` | Yes | Find doctors, network status |
| **Scheduler** | `scheduler_agent` | No | Schedule callbacks |
| **Brand Voice** | `brand_agent` | No | Personalize response |
| **Accuracy Judge** | `ai-judge-accuracy` | - | Evaluate factual accuracy |
| **Coherence Judge** | `ai-judge-coherence` | - | Evaluate response quality |

## LaunchDarkly AI Config Setup

Create these AI Configs in LaunchDarkly:

**Agents (Agent-based configs):**
- `triage_agent`
- `policy_agent` (add custom param: `awskbid` = your-policy-kb-id)
- `provider_agent` (add custom param: `awskbid` = your-provider-kb-id)
- `scheduler_agent`

**Brand (Completion-based config):**
- `brand_agent`

**Judges (Agent-based configs):**
- `ai-judge-accuracy`
- `ai-judge-coherence`

## Testing & Evaluation

### Test Suite (Real AI Calls)

Run full end-to-end tests with actual AI models:

```bash
# Full circuit test (50 iterations)
python test_agent_suite.py

# Test specific agent only
python test_agent_suite.py --evaluate policy_agent
python test_agent_suite.py --evaluate provider_agent

# Custom iterations
TEST_ITERATIONS=100 python test_agent_suite.py
```

### Experiment Simulation (No AI Calls)

Simulate LaunchDarkly experiments with realistic metrics **without** running actual AI models:

```bash
# Run 200 iterations for both policy & provider agents
ITERATIONS=200 python simulate_experiments.py

# More iterations
ITERATIONS=1000 python simulate_experiments.py
```

**What it does:**
- Pre-generates normal distributions for accuracy, duration, and cost
- Sends metrics to LaunchDarkly experiments (`policy_agent` & `provider_agent`)
- Uses unique users per iteration (enables CUPED)
- Simulates realistic model performance characteristics:
  - **Provider Agent**: Sonnet (high accuracy, expensive), Nova (low accuracy), Llama (fast), Haiku (variable)
  - **Policy Agent**: Llama (winner: best accuracy/speed/cost), Nova (slower), Sonnet (expensive), Haiku (variable)

**Metrics sent:**
- `$ld:ai:hallucinations` (accuracy: 0.0-1.0)
- `$ld:ai:duration:total` (duration in ms)
- `$ld:ai:tokens:total` (derived from cost)
- `$ld:ai:tokens:costmanual` (cost in cents)

Perfect for:
- Testing LaunchDarkly experiment visualizations
- Generating realistic data for demos
- A/B testing without incurring AI model costs

## Environment Setup

```bash
# .env file
LAUNCHDARKLY_ENABLED=true
LAUNCHDARKLY_SDK_KEY=sdk-your-key-here
LAUNCHDARKLY_ENVIRONMENT=production

AWS_PROFILE=your-sso-profile
AWS_REGION=us-east-1
```

## Makefile Commands

```bash
make setup       # Install dependencies & verify config
make run         # Run interactive chatbot
make verify      # Check all LaunchDarkly configs loaded
make aws-check   # Check AWS credentials (auto-refresh)
make aws-login   # Force AWS SSO login
make format      # Format code with black
make lint        # Lint with ruff
make clean       # Remove cache files
```

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
│   │   ├── judge.py
│   │   └── agent_evaluator.py
│   ├── graph/               # LangGraph workflow
│   │   ├── workflow.py
│   │   └── state.py
│   ├── tools/               # RAG & utilities
│   │   ├── bedrock_rag.py
│   │   ├── policy_db.py
│   │   └── provider_db.py
│   └── utils/               # Config & helpers
│       ├── launchdarkly_config.py
│       ├── llm_config.py
│       └── user_profile.py
├── data/
│   └── markdown/            # RAG knowledge bases
│       ├── policies/        # Policy documents (90 files)
│       └── providers/       # Provider data (280 files)
├── test_data/
│   └── qa_dataset_demo.json # Test questions
├── ui/                      # Web interface (React + FastAPI)
│   ├── frontend/            # React + TypeScript + Vite
│   └── backend/             # FastAPI server
├── test_agent_suite.py      # Main test suite (real AI)
├── simulate_experiments.py  # Experiment simulator (no AI)
├── interactive_chatbot.py   # Terminal chatbot
└── Makefile                 # Commands
```

## Key Features

### 1. Dynamic AI Config Management
All prompts and model configs managed in LaunchDarkly:
- Agent prompts in "Goal or task" field
- Brand prompts in "Prompt" messages
- Model selection via variations/experiments
- Zero hardcoded prompts in code

### 2. RAG-Only Specialists
Policy and Provider agents use **exclusively** Bedrock Knowledge Base retrieval:
- No database fallback
- No hardcoded data
- All responses grounded in RAG documents
- Catastrophic failure if KB unavailable (no silent fallbacks)

### 3. Online G-Eval Judges
Evaluation runs asynchronously on every response:
- **Accuracy Judge**: Factual correctness vs RAG documents (threshold: 0.8)
- **Coherence Judge**: Response clarity & professionalism (threshold: 0.7)
- Metrics sent to LaunchDarkly: `$ld:ai:judge:accuracy`, `$ld:ai:judge:coherence`

### 4. AI Config Experiments
Full LaunchDarkly AI Config tracking:
- Duration, tokens, cost per agent
- Per-agent accuracy evaluation
- A/B test different models (e.g., Sonnet vs Nova vs Llama)
- CUPED variance reduction

### 5. AWS Token Auto-Refresh
Makefile automatically checks AWS SSO token expiry and refreshes before commands.

## Example Queries

```
What's my copay for seeing a specialist?
Find me a cardiologist in San Francisco
Does my plan cover physical therapy?
I need to schedule a callback
```

## Troubleshooting

### AWS Credentials Expired
```bash
make aws-login
```

### LaunchDarkly Config Missing
```bash
make verify  # Check all 7 configs loaded
```

### No RAG Documents Retrieved
1. Check KB IDs in LaunchDarkly custom params (`awskbid`)
2. Verify AWS Bedrock access
3. Confirm KB has indexed documents

### Low Evaluation Scores
- **Accuracy < 0.3**: Hallucinations or wrong RAG docs retrieved
- **Accuracy 0.3-0.7**: Incomplete information
- **Accuracy 0.7-1.0**: Good RAG grounding ✓
- **Coherence < 0.7**: Response quality issues

## Documentation

- [AI_CONFIG_PROMPTS.md](AI_CONFIG_PROMPTS.md) - Synced AI Config prompts
- [LAUNCHDARKLY.md](LAUNCHDARKLY.md) - LaunchDarkly setup guide
- [ui/README.md](ui/README.md) - Web UI documentation

## Requirements

- Python 3.11+
- AWS CLI with SSO configured
- LaunchDarkly account
- AWS Bedrock access (for RAG)

## License

MIT
