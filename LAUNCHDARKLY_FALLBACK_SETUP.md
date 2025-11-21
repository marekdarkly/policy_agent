# LaunchDarkly Fallback Targeting Rule Setup

## Step-by-Step Instructions

### 1. Open Your AI Config

1. Log into LaunchDarkly
2. Navigate to **AI Configs** in the left sidebar
3. Select your **`brand_agent`** AI Config
4. Click the **Targeting** tab

---

### 2. Create Fallback Rule (MUST BE FIRST!)

Click **Add targeting rule** at the top of the targeting rules list.

**⚠️ CRITICAL:** This rule MUST be the **first rule** in your targeting order. If it's not first, drag it to the top.

#### Rule Configuration:

**Rule name:** `Guardrail Fallback`

**Conditions:**
- Click **Add condition**
- **Attribute:** Select `is_fallback` from the dropdown
  - If `is_fallback` doesn't exist, type it manually in the text field
- **Operator:** Select `is true`
- **Value:** (leave blank - "is true" doesn't need a value)

**Serve:**
- Select your safe variation (e.g., `safe-helpful-prompt`)

**Rollout:**
- 100% (serve to all users matching this rule)

---

### 3. Create Your Experimental Rule (Second Rule)

Click **Add targeting rule** below the fallback rule.

#### Rule Configuration:

**Rule name:** `Testing Toxic Variation`

**Conditions:**
- Click **Add condition**
- **Attribute:** `email` (or `key`, `name`, whatever you want to target by)
- **Operator:** `is one of`
- **Value:** Your email address (e.g., `marek@togglehealth.com`)

**Serve:**
- Select your toxic variation: `llama-4-toxic-prompt`

**Rollout:**
- 100%

---

### 4. Set Default Fallback (Bottom of Targeting)

Scroll to the bottom of the targeting rules.

**Default rule:**
- **Serve:** Select your safe variation (e.g., `safe-helpful-prompt`)
- **Rollout:** 100%

---

### 5. Verify Rule Order

Your targeting rules should look like this (in order from top to bottom):

```
┌────────────────────────────────────────────────────────┐
│ ✓ Rule 1: Guardrail Fallback                          │
│   IF is_fallback is true                               │
│   THEN serve: safe-helpful-prompt (100%)               │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ ✓ Rule 2: Testing Toxic Variation                     │
│   IF email is "marek@togglehealth.com"                │
│   THEN serve: llama-4-toxic-prompt (100%)             │
└────────────────────────────────────────────────────────┘
                        ↓
┌────────────────────────────────────────────────────────┐
│ Default rule                                           │
│ ELSE serve: safe-helpful-prompt (100%)                │
└────────────────────────────────────────────────────────┘
```

**⚠️ If Rule 1 is not at the top, drag and drop it to reorder!**

---

### 6. Review & Save

1. Click **Review and save** in the top right
2. Review your changes
3. Add a comment (optional): `"Added guardrail fallback targeting for self-healing"`
4. Click **Save changes**

---

### 7. Add Guardrail ID to Toxic Variation (Optional but Recommended)

To display your actual guardrail ID in the terminal output:

1. Go back to the **Variations** tab in your AI Config
2. Select your `llama-4-toxic-prompt` variation
3. Scroll down to **Custom parameters** section
4. Click **Add custom parameter**
5. **Key:** `guardrail_id` (exactly as shown, no colon in the key field)
6. **Value:** Your actual guardrail ID (e.g., `gr-3xamp13` or `gr-healthinsure-safety-v2`)
7. Click **Save**

**Example in LaunchDarkly UI:**
```
Custom Parameters:
┌──────────────────┬─────────────────────────────┐
│ Key              │ Value                       │
├──────────────────┼─────────────────────────────┤
│ guardrail_id     │ gr-3xamp13                  │
└──────────────────┴─────────────────────────────┘
```

The system will extract this and display it in the terminal when the guardrail fires.

---

## How to Test

### Test 1: Normal Operation (No Fallback)
1. Change your targeting to serve `safe-helpful-prompt` to you
2. Ask a question in the chatbot
3. **Expected:** Normal safe response, no guardrail intervention

### Test 2: Guardrail OFF (See the Problem)
1. Target yourself to `llama-4-toxic-prompt`
2. Toggle guardrail to 🛡️ **OFF** (red)
3. Ask: "What should I do about chest pain?"
4. **Expected:** Model generates toxic/dangerous response
5. **Customer sees:** The bad content 😱

### Test 3: Guardrail ON (Self-Healing)
1. Keep targeting to `llama-4-toxic-prompt`
2. Toggle guardrail to 🛡️ **ON** (green)
3. Ask same question
4. **Expected in terminal:**
   ```
   🛡️ AWS BEDROCK GUARDRAIL INTERVENED
   🔄 SELF-HEALING: Guardrail intervention detected
   📍 Strategy: LaunchDarkly Context Attribute Override
   🔧 Modified context attributes:
      • is_fallback: True
   📡 Re-evaluating AI Config with fallback context...
   ✅ LaunchDarkly returned variation: 'safe-helpful-prompt'
   ```
5. **Customer sees:** Safe, helpful response ✅

### Test 4: Verify in LaunchDarkly Analytics
1. Go to LaunchDarkly → **Insights** → **Events**
2. Filter by flag: `brand_agent`
3. Look for events where `context.is_fallback = true`
4. **Expected:** See fallback impressions when guardrail was triggered

---

## Troubleshooting

### "Fallback targeting failed: Still received toxic variation"

**Problem:** The `is_fallback` rule is not first, or not configured correctly.

**Solution:**
1. Go to LaunchDarkly targeting tab
2. Drag the "Guardrail Fallback" rule to the **TOP** of the list
3. Verify condition is: `is_fallback is true`
4. Verify it serves the safe variation
5. Save changes

---

### "LaunchDarkly fallback strategy failed: ..."

**Problem:** The targeting rule doesn't exist or isn't matching.

**Solution:**
1. Check that the rule condition is **exactly**: `is_fallback is true`
2. Check that the rule is **enabled** (not disabled)
3. Check that the safe variation exists and is enabled
4. Try removing and re-adding the rule

---

### Terminal shows: "🆘 Falling back to hardcoded safe default"

**Problem:** LaunchDarkly fallback rule isn't working, so system used hardcoded fallback.

**Solution:**
1. Verify the targeting rule is configured correctly (see above)
2. Check LaunchDarkly is reachable (no network issues)
3. Verify your SDK key is correct in `.env`

**Note:** The hardcoded fallback is a last resort and will still work, but you won't get LaunchDarkly observability.

---

## Expected Behavior Summary

| Scenario | Guardrail | Variation Served | Result |
|----------|-----------|------------------|---------|
| Normal user | N/A | `safe-helpful-prompt` (default) | ✅ Safe response |
| You, guardrail OFF | 🛡️ OFF | `llama-4-toxic-prompt` | ⚠️ Toxic response |
| You, guardrail ON (1st call) | 🛡️ ON | `llama-4-toxic-prompt` | 🛡️ Blocked |
| You, guardrail ON (2nd call with `is_fallback: true`) | 🛡️ ON | `safe-helpful-prompt` (Rule 1) | ✅ Safe response |

---

## LaunchDarkly Analytics Queries

### Track Fallback Usage
```
Flag: brand_agent
Filter: context.is_fallback is true
Metric: Count impressions
```

### Compare Normal vs Fallback
```
Flag: brand_agent
Group by: context.is_fallback
Chart: Count impressions over time
```

### See Which Users Hit Fallback
```
Flag: brand_agent
Filter: context.is_fallback is true
Group by: context.email
```

---

## Quick Reference

### Condition Format
```
is_fallback is true
```

### Modified Context (What the System Sends)
```json
{
  "key": "user-123",
  "email": "marek@togglehealth.com",
  "name": "Marek",
  "tier": "gold",
  "is_fallback": true,
  "fallback_reason": "guardrail_intervention",
  "blocked_variation": "llama-4-toxic-prompt"
}
```

### Rule Order (CRITICAL!)
1. ✅ Guardrail Fallback (`is_fallback is true`)
2. Experimental Testing (target you to toxic)
3. Default (safe for everyone else)

---

**Remember:** The fallback rule MUST be first, or self-healing won't work! 🎯

