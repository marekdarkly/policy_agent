# ToggleHealth / ToggleCell Multi-Agent System

Multi-agent customer support system demonstrating **LaunchDarkly AI Configs**, **LangGraph**, **AWS Bedrock RAG**, and **G-Eval** evaluation across two demo brands:

- **ToggleHealth** — Medical insurance support (policy coverage, provider lookup, scheduling)
- **ToggleCell** — Mobile/telecom support (plans, stores, billing)

Both brands share the same AI agent architecture and LaunchDarkly configuration. Prompts adapt per-domain via the `{{domain}}` template variable in AI Config prompts.

## Quick Start

### Web Interface (Recommended)

```bash
# ToggleHealth (medical insurance)
cd ui && ./start.sh
# Open http://localhost:3000

# ToggleCell (telecom)
make togglecell
# Open http://localhost:8080
```

### Terminal Interface

```bash
make setup   # First time only
make run     # Interactive chatbot
```

## Architecture

```
                        ┌─────────────────┐
                        │   USER QUERY    │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
           ┌───────▼────────┐       ┌────────▼───────┐
           │   LangGraph    │       │  LD Agent      │
           │   StateGraph   │       │  Graph SDK     │
           │  (workflow.py) │       │ (agent_graph   │
           │                │       │  _runner.py)   │
           └───────┬────────┘       └────────┬───────┘
                   └────────────┬────────────┘
                                │
                       ┌────────▼────────┐
                       │ TRIAGE ROUTER   │
                       │ (triage_agent)  │
                       └────────┬────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
   ┌───────▼────────┐  ┌───────▼────────┐  ┌───────▼────────┐
   │ POLICY AGENT   │  │ PROVIDER AGENT │  │ SCHEDULER      │
   │ + RAG (Bedrock)│  │ + RAG (Bedrock)│  │ AGENT          │
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

Two workflow engines can drive the same agent graph:

| Engine | Entry Point | Description |
|--------|-------------|-------------|
| **LangGraph** | `src/graph/workflow.py` | LangGraph `StateGraph` with explicit node/edge definitions |
| **LD Agent Graph** | `src/graph/agent_graph_runner.py` | Traverses the graph structure defined in LaunchDarkly, resolving AI Configs at each node |

## Agents & Judges

| Component | LD Config Key | RAG | Purpose |
|-----------|---------------|-----|---------|
| **Triage Router** | `triage_agent` | No | Classify query intent and route |
| **Policy Specialist** | `policy_agent` | Yes | Coverage, benefits, claims |
| **Provider Specialist** | `provider_agent` | Yes | Find doctors, network status |
| **Scheduler** | `scheduler_agent` | No | Schedule callbacks |
| **Brand Voice** | `brand_agent` | No | Personalize response tone |
| **Accuracy Judge** | `ai-judge-accuracy` | - | G-Eval factual accuracy (threshold: 0.8) |
| **Coherence Judge** | `ai-judge-coherence` | - | G-Eval response quality (threshold: 0.7) |

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

## Observability

All execution is instrumented with OpenTelemetry and exported to **LaunchDarkly Monitor > Traces** via the `ObservabilityPlugin` from `ldobserve`.

- `BedrockInstrumentor` auto-creates spans for every LLM call
- Explicit spans in workflow/handler code provide the parent context
- `ModelInvoker` annotates spans with `ld.ai_config.key` for AI Config correlation

See `src/utils/observability.py` for initialization details.

## UI

Two React frontends share a single FastAPI backend:

| Frontend | Brand | Port | Command |
|----------|-------|------|---------|
| `ui/frontend/` | ToggleHealth (medical insurance) | 3000 | `make ui` |
| `ui/frontend-togglecell/` | ToggleCell (telecom) | 8080 | `make togglecell` |

The backend (`ui/backend/server.py`) runs on port 8000 and proxies requests to the multi-agent workflow.

See [ui/README.md](ui/README.md) for full UI documentation.

## Lambda: Synthetic Traffic Generator

Scheduled Lambda functions generate synthetic traffic by exercising the full agent pipeline on a timer (default: hourly, 10 iterations per invocation).

| Handler | File | Engine |
|---------|------|--------|
| **LangGraph** | `lambda/synthetic_traffic/handler.py` | `src/graph/workflow.py` |
| **Agent Graph** | `lambda/synthetic_traffic/handler_agent_graph.py` | LD Agent Graph SDK |

Infrastructure is defined in Terraform (`lambda/synthetic_traffic/terraform/main.tf`) with deployment via `deploy.sh`.

See [lambda/synthetic_traffic/README.md](lambda/synthetic_traffic/README.md) for architecture, trace hierarchy, and deployment instructions.

## Simulations

Scripts in `simulations/` generate synthetic metrics for LaunchDarkly experiments **without** making real model calls:

| Script | Purpose |
|--------|---------|
| `simulate_experiments.py` | General experiment simulator for policy & provider agents |
| `simulate_policy_prompts.py` | Prompt-variation experiments |
| `simulate_brand_agent.py` | Brand voice agent metrics |
| `run_batched_experiments.py` | Orchestrate batch runs with configurable intervals |
| `guarded_release_accuracy_simulator.py` | Demo guarded-release rollback with fake accuracy timelines |

```bash
ITERATIONS=200 python simulations/simulate_experiments.py
```

See [simulations/README.md](simulations/README.md) for details.

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/upload_tools_to_launchdarkly.py` | Upload tool definitions from `launchdarkly_tools_library.json` to LaunchDarkly |
| `scripts/launchdarkly_tools_library.json` | 20 pre-built MCP tool definitions (Snowflake, calendar, NLP, healthcare, etc.) |

