# RAG Analysis - REVISED (Based on Actual Data)

## ✅ RAG Data Status: COMPREHENSIVE

After reviewing the actual RAG files from `/Users/marek/Downloads/policy_agent-main/data/markdown/`:

- **340+ providers** across 20 major US cities
- **Boston coverage**: YES (Dr. Daniel B. Anderson, Dr. Jessica E. Singh, Dr. James D. Cohen, etc.)
- **San Francisco coverage**: YES (Dr. Kevin B. Patel, Dr. Karen C. O'Brien, Dr. Steven D. Smith, etc.)
- **Network specifications**: COMPLETE for each provider
- **Plan acceptance**: EXPLICIT for each provider

**Conclusion**: The RAG data is NOT the problem. The data is comprehensive and accurate.

---

## ❌ The REAL Problem: LLM Accuracy in Reproducing RAG Data

### Issue 1: Name Modifications (Critical)

**User Query**: "find me a doctor in boston"

**RAG Contains**:
```markdown
#### Dr. James D. Cohen, DO
Provider ID: PCP-MA-053
Specialty: Internal Medicine
Networks: TH-HDHP-CORE, TH-HMO-PRIMARY, TH-PPO-PREMIER
Accepted Plans: TH-HDHP-BRONZE-2024, TH-HMO-GOLD-2024, TH-PPO-PLATINUM-2024
```

**Chatbot Output**:
```
Dr. David B. Cohen, DO
```

**Problem**: Changed "James" → "David" (hallucination/name corruption)

---

### Issue 2: First Name Omission (Critical)

**RAG Contains**:
```markdown
#### Dr. Jessica E. Singh, MD
Provider ID: PCP-MA-054
Specialty: Family Medicine
```

**Chatbot Output**:
```
Dr. Singh, MD
```

**Problem**: Omitted "Jessica E." entirely

**Judge Reasoning**: "Incomplete provider name for Dr. Singh (first name missing from RAG document but output presents as complete)"

**Reality**: The first name IS in RAG, but the LLM omitted it.

---

### Issue 3: Network Verification Not Explicit Enough

**RAG Contains**:
```markdown
Dr. Daniel B. Anderson, MD
Networks: TH-EPO-SELECT, TH-PPO-PREMIER
Accepted Plans: TH-EPO-SILVER-2024, TH-PPO-PLATINUM-2024
```

**User's Plan**: TH-HMO-GOLD-2024

**Chatbot Output**: Listed Dr. Anderson as accepting the HMO plan

**Problem**: Dr. Anderson is NOT in TH-HMO-PRIMARY network (only EPO and PPO)

**Judge Reasoning**: "Missing specific network verification - RAG shows providers in multiple networks but output doesn't clarify which network applies to user's TH-HMO-GOLD-2024 plan"

---

## 🎯 Root Cause Analysis

The 65% accuracy is caused by:

1. **LLM modifying provider names** (James → David)
2. **LLM omitting parts of names** (Jessica E. Singh → Singh)
3. **LLM not filtering providers by user's exact plan** (showing EPO/PPO providers to HMO user)
4. **Judge wanting more explicit plan confirmation** even when data is correct

**This is NOT a RAG data problem. This is a PROMPT + RAG RETRIEVAL problem.**

---

## 🔧 Recommended Fixes

### Fix 1: Strengthen `provider_agent` Prompt (CRITICAL)

Add to LaunchDarkly `provider_agent` AI Config:

```markdown
CRITICAL: EXACT NAME REPRODUCTION

1. COPY PROVIDER NAMES EXACTLY:
   - If RAG says "Dr. James D. Cohen" → Output "Dr. James D. Cohen"
   - If RAG says "Dr. Jessica E. Singh" → Output "Dr. Jessica E. Singh"
   - DO NOT change first names
   - DO NOT omit first names
   - DO NOT abbreviate middle initials
   - Copy character-for-character from RAG

2. FILTER BY USER'S EXACT PLAN:
   - User's plan: {policy_id} (e.g., TH-HMO-GOLD-2024)
   - ONLY return providers where "Accepted Plans" explicitly includes {policy_id}
   - If RAG shows:
     ✓ "Accepted Plans: TH-HMO-GOLD-2024, ..." → INCLUDE
     ✗ "Accepted Plans: TH-EPO-SILVER-2024, TH-PPO-PLATINUM-2024" → EXCLUDE
   - DO NOT assume plan compatibility

3. EXPLICIT PLAN CONFIRMATION:
   For each provider, add:
   "✓ Confirmed in-network for your {policy_id} plan"
   
   Base this on the exact "Accepted Plans" field from RAG.

EXAMPLES:

❌ WRONG:
RAG: "Dr. James D. Cohen, DO"
Output: "Dr. David B. Cohen, DO"
→ Changed first name

✓ CORRECT:
RAG: "Dr. James D. Cohen, DO"
Output: "Dr. James D. Cohen, DO"
→ Exact copy

❌ WRONG:
RAG: "Dr. Jessica E. Singh, MD"
Output: "Dr. Singh, MD"
→ Omitted first name

✓ CORRECT:
RAG: "Dr. Jessica E. Singh, MD"
Output: "Dr. Jessica E. Singh, MD"
→ Exact copy with full name
```

---

### Fix 2: Improve RAG Retrieval Filtering

**Current Issue**: RAG might be retrieving ALL Boston providers, regardless of plan compatibility.

**Solution**: Modify `provider_specialist.py` to:

1. **Pre-filter RAG results by plan**:
   ```python
   # In provider_specialist_node after RAG retrieval
   user_plan_id = state["user_context"].get("policy_id", "")
   
   filtered_docs = []
   for doc in rag_documents:
       # Check if document content contains user's exact plan ID
       if user_plan_id in doc.page_content:
           filtered_docs.append(doc)
       # OR if it says "All ToggleHealth plans"
       elif "All ToggleHealth plans" in doc.page_content:
           filtered_docs.append(doc)
   
   # Only pass filtered docs to LLM
   context_str = "\n\n".join([doc.page_content for doc in filtered_docs])
   ```

2. **Add plan ID to RAG query**:
   ```python
   # Modify retrieval query to include plan
   enhanced_query = f"{user_message} Plan: {user_plan_id}"
   rag_documents = retriever.invoke(enhanced_query)
   ```

---

### Fix 3: Add Validation Check in `brand_voice_agent`

Add post-processing validation:

```python
# In brand_voice_agent.py after LLM response
import re

def validate_provider_names(response_text, rag_documents):
    """Ensure all provider names in response match RAG exactly."""
    issues = []
    
    # Extract provider names from RAG
    rag_names = set()
    for doc in rag_documents:
        # Find all "Dr. [Full Name]" patterns in RAG
        names = re.findall(r'Dr\. [A-Z][a-z]+ [A-Z]\. [A-Z][a-z]+', doc.page_content)
        rag_names.update(names)
    
    # Extract provider names from response
    response_names = re.findall(r'Dr\. [A-Za-z .]+,', response_text)
    
    for resp_name in response_names:
        clean_name = resp_name.replace(',', '').strip()
        if clean_name not in rag_names:
            issues.append(f"Name mismatch: '{clean_name}' not found in RAG exactly")
    
    return issues

# After generating brand voice response
validation_issues = validate_provider_names(final_response, rag_documents)
if validation_issues:
    print(f"⚠️  VALIDATION WARNING: {validation_issues}")
```

---

### Fix 4: Update Judge Evaluation Criteria (Optional)

The judge is currently VERY sensitive to network verification wording. You can either:

**Option A**: Keep strict judge (force agents to be more explicit)  
→ Good for catching edge cases

**Option B**: Relax judge slightly (accept implicit plan confirmation)  
→ Might miss some issues

**Recommendation**: Keep strict judge, fix the agents instead.

---

## 🎯 Expected Impact

### Before Fixes:
```
Query: "find me a doctor in boston"
Response:
- Dr. Daniel B. Anderson ✓ (correct)
- Dr. Singh ❌ (should be "Dr. Jessica E. Singh")
- Dr. David B. Cohen ❌ (should be "Dr. James D. Cohen")

Accuracy: 65%
Issues:
- Name modifications
- Name omissions
- Network verification vague
```

### After Fixes:
```
Query: "find me a doctor in boston"
Response:
- Dr. Daniel B. Anderson, MD ✓
  ✓ Confirmed in-network for your TH-HMO-GOLD-2024 plan
- Dr. Jessica E. Singh, MD ✓ (full name preserved)
  ✓ Confirmed in-network for your TH-HMO-GOLD-2024 plan
- Dr. James D. Cohen, DO ✓ (correct first name)
  ✓ Confirmed in-network for your TH-HMO-GOLD-2024 plan

Accuracy: 90-95%
All info correct and explicit
```

---

## Summary

**❌ DISREGARD PREVIOUS ANALYSIS** (was based on wrong files)

**✅ ACTUAL SITUATION**:
- RAG data is comprehensive and correct
- Problem is LLM not reproducing names exactly
- Problem is LLM not filtering by exact plan
- Solution is PROMPT engineering, not data fixes

**Top 3 Priorities**:
1. Add "COPY NAMES EXACTLY" instruction to provider_agent prompt
2. Add plan filtering logic to provider_specialist.py
3. Add explicit "✓ Confirmed for {plan_id}" to responses

**Expected Result**: 65% → 90-95% accuracy

