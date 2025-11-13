# RAG System Improvement Guide

**ToggleHealth AI System - Bedrock Knowledge Base Optimization**
**Version:** 1.0 | **Date:** November 13, 2025

---

## Executive Summary

The RAG (Retrieval-Augmented Generation) system is retrieving documents successfully (98.5% success rate), but retrieval quality is critically low. This guide provides step-by-step instructions to improve RAG performance from current 0.586 mean score to 0.75+ target.

### Current State

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Mean Retrieval Score** | 0.586 | 0.75+ | 🔴 |
| **Excellent Docs (≥0.8)** | 0% | 20%+ | 🔴 |
| **Poor Docs (<0.6)** | 81.2% | <20% | 🔴 |
| **Optimal Chunk Size** | 1.6% | 80%+ | 🔴 |
| **Empty Results** | 1.5% | <1% | 🟡 |

### Impact

Low RAG scores compound prompt issues:
- Models receive low-confidence documents (0.586 vs 0.75+ ideal)
- Large documents (10,166 chars) overwhelm model context windows
- Specialty mismatches occur from parsing multi-provider documents
- False negatives increase when models can't find info in large docs

---

## Problem Analysis

### Issue 1: Poor Document Chunking

**Evidence:**
```
Document Length Distribution (431 documents):
Very Short (<500 chars):   215 docs (49.9%) 🔴
Optimal (500-2000 chars):    7 docs ( 1.6%) 🔴
Too Long (>5000 chars):    205 docs (47.6%) 🔴

Mean: 3,284 chars
Median: 790 chars (bimodal distribution)
Min: 31 chars (way too small!)
Max: 10,166 chars (way too large!)
```

**Why This Matters:**
- **Very short docs** (31-500 chars) lack semantic context for embeddings
- **Very long docs** (>5000 chars) contain multiple entities, making extraction hard
- **Optimal range** (500-2000 chars) provides enough context without overwhelming

**Real Example (Test Q007):**
```
Query: "Find me an endocrinologist in Seattle"
Retrieved: 3 docs totaling 18,428 characters
- Doc 1: 6,429 chars (multiple providers)
- Doc 2: 6,024 chars
- Doc 3: 5,975 chars

Problem: Dr. Cohen (Oncologist) and Dr. O'Brien (Endocrinologist)
         both in same large document
Result: Model confused specialties → 0.15 accuracy
```

### Issue 2: Weak Semantic Matching

**Evidence:**
```
Retrieval Score Distribution (Top Docs):
Mean:   0.586
Median: 0.589
Max:    0.687 (even best retrieval is poor)
StdDev: 0.034 (very consistent = systemically poor)

Industry Standard:
Mean:   0.75+
Excellent: ≥0.8
```

**Possible Root Causes:**
1. Embedding model not optimized for medical terminology
2. Query construction not aligned with document structure
3. No metadata filtering (pure semantic only)
4. Documents embedded without domain context

### Issue 3: No Hybrid Search

**Current Approach:** Pure semantic search

**Query Example:**
```
"Find me an endocrinologist in Seattle (specialty: endocrinol..."
```

**Problem:** Relies 100% on semantic embeddings, no structured filtering

**Better Approach:** Hybrid (semantic + metadata)
```python
Semantic query: "endocrinologist medical specialist Seattle"
+ Metadata filters: {
    specialty: "Endocrinology",
    city: "Seattle",
    accepted_plans: ["TH-HMO-GOLD-2024"]
}
```

**Expected Impact:** Scores 0.586 → 0.75+

---

## Solution Roadmap

### Phase 1: Document Re-Chunking (Week 2-3)

**Goal:** Transform document size distribution to 80%+ in optimal range

**Priority:** HIGH (foundational for all other improvements)

#### Step 1: Analyze Current Documents

