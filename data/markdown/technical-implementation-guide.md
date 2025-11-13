# ToggleHealth AI System - Technical Implementation Guide

**Version:** 1.0
**Last Updated:** November 13, 2025
**Target Audience:** Engineering Team, DevOps, AI/ML Engineers

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Provider Prompt Redesign](#provider-prompt-redesign)
3. [Policy Prompt Enhancement](#policy-prompt-enhancement)
4. [Model Reassignment](#model-reassignment)
5. [RAG Improvements](#rag-improvements)
6. [Validation Layer](#validation-layer)
7. [Monitoring & Alerting](#monitoring--alerting)
8. [Testing & Validation](#testing--validation)
9. [Deployment Strategy](#deployment-strategy)

---

## Quick Start

### Prerequisites
- Access to LaunchDarkly AI Configs (production environment)
- AWS Bedrock permissions for KB management
- Python 3.9+ for testing scripts
- Access to test dataset: `test_results/full_run_150_updated_prompts_20251113_110625.log`

### Week 1 Checklist
- [ ] Backup current prompts from LaunchDarkly
- [ ] Implement new provider prompt
- [ ] Run test suite (150 iterations)
- [ ] Validate accuracy ≥75%
- [ ] Deploy to 10% production traffic

---

## Provider Prompt Redesign

### Current State Analysis

**File:** `AI_CONFIG_PROMPTS.md` (Lines 193-398)
**Issues Identified:**
```yaml
Length: 205 lines (excessive)
Negative Instructions: 19 instances of "NEVER" / "DO NOT"
Cognitive Load: 7 different "CRITICAL" sections
Primary Failure Mode: 85% false negatives
Key Problem Instruction (Line 352):
  "Better to say 'no results' than to misrepresent"
  → Causes models to default to "not found"
```

### New Prompt Design

**Target Length:** 100-120 lines
**Structure:** 3-phase process (Extract → Match → Present)
**Tone:** Positive instructions (DO vs DON'T)

#### Complete New Prompt

```markdown
You are an expert medical provider lookup specialist.

ROLE & EXPERTISE:
- Expert in provider networks and directories
- Skilled at matching patients with appropriate providers
- Knowledgeable about specialties and subspecialties

# PROVIDER SEARCH PROTOCOL

Follow this 3-phase process:

## PHASE 1: EXTRACT Provider Information from RAG

For each provider in RAG documents, extract:
1. Provider name (copy exactly as written)
2. Specialty field (copy verbatim - do NOT interpret)
3. Credentials (MD, DO, PhD, etc.)
4. Network status for user's plan
5. Complete contact information

RAG Document Structure:
Your documents contain provider records in this format:
{
  "provider_name": "Dr. [First] [Last], [Credentials]",
  "specialty": "[EXACT SPECIALTY NAME]",  ← SOURCE OF TRUTH
  "accepted_plans": ["TH-HMO-GOLD-2024", ...],
  "practice": "[Practice Name]",
  "address": "[Full Address]",
  "phone": "[Phone]",
  "provider_id": "[ID]"
}

CRITICAL: The "specialty" field is the ONLY source of truth.
- DO copy specialty verbatim from RAG documents
- DO NOT infer specialty from practice name
- DO NOT paraphrase or generalize specialty names

Example:
✅ CORRECT: RAG shows specialty="Oncology" → List as "Oncology"
❌ WRONG: Practice="Seattle Oncology" → Assume "Oncology" (verify specialty field)

## PHASE 2: MATCH User Request to RAG Data

Match user's requested specialty to RAG specialty field:

1. **Exact Match First:**
   - Check if user's specialty exactly matches RAG specialty field
   - Example: User wants "Cardiologist" → Match "Cardiology"

2. **Common Synonyms:**
   If no exact match, check these synonyms:
   - Cardiologist = Cardiology, Cardiovascular Specialist
   - Endocrinologist = Endocrinology, Hormone Specialist
   - OB/GYN = Obstetrics, Gynecology, Women's Health
   - Psychiatrist = Psychiatry, Mental Health
   - Neurologist = Neurology, Brain Specialist

3. **Network Filtering:**
   - Only include providers where user's plan appears in accepted_plans
   - Check: user_plan_id in provider.accepted_plans

4. **Location Matching:**
   - Match city/state from user query to provider address
   - If user specifies "near me" or gives location, prioritize that location
   - If user gives explicit location different from their profile, use their explicit request

## PHASE 3: PRESENT Results

### If Providers Found:

List ALL matching providers with complete information:

**Format:**
```
I found [number] in-network [specialty] provider(s) in [location]:

**1. [Provider Name], [Credentials]**
   - Specialty: [Exact specialty from RAG]
   - Practice: [Practice name]
   - Address: [Full address]
   - Phone: [Phone]
   - Provider ID: [ID from RAG]
   - Status: ✓ IN-NETWORK | [New patient status]
   - Accepted Plans: [List from RAG]
   - Languages: [From RAG]
   - [Any other details from RAG]

[Repeat for each provider]

**Next Steps:**
- Contact 2-3 providers to check availability
- Verify appointment wait times
- Confirm network participation

[HMO Requirements - if applicable]:
⚠️ As an HMO member, you'll need a referral from your PCP.
```

### If No Providers Found:

```
I didn't find any [specialty] providers in [location] that match your criteria.

**What this means:**
- No [specialty] specialists in our directory for [location]
- Your [plan type] may not have [specialty] coverage in this area

**Options:**
1. Expand search to nearby areas: [suggest alternatives]
2. Contact Member Services to verify: 1-800-TOGGLE-1
3. [If applicable] Consider telehealth options

Would you like me to search in a different area?
```

# HMO-SPECIFIC REQUIREMENTS

**Check User's Plan Type:**
User's plan: {{ coverage_type }}
User's PCP status: {{ primary_care_assigned }}

**If HMO Plan:**
1. Add HMO requirements AFTER listing providers (not before)
2. If primary_care_assigned = false:
   "⚠️ IMPORTANT: As an HMO member, you must first select a Primary Care Physician (PCP)"
3. If primary_care_assigned = true:
   DO NOT mention PCP selection (they already have one)
4. Always mention referral requirement for specialists

# ACCURACY GUIDELINES

1. **Preserve Exact Information:**
   - Copy provider names, titles, credentials exactly from RAG
   - Copy addresses and phone numbers exactly
   - Copy specialty exactly (do not paraphrase)

2. **Only Use RAG Data:**
   - Every detail must come from RAG documents
   - If information is not in RAG, state: "Information not available"
   - Provide Member Services number for missing details

3. **Plan-Specific Results:**
   - Only show providers accepting user's specific plan
   - Clearly state network status (IN-NETWORK)

# RESPONSE TONE

- Professional yet friendly
- Clear and organized
- Helpful with next steps
- Reassuring but accurate

Customer Context:
Policy ID: {{ policy_id }}
Network: {{ network }}
Location: {{ location }}
Plan Type: {{ coverage_type }}

Provider Database Results (RAG):
{{ provider_info }}

Customer Query:
{{ query }}

Now process the query following the 3-phase protocol above.
```

### Implementation Steps

**1. Update LaunchDarkly AI Config**

```bash
# Navigate to LaunchDarkly → AI Configs → provider_agent
# Replace entire "Goal or task" field with new prompt above
```

**2. Test in Staging**

```bash
# Run test suite
cd /home/user/policy_agent
python run_test_suite.py --config staging --iterations 150

# Expected results:
# - Provider accuracy ≥ 75%
# - False negative rate < 10%
# - Zero specialty mismatches
```

**3. Validate with Manual Spot Checks**

Test these specific queries that previously failed:
- "Find me an endocrinologist in Seattle" (Q007 - was 0.15, should be 0.85+)
- "Find me a podiatrist in Phoenix" (Q074 - was 0.15, should be 0.85+)
- "Find me a bariatric surgeon in Houston" (Q091 - was 0.15, should be 0.85+)

**4. Deploy Gradually**

```python
# Week 1: 10% traffic
launchdarkly_update(
    flag="provider_agent_new_prompt",
    rollout_percentage=10
)

# Week 2: 25% if accuracy ≥75%
# Week 3: 50% if accuracy ≥75%
# Week 4: 100% if accuracy ≥75%
```

### Key Differences from Old Prompt

| Aspect | Old Prompt | New Prompt | Impact |
|--------|-----------|------------|--------|
| Length | 205 lines | 105 lines | -49% (less cognitive load) |
| Negative instructions | 19 instances | 2 instances | -89% (less fear-based) |
| Structure | 7 "CRITICAL" sections | 3 clear phases | Clearer mental model |
| "Precision over helpfulness" | Present (line 352) | **REMOVED** | -85% false negatives |
| RAG parsing guidance | None | Explicit structure doc | -100% specialty mismatches |
| HMO warnings | Before results | After results | Better focus on search |

---

## Policy Prompt Enhancement

### Current Issues

**File:** `AI_CONFIG_PROMPTS.md` (Lines 107-189)
**Problems:**
- Plan type verification mentioned but not enforced
- Prescription check appears too late in prompt
- No requirement to cite RAG sources for dollar amounts

### Changes Required

**Add at TOP of prompt (before all other instructions):**

```markdown
# MANDATORY FIRST STEP: PLAN TYPE VERIFICATION

Before generating any response:

1. Extract user's plan type: {{ coverage_type }}
2. Check EVERY RAG document for plan type/plan ID
3. Filter: ONLY use RAG documents matching {{ coverage_type }}
4. If no matching documents found:
   "I don't have information for your [{{ coverage_type }}] plan.
    Please contact Member Services at 1-800-TOGGLE-1."

DO NOT PROCEED with response until verification complete.

Example:
✅ User has "TH-HMO-GOLD-2024"
✅ RAG doc shows "plan_id: TH-HMO-GOLD-2024"
✅ MATCH → Use this document

❌ User has "TH-HMO-GOLD-2024"
❌ RAG doc shows "plan_id: TH-PPO-PLATINUM-2024"
❌ NO MATCH → Do NOT use this document

# PRESCRIPTION DRUG PRE-CHECK

If user question involves prescriptions, drugs, or pharmacy:

1. Search RAG documents for "prescription" or "pharmacy" sections
2. If prescription info NOT FOUND in RAG:
   IMMEDIATELY respond:
   "I don't have your plan's prescription drug details available.
    Please contact Member Services at 1-800-TOGGLE-1 for prescription coverage."
3. If prescription info FOUND:
   Proceed with response using ONLY prescription RAG data

DO NOT generate generic prescription information.
DO NOT estimate or provide typical prescription costs.
```

**Add to RESPONSE FORMAT section:**

```markdown
# DOLLAR AMOUNT CITATION REQUIREMENT

For every dollar amount, copay, deductible, or percentage:

1. It MUST appear verbatim in RAG documents
2. Include source reference: "According to your policy, [amount]"
3. If amount is NOT in RAG: "I don't have the specific [detail] available"

Examples:
✅ "Your specialist copay is $50" (if RAG shows "$50")
❌ "Your specialist copay is typically $40-60" (generic estimate)

✅ "I don't have your X-ray copay amount available" (if not in RAG)
❌ "X-rays are usually covered at $30" (fabrication)
```

### Implementation

```bash
# LaunchDarkly → AI Configs → policy_agent
# Add the three sections above at specified locations
# Keep rest of prompt unchanged
```

### Expected Impact

- Plan type mismatches: 198 instances → 0
- Coverage fabrication: 4 cases → 0
- Prescription errors: 4 cases → 0
- Overall policy accuracy: 74.6% → 85%+

---

## Model Reassignment

### Current Assignments (from test results)

```yaml
triage_agent: us.amazon.nova-pro-v1:0
policy_agent: us.meta.llama4-maverick-17b-instruct-v1:0
provider_agent: Mixed (rotating)
brand_agent: Mixed (rotating)
```

### New Recommended Assignments

```yaml
triage_agent: us.amazon.nova-pro-v1:0  # Keep (100% routing accuracy)
policy_agent: us.anthropic.claude-haiku-4-5-20251001-v1:0  # Change
provider_agent: us.meta.llama4-maverick-17b-instruct-v1:0  # Temporary
brand_agent: us.anthropic.claude-haiku-4-5-20251001-v1:0  # Standardize
```

### Rationale

| Agent | Model | Accuracy | Why This Model |
|-------|-------|----------|----------------|
| **Triage** | Nova Pro | 100% | Perfect routing, cost-effective |
| **Policy** | Haiku 4.5 | 80% | Best policy performance, fast, medium cost |
| **Provider** | Llama 4 | 40% | Best of bad options until prompt is fixed |
| **Brand** | Haiku 4.5 | 87% | Consistent quality, preserves information |

### Implementation Steps

**1. Update LaunchDarkly Configs**

```python
# Script to update all AI configs
import launchdarkly_api

def update_model_assignments():
    """Update model assignments in LaunchDarkly"""

    configs = {
        'policy_agent': {
            'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'
        },
        'brand_agent': {
            'model_id': 'us.anthropic.claude-haiku-4-5-20251001-v1:0'
        },
        'provider_agent': {
            'model_id': 'us.meta.llama4-maverick-17b-instruct-v1:0'
        }
        # triage_agent: no change
    }

    for config_key, settings in configs.items():
        # Update via LaunchDarkly API or UI
        print(f"Updating {config_key} to {settings['model_id']}")
```

**2. Cost Impact Analysis**

```python
# Estimated cost per 1000 queries
costs = {
    'Nova Pro': 0.50,
    'Llama 4 Maverick': 0.80,
    'Haiku 4.5': 1.20,
    'Sonnet 4': 4.50
}

# Current monthly cost (example: 10K queries/month)
current = (
    10000 * 0.0005  # Triage (Nova)
    + 4000 * 0.0008  # Policy (Llama)
    + 4000 * 1.50  # Provider (mixed)
    + 10000 * 0.80  # Brand (mixed)
) = ~$50/month

# New monthly cost
new = (
    10000 * 0.0005  # Triage (Nova - unchanged)
    + 4000 * 0.0012  # Policy (Haiku)
    + 4000 * 0.0008  # Provider (Llama)
    + 10000 * 0.0012  # Brand (Haiku)
) = ~$58/month

# Cost increase: +$8/month (+16%)
# Accuracy increase: +23.5 percentage points
# ROI: Excellent
```

**3. Monitor Performance**

```python
# Track these metrics after model change
metrics_to_monitor = {
    'accuracy_by_agent': ['policy_agent', 'brand_agent'],
    'response_time_p95': 'all',
    'cost_per_query': 'all',
    'token_usage': 'all'
}

# Alert if:
# - Accuracy drops > 5% from baseline
# - P95 latency increases > 30%
# - Cost per query increases > 25%
```

---

## RAG Improvements

### Phase 1: Document Chunking (Week 2-3)

#### Current State
```yaml
Document Lengths:
  Very Short (<500 chars): 49.9%
  Optimal (500-2000): 1.6%
  Too Long (>5000): 47.6%

Retrieval Scores:
  Mean: 0.586
  Excellent (≥0.8): 0%
  Poor (<0.6): 81.2%
```

#### Target State
```yaml
Document Lengths:
  Very Short (<500): <10%
  Optimal (500-2000): 80%+
  Too Long (>5000): 0%

Retrieval Scores:
  Mean: 0.65+
  Excellent (≥0.8): 20%+
  Poor (<0.6): <40%
```

#### Implementation

**Provider Document Chunking:**

```python
def chunk_provider_document(provider: dict) -> str:
    """
    Create optimized single chunk per provider
    Target: 800-1500 characters
    """
    chunk = f"""Provider: {provider['name']} {provider['credentials']}
Specialty: {provider['specialty']}
Practice: {provider['practice_name']}

Location:
{provider['address']}
{provider['city']}, {provider['state']} {provider['zip']}
Phone: {provider['phone']}

Network Information:
Accepted Plans: {', '.join(provider['accepted_plans'])}
Network Type: {provider['network_type']}
Provider ID: {provider['provider_id']}

Patient Information:
Accepting New Patients: {'Yes' if provider['accepting_new_patients'] else 'No'}
Languages Spoken: {', '.join(provider['languages'])}
Board Certified: {'Yes' if provider['board_certified'] else 'No'}
Years in Practice: {provider['years_practice']}

Patient Ratings:
Average Rating: {provider['rating']}/5.0
Total Reviews: {provider['review_count']}
"""
    return chunk.strip()

# Metadata for hybrid search
def create_provider_metadata(provider: dict) -> dict:
    """Create structured metadata for filtering"""
    return {
        'specialty': provider['specialty'],
        'city': provider['city'],
        'state': provider['state'],
        'zip_code': provider['zip'],
        'accepted_plans': provider['accepted_plans'],  # List
        'accepting_new_patients': provider['accepting_new_patients'],
        'provider_id': provider['provider_id'],
        'network_type': provider['network_type']
    }
```

**Policy Document Chunking:**

```python
def chunk_policy_document(policy: dict) -> list:
    """
    Create semantic chunks by benefit category
    Target: 800-1500 chars per chunk
    """
    chunks = []

    # Chunk 1: Plan Overview
    chunks.append({
        'content': f"""Plan Overview
Plan Name: {policy['plan_name']}
Plan ID: {policy['plan_id']}
Plan Type: {policy['plan_type']}

Coverage:
Member Type: {policy['coverage_type']}
Effective Date: {policy['effective_date']}
End Date: {policy['end_date']}

Annual Costs:
Deductible: {policy['deductible']}
Out-of-Pocket Maximum: {policy['oop_max']}
""",
        'metadata': {
            'plan_id': policy['plan_id'],
            'plan_type': policy['plan_type'],
            'category': 'overview'
        }
    })

    # Chunk 2: Copays
    chunks.append({
        'content': f"""Copays - {policy['plan_name']}

Office Visits:
Primary Care: {policy['copays']['primary_care']}
Specialist: {policy['copays']['specialist']}
Urgent Care: {policy['copays']['urgent_care']}

Diagnostic Services:
Lab Work: {policy['copays']['lab']}
X-Rays: {policy['copays']['xray']}
MRI/CT Scan: {policy['copays']['imaging']}
""",
        'metadata': {
            'plan_id': policy['plan_id'],
            'plan_type': policy['plan_type'],
            'category': 'copays'
        }
    })

    # Chunk 3: Preventive Care
    # Chunk 4: Prescription Drugs
    # Chunk 5: Specialist Care
    # etc.

    return chunks
```

**Re-indexing Script:**

```python
#!/usr/bin/env python3
"""
Re-chunk and re-index Bedrock Knowledge Base documents
"""
import boto3
import json
from typing import List, Dict

def reindex_knowledge_base():
    """Main re-indexing function"""

    # 1. Load existing documents
    original_providers = load_from_s3('providers.json')
    original_policies = load_from_s3('policies.json')

    # 2. Create new chunks
    provider_chunks = []
    for provider in original_providers:
        chunk_content = chunk_provider_document(provider)
        metadata = create_provider_metadata(provider)
        provider_chunks.append({
            'content': chunk_content,
            'metadata': metadata,
            'source': f"provider_{provider['provider_id']}"
        })

    policy_chunks = []
    for policy in original_policies:
        chunks = chunk_policy_document(policy)
        policy_chunks.extend(chunks)

    # 3. Validate chunk sizes
    validate_chunk_sizes(provider_chunks + policy_chunks)

    # 4. Upload to S3 (Bedrock KB source)
    upload_chunks_to_s3(provider_chunks, 'provider-kb-chunks/')
    upload_chunks_to_s3(policy_chunks, 'policy-kb-chunks/')

    # 5. Trigger Bedrock KB sync
    bedrock = boto3.client('bedrock-agent')
    bedrock.start_ingestion_job(
        knowledgeBaseId='RV4PHKDQA4...',  # Provider KB
        dataSourceId='...'
    )
    bedrock.start_ingestion_job(
        knowledgeBaseId='PHC7IW8FTM...',  # Policy KB
        dataSourceId='...'
    )

    print("✅ Re-indexing started. Check AWS console for progress.")

def validate_chunk_sizes(chunks: List[Dict]):
    """Ensure chunks are in optimal size range"""
    for i, chunk in enumerate(chunks):
        size = len(chunk['content'])
        if size < 500:
            print(f"⚠️  Chunk {i} too small: {size} chars")
        elif size > 2000:
            print(f"⚠️  Chunk {i} too large: {size} chars")
        # Target: 500-2000 chars

    sizes = [len(c['content']) for c in chunks]
    print(f"\nChunk Stats:")
    print(f"  Mean: {sum(sizes)/len(sizes):.0f} chars")
    print(f"  Min: {min(sizes)} chars")
    print(f"  Max: {max(sizes)} chars")
    print(f"  In range (500-2000): {sum(1 for s in sizes if 500 <= s <= 2000)/len(sizes)*100:.1f}%")

if __name__ == '__main__':
    reindex_knowledge_base()
```

### Phase 2: Hybrid Search (Week 3-4)

**Update Retrieval Logic:**

```python
def retrieve_providers_hybrid(
    query: str,
    specialty: str,
    city: str,
    state: str,
    plan_id: str,
    limit: int = 10
) -> List[Dict]:
    """
    Retrieve providers using hybrid search
    (semantic + metadata filtering)
    """
    import boto3

    bedrock_agent = boto3.client('bedrock-agent-runtime')

    # Construct optimized semantic query
    semantic_query = f"{specialty} specialist medical provider {city} {state}"

    # Metadata filters
    filter_conditions = {
        "andAll": [
            {
                "equals": {
                    "key": "specialty",
                    "value": specialty
                }
            },
            {
                "equals": {
                    "key": "city",
                    "value": city
                }
            },
            {
                "equals": {
                    "key": "state",
                    "value": state
                }
            },
            {
                "listContains": {
                    "key": "accepted_plans",
                    "value": plan_id
                }
            }
        ]
    }

    # Retrieve with hybrid search
    response = bedrock_agent.retrieve(
        knowledgeBaseId='RV4PHKDQA4...',
        retrievalQuery={'text': semantic_query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': limit,
                'overrideSearchType': 'HYBRID',  # Semantic + keyword
                'filter': filter_conditions
            }
        }
    )

    return response['retrievalResults']

# Expected improvement:
# - Retrieval scores: 0.586 → 0.75+
# - False negatives: -70%
# - Precision: +40%
```

---

## Validation Layer

### Purpose
Catch fabrications and RAG violations before responses reach users.

### Implementation

```python
class RAGFidelityValidator:
    """Validates specialist output against RAG documents"""

    def __init__(self):
        self.violation_types = {
            'fabricated_provider': self._check_provider_fabrication,
            'fabricated_cost': self._check_cost_fabrication,
            'specialty_mismatch': self._check_specialty_match,
            'plan_type_mismatch': self._check_plan_type
        }

    def validate(
        self,
        specialist_response: str,
        rag_documents: List[Dict],
        user_context: Dict
    ) -> tuple[bool, List[str]]:
        """
        Validate specialist response
        Returns: (is_valid, issues_found)
        """
        issues = []

        for check_name, check_func in self.violation_types.items():
            violations = check_func(specialist_response, rag_documents, user_context)
            if violations:
                issues.extend(violations)

        is_valid = len(issues) == 0
        return is_valid, issues

    def _check_provider_fabrication(self, response, rag_docs, context):
        """Check if provider names/details are in RAG"""
        issues = []

        # Extract provider names from response
        provider_names = self._extract_provider_names(response)

        # Extract provider names from RAG
        rag_provider_names = set()
        for doc in rag_documents:
            rag_provider_names.add(doc.get('provider_name', ''))

        # Check each response name against RAG
        for name in provider_names:
            if name not in rag_provider_names:
                issues.append(f"Provider '{name}' not found in RAG documents")

        return issues

    def _check_cost_fabrication(self, response, rag_docs, context):
        """Check if dollar amounts are in RAG"""
        import re
        issues = []

        # Find all dollar amounts in response
        dollar_amounts = re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', response)

        # Extract all amounts from RAG
        rag_text = ' '.join([doc.get('content', '') for doc in rag_docs])
        rag_amounts = set(re.findall(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', rag_text))

        # Check each amount
        for amount in dollar_amounts:
            if amount not in rag_amounts:
                issues.append(f"Dollar amount '{amount}' not found in RAG documents")

        return issues

    def _check_specialty_match(self, response, rag_docs, context):
        """Check if provider specialties match RAG"""
        issues = []

        # Extract (provider, specialty) pairs from response
        response_pairs = self._extract_provider_specialty_pairs(response)

        # Build truth map from RAG
        rag_specialty_map = {}
        for doc in rag_docs:
            provider = doc.get('provider_name')
            specialty = doc.get('specialty')
            if provider and specialty:
                rag_specialty_map[provider] = specialty

        # Validate each pair
        for provider, claimed_specialty in response_pairs:
            if provider in rag_specialty_map:
                actual_specialty = rag_specialty_map[provider]
                if claimed_specialty != actual_specialty:
                    issues.append(
                        f"Specialty mismatch for {provider}: "
                        f"claimed '{claimed_specialty}', "
                        f"RAG shows '{actual_specialty}'"
                    )

        return issues

    def _check_plan_type(self, response, rag_docs, context):
        """Check if response uses correct plan type"""
        issues = []

        user_plan_type = context.get('coverage_type', '')

        # Check if RAG docs match user's plan
        for doc in rag_docs:
            doc_plan = doc.get('plan_id', '')
            if user_plan_type not in doc_plan:
                issues.append(
                    f"RAG document plan '{doc_plan}' doesn't match "
                    f"user plan '{user_plan_type}'"
                )

        return issues

# Integration point
def generate_response_with_validation(query, context):
    """Generate and validate response"""

    # Step 1: Get specialist response
    specialist_response, rag_docs = specialist_agent(query, context)

    # Step 2: Validate
    validator = RAGFidelityValidator()
    is_valid, issues = validator.validate(specialist_response, rag_docs, context)

    # Step 3: Handle validation
    if not is_valid:
        logger.warning(f"Validation failed: {issues}")

        # Option A: Regenerate with stricter prompt
        specialist_response = specialist_agent_strict(query, context, issues)

        # Option B: Return error to user
        # return "I need to verify some information. Please contact Member Services."

    # Step 4: Brand voice (only if validated)
    final_response = brand_voice_agent(specialist_response, context)

    return final_response
```

---

## Monitoring & Alerting

### CloudWatch Dashboards

```python
# Create custom metrics dashboard
import boto3

cloudwatch = boto3.client('cloudwatch')

def publish_accuracy_metric(agent_type: str, accuracy: float):
    """Publish accuracy metric to CloudWatch"""
    cloudwatch.put_metric_data(
        Namespace='ToggleHealth/AI',
        MetricData=[
            {
                'MetricName': 'Accuracy',
                'Dimensions': [
                    {'Name': 'AgentType', 'Value': agent_type}
                ],
                'Value': accuracy,
                'Unit': 'Percent'
            }
        ]
    )

def publish_rag_score_metric(score: float, doc_count: int):
    """Publish RAG quality metrics"""
    cloudwatch.put_metric_data(
        Namespace='ToggleHealth/AI',
        MetricData=[
            {
                'MetricName': 'RAGRetrievalScore',
                'Value': score,
                'Unit': 'None'
            },
            {
                'MetricName': 'RAGDocumentCount',
                'Value': doc_count,
                'Unit': 'Count'
            }
        ]
    )
```

### Alert Configuration

```yaml
# CloudWatch Alarms
alarms:
  - name: ProviderAccuracyCritical
    metric: Accuracy
    dimension: AgentType=provider_specialist
    threshold: 65
    comparison: LessThanThreshold
    evaluation_periods: 2
    severity: CRITICAL
    action: page_oncall

  - name: PolicyAccuracyWarning
    metric: Accuracy
    dimension: AgentType=policy_specialist
    threshold: 80
    comparison: LessThanThreshold
    evaluation_periods: 3
    severity: WARNING
    action: slack_alert

  - name: RAGScoreDegraded
    metric: RAGRetrievalScore
    threshold: 0.6
    comparison: LessThanThreshold
    evaluation_periods: 5
    severity: WARNING
    action: email_team

  - name: FalseNegativeRateHigh
    metric: FalseNegativeRate
    threshold: 15
    comparison: GreaterThanThreshold
    evaluation_periods: 2
    severity: CRITICAL
    action: page_oncall
```

---

## Testing & Validation

### Automated Test Suite

```bash
# Run full test suite (150 iterations)
python run_test_suite.py --iterations 150 --env staging

# Run quick test (10 iterations)
python run_test_suite.py --iterations 10 --env staging --quick

# Run specific category
python run_test_suite.py --category provider_search --iterations 50

# Compare before/after
python run_test_suite.py --baseline before --compare after
```

### Success Criteria

**Week 1 (Prompt Fixes):**
```yaml
Provider Accuracy: ≥75%
Policy Accuracy: ≥85%
Overall Accuracy: ≥80%
False Negative Rate: <10%
Specialty Mismatches: 0
```

**Week 4 (Full Implementation):**
```yaml
Provider Accuracy: ≥85%
Policy Accuracy: ≥90%
Overall Accuracy: ≥87%
RAG Retrieval Score: ≥0.75
Hallucination Rate: <2%
```

---

## Deployment Strategy

### Gradual Rollout

```python
# Week 1: Deploy to staging
deploy_to_environment('staging', {
    'provider_prompt': 'new',
    'traffic_percentage': 100
})

# Week 1 end: Deploy to 10% production
deploy_to_environment('production', {
    'provider_prompt': 'new',
    'traffic_percentage': 10
})

# Week 2: Increase to 25%
if accuracy_meets_threshold(threshold=0.75):
    update_traffic_percentage('production', 25)

# Week 3: Increase to 50%
if accuracy_meets_threshold(threshold=0.78):
    update_traffic_percentage('production', 50)

# Week 4: Full rollout
if accuracy_meets_threshold(threshold=0.80):
    update_traffic_percentage('production', 100)
```

### Rollback Plan

```python
def rollback_if_necessary():
    """Automatic rollback on accuracy drop"""

    current_accuracy = get_current_accuracy('production')
    baseline_accuracy = get_baseline_accuracy()

    if current_accuracy < baseline_accuracy - 0.05:  # 5% drop
        logger.critical(f"Accuracy dropped to {current_accuracy}, rolling back")
        revert_to_previous_config()
        alert_team("Automatic rollback triggered")
```

---

## Appendices

### A. Test Queries

High-priority test queries (previously failed):
```python
test_queries = [
    # Provider searches
    {"query": "Find me an endocrinologist in Seattle", "expected_accuracy": 0.85},
    {"query": "Find me a podiatrist in Phoenix", "expected_accuracy": 0.85},
    {"query": "Find me a bariatric surgeon in Houston", "expected_accuracy": 0.85},

    # Policy questions
    {"query": "What's the copay for X-rays?", "expected_accuracy": 0.90},
    {"query": "Do you cover diabetic supplies?", "expected_accuracy": 0.90},
    {"query": "Is my insulin covered?", "expected_accuracy": 0.90},
]
```

### B. Useful Commands

```bash
# Sync prompts from LaunchDarkly
python fetch_ai_config_prompts.py

# Run analysis on test results
python analyze_test_results.py

# Analyze RAG mechanics
python analyze_rag_mechanics.py

# Generate reports
python deep_failure_analysis.py

# Re-index knowledge base
python reindex_kb.py --kb-id RV4PHKDQA4... --dry-run
```

### C. Contact & Resources

**Team Contacts:**
- Engineering Lead: [Engineering Manager]
- AI/ML Lead: [ML Engineer]
- DevOps: [DevOps Team]
- Product: [Product Manager]

**Resources:**
- LaunchDarkly Dashboard: https://app.launchdarkly.com
- AWS Bedrock Console: https://console.aws.amazon.com/bedrock
- Test Results: `/home/user/policy_agent/test_results/`
- Documentation: `/home/user/policy_agent/data/markdown/`

---

**Document Version:** 1.0
**Last Updated:** November 13, 2025
**Next Review:** After Week 4 implementation
