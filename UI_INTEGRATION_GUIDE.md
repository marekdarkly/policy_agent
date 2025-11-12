# ToggleHealth Multi-Agent UI Integration Guide

## Overview

This guide explains how to integrate the multi-agent medical insurance support system into the existing ToggleHealth UI.

## Backend Setup ✅ COMPLETE

### New Endpoints Added

**1. `/api/chat-togglehealth`** - Main multi-agent endpoint
- Location: `LD-ai-rag-nt-togglehealth/backend/fastapi_wrapper.py` (lines 1532-1670)
- Returns: Response + agent_flow array for live status updates
- Flow: Triage → Specialist (+ RAG) → Brand Voice → G-Eval

**2. `/api/chat-metrics-togglehealth`** - G-Eval evaluation metrics
- Location: `LD-ai-rag-nt-togglehealth/backend/fastapi_wrapper.py` (lines 1739-1749)
- Returns: Accuracy & Coherence scores with reasoning

### Next.js API Routes Added

**1. `pages/api/chat-togglehealth.ts`** ✅ Created
- Proxies requests to Python backend

**2. `pages/api/chat-metrics-togglehealth.ts`** ✅ Created
- Fetches evaluation metrics

## Frontend Changes Needed

### 1. Update API Endpoint (Simple Change)

**File**: `components/chatbot/ChatBot.tsx`

**Line 138** - Change from:
```typescript
const response = await fetch("/api/chat", {
```

To:
```typescript
const response = await fetch("/api/chat-togglehealth", {
```

**Line 68** - Change metrics polling from:
```typescript
const response = await fetch(`/api/chat-metrics?request_id=${requestId}`);
```

To:
```typescript
const response = await fetch(`/api/chat-metrics-togglehealth?request_id=${requestId}`);
```

### 2. Add Agent Status State (New)

**File**: `components/chatbot/ChatBot.tsx`

**After line 63** (after `const [websocket, setWebsocket]...`), add:
```typescript
const [agentFlow, setAgentFlow] = useState<any[]>([]);
const [showAgentStatus, setShowAgentStatus] = useState(false);
```

### 3. Extract Agent Flow from Response (Modify)

**File**: `components/chatbot/ChatBot.tsx`

**In `applyChatBotNewMessage` function (around line 222-252)**, add after storing metrics:

```typescript
// Extract and store agent flow for status display
if (chatBotResponse.metrics?.agent_flow) {
	setAgentFlow(chatBotResponse.metrics.agent_flow);
	setShowAgentStatus(true);
	
	// Hide agent status after 3 seconds when assistant message appears
	setTimeout(() => {
		setShowAgentStatus(false);
	}, 3000);
}
```

### 4. Add Agent Status Display Component (New)

**File**: `components/chatbot/ChatBot.tsx`

**Before the messages map (around line 521)**, add:

```typescript
{/* Agent Status Indicator */}
{showAgentStatus && agentFlow.length > 0 && (
	<div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900 rounded-lg border border-blue-200 dark:border-blue-700">
		<div className="text-sm font-semibold text-blue-800 dark:text-blue-200 mb-2">
			🤖 Multi-Agent System
		</div>
		<div className="space-y-1">
			{agentFlow.map((step, idx) => (
				<div key={idx} className="flex items-center text-xs text-blue-700 dark:text-blue-300">
					<span className="mr-2">
						{step.status === 'completed' ? '✅' : '🔄'}
					</span>
					<span>{step.label}</span>
					{step.details?.rag_documents > 0 && (
						<span className="ml-2 text-blue-500">
							({step.details.rag_documents} docs retrieved)
						</span>
					)}
				</div>
			))}
		</div>
	</div>
)}
```

### 5. Add Evaluation Metrics Display (Enhance Existing)

**File**: `components/chatbot/ChatBot.tsx`

**In the metrics display section (after line 582)**, add **before** the existing metrics:

```typescript
{/* G-Eval Evaluation Metrics */}
{lastMetrics.factual_accuracy_score !== undefined && (
	<>
		<div className="border-b pb-2 mb-2">
			<div className="text-xs font-bold text-gray-700 mb-1">
				🧪 G-Eval Judge Results
			</div>
		</div>
		
		{/* Accuracy */}
		<div className="mb-3">
			<div className="flex justify-between items-center">
				<span className="font-semibold">Global System Accuracy:</span>
				<span className={
					lastMetrics.accuracy_passed ? 'text-green-600 font-bold' : 'text-red-600 font-bold'
				}>
					{(lastMetrics.factual_accuracy_score * 100).toFixed(0)}%
					{lastMetrics.accuracy_passed ? ' ✅' : ' ❌'}
				</span>
			</div>
			{lastMetrics.accuracy_reasoning && (
				<details className="mt-1 cursor-pointer">
					<summary className="text-xs text-blue-600 hover:text-blue-800">
						View Reasoning
					</summary>
					<div className="mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded">
						{lastMetrics.accuracy_reasoning}
					</div>
					{lastMetrics.accuracy_issues && lastMetrics.accuracy_issues.length > 0 && (
						<div className="mt-1">
							<div className="text-xs font-semibold text-red-600">Issues Found:</div>
							<ul className="list-disc ml-4 text-xs text-red-500">
								{lastMetrics.accuracy_issues.map((issue: string, idx: number) => (
									<li key={idx}>{issue}</li>
								))}
							</ul>
						</div>
					)}
				</details>
			)}
		</div>
		
		{/* Coherence */}
		<div className="mb-3">
			<div className="flex justify-between items-center">
				<span className="font-semibold">Response Coherence:</span>
				<span className={
					lastMetrics.coherence_passed ? 'text-green-600 font-bold' : 'text-orange-600 font-bold'
				}>
					{(lastMetrics.coherence_score * 100).toFixed(0)}%
					{lastMetrics.coherence_passed ? ' ✅' : ' ⚠️'}
				</span>
			</div>
			{lastMetrics.coherence_reasoning && (
				<details className="mt-1 cursor-pointer">
					<summary className="text-xs text-blue-600 hover:text-blue-800">
						View Reasoning
					</summary>
					<div className="mt-1 text-xs text-gray-600 bg-gray-50 p-2 rounded">
						{lastMetrics.coherence_reasoning}
					</div>
				</details>
			)}
		</div>
		
		<div className="border-t pt-2 mt-2">
			<div className="text-xs text-gray-500">
				Judge Model: {lastMetrics.judge_model || 'G-Eval (Claude Sonnet 4)'}
			</div>
		</div>
	</>
)}
```

