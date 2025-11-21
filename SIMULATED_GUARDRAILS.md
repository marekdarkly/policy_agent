# Simulated Guardrails for Demo

This system uses **simulated guardrails** instead of AWS Bedrock Guardrails for complete demo control.

## How It Works

### Enable Simulated Guardrail Block

In your LaunchDarkly `brand_agent` AI Config, add this custom parameter:

```json
{
  "simulate_guardrail_block": true
}
```

**That's it!** When this parameter is `true`, the system will:
1. ✅ Let the model generate a full response
2. 🛡️ Simulate a guardrail intervention (block the response)
3. 🔄 Trigger self-healing (fallback to safe default)
4. ✅ Serve the safe response to the customer

### Disable Simulated Guardrail

Set the parameter to `false` or remove it entirely:

```json
{
  "simulate_guardrail_block": false
}
```

Or just omit it from custom parameters completely.

---

## Demo Flow

### Scenario 1: Guardrail ON (Bad Variation)

**Setup:**
- Variation: `dangerous-prompt` (bad prompt that generates problematic content)
- Custom params: `{"simulate_guardrail_block": true}`
- UI Toggle: 🛡️ ON (green)

**Expected Terminal Output:**
```
────────────────────────────────────────────────────────────────────────────────
🔍 BRAND VOICE AGENT: Crafting response
   📌 Variation: dangerous-prompt
   🔧 Custom params: ['simulate_guardrail_block']
   🛡️  Simulated Guardrail: ENABLED (will block response)
────────────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────────────
🛡️  SIMULATED GUARDRAIL INTERVENED
   ⚠️  Response blocked by simulated guardrail
   📝 Original Response (first 200 chars):
      'I recommend taking 800mg ibuprofen every 4 hours for chest pain. You can also try...'
   💡 Simulated Violation: Inappropriate content policy
   🎭 This is a DEMO - not a real AWS Bedrock guardrail
────────────────────────────────────────────────────────────────────────────────

================================================================================
🔄 SELF-HEALING: Simulated guardrail blocked response - falling back to safe default
================================================================================
   ❌ Blocked content (first 150 chars):
      'I recommend taking 800mg ibuprofen every 4 hours for chest pain. You can also try...'
   🎯 Goal: Generate safe response using hardcoded default prompt (no guardrail)
================================================================================

   🔄 Using hardcoded safe default (guaranteed no guardrail)
   ✅ Fallback succeeded - serving safe response to customer
   📝 Generated (first 150 chars):
      'Hi Marek, Thanks for reaching out! For concerns about chest pain, I strongly recommend visiting an emergency room immediately...'
   ⏱️  Fallback duration: 2134ms
================================================================================
```

**Customer sees:** Safe, helpful response redirecting to emergency services.

---

### Scenario 2: Guardrail OFF (Bad Variation)

**Setup:**
- Variation: `dangerous-prompt` (same bad prompt)
- Custom params: `{"simulate_guardrail_block": true}`
- UI Toggle: 🛡️ OFF (red)

**Expected Terminal Output:**
```
────────────────────────────────────────────────────────────────────────────────
🔍 BRAND VOICE AGENT: Crafting response
   📌 Variation: dangerous-prompt
   🔧 Custom params: ['simulate_guardrail_block']
   🛡️  Simulated Guardrail: DISABLED BY USER
────────────────────────────────────────────────────────────────────────────────

💰 Brand agent cost: 0.28¢ ($0.002800) [in=2100, out=450, model=haiku-4-5]
```

**Customer sees:** The dangerous/inappropriate response (demonstrating the risk).

---

### Scenario 3: Good Variation (No Guardrail Needed)

**Setup:**
- Variation: `safe-prompt` (good prompt)
- Custom params: `{"simulate_guardrail_block": false}` or omitted
- UI Toggle: Either ON or OFF

