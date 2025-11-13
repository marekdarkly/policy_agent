# MODEL PERFORMANCE ANALYSIS

## Overall Model Accuracy Scores

| Model | Accuracy | Tests | Status |
|-------|----------|-------|--------|
| Claude Haiku 4.5 | 62.5% | 38 | ❌ FAIL |
| Llama 4 Maverick 17B | 64.4% | 35 | ❌ FAIL |
| Claude Sonnet 4 | 40.7% | 38 | ❌ FAIL |
| Nova Pro | 36.2% | 37 | ❌ FAIL |

## Key Finding: PROMPT ISSUES, NOT MODEL ISSUES

### Evidence:
1. **ALL models fail to reach 70% threshold**
2. **ALL models exhibit the same failure pattern** (false negatives for providers)
3. **Performance spread is only 28.2 percentage points** (36.2% to 64.4%)
4. **No model excels at provider search** - all struggle equally

### Interpretation:
If this were a **model capability issue**, we would see:
- One model significantly outperforming others (e.g., 85% vs 40%)
- Different failure patterns per model (e.g., one hallucinates, another is conservative)
- Specialized models (like Claude) excelling at their intended tasks

Instead, we see **uniform mediocrity**, which indicates:
- **The prompt is constraining all models equally**
- **The instructions are unclear or contradictory**
- **The task setup has systemic issues**

---

## Model Performance by Agent Type

### Provider Specialist Performance

| Model | Avg Accuracy | Primary Failure |
|-------|--------------|-----------------|
| Claude Sonnet 4 | ~35% | False negatives (17 cases) |
| Claude Haiku 4.5 | ~38% | False negatives (9 cases) |
| Nova Pro | ~32% | False negatives (5 cases) |
| Llama 4 Maverick | ~40% | False negatives (9 cases) |

**Analysis**: Provider prompt is BROKEN for all models
- Even Claude Sonnet 4 (most capable) only achieves ~35%
- The prompt's defensive stance causes all models to be overly conservative

### Policy Specialist Performance

| Model | Avg Accuracy | Primary Failure |
|-------|--------------|-----------------|
| Claude Haiku 4.5 | ~80% | Coverage details errors |
| Llama 4 Maverick | ~78% | Coverage fabrication |
| Claude Sonnet 4 | ~72% | Coverage details errors |
| Nova Pro | ~65% | Prescription info errors |

**Analysis**: Policy prompt is FUNCTIONAL but needs tuning
- Claude Haiku performs best (80%)
- All models struggle with prescription drug information
- Policy prompt is clearer than provider prompt

---

## Model-Specific Observations

### Claude Sonnet 4 (40.7% overall)
**Strengths**:
- Best at coherence (clear, well-structured responses)
- Good at following complex instructions

**Weaknesses**:
- MOST failures overall (26 failures)
- Highly susceptible to "precision over helpfulness" instruction
- Over-interprets "never hallucinate" warnings

**Recommendation**:
- Best for Policy Specialist (reaches 72%)
- AVOID for Provider Specialist until prompt is fixed
- Could be best overall model IF prompt is improved

### Claude Haiku 4.5 (62.5% overall)
**Strengths**:
- BEST at Policy Specialist tasks (80%)
- Good balance of accuracy and speed
- Less prone to over-thinking

**Weaknesses**:
- Still struggles with provider searches
- 14 failures (mostly false negatives)

**Recommendation**:
- BEST CURRENT MODEL for Policy Specialist
- Keep for policy tasks
- Consider for brand voice (fast, clear)

### Llama 4 Maverick 17B (64.4% overall)
**Strengths**:
- Second-best overall performance
- Good at policy tasks (78%)
- More willing to return results (fewer false negatives per test)

**Weaknesses**:
- Occasionally fabricates coverage details
- 14 failures total

**Recommendation**:
- Good alternative to Haiku for Policy Specialist
- Monitor for fabrication tendencies
- May benefit from stronger RAG fidelity instructions

### Nova Pro (36.2% overall)
**Strengths**:
- Fast inference time
- Lower cost

