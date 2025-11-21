# Simulated Guardrails with LaunchDarkly Context Override

This system uses **simulated guardrails** with **intelligent LaunchDarkly fallback targeting** for complete demo control.

## How It Works

The application automatically detects when the **`llama-4-toxic-prompt`** variation is served and simulates a guardrail intervention. When blocked, it **modifies the user context** to include `is_fallback: true` and re-evaluates the same AI Config, triggering LaunchDarkly to serve a safe variation.

**Key Innovation:** Uses LaunchDarkly's targeting rules to provide intelligent fallback, not hardcoded defaults!

---

## LaunchDarkly Setup

### **Flag: `brand_agent`**

#### **Variations:**
1. **`llama-4-toxic-prompt`** - Risky experimental prompt (triggers guardrail)
2. **`safe-helpful-prompt`** - Approved safe prompt (fallback)
3. **`claude-empathetic-prompt`** - Another safe variation (optional)

#### **Targeting Rules** (IMPORTANT: Order matters!)

```
┌─────────────────────────────────────────────────────────────┐
│ Rule 1: FALLBACK MODE (MUST BE FIRST!)                     │
├─────────────────────────────────────────────────────────────┤
│ IF is_fallback is true                                      │
│ THEN serve: safe-helpful-prompt                            │
│                                                             │
│ Description: When guardrail intervenes, always serve safe  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Rule 2: EXPERIMENTAL TESTING                                │
├─────────────────────────────────────────────────────────────┤
│ IF email is "your-email@togglehealth.com"                  │
│ THEN serve: llama-4-toxic-prompt                           │
│                                                             │
│ Description: Test toxic variation with guardrails enabled  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Rule 3: DEFAULT                                             │
├─────────────────────────────────────────────────────────────┤
│ ELSE serve: safe-helpful-prompt                            │
└─────────────────────────────────────────────────────────────┘
```

**⚠️ CRITICAL**: Rule 1 (fallback) **MUST** be first in the targeting order! This ensures that any request with `is_fallback: true` gets the safe variation, regardless of other targeting rules.

---

## When Guardrail Fires

### Conditions:
1. ✅ Variation name is **exactly** `llama-4-toxic-prompt`
2. ✅ UI toggle is 🛡️ **ON** (green)

### What Happens:
1. Model generates a response (toxic/unsafe content)
2. 🛡️ Simulated AWS Bedrock Guardrail "fires" and blocks it
3. 📋 System logs the blocked content and guardrail details
4. 🔄 System modifies user context: adds `is_fallback: true`
5. 📡 Re-evaluates same AI Config with modified context
6. ✅ LaunchDarkly returns safe variation (via Rule 1)
7. ✅ Safe response generated and served to customer

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
      'For chest pain, take 800mg ibuprofen every 4 hours and rest...'

   🚨 Violation Details:
      • Policy Type: Content Policy
      • Filter Type: MISCONDUCT
      • Confidence: HIGH
      • Action: BLOCKED

   💡 The model generated content that violates health safety guidelines
────────────────────────────────────────────────────────────────────────────────

================================================================================
🔄 SELF-HEALING: Guardrail intervention detected
================================================================================
   ❌ Blocked: Toxic variation 'llama-4-toxic-prompt' violated safety policy
   🎯 Strategy: Modify user context to trigger fallback targeting
================================================================================

   📍 Strategy: LaunchDarkly Context Attribute Override
   🔧 Modified context attributes:
      • is_fallback: True
      • fallback_reason: guardrail_intervention
      • blocked_variation: llama-4-toxic-prompt

   📡 Re-evaluating AI Config with fallback context...
   ✅ LaunchDarkly returned variation: 'safe-helpful-prompt'
   🛡️  Verified: Safe variation (not toxic)

   🔄 Generating response with fallback variation...
   ✅ Self-healing succeeded!
   📦 Used LaunchDarkly variation: 'safe-helpful-prompt'
   💬 Safe response (first 150 chars):
      'I understand you're experiencing chest pain. This is a serious symptom that requires immediate medical attention. I strongly recommend...'
   ⏱️  Fallback duration: 1847ms
   🎯 Customer receives safe response via LaunchDarkly fallback targeting
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

## Demo Script

### Part 1: Show the LaunchDarkly Targeting Rules

**Open LaunchDarkly UI:**

> "Let me show you our `brand_agent` AI Config targeting rules. See Rule 1? That's our fallback rule. If the context has `is_fallback: true`, we ALWAYS serve the safe variation, no matter what other rules match.
>
> "Rule 2 targets me to the experimental toxic variation. This lets us safely test risky prompts in production because we know there's a safety net."