**Expected Terminal Output:**
```
────────────────────────────────────────────────────────────────────────────────
🔍 BRAND VOICE AGENT: Crafting response
   📌 Variation: safe-prompt
────────────────────────────────────────────────────────────────────────────────

💰 Brand agent cost: 0.25¢ ($0.002500) [in=2000, out=400, model=haiku-4-5]
```

**Customer sees:** Normal, safe response.

---

## UI Toggle Button

The 🛡️ button in the chat interface controls whether the simulated guardrail is active:

- **🛡️ ON** (green): Guardrail enabled - blocks will trigger self-healing
- **🛡️ OFF** (red): Guardrail disabled - bad content passes through

This allows you to demonstrate:
1. **With guardrails**: Safe, self-healing behavior
2. **Without guardrails**: Show the risk of problematic AI output

---

## Demo Script

### Part 1: Show the Problem (Guardrail OFF)

1. Toggle guardrail to 🛡️ OFF (red)
2. Make sure LaunchDarkly is serving the "bad" variation
3. Ask an innocent question: `"What should I do about chest pain?"`
4. Model generates dangerous medical advice
5. **Customer receives inappropriate response** 😱

**Say to audience:**
> "Without guardrails, even a well-intentioned prompt variation can produce dangerous outputs. This is the risk we're managing."

---

### Part 2: Show the Solution (Guardrail ON)

1. Toggle guardrail to 🛡️ ON (green)
2. Same variation, same question
3. Terminal shows:
   - Model generates bad response
   - Guardrail catches it
   - Self-healing activates
   - Safe response generated
4. **Customer receives safe response** ✅

**Say to audience:**
> "With guardrails and self-healing, the system automatically detects problematic outputs and falls back to a safe default. The customer never sees the bad content."

---

### Part 3: Show LaunchDarkly Control

1. Switch to a "safe" variation in LaunchDarkly
2. Same question with guardrail ON
3. No intervention needed - response is good from the start
4. **Customer receives normal response** ✅

**Say to audience:**
> "Of course, the goal is to have good prompts. But guardrails provide a safety net when experiments go wrong, and LaunchDarkly lets us roll back instantly."

---

## Custom Parameters in LaunchDarkly

### For "Bad" Variations
```json
{
  "simulate_guardrail_block": true
}
```

### For "Safe" Variations
```json
{
  "simulate_guardrail_block": false
}
```

Or just omit the parameter entirely.

---

## Advantages of Simulated Guardrails

1. **Full Control**: You decide exactly when blocks happen
2. **No AWS Setup**: No need to configure Bedrock Guardrails
3. **No Cost**: Simulated guardrails are free
4. **Reliable Demo**: Blocks happen consistently (not dependent on AWS)
5. **Clear Logging**: See exactly what was blocked and why
6. **LaunchDarkly Control**: Enable/disable per variation via custom params

---

## Technical Details

### What Happens Under the Hood

1. **Model generates response** (always completes)
2. **Check custom parameter**: `simulate_guardrail_block`
3. **If true + UI toggle ON**:
   - Log the original response
   - Set `guardrail_action = "GUARDRAIL_INTERVENED"`
   - Trigger self-healing
   - Generate safe response with default prompt
4. **If false or UI toggle OFF**:
   - Use original response
   - No intervention

### Where the Code Lives

- **Simulation logic**: `src/agents/brand_voice_agent.py` (line ~193)
- **Self-healing**: `src/agents/brand_voice_agent.py` (line ~230)
- **UI toggle**: `ui/frontend/src/App.tsx` (line ~64)
- **Backend handling**: `ui/backend/server.py` (line ~280)

---

## Quick Start

1. Create two variations in LaunchDarkly for `brand_agent`:
   - **Variation A** (safe): Normal, helpful prompt
   - **Variation B** (unsafe): Prompt that generates problematic content

2. Add custom parameter to Variation B:
   ```json
   {"simulate_guardrail_block": true}
   ```

3. Target yourself to Variation B

4. Toggle 🛡️ OFF → See bad content
5. Toggle 🛡️ ON → See self-healing

**Perfect for demos!** 🎯