```python
#!/usr/bin/env python3
"""
Analyze current document structure
"""
import boto3
import json

def analyze_current_kb():
    """Pull sample docs from S3/Bedrock to analyze structure"""

    s3 = boto3.client('s3')

    # Download current provider documents
    response = s3.get_object(
        Bucket='your-bedrock-kb-bucket',
        Key='providers/providers.json'
    )
    providers = json.loads(response['Body'].read())

    # Analyze structure
    for i, provider in enumerate(providers[:5]):  # Sample
        print(f"\nProvider {i+1}:")
        print(f"  Keys: {provider.keys()}")
        print(f"  Name: {provider.get('name')}")
        print(f"  Specialty: {provider.get('specialty')}")
        print(f"  Has multiple providers: {len(provider.get('providers', [])) > 1}")

    # Check if documents are already chunked or need chunking
    print(f"\nTotal providers: {len(providers)}")
    print("Structure type: [Document-per-provider or Multi-provider-per-doc]")

analyze_current_kb()
```

#### Step 2: Design Chunking Strategy

**Provider Documents (One Provider Per Chunk):**

```python
def create_provider_chunk(provider: dict) -> dict:
    """
    Create single optimized chunk per provider
    Target: 800-1500 characters
    """

    # Build content (plain text for semantic search)
    content = f"""Provider Information

Name: {provider['name']} {provider['credentials']}
Specialty: {provider['specialty']}
Practice: {provider['practice_name']}

Location
{provider['address']}
{provider['city']}, {provider['state']} {provider['zip']}
Phone: {provider['phone']}

Network Information
Provider ID: {provider['provider_id']}
Accepted Insurance Plans: {', '.join(provider['accepted_plans'])}
Network Type: {provider['network_type']}
In-Network Status: {'In-Network' if provider['in_network'] else 'Out-of-Network'}

Provider Details
Accepting New Patients: {'Yes' if provider['accepting_new_patients'] else 'No'}
Languages Spoken: {', '.join(provider['languages'])}
Board Certified: {'Yes' if provider['board_certified'] else 'No'}
Years in Practice: {provider['years_practice']}

Patient Reviews
Average Rating: {provider['rating']}/5.0
Total Reviews: {provider['review_count']}

Medical Specializations
Primary Specialty: {provider['specialty']}
{f"Subspecialties: {', '.join(provider['subspecialties'])}" if provider.get('subspecialties') else ''}
"""

    # Build metadata (for filtering)
    metadata = {
        'provider_id': provider['provider_id'],
        'specialty': provider['specialty'],  # CRITICAL for filtering
        'city': provider['city'],
        'state': provider['state'],
        'zip_code': provider['zip'],
        'accepted_plans': provider['accepted_plans'],  # List
        'in_network': provider['in_network'],
        'accepting_new_patients': provider['accepting_new_patients'],
        'rating': provider['rating'],
        'network_type': provider['network_type'],
        'board_certified': provider['board_certified']
    }

    return {
        'content': content.strip(),
        'metadata': metadata,
        'source': f"provider_{provider['provider_id']}"
    }

# Validate chunk size
chunk = create_provider_chunk(sample_provider)
length = len(chunk['content'])
print(f"Chunk length: {length} chars")
assert 500 <= length <= 2000, f"Chunk size {length} out of range!"
```

**Policy Documents (One Benefit Category Per Chunk):**

