# PROMPT CORRELATION ANALYSIS

## PROVIDER SPECIALIST PROMPT ISSUES

### Current State: 40.1% Accuracy (FAILING)

### Primary Failure: FALSE_NEGATIVE_RESULTS (85% of failures)
**Symptom**: System claims "no providers found" when providers exist in RAG documents

### Root Cause Analysis of Provider Prompt (Lines 193-398)

#### ISSUE 1: PROMPT OVERLOAD & COGNITIVE BURDEN
**Problem**: The prompt is 205 lines with excessive nested instructions
- 7 different "CRITICAL INSTRUCTIONS" sections
- 3 "IMPORTANT NOTES" sections
- Multiple conflicting priorities
- Too many "NEVER" and "ALWAYS" directives (creates confusion)

**Impact**: Model gets overwhelmed and defaults to conservative "no results" response

**Evidence from Prompt**:
```
Line 313: "IMPORTANT NOTES:"
Line 336: "CRITICAL INSTRUCTIONS FOR PROVIDER RESPONSES:"
Line 217: "FURTHER NOTES:"
Line 234: "CRITICAL: CHECK USER'S PCP STATUS BEFORE RESPONDING"
```

#### ISSUE 2: NEGATIVE FRAMING DOMINATES
**Problem**: 40% of prompt focuses on what NOT to do rather than what TO do

**Negative Instructions Count**:
- "NEVER" appears 11 times
- "DO NOT" appears 8 times
- "If no providers found" instructions more detailed than "If providers found"

**Impact**: Models over-index on avoiding mistakes (saying "no results") rather than finding results

**Evidence**:
- Lines 313-334: Entire section on "IMPORTANT NOTES" about NOT inventing data
- Lines 319-323: "If RAG documents mention network coverage but DO NOT include specific providers..."
- Line 334: "If you hallucinate providers, patients will call non-existent numbers..."

This creates FEAR-BASED decision making → False negatives

#### ISSUE 3: RAG RETRIEVAL INTERPRETATION AMBIGUITY
**Problem**: Prompt doesn't clearly instruct how to parse provider data structures

**Missing**:
- No explicit instruction on how to extract provider specialty from RAG docs
- No guidance on matching user query specialty to RAG document specialty field
- No instruction on handling partial matches or specialty synonyms

**Evidence**: Test Q007 - Model saw "Seattle Oncology Center" and labeled Dr. Cohen as endocrinologist when she's an oncologist

#### ISSUE 4: CONTRADICTORY PRECISION REQUIREMENTS
**Problem**: Lines 352-354 say:
```
"PRECISION OVER HELPFULNESS:
   - Better to say 'no results' than to misrepresent what you found"
```

**Impact**: This DIRECTLY causes false negatives. Models err on side of saying "nothing found" to avoid mistakes.

#### ISSUE 5: HMO WARNING OVEREMPHASIS
**Problem**: PCP requirement check (lines 237-246) appears BEFORE search results logic

**Impact**: Model spends tokens/attention on HMO warnings before thoroughly analyzing RAG results

---

## POLICY SPECIALIST PROMPT ISSUES

### Current State: 74.6% Accuracy (PASSING but needs improvement)

### Primary Failures:
1. COVERAGE_DETAILS_ERROR (50% of failures)
2. COVERAGE_FABRICATION (25% of failures)
3. PRESCRIPTION_INFO_ERROR (25% of failures)

### Root Cause Analysis of Policy Prompt (Lines 107-189)

#### ISSUE 1: INSUFFICIENT PLAN TYPE VERIFICATION
**Problem**: Line 119 says "ALWAYS verify RAG document plan type matches plan type" but doesn't enforce it strongly

**Evidence**: Test failures show wrong plan information being used

**Fix Needed**: Add explicit verification step BEFORE generating response

#### ISSUE 2: PRESCRIPTION DRUG FALLBACK IS TOO LATE
**Problem**: Line 164 mentions prescription drug absence but AFTER all the response guidelines

**Impact**: Model generates response first, then realizes prescription info missing (too late)

**Fix Needed**: Check for prescription info BEFORE generating response, not in response

#### ISSUE 3: MISSING EXPLICIT COVERAGE AMOUNTS REQUIREMENT
**Problem**: Lines 138-139 say "Provide specific dollar amounts and percentages" but not enforced

**Evidence**: Many failures involve generic responses without specific numbers

**Fix Needed**: Require citing exact RAG document excerpts for all dollar amounts

---

## BRAND VOICE AGENT ANALYSIS

### Current State: Contributing to accuracy problems

### ISSUE: INFORMATION LOSS IN TRANSFORMATION
**Problem**: Lines 606-609 say preserve ALL factual information, but line 650 says:
```
"WHAT TO TRANSFORM:
- ❌ Technical or clinical language → Simple, clear explanations"
```

**Impact**: In attempting to "simplify," brand agent sometimes removes critical details

**Evidence**: Some low-accuracy tests show brand agent smoothing over specialist's caveats

---

## ACCURACY JUDGE PROMPT ANALYSIS

### The judge is CORRECTLY identifying issues
- Judge reasoning is sound (lines 696-750)
- Judge penalizes hallucinations appropriately
- Judge correctly identifies RAG violations

**Conclusion**: The problem is NOT the judge - it's the specialist prompts

---

## MODEL PERFORMANCE CORRELATION

### Key Finding: ALL models fail similarly
- Nova Pro: 36.2% accuracy
- Claude Haiku: 62.5% accuracy
- Claude Sonnet 4: 40.7% accuracy
- Llama 4 Maverick: 64.4% accuracy

### Analysis:
**This indicates PROMPT ISSUES, not model capability issues**

Why? If one model succeeded and others failed, it would suggest model capability differences.
But ALL models failing on the same pattern (false negatives) suggests the PROMPT is causing the behavior.

---

## COHERENCE ANALYSIS (87% - Good)

### Why coherence is high but accuracy is low:
- Coherence judge evaluates structure, tone, clarity (lines 755-823)
- Accuracy judge evaluates factual correctness
- Models can produce well-structured WRONG answers

**Finding**: The prompts are good at creating CLEAR responses, but not ACCURATE responses

---

## SUMMARY OF ROOT CAUSES

1. **Provider Prompt is TOO DEFENSIVE** → False negatives
2. **Provider Prompt is TOO LONG** → Cognitive overload
3. **Negative framing dominates** → Conservative "no results" responses
4. **Missing RAG parsing instructions** → Specialty mismatches
5. **Policy prompt lacks enforcement** → Coverage fabrication
6. **Prescription check is too late in prompt** → Missing critical info