```bash
make upload-tools
```

See [scripts/README.md](scripts/README.md) for the full tool catalog.

## Testing & Evaluation

Test harnesses live in `tests/` and run real agent evaluations:

```bash
# Full test suite (50 iterations)
make test-suite

# Quick test (5 iterations)
make test-quick

# Evaluate a specific agent
python tests/test_agent_suite.py --evaluate policy_agent --limit 10
```

| Script | Purpose |
|--------|---------|
| `test_agent_suite.py` | End-to-end circuit test with real model calls, CSV/JSON export |
| `test_agent_evaluation.py` | Per-agent evaluation with G-Eval scoring |
| `test_evaluation_mode_demo.py` | Demo script for evaluation mode |
| `test_metrics_diagnostic.py` | Diagnostic for metric delivery and attribution |

Test datasets are in `test_data/`:
- `qa_dataset.json` — Full question-answer dataset
- `qa_dataset_demo.json` — Smaller demo subset

## RAG Knowledge Base Data

Markdown documents in `data/markdown/` serve as the source corpus for AWS Bedrock Knowledge Bases:

| Directory | Count | Content |
|-----------|-------|---------|
| `policies/` | 90 | ToggleHealth insurance plans (HMO Gold, PPO Platinum, EPO Silver, HDHP Bronze), claims, pharmacy, special programs |
| `providers/` | 280 | ToggleHealth provider directory (PCPs, specialists, mental health, pharmacies across 20 states) |
| `togglecell-plans/` | 23 | ToggleCell mobile plans (5G Unlimited, Family Share, SIM Flex, Pay-As-You-Go), coverage, devices |
| `togglecell-stores/` | 20 | ToggleCell retail store locations across the UK |

## Environment Setup

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required variables:

| Variable | Description |
|----------|-------------|
| `LAUNCHDARKLY_SDK_KEY` | Server-side SDK key (`sdk-...`) |
| `LAUNCHDARKLY_PROJECT_KEY` | LaunchDarkly project key |
| `LAUNCHDARKLY_ACCESS_TOKEN` | LaunchDarkly API access token (`api-...`) for tool uploads |
| `AWS_PROFILE` | AWS SSO profile name |
| `AWS_REGION` | AWS region (default: `us-east-1`) |

Optional:

| Variable | Description |
|----------|-------------|
| `BEDROCK_POLICY_KB_ID` | Bedrock Knowledge Base ID for policy documents |
| `BEDROCK_PROVIDER_KB_ID` | Bedrock Knowledge Base ID for provider documents |
| `LLM_PROVIDER` | LLM provider fallback (default: `bedrock`) |
| `LLM_MODEL` | Model fallback (default: `claude-3-5-sonnet`) |

## Makefile Commands

```bash
make setup          # Install dependencies & check AWS
make run            # Interactive chatbot (terminal)
make ui             # ToggleHealth web UI
make togglecell     # ToggleCell web UI
make test-suite     # Full agent test suite (50 iterations)
make test-quick     # Quick test (5 iterations)
make upload-tools   # Upload tools to LaunchDarkly
make verify         # Check AWS + system status
make info           # Show system information
make format         # Format code with black
make lint           # Lint with ruff
make clean          # Remove cache files
```

## Project Structure