---

### Part 2: Show the Problem (Guardrail OFF)

1. **Target yourself to `llama-4-toxic-prompt`** (via email/name rule)
2. **Toggle guardrail to 🛡️ OFF** (red button in UI)
3. Ask: `"What should I do about chest pain?"`
4. Model generates dangerous medical advice
5. **Customer receives inappropriate response** 😱

**Say to audience:**
> "Without guardrails, this toxic variation generates dangerous medical advice. The model is just trying to be helpful, but it's giving advice that could harm someone."

---

### Part 3: Show the Solution (Guardrail ON)

1. **Keep targeting `llama-4-toxic-prompt`**
2. **Toggle guardrail to 🛡️ ON** (green button)
3. Same question: `"What should I do about chest pain?"`
4. **Watch the terminal output carefully:**
   - Model generates unsafe response
   - AWS Bedrock Guardrail (simulated) catches it
   - System adds `is_fallback: true` to context
   - Re-evaluates LaunchDarkly with modified context
   - LaunchDarkly returns safe variation
   - Safe response generated
5. **Customer receives safe response** ✅

**Say to audience:**
> "Now watch what happens with guardrails enabled. The model generates the same dangerous content, but the guardrail catches it. Instead of serving it to the customer, the system automatically modifies the user context to include `is_fallback: true`.
>
> "It then asks LaunchDarkly again: 'What should I serve for this user?' LaunchDarkly looks at the context, sees the fallback flag, and Rule 1 kicks in—serving the safe variation.
>
> "This is **LaunchDarkly-native AI safety**. We're not hardcoding fallbacks; we're using LaunchDarkly's intelligent targeting to make real-time decisions about which variation to serve based on the current safety context."

---

### Part 4: Show LaunchDarkly Analytics

**Open LaunchDarkly Analytics:**

> "And here's the best part—we can track this in LaunchDarkly. Look at the impressions for the safe variation. Some have `is_fallback: false` (normal usage) and some have `is_fallback: true` (guardrail interventions).
>
> "We can create custom metrics to track exactly how many times self-healing was triggered, which users hit it, and even set up alerts if fallback usage spikes."

---

### Part 5: Show Normal Operation

1. **Switch targeting to `safe-helpful-prompt`** (or remove targeting rule)
2. **Keep guardrail ON**
3. Same question
4. No guardrail intervention - prompt is safe from the start
5. **Customer receives normal response** ✅

**Say to audience:**
> "Of course, the goal is to have safe prompts from the start. LaunchDarkly lets us experiment with new variations, and guardrails provide a safety net when experiments go wrong. We can progressively deliver new prompts with confidence."

---

## LaunchDarkly Analytics Benefits

With this approach, you get **rich observability**:

### **Track Fallback Usage:**
```
Events where:
  flag = "brand_agent"
  AND context.is_fallback = true

→ Shows how many times self-healing was triggered
```

### **Custom Metrics:**
```
Name: Guardrail Interventions
Event: brand_agent evaluation
Filter: context.is_fallback is true
Unit: Count

→ Create alerts if fallbacks spike
```

### **Experimentation:**
You can even A/B test different fallback strategies:
- Variation A: Haiku model with safe prompt
- Variation B: Sonnet model with empathetic prompt

---

## Multi-Layer Fallback Strategy

The system implements **defense in depth**:

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 1: LaunchDarkly Context Override (Primary)           │
├─────────────────────────────────────────────────────────────┤
│ Modify context with is_fallback: true                      │
│ Re-evaluate same AI Config                                  │
│ LaunchDarkly returns safe variation via targeting rules     │
│                                                             │
│ ✅ Best case: LaunchDarkly-native fallback                 │
└─────────────────────────────────────────────────────────────┘
                              ↓ (if fails)
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Hardcoded Safe Default (Last Resort)              │
├─────────────────────────────────────────────────────────────┤
│ Use DEFAULT_BRAND_AGENT_CONFIG directly                     │
│ Build LLM manually with safe settings                      │
│                                                             │
│ ✅ Failsafe: Works even if LaunchDarkly is down            │
└─────────────────────────────────────────────────────────────┘
                              ↓ (if fails)
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Generic Safe Message (Ultimate Fallback)          │
├─────────────────────────────────────────────────────────────┤
│ Static error message                                        │
│ "Please contact support..."                                 │
│                                                             │
│ ✅ Always works: No external dependencies                   │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Features

### **LaunchDarkly-Native**
- Uses targeting rules, not hardcoded logic
- Change fallback variation in UI without code changes
- Can experiment with different fallback strategies

