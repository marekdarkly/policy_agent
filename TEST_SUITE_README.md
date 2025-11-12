# Automated Agent Test Suite

## Overview

Comprehensive testing framework for the ToggleHealth multi-agent system that runs full agent circuits with automated evaluation.

## What It Does

The test suite performs **end-to-end testing** of the entire agent system:

```
Initialize → Triage → Specialist → Brand Voice → Evaluate → Terminate
```

Each test iteration is a **complete circuit** that:
- ✅ Uses real LaunchDarkly AI Configs
- ✅ Invokes real Bedrock models
- ✅ Performs real RAG retrieval
- ✅ Runs real G-Eval judge evaluation
- ✅ Tracks all metrics to LaunchDarkly
- ✅ Generates OpenTelemetry traces

**This is NOT a mock test - it's the real system.**

---

## Quick Start

### Run Full Test Suite (50 iterations)
```bash
make test-suite
```

### Run Quick Test (5 iterations)
```bash
make test-quick
```

### Diagnose Chunk Sizes
```bash
make test-chunks
```

---

## Test Dataset

**Location**: `test_data/qa_dataset.json`

**Contents**:
- 100 questions across 6 categories
- Policy coverage (deductibles, copays, benefits)
- Provider search (multiple cities, specialties)
- Pharmacy benefits (formulary, mail order)
- Special programs (disease management, wellness)
- Claims & preauthorization
- Scheduling & customer service

**Distribution**:
- 40% Provider search questions
- 30% Policy coverage questions
- 15% Pharmacy benefits
- 10% Special programs
- 5% Other (scheduling, claims)

---

## Test Execution

### How It Works

Each iteration:
1. **Selects random question** from dataset
2. **Creates user context** (location-aware based on question)
3. **Runs full workflow** (same as `/api/chat` endpoint)
4. **Waits for evaluation** (async G-Eval judges)
5. **Collects all metrics**:
   - Routing accuracy
   - Confidence scores
   - Duration metrics
   - TTFT (Time to First Token)
   - Token usage per agent
   - Accuracy & coherence scores
   - RAG document count
6. **Terminates cleanly**
7. **Repeats**

### Observability

All test runs send data to LaunchDarkly:
- **AI Config Monitoring**: Token usage, duration, TTFT per config
- **Traces**: OpenTelemetry spans in Monitor → Traces
- **Experiments**: If you set up A/B tests on configs

---

## Results

### Output Files

After running, results are saved in `test_results/`:

```
test_results/
├── test_results_20251112_175351.json  (Full details)
├── test_results_20251112_175351.csv   (Spreadsheet-ready)
```

### CSV Columns

The CSV includes comprehensive metrics:

**Identification**:
- iteration, request_id, timestamp, question_id, question, category

**Routing**:
- expected_route, actual_route, route_match, confidence

**Performance**:
- total_duration_ms, triage_duration_ms, specialist_duration_ms, brand_duration_ms
- triage_ttft_ms, specialist_ttft_ms, brand_ttft_ms

**Token Usage**:
- *_tokens_input, *_tokens_output (per agent)

**RAG**:
- specialist_rag_docs (number retrieved)

**Evaluation**:
- accuracy_score, coherence_score, accuracy_reasoning

**Status**:
- status (success/error), error (if failed)

---

## Analysis

### In LaunchDarkly

**AI Config Monitoring**:
- Go to each AI Config (triage_agent, policy_agent, etc.)
- Click "Monitoring" tab
- View aggregate metrics across all test runs

**Traces**:
- Monitor → Traces
- Filter by service: `togglehealth-policy-agent`
- Filter by time range: Last hour
- Look for spans with `ld.ai_config.key` attribute

### In Spreadsheet

Import CSV to analyze:
- **Routing accuracy**: `route_match` column (% true)
- **Confidence distribution**: `confidence` column (histogram)
- **Duration trends**: `total_duration_ms` (avg, p50, p95, p99)
- **Evaluation scores**: `accuracy_score`, `coherence_score` (avg)
- **Error rate**: `status` column (% success)

### Quick Analysis Commands

```bash
# Count successful tests
grep "success" test_results/test_results_*.csv | wc -l

# Average accuracy score
awk -F',' 'NR>1 {sum+=$26; count++} END {print sum/count}' test_results/test_results_*.csv

# Average duration
awk -F',' 'NR>1 {sum+=$12; count++} END {print sum/count}' test_results/test_results_*.csv
```

---

## Current Known Issues

⚠️ **Policy KB Data Source Missing**

The Policy KB data source was deleted during chunking fix attempts. You need to recreate it:

1. **AWS Console** → Bedrock → Knowledge Bases → Policy KB
2. **Add data source** → S3
3. **Configure chunking**:
   - Strategy: Fixed-size
   - Max tokens: 2000
   - Overlap: 20%
4. **Sync data**

Until then, policy questions will fail with "No documents retrieved".

**Provider KB**: Same issue - needs data source recreation with proper chunking.

---

## Customization

### Run Custom Number of Iterations

```bash
TEST_ITERATIONS=100 python test_agent_suite.py
```

### Filter by Category

Edit `test_agent_suite.py` to filter questions:

```python
# In get_random_question()
def get_random_question(self, category=None):
    questions = self.dataset['questions']
    if category:
        questions = [q for q in questions if q['category'] == category]
    return random.choice(questions)
```

Then:
```python
question_data = self.get_random_question(category="provider_search")
```

---

## Expected Results (After KB Fix)

| Metric | Target | Notes |
|--------|--------|-------|
| **Success Rate** | 95%+ | 5% acceptable failure for edge cases |
| **Routing Accuracy** | 90%+ | Triage should correctly identify intent |
| **Confidence** | 85%+ | High confidence in routing decisions |
| **Avg Duration** | <20s | Full circuit including evaluation |
| **Accuracy Score** | 85%+ | Judge evaluation of factual correctness |
| **Coherence Score** | 90%+ | Judge evaluation of response quality |
| **TTFT** | <2s | Per agent time to first token |

---

## Troubleshooting

### No Documents Retrieved

```
❌ CATASTROPHIC: No policy documents retrieved from Bedrock Knowledge Base!
```

**Solution**: Recreate KB data sources (see "Current Known Issues" above)

### LaunchDarkly Client Not Initialized

```
Exception: set_config was not called
```

**Solution**: Script already initializes observability. Check your `.env` has:
```
LAUNCHDARKLY_SDK_KEY=sdk-...
LAUNCHDARKLY_AI_CONFIG_KEY=sdk-...
```

### AWS Credentials Expired

```
Error: credentials may be expired
```

**Solution**:
```bash
make aws-login
```

---

## Next Steps

1. **Fix KB data sources** (recreate with 2000-token chunks)
2. **Run quick test**: `make test-quick`
3. **Verify metrics** in LaunchDarkly
4. **Run full suite**: `make test-suite`
5. **Analyze results** in CSV
6. **Iterate on prompts** based on evaluation scores

