# Medical Insurance Support Multi-Agent System

A LangGraph-based multi-agent system for intelligent triage and handling of medical insurance customer support queries. The system automatically routes customer questions to specialized agents for efficient and accurate responses.

## Overview

This system provides:
- 🤖 **Intelligent Triage**: Automatically classifies and routes customer queries
- 📋 **Policy Specialist**: Answers coverage, benefits, and claims questions
- 🏥 **Provider Lookup**: Helps find in-network doctors and specialists
- 📅 **Live Agent Scheduling**: Handles complex issues and schedules callbacks

## Architecture

```
Customer Query → Triage Router → [Policy | Provider | Scheduler] Specialist → Response
```

See [SDD.md](SDD.md) for detailed architecture documentation.

## Features

- Multi-agent orchestration using LangGraph
- State management with Pydantic
- Modular agent design for easy extension
- Simulated backends (policy DB, provider directory, calendar)
- Configurable LLM providers (OpenAI or Anthropic)
- Confidence-based routing and escalation
- Comprehensive test suite

## Quick Start

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd policy_agent
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Edit `.env` file:

```bash
# For OpenAI
OPENAI_API_KEY=your_key_here
LLM_PROVIDER=openai
LLM_MODEL=gpt-4-turbo-preview

# Or for Anthropic
ANTHROPIC_API_KEY=your_key_here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-3-5-sonnet-20241022
```

### Running Examples

Run predefined examples:
```bash
python examples/run_example.py
```

Run in interactive mode:
```bash
python examples/run_example.py interactive
```

### Basic Usage

```python
from src.graph.workflow import run_workflow

# Run a query
result = run_workflow(
    user_message="What is my copay for seeing a specialist?",
    user_context={
        "policy_id": "POL-12345",
        "coverage_type": "Gold Plan"
    }
)

print(result["final_response"])
```

## Project Structure

```
policy_agent/
├── src/
│   ├── agents/              # Agent implementations
│   │   ├── triage_router.py
│   │   ├── policy_specialist.py
│   │   ├── provider_specialist.py
│   │   └── scheduler_specialist.py
│   ├── graph/               # LangGraph workflow
│   │   ├── state.py        # State management
│   │   └── workflow.py     # Graph orchestration
│   ├── tools/               # Backend tools (simulated)
│   │   ├── policy_db.py
│   │   ├── provider_db.py
│   │   └── calendar.py
│   └── utils/               # Utilities
│       ├── prompts.py
│       └── llm_config.py
├── tests/                   # Test suite
├── examples/                # Example scripts
├── SDD.md                   # Software Design Document
└── README.md
```

## Testing

Run the test suite:
```bash
pytest tests/
```

Run with coverage:
```bash
pytest tests/ --cov=src --cov-report=html
```

## Agent Types

### Triage Router
- Classifies incoming queries
- Extracts relevant context
- Routes to appropriate specialist
- Handles low-confidence escalation

### Policy Specialist
- Answers coverage questions
- Explains benefits and deductibles
- Provides claim procedure information
- Accesses policy database

### Provider Specialist
- Searches provider directory
- Filters by specialty and location
- Verifies network status
- Returns provider contact information

### Scheduler Specialist
- Handles complex queries
- Schedules live agent callbacks
- Collects necessary information
- Provides confirmation details

## Extending the System

### Adding a New Agent

1. Create agent module in `src/agents/`:
```python
def new_agent_node(state: AgentState) -> dict:
    # Agent logic here
    return updated_state
```

2. Update workflow in `src/graph/workflow.py`:
```python
workflow.add_node("new_agent", new_agent_node)
workflow.add_edge("triage", "new_agent")
```

3. Add routing logic and tests

### Adding New Tools

Create tool module in `src/tools/`:
```python
def new_tool(params):
    # Tool implementation
    return result
```

## Configuration Options

- **LLM Provider**: OpenAI or Anthropic
- **Model Selection**: Any supported chat model
- **Temperature**: Control response randomness
- **Confidence Threshold**: Adjust escalation sensitivity

## Sample Data

The system includes simulated data:
- 2 sample insurance policies
- 5 sample healthcare providers
- Generated appointment slots

Replace with real database connections in production.

## Development

### Code Style
```bash
black src/ tests/
ruff check src/ tests/
mypy src/
```

### Adding Dependencies
```bash
# Add to requirements.txt or pyproject.toml
pip install -e ".[dev]"
```

## Security & Compliance

- HIPAA compliance considerations included in design
- PII data handling guidelines in SDD
- Audit logging hooks available
- Role-based access control ready

## Roadmap

- [ ] RAG integration for policy documents
- [ ] Real database connectors
- [ ] Multi-turn conversation support
- [ ] Voice interface integration
- [ ] Analytics dashboard
- [ ] Multi-language support

## License

MIT License - see [LICENSE](LICENSE) file

## Contributing

Contributions welcome! Please read the SDD first to understand the architecture.

## Support

For issues and questions, please open a GitHub issue.
