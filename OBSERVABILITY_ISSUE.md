# LaunchDarkly AI Observability Issue: Spans Not Appearing in AI Config Monitoring Tab

## Summary
Spans are appearing in **LaunchDarkly > Traces** but NOT in **AI Configs > [Config] > Monitoring tab**, despite following the documented pattern.

**UPDATE**: We have a **multi-config system** (triage_agent, policy_agent, brand_agent, judges) but were setting `ld.ai_config.key` only once at endpoint level. ToggleBank RAG (working example) uses only ONE config per request, so endpoint-level works for them. We need per-agent correlation.

## Environment
- **SDK**: `launchdarkly-server-sdk>=9.12.0`, `launchdarkly-server-sdk-ai>=0.8.0`, `launchdarkly-observability>=0.1.0`
- **Language**: Python 3.13
- **Framework**: FastAPI
- **LLM Provider**: AWS Bedrock (Anthropic Claude)
- **Instrumentation**: `opentelemetry-instrumentation-bedrock`

## What We're Doing (Following ToggleBank RAG Pattern)

```python
# 1. Initialize LD with ObservabilityPlugin
from ldobserve import ObservabilityConfig, ObservabilityPlugin
obs_config = ObservabilityConfig(service_name="my-service", service_version="1.0.0")
ldclient.set_config(Config(SDK_KEY, plugins=[ObservabilityPlugin(obs_config)]))
ld = ldclient.get()

# 2. Instrument Botocore and Bedrock
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.bedrock import BedrockInstrumentor
BotocoreInstrumentor().instrument()
BedrockInstrumentor().instrument()

# 2b. Instrument FastAPI (CRITICAL for parent span context)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor().instrument_app(app)

# 3. In endpoint, set correlation attributes
from opentelemetry import trace
parent_span = trace.get_current_span()
parent_span.set_attribute("ld.ai_config.key", "triage_agent")
parent_span.add_event("feature_flag", attributes={
    "feature_flag.key": "triage_agent",
    "feature_flag.provider.name": "LaunchDarkly",
    "feature_flag.context.id": ctx_id,
    "feature_flag.result.value": True,
})

# 4. Trigger LD variation
_ = ld.variation("triage_agent", context, True)
ld.flush()

# 5. Make Bedrock call
raw = bedrock.converse(modelId=model_id, messages=[...])

# 6. Track metrics
tracker.track_bedrock_converse_metrics(raw)
ld.flush()
```

## What We See

### ✅ Working: Traces Page
- Spans appear in **LaunchDarkly > Monitor > Traces**
- LLM spans have green 🟢 LLM marker
- BedrockConverseLLM.chat spans are captured
- Service name appears correctly

### ❌ Not Working: AI Config Monitoring Tab
- **LaunchDarkly > AI Configs > triage_agent > Monitoring** shows NO spans
- Even though we set `ld.ai_config.key` on parent span
- Even though we call `ld.variation()` before the LLM call
- Even though we add the `feature_flag` event

## What We've Tried

1. ✅ Removed duplicate `ldclient.set_config()` calls (was overwriting ObservabilityPlugin)
2. ✅ Moved span correlation to endpoint level (not inside model invocation)
3. ✅ Added `ld.variation()` call with `ld.flush()`
4. ✅ Added complete `feature_flag` event with all attributes
5. ✅ Verified AI Config exists in LaunchDarkly (key: `triage_agent`)
6. ✅ Verified spans have `ld.ai_config.key` attribute (checked in span details)

## Minimal Reproducible Example

See `minimal_observability_test.py` in this directory.

**To run:**
```bash
# Set environment variable
export LAUNCHDARKLY_SDK_KEY="your-sdk-key"

# Run
python minimal_observability_test.py

# Test
curl -X POST http://localhost:8000/test-chat \
  -H 'Content-Type: application/json' \
  -d '{"userInput":"hello"}'
```

**Expected:** Spans appear in AI Config Monitoring tab  
**Actual:** Spans only appear in general Traces page

## Question for Support

What are we missing to link spans to the AI Config Monitoring tab? The spans are being captured and appear in Traces, but the correlation to the specific AI Config isn't working.

## Reference: Working Example (ToggleBank RAG)

We've based our implementation on the ToggleBank RAG example which successfully shows spans in the AI Config Monitoring tab. The key differences we can see:
- ToggleBank uses `ai_client.config()` (we do too)
- ToggleBank sets `ld.ai_config.key` at endpoint level (we do too now)
- ToggleBank calls `ld.variation()` (we do too now)

But our spans still don't appear in the Monitoring tab. What's different?

## Screenshots Available
- Spans appearing in Traces (with green LLM marker)
- Empty Monitoring tab in AI Config
- Span attributes showing `ld.ai_config.key` is set

