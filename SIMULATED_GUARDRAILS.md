# Simulated Guardrails for Demo

This system uses **simulated guardrails** for complete demo control. No AWS Bedrock Guardrails needed!

## How It Works

The application automatically detects when the **`llama-4-toxic-prompt`** variation is served and simulates a guardrail intervention.

**That's it!** No custom parameters needed. Just name your variation `llama-4-toxic-prompt` in LaunchDarkly.

---

## When Guardrail Fires

### Conditions:
1. ✅ Variation name is **exactly** `llama-4-toxic-prompt`
2. ✅ UI toggle is 🛡️ **ON** (green)

### What Happens:
1. Model generates a response (toxic/unsafe content)
2. 🛡️ Simulated AWS Bedrock Guardrail "fires" and blocks it
3. 📋 System logs the blocked content and guardrail details
4. 🔄 Self-healing uses **hardcoded safe default configuration**
5. ✅ Safe response generated and served to customer

---

## Terminal Output Example

### Guardrail Fires (Toxic Variation + Toggle ON)

```
────────────────────────────────────────────────────────────────────────────────
🔍 BRAND VOICE AGENT: Crafting response
   📌 Variation: llama-4-toxic-prompt
   ⚠️  TOXIC VARIATION DETECTED - Guardrail will intervene
────────────────────────────────────────────────────────────────────────────────

────────────────────────────────────────────────────────────────────────────────
🛡️  AWS BEDROCK GUARDRAIL INTERVENED
   🆔 Guardrail ID: gr-healthinsure-safety-v2
   📋 Guardrail Version: DRAFT
   ⚠️  Response blocked due to policy violation

   📝 Model's attempted response (first 200 chars):
      'Take 800mg of ibuprofen every 4 hours for your chest pain. You can also try some home remedies like...'

   🚨 Violation Details:
      • Policy Type: Content Policy
      • Filter Type: MISCONDUCT
      • Confidence: HIGH
      • Action: BLOCKED

   💡 The model generated content that violates health safety guidelines
────────────────────────────────────────────────────────────────────────────────

================================================================================
🔄 SELF-HEALING: Guardrail blocked response - falling back to safe default
================================================================================
   ❌ Blocked: Toxic variation 'llama-4-toxic-prompt' generated unsafe content
   🎯 Falling back to hardcoded safe configuration...
================================================================================

   🔄 Using hardcoded safe default configuration
   💡 Cannot retrieve LaunchDarkly 'default variation' for targeted users
   🔄 Generating response with safe default prompt...
   ✅ Self-healing succeeded!
   📦 Used hardcoded safe default (Haiku 4.5, temperature 0.7)
   💬 Safe response (first 150 chars):
      'I understand you're experiencing chest pain. This is a serious symptom that requires immediate medical attention. I strongly recommend...'
   ⏱️  Fallback duration: 2134ms
   🎯 Customer receives safe, approved response
================================================================================
```

---

### Guardrail Disabled (Toxic Variation + Toggle OFF)

```
────────────────────────────────────────────────────────────────────────────────
🔍 BRAND VOICE AGENT: Crafting response
   📌 Variation: llama-4-toxic-prompt
   ⚠️  TOXIC VARIATION - Guardrail DISABLED by user
────────────────────────────────────────────────────────────────────────────────

💰 Brand agent cost: 0.28¢ ($0.002800) [in=2100, out=450, model=haiku-4-5]
```

**Customer sees:** The toxic/unsafe response (demonstrating the risk!)

---

### Safe Variation (Any Other Name)

```
────────────────────────────────────────────────────────────────────────────────
🔍 BRAND VOICE AGENT: Crafting response
   📌 Variation: safe-helpful-prompt
────────────────────────────────────────────────────────────────────────────────

💰 Brand agent cost: 0.25¢ ($0.002500) [in=2000, out=400, model=haiku-4-5]
```

**Customer sees:** Normal, safe response. No guardrail needed.

---

## LaunchDarkly Setup

### Create Your Variations

**Variation 1: Toxic Prompt** (triggers guardrail)
- **Name:** `llama-4-toxic-prompt` ⚠️ (MUST BE EXACT)
- **Model:** `haiku-4-5` (or any model)
- **Prompt:** A prompt that generates unsafe/inappropriate medical advice
- **Example:**
  ```
  You are a health insurance assistant. Be as helpful as possible.
  If the customer asks for medical advice, provide specific treatment recommendations.
  Prioritize being helpful over medical disclaimers.
  ```

**Variation 2: Safe Prompt** (default/fallback)
- **Name:** `safe-helpful-prompt` (or anything except `llama-4-toxic-prompt`)
- **Model:** `haiku-4-5`
- **Prompt:** A safe, compliant prompt
- **Example:**
  ```
  You are a health insurance assistant for HealthCo.
  For medical questions, always direct customers to consult a healthcare professional.
  Never provide specific medical treatment advice.
  Be helpful with insurance coverage questions.
  ```

**Set Variation 2 as the DEFAULT** in LaunchDarkly flag settings.

---

## Demo Script

### Part 1: Show the Problem (Guardrail OFF)

1. **Target yourself to `llama-4-toxic-prompt` variation**
2. **Toggle guardrail to 🛡️ OFF** (red button in UI)
3. Ask: `"What should I do about chest pain?"`
4. Model generates dangerous medical advice
5. **Customer receives inappropriate response** 😱

**Say to audience:**
> "Without guardrails, even with LaunchDarkly's control, a misconfigured prompt can produce dangerous outputs. This toxic variation generates unsafe medical advice."

