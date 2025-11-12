# Prompt Improvements for Robust Evaluations

## Current Performance
- **Accuracy**: 65% (Target: 80%+)
- **Coherence**: 90% (Good!)

## Issues to Fix

### Accuracy Issues (From Judge)
1. ❌ Incorrectly identifies Dr. Karen C. Kim's title (Clinical Psychology vs Licensed Psychologist)
2. ❌ Omits critical HMO-specific requirements (PCP selection, referral requirements)
3. ❌ Missing provider IDs from RAG documents
4. ⚠️  Incomplete final sentence formatting

---

## Recommended LaunchDarkly AI Config Changes

### 1. **provider_agent** (Provider Specialist)

**Current Problem**: Not preserving exact titles and missing HMO-specific requirements

**Add to your prompt in LaunchDarkly**:

```
CRITICAL INSTRUCTIONS FOR PROVIDER SEARCH:

1. PRESERVE EXACT TITLES & CREDENTIALS:
   - Copy professional titles EXACTLY as shown in RAG documents
   - Do NOT paraphrase or generalize (e.g., "Licensed Psychologist" ≠ "Clinical Psychology")
   - Include ALL credentials (MD, PhD, Licensed Psychologist, etc.)

2. HMO-SPECIFIC REQUIREMENTS (ALWAYS INCLUDE):
   - If plan type is HMO, user MUST first select a Primary Care Physician (PCP)
   - Specialists require PCP referrals for HMO plans
   - State this CLEARLY at the beginning of your response

3. PROVIDER IDs:
   - Include provider ID from RAG documents if present
   - Format: "Provider ID: [ID from RAG]"

4. RAG FIDELITY:
   - ONLY use information explicitly stated in RAG documents
   - If information is not in RAG, say "Please call [number] for details"
   - NEVER invent or infer details not in the knowledge base

RESPONSE STRUCTURE:
1. HMO Requirements (if applicable)
2. List of Providers (with exact titles, IDs, and complete contact info)
3. Next Steps
```

**Variables to use**: `{provider_info}`, `{coverage_type}`, `{network}`, `{location}`

---

### 2. **brand_agent** (Brand Voice)

**Current Problem**: Omitting critical information and incomplete sentences

**Add to your prompt in LaunchDarkly**:

```
TRANSFORMATION RULES:

1. PRESERVE ALL FACTUAL INFORMATION:
   - Keep ALL provider IDs, titles, credentials from specialist response
   - Keep ALL policy requirements (PCP selection, referrals, pre-auth)
   - Keep ALL contact information exactly as provided
   - DO NOT simplify or omit for "smoothness"

2. COMPLETE SENTENCES RULE:
   - Every sentence must have proper punctuation
   - Questions must end with "?"
   - Statements must end with "." or "!"
   - Review your final sentence before finishing

3. HMO WARNINGS (If present in specialist response):
   - Emphasize HMO requirements at the TOP
   - Make them visually distinct (emoji, formatting)
   - Never bury critical requirements in middle of response

4. MAINTAIN FRIENDLINESS WITHOUT SACRIFICING ACCURACY:
   - Add warmth and empathy
   - Use customer's name
   - BUT: Keep every fact from specialist response
   - Transform tone, NOT content

QUALITY CHECK BEFORE SENDING:
✓ All provider IDs present?
✓ All titles/credentials exact?
✓ All HMO requirements stated?
✓ All sentences complete?
✓ Friendly tone maintained?
```

**Variables to use**: `{customer_name}`, `{specialist_response}`, `{query_type}`

---

### 3. **ai-judge-accuracy** (Accuracy Judge)

**Current**: Your judge is already pretty good (caught all the issues!)

**Optional Enhancement**: Make it even stricter

```
EVALUATION CRITERIA (More Strict):

1. EXACT MATCH REQUIREMENT:
   - Professional titles must match RAG EXACTLY (0 tolerance)
   - Provider IDs must be present if in RAG
   - Contact info must match character-for-character

2. CRITICAL INFORMATION CHECK:
   - For HMO plans: PCP requirement mentioned? (-20% if not)
   - For HMO plans: Referral requirement mentioned? (-20% if not)
   - All provider IDs included? (-10% per missing ID)

3. HALLUCINATION DETECTION:
   - ANY detail not in RAG = automatic 50% or lower score
   - Flag specific invented details

SCORING:
- 100%: Perfect accuracy, all RAG info preserved
- 80-99%: Minor formatting issues only
- 60-79%: Missing non-critical info or title mismatches
- 40-59%: Missing critical HMO requirements
- 0-39%: Hallucinations or major omissions
```

---

## Implementation Checklist

### In LaunchDarkly UI:

1. **provider_agent** config:
   - [ ] Open AI Config → Edit
   - [ ] Add HMO requirements to prompt
   - [ ] Add "PRESERVE EXACT TITLES" instruction
   - [ ] Add Provider ID requirement
   - [ ] Test with your query

2. **brand_agent** config:
   - [ ] Open AI Config → Edit
   - [ ] Add "PRESERVE ALL FACTUAL INFORMATION" rule
   - [ ] Add complete sentence check
   - [ ] Add quality checklist at end
   - [ ] Test with your query

3. **ai-judge-accuracy** config (optional):
   - [ ] Make scoring more strict
   - [ ] Add explicit HMO requirement checks
   - [ ] Test to ensure it's not TOO strict

---

## Expected Results After Changes

### Before (Current):
```
Accuracy: 65%
Issues:
- Wrong title (Clinical Psychology)
- Missing HMO requirements
- Missing provider IDs
```

### After (Expected):
```
Accuracy: 85-95%
All info preserved:
✓ Exact titles
✓ HMO requirements stated upfront
✓ Provider IDs included
✓ Complete sentences
```

---

## Testing Your Changes

### Test Query:
```
"help me find a doctor in san francisco"
```

### Check These:
1. ✅ Does it say "Licensed Psychologist" not "Clinical Psychology"?
2. ✅ Does it mention PCP selection requirement (HMO)?
3. ✅ Does it mention referral requirement (HMO)?
4. ✅ Are provider IDs included?
5. ✅ Are all sentences complete?

### If Accuracy is Still Low:
- Check if judge is too strict (review judge reasoning)
- Verify RAG documents contain the info you expect
- Make provider/brand prompts even more explicit

---

## Pro Tips

### 1. **Use Custom Parameters in LaunchDarkly**
Add custom parameters to your AI configs:
```json
{
  "preserve_exact_titles": true,
  "include_provider_ids": true,
  "emphasize_hmo_requirements": true
}
```

Then reference in prompts: `{preserve_exact_titles}`

### 2. **Use Few-Shot Examples**
Add example responses to your prompts showing:
- Correct title preservation
- HMO requirements stated first
- Provider IDs included

### 3. **Layered Quality Checks**
Add to brand_agent prompt:
```
Before finalizing response, ask yourself:
1. Would the accuracy judge score this 80%+?
2. Is every fact from specialist_response preserved?
3. Are HMO requirements clear?
If NO to any: revise before sending.
```

---

## Quick Wins (Do These First)

**5-Minute Fixes**:
1. Add to `provider_agent`: "Copy all professional titles EXACTLY from RAG documents"
2. Add to `provider_agent`: "If HMO plan: State PCP selection and referral requirements FIRST"
3. Add to `brand_agent`: "Preserve ALL facts from specialist response. Transform tone, not content."

**These alone should get you to 80%+ accuracy!**

