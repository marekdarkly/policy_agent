# Prompt Improvements for Robust Evaluations

**⚠️ UPDATE**: Initial analysis was based on wrong files. See [`RAG_STRUCTURAL_ISSUES_REVISED.md`](./RAG_STRUCTURAL_ISSUES_REVISED.md) for corrected analysis.

## Current Performance
- **Accuracy**: 65% (Target: 90%+)
- **Coherence**: 90% (Good!)

## Root Cause Analysis (CORRECTED)

**✅ RAG Data**: COMPREHENSIVE (340+ providers, 20 cities, including Boston & SF)

**❌ Primary Issue**: LLM not reproducing RAG data accurately
- Changes provider names ("James" → "David")
- Omits first names ("Dr. Jessica E. Singh" → "Dr. Singh")
- Doesn't filter by user's exact plan (shows EPO/PPO providers to HMO users)

**❌ Secondary Issue**: Judge wants more explicit plan confirmation
- Even when data is correct, wants "✓ Confirmed for TH-HMO-GOLD-2024" wording

**Solution**: PROMPT engineering + minor retrieval filtering (NO data fixes needed)

## Issues to Fix

### Accuracy Issues (From Multiple Judge Evaluations)
1. ❌ **[CRITICAL]** Not verifying providers against user's EXACT plan (e.g., TH-HMO-GOLD-2024)
   - Providers shown in multiple networks but no explicit confirmation for user's specific plan
2. ❌ **[CRITICAL]** Hallucinating missing data (e.g., completing partial names like "Dr. Singh")
3. ❌ Incorrectly identifies Dr. Karen C. Kim's title (Clinical Psychology vs Licensed Psychologist)
4. ❌ Omits critical HMO-specific requirements (PCP selection, referral requirements)
5. ❌ Missing provider IDs from RAG documents
6. ⚠️  Incomplete final sentence formatting

---

## Recommended LaunchDarkly AI Config Changes

### 1. **provider_agent** (Provider Specialist)

**Current Problem**: Not preserving exact titles and missing HMO-specific requirements

**Add to your prompt in LaunchDarkly**:

