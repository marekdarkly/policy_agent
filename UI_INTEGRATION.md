# Multi-Agent System UI Integration

This document explains how the multi-agent policy system is integrated into the ToggleHealth UI.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     Next.js Frontend                             │
│  /components/chatbot/ChatBotMultiAgent.tsx                      │
│  - Shows agent status updates in real-time                       │
│  - Displays agent flow and metrics                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Next.js API Route                                   │
│  /pages/api/chat-multiagent.ts                                  │
│  - Proxies requests to Python backend                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│         FastAPI Backend                                          │
│  /backend/fastapi_wrapper.py                                    │
│  - Endpoint: POST /api/chat-multiagent                          │
│  - Calls api_wrapper.py                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│       Policy Agent API Wrapper                                   │
│  /api_wrapper.py                                                │
│  - Converts request to workflow format                           │
│  - Calls run_workflow from src/graph/workflow.py                │
│  - Returns response in UI-compatible format                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│          Multi-Agent Workflow                                    │
│  src/graph/workflow.py                                          │
│  Triage → Specialist → Brand Voice → Evaluation                │
└─────────────────────────────────────────────────────────────────┘
```

## Files Created/Modified

### New Files:

1. **`/api_wrapper.py`**
   - Bridges the multi-agent system with the UI
   - Handles user context creation from `user_profile.py`
   - Transforms workflow responses to UI format

2. **`/LD-ai-rag-nt-togglehealth/pages/api/chat-multiagent.ts`**
   - Next.js API route for the multi-agent system
   - Proxies requests to Python backend

3. **`/LD-ai-rag-nt-togglehealth/components/chatbot/ChatBotMultiAgent.tsx`**
   - New React component for multi-agent chatbot
   - Shows animated agent status updates
   - Displays agent flow and metrics

### Modified Files:

1. **`/LD-ai-rag-nt-togglehealth/backend/fastapi_wrapper.py`**
   - Added `/api/chat-multiagent` endpoint
   - Imports from `api_wrapper.py`

## Agent Status Updates

The UI shows real-time status updates during workflow execution:

1. **🔍 Analyzing your question...** - Triage Router
2. **📋 Reaching out to Policy Specialist...** - Policy Agent (with RAG)
3. **🏥 Reaching out to Provider Specialist...** - Provider Agent (with RAG)
4. **📅 Reaching out to Scheduler Specialist...** - Scheduler Agent
5. **✨ Putting an answer together...** - Brand Voice Agent

Status box **disappears** when the final answer is delivered.

## Metrics Display

After response delivery, users can expand metrics panel to see:

- **Agent Flow**: Visual representation of agents that ran
- **Query Type**: Classified intent (POLICY_QUESTION, PROVIDER_LOOKUP, etc.)
- **RAG Documents**: Number of documents retrieved per specialist
- **Evaluation Scores**: (Future) Accuracy and coherence from G-Eval judges

## Usage

### To use the new multi-agent chatbot:

1. **Start Python backend:**
   ```bash
   cd LD-ai-rag-nt-togglehealth/backend
   python fastapi_wrapper.py
   ```

2. **Start Next.js frontend:**
   ```bash
   cd LD-ai-rag-nt-togglehealth
   npm run dev
   ```

3. **Import the new chatbot component:**
   ```typescript
   import ChatBotMultiAgent from "@/components/chatbot/ChatBotMultiAgent";
   
   // In your page:
   <ChatBotMultiAgent />
   ```

### Example Usage in a Page:

```typescript
// pages/health-assistant.tsx
import ChatBotMultiAgent from "@/components/chatbot/ChatBotMultiAgent";

export default function HealthAssistant() {
  return (
    <div>
      <h1>Health Insurance Assistant</h1>
      <ChatBotMultiAgent />
    </div>
  );
}
```

## Configuration

### Environment Variables:

Add to `/LD-ai-rag-nt-togglehealth/.env`:
```bash
PYTHON_API_URL=http://localhost:8000
```

### LaunchDarkly AI Configs Required:

The multi-agent system requires these AI Configs in LaunchDarkly:

**Agents:**
- `triage_agent` - Routes queries
- `policy_agent` - Answers policy questions (needs `awskbid` custom param)
- `provider_agent` - Finds providers (needs `awskbid` custom param)
- `scheduler_agent` - Handles scheduling
- `brand_agent` - Applies brand voice

**Judges:**
- `ai-judge-accuracy` - Evaluates accuracy
- `ai-judge-coherence` - Evaluates coherence

## Testing

Test the integration:

```bash
# Test Python backend directly
curl -X POST http://localhost:8000/api/chat-multiagent \
  -H "Content-Type: application/json" \
  -d '{"aiConfigKey": "policy_multiagent", "userInput": "What is my copay?"}'

# Test via Next.js API
curl -X POST http://localhost:3000/api/chat-multiagent \
  -H "Content-Type: application/json" \
  -d '{"aiConfigKey": "policy_multiagent", "userInput": "What is my copay?"}'
```

## Troubleshooting

### "Multi-agent system not available" error:

**Cause**: `api_wrapper.py` not found or import failed

**Fix**:
1. Ensure `api_wrapper.py` is in project root
2. Check Python path in `fastapi_wrapper.py`
3. Restart Python backend

### Agent status not showing:

**Cause**: Response too fast or no `agentFlow` in response

**Fix**: Agent flow is simulated in UI based on `agentFlow` data from backend

### No metrics displayed:

**Cause**: Metrics not returned from backend

**Fix**: Check that `api_wrapper.py` is extracting metrics from workflow result

## Future Enhancements

1. **WebSocket support** for real-time agent status updates
2. **Evaluation metrics** displayed after judge runs
3. **RAG document preview** - show snippets of retrieved documents
4. **Agent confidence scores** from triage router
5. **Streaming responses** for faster perceived performance

## Comparison: Existing vs New Chatbot

| Feature | Existing ChatBot.tsx | New ChatBotMultiAgent.tsx |
|---------|---------------------|---------------------------|
| Backend | ToggleBank RAG | Multi-Agent System |
| Agents | Single AI call | Triage → Specialist → Brand Voice |
| Status Updates | Loading spinner only | Agent-by-agent progress |
| Metrics | Guardrail + Judge | Agent flow + Evaluation |
| RAG | Single KB | Multiple KBs (policy + provider) |
| Evaluation | LLM-as-judge (accuracy + toxicity) | G-Eval (accuracy + coherence) |
| Use Case | General banking/health | Specialized health insurance |

Both chatbots can coexist in the UI - use flags to toggle between them!

