# RAG Structural Issues - Provider Data

## Problem Summary

**Current Accuracy**: 65%  
**Root Cause**: Mismatch between claimed coverage and actual provider data

---

## Critical Issues Found

### Issue 1: Coverage Claims Without Provider Data ❌

**`provider_directory_overview.md` claims:**
```
California Coverage:
- San Francisco Bay Area (ALL plans)
- Sacramento (PPO, HDHP, HMO)
- San Diego (PPO, HDHP)
- Los Angeles (PPO only)
```

**`providers_detailed.md` ACTUALLY has:**
- **San Francisco**: 1 provider (Dr. Sarah J. Goldman - Endocrinologist, SPEC-CA-001)
- **Sacramento**: 0 providers
- **San Diego**: 0 providers  
- **Los Angeles**: 0 providers

**Result**: LLM hallucinates providers to fulfill queries because overview says coverage exists.

### Issue 2: Boston Not in Coverage Area ❌

**User Query**: "find me a doctor in boston"  
**Coverage Area** (from overview):
- Washington, Oregon, California, Idaho, Montana
- **Massachusetts NOT mentioned**

**LLM Response**: Returned 3 Boston providers (Dr. Daniel B. Anderson, Dr. Singh, Dr. David B. Cohen)  
**Reality**: All 3 are **completely hallucinated** - not in RAG at all

**Result**: 65% accuracy because judge correctly identified hallucinations.

### Issue 3: Multiple Networks, No Plan-Specific Mapping ⚠️

**Example from `providers_detailed.md`:**
```
Dr. Michael R. Chen, MD
Networks: HMO, PPO, HDHP (not EPO)
Accepted Plans: TH-HMO-GOLD-2024, TH-PPO-PLATINUM-2024, TH-HDHP-BRONZE-2024
```

**Good**: This provider HAS explicit plan acceptance.

**Example from another provider:**
```
Dr. Sarah J. Anderson, MD
Networks: All networks (HMO, PPO, EPO, HDHP)
Accepted Plans: All ToggleHealth plans
```

**Problem**: "All ToggleHealth plans" is vague - doesn't explicitly list TH-HMO-GOLD-2024.

**Result**: Judge flags "Missing specific network verification" because output can't confirm user's exact plan.

### Issue 4: Incomplete Provider Names ⚠️

**Judge Reasoning from Boston evaluation:**
> "Incomplete provider name for Dr. Singh (first name missing from RAG document but output presents as complete)"

**Reality**: There is NO "Dr. Singh" in the RAG at all (hallucination).

**But IF there was**, the judge is correct - partial names create ambiguity.

---

## Recommended RAG Fixes

### Fix 1: Align Coverage Claims with Actual Data ✅

**Option A: Add Real Provider Data**

Create provider entries for claimed coverage areas:

```markdown
### PRIMARY CARE - SAN FRANCISCO

1. Dr. [Name], MD - Family Medicine
   Provider ID: PCP-CA-001
   Address: [Real or synthetic SF address]
   Phone: 415-555-XXXX
   Networks: HMO, PPO, EPO, HDHP
   Accepted Plans: TH-HMO-GOLD-2024, TH-PPO-PLATINUM-2024, TH-EPO-SILVER-2024, TH-HDHP-BRONZE-2024
   Accepting New Patients: Yes
   ...

2. Dr. [Name], MD - Internal Medicine
   Provider ID: PCP-CA-002
   ...

[Add 5-10 providers per specialty for San Francisco]
[Add 5-10 providers per specialty for Sacramento]
[Add 5-10 providers per specialty for San Diego]
```

**Option B: Remove False Coverage Claims**

Update `provider_directory_overview.md`:

```markdown
### California

**Major Areas Covered:**
- San Francisco Bay Area (LIMITED - specialist only)
  - SPECIALTY ONLY: Endocrinology (Dr. Goldman)
  - For primary care, use provider search: my.togglehealth.com/find-provider
- Sacramento: Use provider search for local providers
- San Diego: Use provider search for local providers
```

