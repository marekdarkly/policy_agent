# LaunchDarkly AI Observability

This project integrates LaunchDarkly AI Observability using OpenLLMetry to provide visibility into LLM behavior in production.

## What Gets Tracked

Every LLM request generates spans that capture:
- **Prompts** - Input text sent to the model
- **Responses** - Generated output from the model  
- **Latency** - Time taken for model inference
- **Token Usage** - Input and output tokens consumed
- **Model Metadata** - Provider, model name, temperature, etc.
- **Errors** - Any failures or exceptions during generation

## How It Works

### Architecture

```
Your Application
       ↓
   (imports observability module)
       ↓
Traceloop SDK (OpenLLMetry)
       ↓
OpenTelemetry Instrumentation
       ↓
  (captures LLM spans)
       ↓
LaunchDarkly Observability
       ↓
  LaunchDarkly UI
  (Monitor > Traces)
```

### Initialization Order (CRITICAL!)

The order of imports is crucial for proper span capture:

1. **Load environment variables** (`.env`)
2. **Initialize observability** (`src/utils/observability.py`)
3. **Import LLM modules** (LangChain, agents, workflow, etc.)

This order ensures that:
- OpenLLMetry instruments frameworks before they're used
- Parent-child span relationships are correctly established
- All LLM calls are captured and tracked

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `traceloop-sdk` - OpenLLMetry core
- `opentelemetry-*` - Instrumentation packages
- LaunchDarkly SDK with AI support

### 2. Configure Environment

Add to your `.env`:

```bash
# LaunchDarkly SDK Key (required for observability)
LAUNCHDARKLY_SDK_KEY=sdk-your-key-here

# Optional: Custom observability endpoint
LD_OBSERVABILITY_ENDPOINT=https://events.launchdarkly.com

# Optional: Environment name
ENVIRONMENT=production
```

### 3. Observability Auto-Initializes

The observability module auto-initializes when imported if `LAUNCHDARKLY_SDK_KEY` is set.

Both entry points are already configured:
- `interactive_chatbot.py` - Terminal chatbot
- `ui/backend/server.py` - FastAPI server

## Viewing Spans in LaunchDarkly

### Access Traces

1. Navigate to **LaunchDarkly Dashboard**
2. Click **"Monitor"** in the left sidebar
3. Click **"Traces"**

### Identify LLM Spans

LLM spans are marked with a **green LLM symbol** 🟢

### Span Details

Click any LLM span to view:

**Summary Tab:**
- Model name and provider
- Prompt text (input)
- Response text (output)
- Token counts (input/output)
- Latency (duration)
- Status (success/error)

**All Attributes Tab:**
- Raw OpenTelemetry span attributes
- Service information
- Environment details
- Custom metadata

### Querying Spans

Use the search bar to filter by:
- `gen_ai.model:claude-3-sonnet` - Specific model
- `gen_ai.prompt_tokens > 1000` - High token usage
- `duration > 5s` - Slow requests
- `service.name:togglehealth-policy-agent` - Our service
- `deployment.environment:production` - Environment

### Use Cases

**Optimize Latency & Cost:**
- Monitor model performance by latency
- Track token usage to control costs
- Compare model versions

**Identify Runtime Errors:**
- Correlate failed generations with error logs
- View provider exceptions in span events

**Validate Model Outputs:**
- Review prompt/response pairs for accuracy
- Check consistency across model calls

**Debug Multi-Agent Flows:**
- See hierarchical timeline of agent interactions
- Track RAG document retrieval
- Monitor evaluation (judge) calls

## Supported Frameworks

Our implementation automatically instruments:

✅ **LangChain** - All LLM calls via LangChain  
✅ **AWS Bedrock** - Converse API calls  
✅ **Custom BedrockConverseLLM** - Our wrapper class

## Instrumentation Details

### What Gets Instrumented

All LLM calls made through:
- `BedrockConverseLLM.invoke()`
- `ChatBedrock.invoke()`
- LangChain chains and agents
- Model invocations in triage, specialists, and brand voice agents
- Evaluation (judge) calls

### Span Hierarchy

```
Request Span (user query)
├── Triage Agent Span
│   └── LLM Span (intent classification)
├── Specialist Agent Span  
│   ├── RAG Retrieval Span
│   └── LLM Span (specialist response)
├── Brand Voice Agent Span
│   └── LLM Span (brand transformation)
└── Evaluation Span
    ├── Accuracy Judge LLM Span
    └── Coherence Judge LLM Span
```

### Standard Attributes

Every LLM span includes:
- `gen_ai.model` - Model ID
- `gen_ai.prompt_tokens` - Input tokens
- `gen_ai.completion_tokens` - Output tokens  
- `gen_ai.input` - Prompt text
- `gen_ai.output` - Response text
- `duration` - Total latency
- `service.name` - Service identifier
- `deployment.environment` - Environment

## Privacy & Data Handling

⚠️ **Important:** LLM spans include full prompt and response text as attributes.

**This may contain:**
- Personally Identifiable Information (PII)
- Protected Health Information (PHI)
- Sensitive user data

**Before enabling in production:**
1. Review your organization's data handling policies
2. Ensure compliance with HIPAA, GDPR, etc.
3. Consider redacting sensitive data at the source
4. Configure span attribute filtering if needed

## Troubleshooting

### Spans Not Appearing

**Check SDK Key:**
```bash
echo $LAUNCHDARKLY_SDK_KEY
```

**Check Initialization Logs:**
Look for these in terminal:
```
🔧 Initializing LaunchDarkly AI Observability with OpenLLMetry...
✅ Traceloop SDK (OpenLLMetry) initialized
✅ LangChain instrumentation registered
🎉 AI Observability fully initialized!
```

**Verify Import Order:**
Ensure `src/utils/observability` is imported BEFORE any LLM modules.

### Import Order Errors

If you see instrumentation warnings, check that:
1. `observability.initialize_observability()` is called first
2. LangChain/Bedrock modules are imported after
3. No circular imports exist

### Missing Spans

If some LLM calls aren't captured:
- Ensure they go through instrumented frameworks (LangChain)
- Check if custom wrappers bypass instrumentation
- Verify OpenTelemetry context propagation

## Performance Impact

Observability adds minimal overhead:
- **Latency:** ~5-10ms per LLM call
- **Memory:** ~1-2MB for span buffering
- **Network:** Async batch export (non-blocking)

Spans are batched and exported asynchronously to avoid blocking LLM calls.

## Disabling Observability

To disable (e.g., for local development):

```bash
# Remove or comment out in .env
# LAUNCHDARKLY_SDK_KEY=sdk-...
```

Or set explicitly:
```bash
LAUNCHDARKLY_SDK_KEY=""
```

The system will continue to work without observability, logging:
```
⚠️  No LaunchDarkly SDK key found. Observability disabled.
```

## References

- [LaunchDarkly LLM Observability Docs](https://launchdarkly.com/docs/home/observability/llm-observability)
- [OpenLLMetry GitHub](https://github.com/traceloop/openllmetry)
- [OpenTelemetry Semantic Conventions for GenAI](https://opentelemetry.io/docs/specs/semconv/gen-ai/)

