"""
Minimal reproducible example for LaunchDarkly AI Observability
Demonstrates issue: Spans appear in Traces but not in AI Config Monitoring tab
"""
import os
from fastapi import FastAPI
from pydantic import BaseModel

# ========== STEP 1: LaunchDarkly + Observability FIRST ==========
import ldclient
from ldclient.config import Config
from ldclient import Context
from ldobserve import ObservabilityConfig, ObservabilityPlugin
from ldai.client import LDAIClient, AIConfig, ModelConfig

# Initialize LaunchDarkly with ObservabilityPlugin
LD_SDK_KEY = os.getenv("LAUNCHDARKLY_SDK_KEY")
obs_config = ObservabilityConfig(
    service_name="minimal-test",
    service_version="1.0.0",
)
ldclient.set_config(Config(LD_SDK_KEY, plugins=[ObservabilityPlugin(obs_config)]))
ld = ldclient.get()
ai_client = LDAIClient(ld)

# ========== STEP 2: OpenLLMetry Instrumentation ==========
from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
from opentelemetry.instrumentation.bedrock import BedrockInstrumentor
BotocoreInstrumentor().instrument()
BedrockInstrumentor().instrument()

# ========== STEP 3: AWS Bedrock Client ==========
import boto3
session = boto3.Session(profile_name='marek', region_name='us-east-1')
bedrock = session.client("bedrock-runtime")

# ========== STEP 4: FastAPI App ==========
app = FastAPI()

# Instrument FastAPI (CRITICAL: Ensures request spans exist as parents for LLM spans)
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
FastAPIInstrumentor().instrument_app(app)

class ChatRequest(BaseModel):
    userInput: str

@app.post("/test-chat")
def test_chat(req: ChatRequest):
    """
    Minimal endpoint to test AI Config observability correlation.
    
    Expected: Spans should appear in LaunchDarkly > AI Configs > triage_agent > Monitoring
    Actual: Spans appear in Traces but NOT in AI Config Monitoring tab
    """
    from opentelemetry import trace
    
    # Create user context
    context = Context.builder("test-user").set("name", "Test User").build()
    
    # Get AI Config
    default_cfg = AIConfig(
        enabled=True,
        model=ModelConfig(name="us.anthropic.claude-3-5-sonnet-20241022-v2:0"),
        messages=[]
    )
    cfg, tracker = ai_client.config("triage_agent", context, default_cfg, {})
    
    # ========== CORRELATION LOGIC (from ToggleBank RAG) ==========
    try:
        parent_span = trace.get_current_span()
        if parent_span and parent_span.is_recording():
            # Set ld.ai_config.key attribute
            parent_span.set_attribute("ld.ai_config.key", "triage_agent")
            
            # Add feature_flag event
            ctx_dict = context.to_dict()
            ctx_id = ctx_dict.get('key', 'anonymous')
            parent_span.add_event(
                "feature_flag",
                attributes={
                    "feature_flag.key": "triage_agent",
                    "feature_flag.provider.name": "LaunchDarkly",
                    "feature_flag.context.id": ctx_id,
                    "feature_flag.result.value": True,
                },
            )
            
            # Trigger LD variation
            _ = ld.variation("triage_agent", context, True)
            ld.flush()
    except Exception as e:
        print(f"Correlation error: {e}")
    
    # Make Bedrock call
    model_id = cfg.model.name if cfg.model else "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
    raw = bedrock.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": req.userInput}]}],
    )
    
    # Track metrics
    if tracker:
        tracker.track_bedrock_converse_metrics(raw)
        ld.flush()
    
    reply = raw["output"]["message"]["content"][0]["text"]
    usage = raw.get("usage", {})
    
    return {
        "response": reply,
        "model": model_id,
        "tokens": {"input": usage.get("inputTokens"), "output": usage.get("outputTokens")},
        "span_recording": parent_span.is_recording() if 'parent_span' in locals() else False,
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*80)
    print("MINIMAL OBSERVABILITY TEST")
    print("="*80)
    print(f"Service: minimal-test")
    print(f"AI Config Key: triage_agent")
    print(f"Expected: Spans in LaunchDarkly > AI Configs > triage_agent > Monitoring")
    print(f"Test: curl -X POST http://localhost:8000/test-chat -H 'Content-Type: application/json' -d '{{\"userInput\":\"hello\"}}'")
    print("="*80 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