```
policy_agent/
├── src/
│   ├── agents/                     # Agent implementations
│   │   ├── triage_router.py
│   │   ├── policy_specialist.py
│   │   ├── provider_specialist.py
│   │   ├── scheduler_specialist.py
│   │   └── brand_voice_agent.py
│   ├── evaluation/                 # G-Eval judges
│   │   ├── judge.py
│   │   └── agent_evaluator.py
│   ├── graph/                      # Workflow orchestration
│   │   ├── workflow.py             # LangGraph StateGraph
│   │   ├── agent_graph_runner.py   # LD Agent Graph traversal
│   │   └── state.py               # Shared state definitions
│   ├── tools/                      # RAG & utility tools
│   │   ├── bedrock_rag.py
│   │   ├── policy_db.py
│   │   ├── provider_db.py
│   │   └── calendar.py
│   └── utils/
│       ├── launchdarkly_config.py  # LD SDK initialization
│       ├── observability.py        # OpenTelemetry + LD tracing
│       ├── bedrock_llm.py          # Bedrock model invoker
│       ├── llm_config.py           # Model config resolution
│       ├── user_profile.py         # User context for LD
│       ├── aws_sso.py              # AWS SSO token management
│       ├── aws_token_monitor.py    # Token expiry monitoring
│       └── fetch_ai_config_prompts.py
├── data/
│   └── markdown/                   # RAG knowledge base source
│       ├── policies/               # ToggleHealth policy docs (90)
│       ├── providers/              # ToggleHealth provider directory (280)
│       ├── togglecell-plans/       # ToggleCell plan docs (23)
│       └── togglecell-stores/      # ToggleCell store locations (20)
├── ui/
│   ├── backend/                    # FastAPI server
│   │   ├── server.py
│   │   └── requirements.txt
│   ├── frontend/                   # React + Vite (ToggleHealth)
│   ├── frontend-togglecell/        # React + Vite (ToggleCell)
│   ├── public/                     # Shared static assets
│   └── start.sh                    # Auto-setup launcher
├── lambda/
│   └── synthetic_traffic/          # Scheduled Lambda traffic generator
│       ├── handler.py              # LangGraph handler
│       ├── handler_agent_graph.py  # LD Agent Graph handler
│       ├── common.py               # Shared user/question pools
│       ├── terraform/main.tf       # Infrastructure as code
│       ├── deploy.sh               # Build & deploy script
│       ├── Dockerfile
│       └── requirements-lambda.txt
├── simulations/                    # Synthetic metric generators (no AI calls)
│   ├── simulate_experiments.py
│   ├── simulate_policy_prompts.py
│   ├── simulate_brand_agent.py
│   ├── run_batched_experiments.py
│   └── guarded_release_accuracy_simulator.py
├── scripts/
│   ├── upload_tools_to_launchdarkly.py
│   └── launchdarkly_tools_library.json
├── tests/                          # Agent evaluation harnesses
│   ├── test_agent_suite.py
│   ├── test_agent_evaluation.py
│   ├── test_evaluation_mode_demo.py
│   └── test_metrics_diagnostic.py
├── test_data/
│   ├── qa_dataset.json
│   └── qa_dataset_demo.json
├── interactive_chatbot.py          # Terminal chatbot
├── Makefile
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## Key Features

### Dynamic AI Config Management
All prompts and model configurations are managed in LaunchDarkly AI Configs -- zero hardcoded prompts in application code. Model selection, prompt engineering, and agent behavior can be changed via LaunchDarkly without redeployment.

### Multi-Domain Support
A single set of AI Configs powers both ToggleHealth and ToggleCell. The `{{domain}}` template variable in prompts adapts agent behavior to the active brand.

### Dual Workflow Engines
The system supports two orchestration approaches: a LangGraph `StateGraph` with explicit Python node/edge definitions, and the LaunchDarkly Agent Graph SDK which resolves graph structure from the LaunchDarkly platform.

### RAG-Only Specialists
Policy and Provider agents use exclusively Bedrock Knowledge Base retrieval. All responses are grounded in RAG documents with no database fallback or hardcoded data.

### Online G-Eval Judges
Evaluation runs asynchronously on every response, sending scores to LaunchDarkly as experiment metrics (`$ld:ai:judge:accuracy`, `$ld:ai:judge:coherence`).

### AI Config Experiments
Full LaunchDarkly experiment support: duration, tokens, cost per agent, per-agent accuracy evaluation, A/B testing across models (Sonnet, Nova, Llama, Haiku), and CUPED variance reduction.

### Observability
OpenTelemetry instrumentation exports structured traces to LaunchDarkly Monitor, with auto-instrumented Bedrock LLM spans nested under explicit workflow spans.

## Requirements

- Python 3.11+
- Node.js 18+ (for UI frontends)
- AWS CLI with SSO configured
- LaunchDarkly account with AI Configs enabled
- AWS Bedrock access (us-east-1)

## License

MIT