```python
def create_policy_chunks(policy: dict) -> list:
    """
    Create multiple chunks per policy (by benefit category)
    Target: 800-1500 chars per chunk
    """
    chunks = []
    base_metadata = {
        'plan_id': policy['plan_id'],
        'plan_type': policy['plan_type'],  # HMO, PPO, HDHP
        'plan_name': policy['plan_name']
    }

    # Chunk 1: Plan Overview
    chunks.append({
        'content': f"""Health Insurance Plan Overview

Plan Name: {policy['plan_name']}
Plan ID: {policy['plan_id']}
Plan Type: {policy['plan_type']}

Coverage Details
Coverage Type: {policy['coverage_type']}
Effective Date: {policy['effective_date']}
End Date: {policy['end_date']}

Annual Financial Information
Annual Deductible: {policy['deductible']}
Out-of-Pocket Maximum: {policy['oop_max']}
Premium: {policy['premium']}
""",
        'metadata': {**base_metadata, 'category': 'overview'},
        'source': f"{policy['plan_id']}_overview"
    })

    # Chunk 2: Copays and Cost-Sharing
    chunks.append({
        'content': f"""Copays and Cost-Sharing - {policy['plan_name']}

Office Visit Copays
Primary Care Physician: {policy['copays']['primary_care']}
Specialist Visit: {policy['copays']['specialist']}
Urgent Care Visit: {policy['copays']['urgent_care']}
Emergency Room: {policy['copays']['emergency_room']}

Diagnostic Services Copays
Laboratory Services: {policy['copays']['lab']}
X-Ray Imaging: {policy['copays']['xray']}
Advanced Imaging (MRI/CT): {policy['copays']['imaging']}

Therapy Services Copays
Physical Therapy: {policy['copays']['physical_therapy']}
Occupational Therapy: {policy['copays']['occupational_therapy']}
Mental Health Therapy: {policy['copays']['mental_health']}

Coinsurance
After meeting your deductible, you pay {policy['coinsurance']} of covered services.
""",
        'metadata': {**base_metadata, 'category': 'copays'},
        'source': f"{policy['plan_id']}_copays"
    })

    # Chunk 3: Preventive Care
    chunks.append({
        'content': f"""Preventive Care Coverage - {policy['plan_name']}

Preventive Services (No Copay)
Annual Physical Exam: Covered at 100%, no copay
Immunizations: Covered at 100%, no copay
Cancer Screenings: Covered at 100%, no copay
Well-Child Visits: Covered at 100%, no copay

Specific Preventive Services
{format_preventive_services(policy['preventive_care'])}

Important Note
Preventive care must be from in-network providers to receive 100% coverage.
""",
        'metadata': {**base_metadata, 'category': 'preventive_care'},
        'source': f"{policy['plan_id']}_preventive"
    })

    # Chunk 4: Prescription Drug Coverage (if available)
    if policy.get('prescription_coverage'):
        chunks.append({
            'content': f"""Prescription Drug Coverage - {policy['plan_name']}

Pharmacy Copays
Tier 1 (Generic): {policy['prescription_coverage']['tier1']}
Tier 2 (Preferred Brand): {policy['prescription_coverage']['tier2']}
Tier 3 (Non-Preferred Brand): {policy['prescription_coverage']['tier3']}
Tier 4 (Specialty Drugs): {policy['prescription_coverage']['tier4']}

Pharmacy Options
Retail Pharmacy: 30-day supply at above copays
Mail Order Pharmacy: 90-day supply (may have different copays)

Coverage Rules
{format_prescription_rules(policy['prescription_coverage'])}
""",
            'metadata': {**base_metadata, 'category': 'prescription'},
            'source': f"{policy['plan_id']}_prescription"
        })

    # Chunk 5: Specialist and Hospital Care
    # Chunk 6: Special Programs
    # etc.

    return chunks

# Validate all chunks
for i, chunk in enumerate(chunks):
    length = len(chunk['content'])
    print(f"Chunk {i+1}: {length} chars, category: {chunk['metadata']['category']}")
    assert 500 <= length <= 2000, f"Chunk {i+1} size {length} out of range!"
```

#### Step 3: Generate New Chunks