**RECOMMENDED: Option A** - Add real provider data to match coverage claims.

### Fix 2: Explicitly State Out-of-Network Areas ✅

Add to `provider_directory_overview.md`:

```markdown
## Areas NOT Covered

ToggleHealth networks do NOT provide in-network coverage in:
- Massachusetts (including Boston)
- New York
- Texas
- Florida
- [Other states not in WA, OR, CA, ID, MT]

**If you live in these areas:**
- Contact Member Services: 1-800-TOGGLE-1
- Out-of-network claims may be subject to higher costs
- Consider our nationwide PPO option (if available)
```

Add to `providers_detailed.md` at the top:

```markdown
## Coverage Verification

⚠️ **IMPORTANT**: ToggleHealth only provides in-network coverage in:
- Washington
- Oregon  
- California (San Francisco Bay Area specialists only - see notes)
- Idaho (Boise metro - PPO only)
- Montana (select metros - PPO only)

**All provider listings below are within these coverage areas only.**

If you need care outside these areas, call 1-800-TOGGLE-1.
```

### Fix 3: Make Plan Acceptance Explicit for ALL Providers ✅

**Current (vague):**
```markdown
**Networks:** All networks (HMO, PPO, EPO, HDHP)
**Accepted Plans:** All ToggleHealth plans
```

**Fixed (explicit):**
```markdown
**Networks:** TH-HMO-PRIMARY, TH-PPO-PREMIER, TH-EPO-SELECT, TH-HDHP-CORE

**Explicitly Accepted Plans:**
- ✓ TH-HMO-GOLD-2024
- ✓ TH-PPO-PLATINUM-2024
- ✓ TH-EPO-SILVER-2024
- ✓ TH-HDHP-BRONZE-2024
```

**Apply to EVERY provider in `providers_detailed.md`.**

### Fix 4: Complete All Provider Names ✅

**Search for partial names:**
```bash
grep -i "Dr\. [A-Z][a-z]*," providers_detailed.md
```

**Ensure format:**
```markdown
### Dr. [FirstName] [MiddleInitial]. [LastName], [Credentials]
```

**Examples:**
- ❌ `Dr. Singh` → ❌ INCOMPLETE
- ✓ `Dr. Rajesh Singh, MD` → ✓ COMPLETE
- ✓ `Dr. Sarah J. Anderson, MD` → ✓ COMPLETE

### Fix 5: Add Plan Verification Instructions to Overview ✅

Add to `provider_directory_overview.md`:

```markdown
## Before You See a Provider

### ✅ ALWAYS Verify In-Network Status

Even if a provider is listed in this directory:

1. **Call Member Services**: 1-800-TOGGLE-1
2. **Verify your EXACT plan**: Provide your policy ID (e.g., TH-HMO-GOLD-2024)
3. **Confirm provider accepts YOUR specific plan**
4. **Check if provider is accepting new patients**

**Why?**
- Provider networks change
- Some providers accept certain plans but not others
- Verification prevents unexpected out-of-network charges

### 📍 Location-Specific Requirements

**HMO Plans (TH-HMO-GOLD-2024):**
- ⚠️ MUST select a Primary Care Physician (PCP) FIRST
- ⚠️ MUST get PCP referral before seeing specialists
- ⚠️ Limited to network providers (no out-of-network coverage except emergencies)

**PPO Plans (TH-PPO-PLATINUM-2024):**
- Can see any in-network provider without referral
- Can see out-of-network providers (higher cost-sharing)
- No PCP requirement

**EPO Plans (TH-EPO-SILVER-2024):**
- Can see any in-network provider without referral
- NO out-of-network coverage (except emergencies)
- No PCP requirement

**HDHP Plans (TH-HDHP-BRONZE-2024):**
- Can see any in-network provider without referral
- High deductible applies to most services
- HSA-eligible
```

