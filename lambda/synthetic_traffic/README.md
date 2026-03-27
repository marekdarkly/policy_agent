# Synthetic Traffic Generator

Generates synthetic event data for ToggleHealth's multi-agent insurance chatbot by exercising the full workflow pipeline on a schedule.

## Architecture

Two Lambda handlers run **10 iterations each, every hour** via EventBridge:

| Handler | File | Workflow Engine | Description |
|---------|------|-----------------|-------------|
| **LangGraph** | `handler.py` | `src/graph/workflow.py` (LangGraph `StateGraph`) | Uses the existing LangGraph-based multi-agent workflow |
| **Agent Graph** | `handler_agent_graph.py` | LaunchDarkly Agent Graph SDK | Traverses the graph structure defined in LaunchDarkly |

Both handlers share common infrastructure from `common.py` (user pool, question pool, beta tester profile generation).

## Observability

All execution is wrapped in OpenTelemetry spans that export to **LaunchDarkly > Monitor > Traces** via the `ObservabilityPlugin`.

### Trace Hierarchy

```
synthetic-traffic-batch                    # Root span (1 per Lambda invocation)
├── synthetic-iteration                    # Per-iteration span (x10)
│   └── multi-agent-workflow               # Workflow execution
│       ├── agent.triage                   # Triage routing
│       │   └── [Bedrock LLM span]         # Auto-instrumented
│       ├── agent.policy_specialist        # (or provider/scheduler)
│       │   └── [Bedrock LLM span]
│       └── agent.brand_voice              # Brand voice synthesis
│           └── [Bedrock LLM span]
```

### How It Works

1. **`ObservabilityPlugin`** (from `ldobserve`) configures the OTEL `TracerProvider` to export spans to LaunchDarkly
2. **`BedrockInstrumentor`** auto-creates spans for every LLM call
3. **Explicit spans** in `handler.py`, `workflow.py` provide the parent context that groups auto-instrumented spans into coherent traces
4. **`ModelInvoker`** annotates spans with `ld.ai_config.key` for AI Config correlation
5. **`_flush_traces()`** force-flushes the `TracerProvider` before Lambda exits

### Key Attributes on Spans

| Span | Attributes |
|------|------------|
| `synthetic-traffic-batch` | `synthetic.total_iterations`, `synthetic.source`, `synthetic.timestamp` |
| `synthetic-iteration` | `synthetic.user.name`, `synthetic.question`, `synthetic.request_id`, `synthetic.feedback`, `synthetic.query_type` |
| `multi-agent-workflow` | `workflow.user_message`, `workflow.request_id`, `workflow.query_type`, `workflow.response_length` |
| `agent.<name>` | `agent.name`, `agent.model`, `agent.tokens.input`, `agent.tokens.output`, `agent.duration_ms` |

### Verifying Traces

1. Run the handler locally or invoke the Lambda
2. Check logs for `trace_sampled=True` — confirms spans are being collected
3. Check for `Trace spans flushed to LaunchDarkly` — confirms export
4. View traces in **LaunchDarkly > Monitor > Traces**

## Beta Tester Targeting

Synthetic users are configured to land in the **Beta Testers** segment:

- `role = "Beta"` — matches the segment rule
- `customer_tier = "beta"`, `plan = "beta"` — prevents matching the Commercial Segment rule
- `user_key` prefixed with `synthetic-` for identification

## Local Development

```bash
# From project root
source venv/bin/activate
python lambda/synthetic_traffic/handler.py
```

Requires `.env` with `LAUNCHDARKLY_SDK_KEY` and valid AWS SSO credentials.

## Deployment

```bash
cd lambda/synthetic_traffic
./deploy.sh build    # Build Docker image
./deploy.sh push     # Push to ECR
./deploy.sh infra    # Terraform apply
./deploy.sh update   # Build + push + update Lambda
./deploy.sh invoke   # Manual test invocation
./deploy.sh logs     # Tail CloudWatch logs
```