```python
#!/usr/bin/env python3
"""
Re-chunk all documents for Bedrock KB
"""
import boto3
import json
from typing import List, Dict

def reindex_knowledge_base():
    """Main re-indexing function"""

    print("Starting re-chunking process...")

    # 1. Load source data
    providers = load_providers_from_source()  # Your data source
    policies = load_policies_from_source()

    print(f"Loaded {len(providers)} providers, {len(policies)} policies")

    # 2. Create new chunks
    print("\nCreating provider chunks...")
    provider_chunks = []
    for provider in providers:
        chunk = create_provider_chunk(provider)
        provider_chunks.append(chunk)

    print(f"Created {len(provider_chunks)} provider chunks")

    print("\nCreating policy chunks...")
    policy_chunks = []
    for policy in policies:
        chunks = create_policy_chunks(policy)
        policy_chunks.extend(chunks)

    print(f"Created {len(policy_chunks)} policy chunks")

    # 3. Validate chunk quality
    print("\nValidating chunks...")
    all_chunks = provider_chunks + policy_chunks
    validate_chunk_distribution(all_chunks)

    # 4. Prepare for upload
    print("\nPreparing for upload...")
    prepare_bedrock_documents(provider_chunks, 'providers/')
    prepare_bedrock_documents(policy_chunks, 'policies/')

    # 5. Upload to S3
    print("\nUploading to S3...")
    upload_to_s3(provider_chunks, bucket='your-kb-bucket', prefix='providers/')
    upload_to_s3(policy_chunks, bucket='your-kb-bucket', prefix='policies/')

    # 6. Trigger Bedrock KB sync
    print("\nTriggering Bedrock KB ingestion...")
    trigger_kb_sync('RV4PHKDQA4...')  # Provider KB
    trigger_kb_sync('PHC7IW8FTM...')  # Policy KB

    print("\n✅ Re-chunking complete! Monitor AWS console for sync status.")

def validate_chunk_distribution(chunks: List[Dict]):
    """Validate chunk sizes meet targets"""
    sizes = [len(c['content']) for c in chunks]

    very_short = sum(1 for s in sizes if s < 500)
    optimal = sum(1 for s in sizes if 500 <= s <= 2000)
    too_long = sum(1 for s in sizes if s > 2000)

    total = len(sizes)

    print("\nChunk Size Distribution:")
    print(f"  Very Short (<500):     {very_short:4d} ({very_short/total*100:5.1f}%)")
    print(f"  Optimal (500-2000):    {optimal:4d} ({optimal/total*100:5.1f}%) ✅")
    print(f"  Too Long (>2000):      {too_long:4d} ({too_long/total*100:5.1f}%)")
    print(f"  Mean: {sum(sizes)/len(sizes):.0f} chars")
    print(f"  Median: {sorted(sizes)[len(sizes)//2]:.0f} chars")

    # Assert quality
    assert optimal/total >= 0.8, f"Only {optimal/total*100:.1f}% optimal (need 80%+)"
    print("\n✅ Chunk distribution meets targets!")

def prepare_bedrock_documents(chunks: List[Dict], prefix: str):
    """Format chunks for Bedrock KB ingestion"""
    documents = []
    for chunk in chunks:
        # Bedrock KB document format
        doc = {
            'documentId': chunk['source'],
            'content': {
                'text': chunk['content']
            },
            'metadata': chunk['metadata']
        }
        documents.append(doc)
    return documents

def trigger_kb_sync(kb_id: str):
    """Trigger Bedrock KB ingestion job"""
    bedrock_agent = boto3.client('bedrock-agent')

    response = bedrock_agent.start_ingestion_job(
        knowledgeBaseId=kb_id,
        dataSourceId='...',  # Your data source ID
        description='Re-chunked documents for optimal retrieval'
    )

    job_id = response['ingestionJob']['ingestionJobId']
    print(f"  Started ingestion job: {job_id}")
    print(f"  Monitor at: https://console.aws.amazon.com/bedrock/knowledge-bases/{kb_id}")

if __name__ == '__main__':
    reindex_knowledge_base()
```

#### Step 4: Test New Chunks