## Testing

### 1. Start Backend

```bash
cd /Users/marek/Documents/policy_agent/LD-ai-rag-nt-togglehealth/backend
python fastapi_wrapper.py
```

Expected output:
```
INFO:     Started server process
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. Test Multi-Agent Endpoint

```bash
curl -X POST http://localhost:8000/api/chat-togglehealth \
  -H "Content-Type: application/json" \
  -d '{"aiConfigKey": "toggle-rag", "userInput": "What is my copay?"}'
```

Expected response includes:
- `response`: Final answer
- `metrics.agent_flow`: Array of agent steps
- `requestId`: For fetching eval metrics later
- `pendingMetrics`: true (evaluation running in background)

### 3. Test Metrics Endpoint

```bash
curl http://localhost:8000/api/chat-metrics-togglehealth?request_id=<requestId>
```

Expected response (after ~5-10 seconds):
```json
{
  "status": "ready",
  "metrics": {
    "factual_accuracy_score": 0.85,
    "accuracy_passed": true,
    "accuracy_reasoning": "...",
    "coherence_score": 0.90,
    "coherence_passed": true,
    "coherence_reasoning": "..."
  }
}
```

### 4. Start Frontend

```bash
cd /Users/marek/Documents/policy_agent/LD-ai-rag-nt-togglehealth
npm run dev
```

### 5. Test in Browser

1. Open http://localhost:3000
2. Click chatbot icon
3. Ask: "What's my copay for seeing a specialist?"
4. **Observe**:
   - Blue status box appears showing agent progression
   - "Analyzing your question..." → "Checking your policy details..." → "Putting together your answer..."
   - Box disappears after answer is delivered
   - Metrics show G-Eval scores with reasoning

## Agent Flow Labels

The backend provides these labels for the UI:

| Agent | Label | When Shown |
|-------|-------|------------|
| Triage | "Analyzing your question..." | Always |
| Policy Specialist | "Checking your policy details..." | For policy questions |
| Provider Specialist | "Finding providers in your network..." | For provider lookups |
| Scheduler Specialist | "Scheduling your request..." | For callbacks/scheduling |
| Brand Voice | "Putting together your answer..." | Always (final step) |

## Troubleshooting

### Backend Import Error

**Error**: `ModuleNotFoundError: No module named 'src'`

**Fix**:
```bash
# Ensure the parent policy_agent directory is in the path
cd /Users/marek/Documents/policy_agent
export PYTHONPATH=$PYTHONPATH:/Users/marek/Documents/policy_agent
```

Or set in the backend code (already done in fastapi_wrapper.py line 1518).

### Evaluation Not Running

**Symptom**: `pendingMetrics` is false or metrics never arrive

**Check**:
1. Are RAG documents being retrieved? (Check backend logs)
2. Is LaunchDarkly SDK initialized? (Check `LAUNCHDARKLY_SDK_KEY` in .env)
3. Do judge configs exist? (`ai-judge-accuracy`, `ai-judge-coherence`)

### Agent Status Not Showing

**Check**:
1. Is `metrics.agent_flow` in the response? (Check browser devtools)
2. Is `showAgentStatus` state being set? (Add console.log)
3. Is CSS conflicting with the status box? (Check z-index)

## Architecture Flow

```
User Input
    ↓
Next.js Frontend (ChatBot.tsx)
    ↓
/api/chat-togglehealth (Next.js API Route)
    ↓
/api/chat-togglehealth (FastAPI Backend)
    ↓
run_workflow() (Your Multi-Agent System)
    ├─ Triage Router
    ├─ Specialist (Policy/Provider/Scheduler) + RAG
    └─ Brand Voice
    ↓
Response + agent_flow
    ↓
[Background] G-Eval Judge
    ├─ Accuracy (vs RAG docs)
    └─ Coherence (response quality)
    ↓
/api/chat-metrics-togglehealth
    ↓
Display in UI
```

## Summary

**Backend**: ✅ Complete
- New endpoint handles multi-agent workflow
- Returns agent flow for live UI updates
- G-Eval runs in background
- Metrics endpoint serves evaluation results

**Frontend**: 📝 Needs 5 changes (see above)
- Change API endpoint URLs (2 places)
- Add agent flow state
- Add agent status display component
- Enhance metrics display with G-Eval scores

**Estimated Time**: 30 minutes for frontend changes

All the heavy lifting is done - the multi-agent system, RAG, evaluation, and API integration are working. The UI just needs to display the information!