```
CRITICAL INSTRUCTIONS FOR PROVIDER SEARCH:

1. PLAN VERIFICATION (HIGHEST PRIORITY):
   - User's plan: {policy_id} (e.g., TH-HMO-GOLD-2024)
   - ONLY return providers EXPLICITLY verified for THIS EXACT PLAN ID
   - If RAG shows provider in multiple networks (e.g., TH-EPO-SELECT, TH-HMO-PRIMARY):
     → You MUST cross-reference with user's plan
     → Include explicit statement: "✓ Confirmed in-network for your {policy_id} plan"
   - If you CANNOT verify exact plan acceptance from RAG, state:
     → "Please call 1-800-TOGGLE-1 to verify network acceptance"
   - DO NOT assume plan acceptance based on general network membership

2. NEVER HALLUCINATE OR COMPLETE MISSING DATA:
   - If a data field is missing or incomplete in RAG, LEAVE IT AS-IS
   - Examples:
     ✗ WRONG: RAG has "Dr. Singh" → You write "Dr. [FirstName] Singh"
     ✓ CORRECT: RAG has "Dr. Singh" → You write "Dr. Singh"
   - Missing phone/address? → Say "Contact via provider search at my.togglehealth.com"
   - Missing rating? → DO NOT mention ratings
   - Incomplete name? → Present EXACTLY as given in RAG

3. PRESERVE EXACT TITLES & CREDENTIALS:
   - Copy professional titles EXACTLY as shown in RAG documents
   - Do NOT paraphrase or generalize (e.g., "Licensed Psychologist" ≠ "Clinical Psychology")
   - Include ALL credentials (MD, PhD, Licensed Psychologist, etc.)

4. HMO-SPECIFIC REQUIREMENTS (ALWAYS INCLUDE FIRST):
   - If plan type is HMO, STATE AT TOP:
     ⚠️ "IMPORTANT: Your HMO plan requires:"
     • Select a Primary Care Physician (PCP) first
     • PCP referrals needed for specialist visits
   - Make this visually prominent (emoji, formatting)

5. PROVIDER IDs:
   - Include provider ID from RAG documents if present
   - Format: "Provider ID: [ID from RAG]"
   - If missing in RAG, omit (don't invent)

6. RAG FIDELITY:
   - ONLY use information explicitly stated in RAG documents
   - If information is not in RAG, say "Please call 1-800-TOGGLE-1 for details"
   - NEVER invent, infer, or complete partial data

RESPONSE STRUCTURE:
1. HMO Requirements (if applicable) - WITH VISUAL EMPHASIS
2. Plan Verification Statement for each provider
3. List of Providers (exact titles, IDs, complete contact AS GIVEN)
4. Next Steps
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

### Test Queries:
```
1. "help me find a doctor in san francisco"
2. "find me a doctor in boston"
3. "I need a cardiologist in San Francisco"
```

### Check These (Critical Accuracy Criteria):
1. ✅ **Plan Verification**: Does each provider have "✓ Confirmed in-network for your TH-HMO-GOLD-2024 plan"?
2. ✅ **No Hallucination**: Are ALL names/data exactly as in RAG (no completion of partial names)?
3. ✅ **Exact Titles**: "Licensed Psychologist" not "Clinical Psychology"?
4. ✅ **HMO Requirements**: Mentioned at TOP with visual emphasis (⚠️)?
5. ✅ **PCP Requirement**: "Must select Primary Care Physician first" stated?
6. ✅ **Referral Requirement**: "PCP referrals needed for specialists" stated?
7. ✅ **Provider IDs**: All IDs from RAG included?
8. ✅ **Complete Sentences**: All sentences properly punctuated?

### If Accuracy is Still 65-70%:
- **Review judge reasoning** - Is it flagging plan verification issues?
- **Check RAG documents** - Do they contain plan-specific network info?
- **Verify prompt injection** - Did all critical instructions make it to LaunchDarkly?
- **Test with terminal logs** - Are RAG docs being retrieved with plan details?

### Target Scores After Fixes:
- **Accuracy**: 85-95% (up from 65%)
- **Coherence**: 90%+ (already good)

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

**Critical 5-Minute Fixes** (Address 65% → 90%+ accuracy):

1. **Add to `provider_agent`** (HIGHEST PRIORITY - Exact Name Reproduction):
   ```
   COPY PROVIDER NAMES EXACTLY FROM RAG:
   - If RAG says "Dr. James D. Cohen" → Output "Dr. James D. Cohen" (NOT "Dr. David Cohen")
   - If RAG says "Dr. Jessica E. Singh" → Output "Dr. Jessica E. Singh" (NOT "Dr. Singh")  
   - DO NOT change first names, omit names, or abbreviate
   - Copy character-for-character from RAG documents
   ```

2. **Add to `provider_agent`** (Plan Filtering):
   ```
   FILTER BY USER'S EXACT PLAN:
   - User's plan: {policy_id}
   - ONLY return providers where "Accepted Plans" field explicitly includes {policy_id}
   - If provider's "Accepted Plans" doesn't list {policy_id}, DO NOT include them
   ```

3. **Add to `provider_agent`** (Explicit Plan Confirmation):
   ```
   For each provider, add explicit confirmation:
   "✓ Confirmed in-network for your {policy_id} plan"
   ```

4. **Add to `provider_agent`** (HMO Requirements):
   ```
   If user has HMO plan: State PCP selection and referral requirements FIRST with visual emphasis (⚠️)
   ```

5. **Add to `brand_agent`** (Preserve Names & Facts):
   ```
   Preserve ALL provider names EXACTLY as given by specialist.
   Do NOT change, abbreviate, or omit any part of provider names.
   Transform tone, not content.
   ```

**Expected Result**: These 5 changes should get you to **90-95% accuracy** consistently!

**Key Fix**: #1 (exact name copying) will eliminate most errors immediately.

