# Software Design Document: Medical Insurance Support Multi-Agent System

## 1. Overview

A LangGraph-based multi-agent system for triaging and handling medical insurance customer support queries. The system intelligently routes customer questions to specialized agents, providing efficient and accurate responses.

## 2. Architecture

### 2.1 System Components

```
┌─────────────────────────────────────────────────────────────┐
│                       Customer Query                         │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
                    ┌───────────────┐
                    │ Triage Router │
                    │    Agent      │
                    └───────┬───────┘
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
    ┌───────────┐   ┌──────────────┐   ┌──────────────┐
    │  Policy   │   │   Provider   │   │ Live Agent   │
    │ Specialist│   │    Lookup    │   │  Scheduler   │
    │   Agent   │   │  Specialist  │   │  Specialist  │
    └─────┬─────┘   └──────┬───────┘   └──────┬───────┘
          │                │                   │
          └────────────────┼───────────────────┘
                           │
                           ▼
                    ┌────────────┐
                    │  Response  │
                    │   to User  │
                    └────────────┘
```

### 2.2 State Management

**AgentState Schema:**
- `messages`: List of conversation messages
- `next_agent`: Name of the next agent to route to
- `query_type`: Classified query type (policy/provider/live_agent)
- `user_context`: Customer metadata (policy_id, location, etc.)
- `confidence_score`: Router confidence in classification
- `escalation_needed`: Boolean flag for complex queries

## 3. Agent Specifications

### 3.1 Triage Router Agent

**Purpose:** Classify incoming queries and route to appropriate specialist

**Responsibilities:**
- Analyze customer query using LLM
- Classify into categories: policy_question, provider_lookup, schedule_agent
- Extract relevant context (policy numbers, locations, symptoms)
- Determine confidence level
- Route to appropriate specialist or escalate

**Decision Logic:**
- Policy-related keywords → Policy Specialist
- Provider/doctor/network keywords → Provider Lookup Specialist
- Complex/urgent/speak-to-agent keywords → Live Agent Scheduler
- Low confidence (< 0.7) → Live Agent Scheduler

### 3.2 Policy Specialist Agent

**Purpose:** Answer policy-related questions

**Responsibilities:**
- Handle coverage inquiries
- Explain benefits and deductibles
- Clarify claim procedures
- Provide policy document references

**Capabilities:**
- RAG-enabled for policy document retrieval
- Access to policy database (simulated in MVP)
- Natural language explanation of policy terms

### 3.3 Provider Lookup Specialist Agent

**Purpose:** Help customers find in-network providers

**Responsibilities:**
- Search provider directory by specialty
- Filter by location and insurance network
- Provide contact information
- Check provider availability

**Capabilities:**
- Geographic search
- Specialty-based filtering
- Network verification
- Return structured provider information

### 3.4 Live Agent Scheduler Specialist

**Purpose:** Schedule conversations with human agents

**Responsibilities:**
- Handle complex queries requiring human intervention
- Schedule callback appointments
- Collect necessary information for agent
- Provide confirmation details

**Capabilities:**
- Calendar integration (simulated in MVP)
- Availability checking
- Confirmation generation
- Query summarization for human agent

## 4. Technology Stack

- **LangGraph**: Orchestration and state machine management
- **LangChain**: LLM integration and prompt management
- **LaunchDarkly**: AI Config management for per-agent model configuration
- **Python 3.11+**: Core implementation language
- **Pydantic**: State validation and data models
- **OpenAI/Anthropic API**: LLM backend (configurable)

## 5. Data Flow

1. **Input**: Customer submits query via chat interface
2. **Triage**: Router agent analyzes and classifies query
3. **Route**: Graph routes to appropriate specialist node
4. **Process**: Specialist agent processes query with domain knowledge
5. **Response**: System returns formatted response
6. **Feedback Loop**: Optional human-in-the-loop for quality assurance

## 6. Implementation Phases

### Phase 1: Core Structure (Current)
- LangGraph state machine setup
- Basic agent node implementation
- Router logic with LLM classification
- Simulated backends for specialists

### Phase 2: Enhanced Capabilities
- RAG integration for policy documents
- Real provider database integration
- Actual calendar system integration
- Conversation memory and context retention

### Phase 3: Production Features
- Multi-turn conversation support
- Confidence-based human escalation
- Analytics and monitoring
- A/B testing framework

## 7. Extension Points

- **Additional Specialists**: Claims processing, billing inquiries
- **Multi-language Support**: Translation layer for agents
- **Voice Integration**: Speech-to-text preprocessing
- **Analytics Dashboard**: Query patterns and agent performance

## 8. Success Metrics

- Classification accuracy > 90%
- Average response time < 3 seconds
- Customer satisfaction score > 4.5/5
- Escalation rate < 15%
- Query resolution rate > 85%

## 9. Security & Compliance

- HIPAA compliance for medical information
- PII data encryption and handling
- Audit logging for all interactions
- Role-based access control for agent backends

## 10. File Structure

```
policy_agent/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── triage_router.py
│   │   ├── policy_specialist.py
│   │   ├── provider_specialist.py
│   │   └── scheduler_specialist.py
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── state.py
│   │   └── workflow.py
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── policy_db.py
│   │   ├── provider_db.py
│   │   └── calendar.py
│   └── utils/
│       ├── __init__.py
│       └── prompts.py
├── tests/
│   ├── test_triage.py
│   ├── test_agents.py
│   └── test_workflow.py
├── examples/
│   └── run_example.py
├── requirements.txt
├── pyproject.toml
└── README.md
```