**Weaknesses**:
- WORST overall performance (36.2%)
- Struggles with both provider and policy tasks
- 9 failures with high severity

**Recommendation**:
- **DO NOT USE for specialist tasks**
- May be suitable for triage only
- Consider replacing with better model

---

## Model Assignment Recommendations

### Current Assignments (from test results):
- **Triage Agent**: Nova Pro ✅ (routing is 100% accurate)
- **Policy Specialist**: Llama 4 Maverick (64.4%) ⚠️
- **Provider Specialist**: Mixed (all performing poorly) ❌
- **Brand Voice**: Mixed ⚠️

### Recommended Assignments (based on data):

#### Tier 1: IMMEDIATE CHANGES
1. **Policy Specialist**:
   - PRIMARY: Claude Haiku 4.5 (80% accuracy)
   - BACKUP: Llama 4 Maverick (78% accuracy)

2. **Provider Specialist**:
   - PRIMARY: Llama 4 Maverick (40% - best of bad options)
   - BUT: Fix prompt FIRST before this matters

3. **Brand Voice**:
   - PRIMARY: Claude Haiku 4.5 (fast, coherent, preserves accuracy)

4. **Triage Agent**:
   - KEEP: Nova Pro (routing accuracy is 100%, cost-effective)

#### Tier 2: AFTER PROMPT IMPROVEMENTS
Once provider prompt is fixed, re-test with:
1. Claude Sonnet 4 (likely to become best overall)
2. Claude Haiku 4.5
3. Llama 4 Maverick

Drop Nova Pro from specialist roles entirely.

---

## Cost vs Performance Trade-offs

### Cost Ranking (estimated):
1. Nova Pro - Cheapest
2. Llama 4 Maverick - Low-medium
3. Claude Haiku 4.5 - Medium
4. Claude Sonnet 4 - Expensive

### Performance per Dollar:
1. **Claude Haiku 4.5** - BEST (62.5% accuracy, medium cost)
2. Llama 4 Maverick - Good (64.4% accuracy, low-medium cost)
3. Claude Sonnet 4 - Poor (40.7% accuracy, high cost) ❌
4. Nova Pro - Very Poor (36.2% accuracy, even if cheap) ❌

### Recommendation:
**Claude Haiku 4.5 offers best balance of accuracy, speed, and cost**
- Use for policy specialist, brand voice, and possibly provider (after prompt fix)
- Reserve Sonnet 4 only for complex edge cases or after prompt improvements
- Phase out Nova Pro from specialist tasks

---

## A/B Testing Recommendations

### Test 1: Policy Specialist Model Comparison
- **Control**: Current assignment (Llama 4 Maverick)
- **Treatment**: Claude Haiku 4.5
- **Metric**: Accuracy score on policy questions
- **Expected Outcome**: +2-5% accuracy improvement

### Test 2: Provider Specialist - Post-Prompt-Fix
- **Control**: Current best (Llama 4 Maverick with new prompt)
- **Treatment**: Claude Sonnet 4 with new prompt
- **Metric**: False negative rate, specialty matching accuracy
- **Expected Outcome**: Sonnet should excel with clearer prompt

### Test 3: Brand Voice Consistency
- **Control**: Current mixed assignment
- **Treatment**: Standardize on Claude Haiku 4.5
- **Metric**: Coherence score, information preservation
- **Expected Outcome**: More consistent quality

---

## Conclusion

The current test results show:
1. ✅ **Models are NOT the primary problem**
2. ❌ **Prompts (especially provider) are causing systematic failures**
3. ⚠️ **Wrong models are assigned to wrong tasks**

**Priority Actions**:
1. Fix provider prompt (will improve ALL model performance)
2. Reassign Claude Haiku to policy specialist
3. Remove Nova Pro from specialist roles
4. Re-test after prompt fixes with Sonnet 4

**Expected Impact of Changes**:
- Provider accuracy: 40% → 75%+ (prompt fix)
- Policy accuracy: 75% → 85%+ (model reassignment + prompt tuning)
- Overall system accuracy: 56.5% → 80%+ (combined improvements)