```bash
# After re-indexing completes (check AWS console)
python run_test_suite.py --iterations 50 --env staging

# Expected improvements:
# - Mean RAG score: 0.586 → 0.65+
# - Optimal chunk %: 1.6% → 80%+
# - Provider accuracy: 40% → 65%+ (chunk improvement alone)
```

---

### Phase 2: Implement Hybrid Search (Week 3-4)

**Goal:** Combine semantic search with metadata filtering

**Priority:** HIGH (biggest score improvement: +0.15)

#### Update Retrieval Logic

**Current (Pure Semantic):**
```python
def retrieve_providers(query: str, limit: int = 5):
    """Current approach - semantic only"""
    bedrock = boto3.client('bedrock-agent-runtime')

    response = bedrock.retrieve(
        knowledgeBaseId='RV4PHKDQA4...',
        retrievalQuery={'text': query},  # Natural language only
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': limit
            }
        }
    )
    return response['retrievalResults']
```

**New (Hybrid - Semantic + Metadata):**
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
    New approach - hybrid search
    Semantic search + metadata filtering
    """
    bedrock = boto3.client('bedrock-agent-runtime')

    # Step 1: Optimize semantic query
    # Remove location/filters (handled by metadata)
    semantic_query = f"{specialty} specialist medical doctor physician"

    # Step 2: Build metadata filters
    metadata_filter = {
        "andAll": [  # All conditions must match
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
                "listContains": {  # For array fields
                    "key": "accepted_plans",
                    "value": plan_id
                }
            },
            {
                "equals": {
                    "key": "accepting_new_patients",
                    "value": True
                }
            }
        ]
    }

    # Step 3: Retrieve with hybrid search
    response = bedrock.retrieve(
        knowledgeBaseId='RV4PHKDQA4...',
        retrievalQuery={'text': semantic_query},
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': limit,
                'overrideSearchType': 'HYBRID',  # Enable hybrid!
                'filter': metadata_filter  # Apply filters
            }
        }
    )

    results = response['retrievalResults']

    print(f"Retrieved {len(results)} results")
    if results:
        print(f"Top score: {results[0]['score']:.3f}")

    return results

# Expected improvement:
# - Scores: 0.65 → 0.75+
# - Precision: +40% (only relevant docs)
# - False negatives: -50% (better recall)
```

#### Handle Edge Cases

```python
def retrieve_with_fallback(
    query: str,
    specialty: str,
    city: str,
    state: str,
    plan_id: str
) -> tuple[List[Dict], str]:
    """
    Retrieve with progressive fallback
    1. Try: city + state + specialty + plan
    2. Fallback: state + specialty + plan
    3. Fallback: specialty + plan only
    """

    # Try 1: Full filters
    results = retrieve_providers_hybrid(query, specialty, city, state, plan_id)

    if len(results) >= 3:
        return results, 'full_match'

    # Fallback 1: Remove city, keep state
    print(f"No results in {city}, expanding to {state}")
    results = retrieve_providers_hybrid(query, specialty, None, state, plan_id)

    if len(results) >= 3:
        return results, 'state_match'

    # Fallback 2: Remove location, keep specialty + plan
    print(f"No results in {state}, searching nationwide")
    results = retrieve_providers_hybrid(query, specialty, None, None, plan_id)

    if len(results) >= 1:
        return results, 'nationwide_match'

    # No results found
    return [], 'no_match'
```

---

### Phase 3: Query Optimization (Week 4)

**Goal:** Improve query construction for better semantic matching

#### Add Query Preprocessing

```python
def preprocess_query(
    user_query: str,
    query_type: str,
    context: dict
) -> str:
    """
    Optimize queries before RAG retrieval
    """

    if query_type == 'provider_search':
        # Extract entities
        specialty = extract_specialty(user_query)
        location = extract_location(user_query)

        # Add medical terminology context
        specialty_terms = get_specialty_terms(specialty)

        # Build optimized query
        optimized = f"{' '.join(specialty_terms)} medical doctor specialist physician"

        return optimized

    elif query_type == 'policy_question':
        # Extract benefit type
        benefit = extract_benefit_type(user_query)

        # Add insurance terminology
        optimized = f"{benefit} coverage insurance benefits copay deductible plan"

        return optimized

    return user_query

# Specialty term expansion
SPECIALTY_TERMS = {
    'endocrinologist': [
        'endocrinologist', 'endocrinology',
        'hormone specialist', 'diabetes specialist',
        'thyroid specialist', 'metabolic specialist'
    ],
    'cardiologist': [
        'cardiologist', 'cardiology',
        'heart specialist', 'cardiovascular specialist',
        'heart doctor'
    ],
    # etc.
}

def get_specialty_terms(specialty: str) -> List[str]:
    """Get expanded terms for specialty"""
    specialty_lower = specialty.lower()
    for key, terms in SPECIALTY_TERMS.items():
        if key in specialty_lower:
            return terms
    return [specialty]  # Default to original
```

---

## Expected Outcomes

### Retrieval Score Improvements

| Phase | Intervention | Mean Score | Excellent (≥0.8) | Poor (<0.6) |
|-------|--------------|------------|------------------|-------------|
| **Baseline** | Current state | 0.586 | 0% | 81.2% |
| **Phase 1** | Re-chunking | 0.650 | 15% | 45% |
| **Phase 2** | Hybrid search | 0.750 | 35% | 15% |
| **Phase 3** | Query optimization | 0.780 | 45% | 10% |

### End-to-End System Impact

| Metric | Baseline | + Prompts | + RAG Phase 1 | + RAG Phase 2 | Target |
|--------|----------|-----------|---------------|---------------|--------|
| Provider Accuracy | 40.1% | 75% | 78% | 85% | 85%+ |
| Policy Accuracy | 74.6% | 85% | 88% | 90% | 90%+ |
| Overall Accuracy | 56.5% | 80% | 83% | 87% | 87%+ |

**Key Insight:** RAG improvements add +7% accuracy on top of prompt fixes

---

## Monitoring RAG Quality

### Metrics to Track

```python
# Add to monitoring dashboard
rag_metrics = {
    # Retrieval quality
    'retrieval_score_mean': 0.650,
    'retrieval_score_p50': 0.645,
    'retrieval_score_p95': 0.720,

    # Document quality
    'chunk_size_mean': 1250,
    'chunk_size_optimal_pct': 85.0,

    # Result quality
    'empty_result_rate': 0.005,
    'low_score_rate': 0.30,  # % scoring <0.6

    # Performance
    'retrieval_latency_p95': 850,  # ms
    'documents_per_query': 5.2
}

# Alert conditions
alerts = {
    'retrieval_score_mean < 0.6': 'CRITICAL',
    'empty_result_rate > 0.05': 'CRITICAL',
    'chunk_size_optimal_pct < 0.7': 'WARNING',
    'retrieval_latency_p95 > 2000': 'WARNING'
}
```

### Validation Queries

Test these specific queries weekly:

```python
validation_queries = [
    # Previously failed (should now succeed)
    {
        'query': 'Find me an endocrinologist in Seattle',
        'expected_score': 0.75,
        'expected_results': 1  # Dr. O'Brien only (right specialty)
    },
    {
        'query': 'Find me a podiatrist in Phoenix',
        'expected_score': 0.80,
        'expected_results': 2  # Should find podiatrists
    },

    # Edge cases
    {
        'query': 'Find me a bariatric surgeon in Houston',
        'expected_score': 0.75,
        'expected_results': 1
    }
]
```

---

## Common Issues & Troubleshooting

### Issue: Scores Still Low After Re-Chunking

**Symptoms:**
- Re-chunked documents
- Chunk sizes in optimal range
- But scores still <0.65

**Possible Causes:**
1. Embedding model not suitable for medical domain
2. Documents not re-indexed properly
3. Metadata not properly formatted

**Solutions:**
```bash
# Check if KB sync completed
aws bedrock-agent get-ingestion-job \
  --knowledge-base-id RV4PHKDQA4... \
  --data-source-id ... \
  --ingestion-job-id ...

# Verify document count increased (more chunks)
aws bedrock-agent list-data-sources \
  --knowledge-base-id RV4PHKDQA4...

# Consider upgrading embedding model
# (if supported by your Bedrock KB configuration)
```

### Issue: Hybrid Search Returns No Results

**Symptoms:**
- Metadata filters too restrictive
- Empty results even when providers exist

**Solutions:**
```python
# Log filter conditions
print(f"Filters: {json.dumps(metadata_filter, indent=2)}")

# Try progressive fallback (remove filters one by one)
# 1. Try all filters
# 2. Remove city filter
# 3. Remove state filter
# 4. Keep only specialty + plan

# Validate metadata values
# Ensure exact string matching (case-sensitive!)
```

### Issue: Latency Increased

**Symptoms:**
- Retrieval taking >2 seconds
- Timeout errors

**Solutions:**
```python
# Reduce number of results
numberOfResults = 5  # Instead of 15

# Use parallel retrieval for multiple queries
import asyncio

async def retrieve_parallel(queries):
    tasks = [retrieve_async(q) for q in queries]
    return await asyncio.gather(*tasks)

# Enable caching for common queries
from functools import lru_cache

@lru_cache(maxsize=1000)
def retrieve_cached(query_hash):
    return retrieve(query)
```

---

## Timeline & Effort

### Week 2-3: Re-Chunking
- **Effort:** 3-4 days engineering
- **Tasks:**
  - Analyze current docs (0.5 days)
  - Design chunking strategy (0.5 days)
  - Implement chunking scripts (1 day)
  - Generate and validate chunks (0.5 days)
  - Upload and re-index (0.5 days)
  - Test and validate (1 day)

### Week 3-4: Hybrid Search
- **Effort:** 5-7 days engineering
- **Tasks:**
  - Update metadata schema (1 day)
  - Implement hybrid retrieval (2 days)
  - Add fallback logic (1 day)
  - Test and validate (1-2 days)
  - Deploy and monitor (1 day)

### Week 4: Query Optimization
- **Effort:** 2-3 days engineering
- **Tasks:**
  - Build term expansion dictionaries (1 day)
  - Implement preprocessing (1 day)
  - Test and validate (0.5-1 day)

**Total:** ~10-14 days engineering effort over 3 weeks

---

## Success Criteria

### Phase 1 Complete (Re-Chunking)
- ✅ Chunk size optimal: 80%+
- ✅ Mean retrieval score: ≥0.65
- ✅ Provider accuracy: ≥65%

### Phase 2 Complete (Hybrid Search)
- ✅ Mean retrieval score: ≥0.75
- ✅ Excellent docs (≥0.8): ≥35%
- ✅ Provider accuracy: ≥80%

### Phase 3 Complete (Full System)
- ✅ Mean retrieval score: ≥0.78
- ✅ Provider accuracy: ≥85%
- ✅ Overall system accuracy: ≥87%

---

## Resources

### Documentation
- [AWS Bedrock KB Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Hybrid Search Guide](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-test-config.html)
- [Metadata Filtering](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-chunking-parsing.html)

### Tools
- Chunking scripts: `/scripts/reindex_kb.py`
- Analysis tools: `analyze_rag_mechanics.py`
- Test suite: `run_test_suite.py --rag-analysis`

### Support
- RAG Issues: [Engineering Lead]
- AWS Bedrock: [DevOps Team]
- Testing: [QA Lead]

---

**Last Updated:** November 13, 2025
**Next Review:** After Phase 2 completion
**Document Owner:** AI/ML Engineering Team