### **Observable**
- Track normal vs fallback impressions in LaunchDarkly
- See which users triggered self-healing
- Create custom metrics for guardrail interventions
- Set up alerts for anomalies

### **Testable**
- Easy to verify fallback targeting in LaunchDarkly UI
- Can test with different context attributes
- Preview targeting results before going live

### **Flexible**
- Update fallback variation without deploying code
- A/B test different fallback approaches
- Target different fallbacks to different user segments

### **Reliable**
- Multi-layer fallback strategy
- Hardcoded default if LaunchDarkly unavailable
- Generic message if all else fails

---

## Technical Details

### **Modified Context Structure**

```python
# Original context
{
  "key": "user-123",
  "email": "marek@togglehealth.com",
  "name": "Marek",
  "tier": "gold"
}

# Modified context (when guardrail fires)
{
  "key": "user-123",
  "email": "marek@togglehealth.com",
  "name": "Marek",
  "tier": "gold",
  "is_fallback": True,                        # NEW: Triggers fallback rule
  "fallback_reason": "guardrail_intervention", # Why we're in fallback mode
  "blocked_variation": "llama-4-toxic-prompt", # Which variation was blocked
  "original_request_id": "req-abc123"          # Request tracking
}
```

### **Fallback Flow**

```
1. User request → LaunchDarkly evaluation
   └─> Context: {email: "marek@...", tier: "gold"}
   └─> Rule 2 matches → Serves: llama-4-toxic-prompt

2. Model generates response
   └─> Output: "Take 800mg ibuprofen..."
   └─> Guardrail check: MISCONDUCT detected → BLOCKED

3. Self-healing activates
   └─> Modify context: Add is_fallback: True
   └─> Re-evaluate LaunchDarkly with new context

4. LaunchDarkly evaluation (second time)
   └─> Context: {email: "marek@...", tier: "gold", is_fallback: True}
   └─> Rule 1 matches FIRST → Serves: safe-helpful-prompt
   
5. Model generates safe response
   └─> Output: "Chest pain requires immediate medical attention..."
   └─> No guardrail needed → Serve to customer
```

### **Where the Code Lives**
- **Detection & simulation:** `src/agents/brand_voice_agent.py` (line ~140)
- **Guardrail intervention:** `src/agents/brand_voice_agent.py` (line ~194)
- **Self-healing logic:** `src/agents/brand_voice_agent.py` (line ~223)
- **UI toggle:** `ui/frontend/src/App.tsx`
- **Backend handling:** `ui/backend/server.py`

---

## Quick Start Checklist

- [ ] Create `brand_agent` AI Config in LaunchDarkly
- [ ] Create variations:
  - [ ] `llama-4-toxic-prompt` (bad prompt that triggers guardrail)
  - [ ] `safe-helpful-prompt` (safe fallback prompt)
- [ ] Configure targeting rules in this **exact order**:
  - [ ] **Rule 1** (FIRST!): `IF is_fallback is true THEN serve safe-helpful-prompt`
  - [ ] **Rule 2**: `IF email is "your-email" THEN serve llama-4-toxic-prompt`
  - [ ] **Rule 3** (default): `serve safe-helpful-prompt`
- [ ] Target yourself to toxic variation (Rule 2)
- [ ] Test with guardrail OFF → See bad response
- [ ] Test with guardrail ON → See self-healing
- [ ] Check LaunchDarkly analytics → See fallback impressions

---

## Advantages Over Hardcoded Fallback

| Feature | Hardcoded Fallback | LaunchDarkly Context Override |
|---------|-------------------|------------------------------|
| **Flexibility** | Requires code changes | Update in LaunchDarkly UI |
| **Observability** | No tracking | Full analytics in LaunchDarkly |
| **Experimentation** | Can't A/B test | Can test different fallbacks |
| **Targeting** | One-size-fits-all | Can vary by user segment |
| **Updates** | Code deploy required | Instant, no deploy |
| **Demo Value** | Hidden logic | Visible in LaunchDarkly UI |

---

## Why This Approach Is Powerful

1. **LaunchDarkly-Native**: Uses the platform's core strength (targeting rules)
2. **Observable**: Track fallbacks in LaunchDarkly analytics
3. **Flexible**: Change fallback variation without code changes
4. **Testable**: Easy to verify in LaunchDarkly UI
5. **Auditable**: See exactly which users hit fallback mode
6. **Experimental**: Can A/B test different fallback strategies
7. **Demo-Friendly**: Visual proof in LaunchDarkly UI
8. **Production-Ready**: Multi-layer fallback for reliability

**This demonstrates how LaunchDarkly and AI safety work together to enable safe experimentation in production.** 🎯