---

## Impact on Accuracy

### Current State (with issues):
```
Query: "find me a doctor in boston"
RAG Retrieved:
  - provider_directory_overview.md (mentions coverage but not Boston)
  - providers_detailed.md (no Boston providers)

LLM Logic:
  - User wants Boston doctor
  - RAG has no Boston providers
  - But RAG doesn't say "Boston is NOT covered"
  - LLM hallucinates 3 realistic providers

Judge Evaluation: 65% accuracy ❌
```

### Fixed State:
```
Query: "find me a doctor in boston"
RAG Retrieved:
  - provider_directory_overview.md (EXPLICITLY says Boston NOT covered)
  - providers_detailed.md (states at top: only WA/OR/CA coverage)

LLM Response:
  "I'm sorry, ToggleHealth doesn't currently provide in-network
   coverage in Massachusetts (Boston area). Our network covers
   Washington, Oregon, California, Idaho, and Montana.
   
   Please call Member Services at 1-800-TOGGLE-1 to discuss
   out-of-network options or alternative coverage."

Judge Evaluation: 95%+ accuracy ✓
```

---

## Implementation Checklist

### High Priority (Prevents Hallucination):

- [ ] **Add explicit "Areas NOT Covered" section** to overview
- [ ] **Add coverage area warning** at top of providers_detailed.md
- [ ] **Add 5-10 San Francisco providers** (primary care + common specialties)
- [ ] **Make plan acceptance explicit** for ALL providers (not "All plans")

### Medium Priority (Improves Accuracy):

- [ ] **Complete all partial provider names** (no "Dr. Singh" without first name)
- [ ] **Add verification instructions** to overview (HMO requirements, plan checking)
- [ ] **Add plan-specific network names** (TH-HMO-PRIMARY vs just "HMO")

### Low Priority (Nice to Have):

- [ ] Add Sacramento providers (if claiming coverage)
- [ ] Add San Diego providers (if claiming coverage)
- [ ] Add more SF specialists beyond endocrinology

---

## Expected Results After Fixes

### Before Fixes:
```
Accuracy: 65%
Issues:
- Hallucinated Boston providers (not in coverage area)
- Vague plan acceptance ("All plans")
- Missing specific plan verification
```

### After Fixes:
```
Accuracy: 85-95%
Improvements:
- ✓ Explicit out-of-coverage handling (no hallucination)
- ✓ Explicit plan acceptance per provider
- ✓ Clear HMO requirements in documentation
- ✓ Plan verification instructions
```

---

## Quick Win: Immediate Fix

**Add this to the TOP of `providers_detailed.md` NOW:**

```markdown
---

## ⚠️ IMPORTANT: Coverage Area Verification

**ToggleHealth In-Network Coverage is LIMITED to:**
- ✅ Washington (all counties)
- ✅ Oregon (western counties, Portland metro)
- ✅ California - **SAN FRANCISCO BAY AREA ONLY** (specialists)
- ✅ Idaho (Boise metro - PPO only)
- ✅ Montana (select metros - PPO only)

**❌ NO in-network coverage in:**
- Massachusetts (Boston)
- New York
- Texas
- Florida
- Any state not listed above

**If you need care outside these areas:**
Call Member Services: 1-800-TOGGLE-1

---
```

**Expected impact**: Prevents hallucination immediately, accuracy jumps to 80%+.

---

## Testing After Fixes

### Test Queries:
1. "find me a doctor in boston" → Should say NOT COVERED
2. "help me find a doctor in san francisco" → Should return actual providers from RAG
3. "I need a cardiologist in San Francisco" → Should say limited specialists or direct to search
4. "find me a primary care doctor in sacramento" → Should say limited or direct to search

### Success Criteria:
- ✅ No hallucinated providers
- ✅ Explicit plan acceptance verification
- ✅ Clear HMO requirements stated
- ✅ Accuracy: 85-95%