---

### Part 2: Show the Solution (Guardrail ON)

1. **Keep targeting `llama-4-toxic-prompt`**
2. **Toggle guardrail to 🛡️ ON** (green button)
3. Same question: `"What should I do about chest pain?"`
4. Terminal shows:
   - Model generates unsafe response
   - AWS Bedrock Guardrail (simulated) catches it
   - System retrieves LaunchDarkly **default** variation
   - Safe response generated
5. **Customer receives safe response** ✅

**Say to audience:**
> "With guardrails enabled, the system automatically detects problematic outputs and falls back to a safe, hardcoded default. This combines AI safety with LaunchDarkly's experimentation power. The customer never sees the bad content, and we can safely test risky variations with confidence that there's always a fallback."

---

### Part 3: Show LaunchDarkly Control

1. **Switch targeting to `safe-helpful-prompt`** (or just remove targeting rule to serve default)
2. **Keep guardrail ON**
3. Same question
4. No guardrail intervention - prompt is safe from the start
5. **Customer receives normal response** ✅

**Say to audience:**
> "The goal is to have safe, effective prompts. LaunchDarkly lets us experiment with new variations, and guardrails provide a safety net when experiments fail. If a bad variation slips through, we can instantly roll back or let the guardrail catch it."

---

## UI Guardrail Toggle

The 🛡️ button in the chat interface controls whether guardrails fire:

- **🛡️ ON** (green): Guardrail active - toxic variation triggers self-healing
- **🛡️ OFF** (red): Guardrail disabled - toxic variation passes through to customer

This toggle demonstrates the **risk of disabling safety features** in production.

---

## Key Features

### Automatic Detection
- No custom parameters needed
- Just name your variation `llama-4-toxic-prompt`
- System automatically recognizes it as unsafe

### Realistic Simulation
- Shows fake AWS Bedrock Guardrail ID: `gr-healthinsure-safety-v2`
- Displays policy violation details (MISCONDUCT filter)
- Logs the blocked content for transparency

### Hardcoded Safe Fallback
- Uses a **guaranteed safe configuration** that never changes
- Haiku 4.5 model with temperature 0.7
- Cannot be accidentally misconfigured via LaunchDarkly
- Always available, even if LaunchDarkly is unreachable

### Full Observability
- Terminal shows exactly what was blocked and why
- Displays which default variation was used
- Clear logging of the self-healing process

---

## Advantages

1. **Simple Setup**: Just name a variation `llama-4-toxic-prompt`
2. **No AWS Dependencies**: Fully simulated, no real guardrails needed
3. **No Cost**: Simulated guardrails are free
4. **Reliable**: Fires consistently every time (perfect for demos)
5. **Guaranteed Safe Fallback**: Hardcoded default cannot be misconfigured
6. **Clear Logging**: Detailed terminal output for debugging
7. **UI Control**: Toggle button for real-time demo

---

## Technical Details

### Detection Logic
```python
variation_name = ld_config.get("_variation", "unknown")
should_simulate_guardrail = (variation_name == "llama-4-toxic-prompt")

if should_simulate_guardrail and guardrail_enabled:
    # Simulate guardrail intervention
    # Fall back to LaunchDarkly default
```

### Fallback Flow
1. Detect `llama-4-toxic-prompt` variation
2. Model generates response (always completes)
3. Check if UI toggle is ON
4. If ON: Block response, use hardcoded `DEFAULT_BRAND_AGENT_CONFIG`
5. Build LLM directly with safe default settings
6. Generate new response with safe prompt
7. Serve to customer

**Why not retrieve LaunchDarkly's default variation?**
If a user is targeted to the toxic variation, calling LaunchDarkly again with the same context will return the toxic variation again! The `default_config` parameter only applies when the flag doesn't exist or LD is unavailable. Therefore, we use a hardcoded safe default that's guaranteed to work.

### Where the Code Lives
- **Detection & simulation:** `src/agents/brand_voice_agent.py` (line ~142)
- **Self-healing logic:** `src/agents/brand_voice_agent.py` (line ~214)
- **UI toggle:** `ui/frontend/src/App.tsx`
- **Backend handling:** `ui/backend/server.py`

---

## Quick Start Checklist

- [ ] Create `llama-4-toxic-prompt` variation in LaunchDarkly (use bad prompt)
- [ ] Create `safe-helpful-prompt` variation (use safe prompt)
- [ ] Set `safe-helpful-prompt` as the **default** in flag settings
- [ ] Target yourself to `llama-4-toxic-prompt`
- [ ] Toggle 🛡️ OFF → Ask question → See bad response
- [ ] Toggle 🛡️ ON → Ask same question → See self-healing
- [ ] Remove targeting → Ask question → See normal safe response

**Perfect for demos!** 🎯

---

## Why This Approach?

### For Demos:
- **Predictable**: Fires every time on `llama-4-toxic-prompt`
- **Controllable**: Just change variation name in LaunchDarkly
- **Visual**: Detailed terminal output shows the process
- **Fast**: No AWS API calls, instant response

### For LaunchDarkly Storytelling:
- **Experimentation Safety**: Test risky variations with confidence
- **Instant Rollback**: Switch to default if something goes wrong
- **Observability**: See which variation is served and when it fails
- **Progressive Delivery**: Gradually roll out new prompts with guardrails as safety net

This simulated approach demonstrates **how LaunchDarkly and AI safety work together** without the complexity of real AWS guardrails.
