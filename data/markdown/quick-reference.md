# ToggleHealth AI System - Quick Reference Guide

**Last Updated:** November 13, 2025

---

## Current Performance Snapshot

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| **Overall Accuracy** | 56.5% | 80%+ | 🔴 |
| **Provider Accuracy** | 40.1% | 85%+ | 🔴 |
| **Policy Accuracy** | 74.6% | 90%+ | ⚠️ |
| **Coherence** | 87.0% | 70%+ | ✅ |
| **Routing** | 100% | 95%+ | ✅ |
| **RAG Score** | 0.586 | 0.75+ | 🔴 |

---

## Top 5 Critical Issues

| # | Issue | Impact | Fix |
|---|-------|--------|-----|
| **1** | Provider false negatives (85%) | 🔴 Critical | Redesign prompt (Week 1) |
| **2** | Poor RAG chunking (1.6% optimal) | 🔴 High | Re-chunk documents (Week 2-3) |
| **3** | Low RAG scores (0.586) | 🔴 High | Hybrid search (Week 3-4) |
| **4** | Specialty mismatches | 🔴 Critical | Add RAG parsing guide (Week 1) |
| **5** | Coverage fabrication | 🟡 Medium | Enhance policy prompt (Week 2) |

---

## Implementation Roadmap

### Week 1: Prompt Fixes (CRITICAL)
- [ ] Backup current prompts
- [ ] Deploy new provider prompt
- [ ] Test with 150 iterations
- [ ] Validate accuracy ≥75%
- [ ] Deploy to 10% production

**Expected Impact:** 56.5% → 80%+ accuracy

### Week 2: Model & Policy Updates
- [ ] Reassign Claude Haiku to policy agent
- [ ] Enhance policy prompt (plan verification)
- [ ] Begin RAG document re-chunking
- [ ] Monitor accuracy metrics

**Expected Impact:** 80% → 83%+ accuracy

### Week 3: RAG Improvements
- [ ] Complete RAG re-chunking
- [ ] Test chunking impact
- [ ] Implement hybrid search
- [ ] Deploy validation layer

**Expected Impact:** 83% → 85%+ accuracy

### Week 4: Full Rollout
- [ ] Increase traffic to 100%
- [ ] Set up monitoring dashboards
- [ ] Configure alerts
- [ ] Final validation

**Expected Impact:** 85% → 87%+ accuracy

---

## Model Assignments

### Current (Suboptimal)
```
Triage:   Nova Pro (100% routing ✅)
Policy:   Llama 4 (64.4% overall)
Provider: Mixed (40.1% avg)
Brand:    Mixed (87% coherence)
```

### Recommended (Optimized)
```
Triage:   Nova Pro (keep - excellent routing)
Policy:   Haiku 4.5 (80% on policy tasks) ⬆️ CHANGE
Provider: Llama 4 (temporary - fix prompt first)
Brand:    Haiku 4.5 (consistent quality) ⬆️ CHANGE
```

**Cost Impact:** +$8/month (+16%)
**Accuracy Impact:** +5-10% improvement

---

## Key Prompt Changes

### Provider Prompt

**Remove:**
- ❌ "Precision over helpfulness" instruction (causes false negatives)
- ❌ Excessive "NEVER" instructions (19 instances → 2)
- ❌ 7 "CRITICAL" sections (overwhelming)

**Add:**
- ✅ 3-phase process (Extract → Match → Present)
- ✅ Explicit RAG document structure guide
- ✅ Specialty matching algorithm
- ✅ Positive instructions (DO vs DON'T)

**Result:** 205 lines → 105 lines (-49%), 40% → 75%+ accuracy

### Policy Prompt

**Add at TOP:**
1. Mandatory plan type verification
2. Prescription drug pre-check
3. Dollar amount citation requirement

**Result:** 74.6% → 85%+ accuracy, zero fabrication

---

## RAG Improvements

### Document Chunking

**Current Problem:**
- 49.9% too small (<500 chars)
- 47.6% too large (>5000 chars)
- 1.6% optimal size

**Solution:**
- One provider per chunk (800-1500 chars)
- One benefit category per chunk
- Add structured metadata

**Expected Impact:** Scores 0.586 → 0.65

### Hybrid Search

**Current:** Pure semantic search

**New:** Semantic + metadata filtering
```python
filters = {
    "specialty": "Endocrinology",
    "city": "Seattle",
    "plan_type": "TH-HMO-GOLD-2024"
}
```

**Expected Impact:** Scores 0.65 → 0.75+

---

## Testing Checklist

### Before Deployment
- [ ] Run 150-iteration test suite
- [ ] Validate accuracy ≥75% (Week 1 target)
- [ ] Test specific failed queries (Q007, Q074, Q091)
- [ ] Check for new failure modes
- [ ] Validate coherence maintained ≥85%

### After Deployment (10% traffic)
- [ ] Monitor accuracy for 24 hours
- [ ] Check error rates
- [ ] Review user feedback
- [ ] Compare to baseline
- [ ] Verify no regression in other metrics

### Before Scaling Up
- [ ] Accuracy stable for 48 hours
- [ ] No new critical errors
- [ ] Latency within acceptable range
- [ ] Cost within budget

---

## Monitoring & Alerts

### Critical Alerts (Page On-Call)
```
Provider accuracy < 65%
Policy accuracy < 70%
False negative rate > 20%
Catastrophic errors (specialty mismatch)
```

### Warning Alerts (Slack)
```
Provider accuracy < 75%
Policy accuracy < 85%
RAG score < 0.6
Hallucination rate > 5%
```

### Dashboards
```
LaunchDarkly: AI Config monitoring
CloudWatch: Custom metrics
Application: Real-time accuracy
```

---

## Rollback Plan

### Trigger Conditions
- Accuracy drops >5% from baseline
- Increase in catastrophic errors
- User complaints spike
- System errors >2%

### Rollback Process
```bash
1. Revert LaunchDarkly AI Config to previous version
2. Alert team via Slack/PagerDuty
3. Investigate root cause
4. Fix and re-test in staging
5. Deploy again with 5% traffic
```

### Automatic Rollback
Configured for accuracy drop >10% (critical)

---

## Success Criteria

### Week 1 (Minimum Viable)
- ✅ Provider accuracy ≥75%
- ✅ Policy accuracy ≥85%
- ✅ Overall accuracy ≥80%
- ✅ Zero specialty mismatches

### Week 4 (Production Ready)
- ✅ Provider accuracy ≥85%
- ✅ Policy accuracy ≥90%
- ✅ Overall accuracy ≥87%
- ✅ RAG score ≥0.75
- ✅ Hallucination rate <2%

### Month 3 (Fully Optimized)
- ✅ Overall accuracy ≥90%
- ✅ Member satisfaction >85%
- ✅ Call center escalations -40%
- ✅ Positive ROI achieved

---

## Quick Commands

### Testing
```bash
# Full test suite
python run_test_suite.py --iterations 150

# Quick validation
python run_test_suite.py --iterations 10 --quick

# Specific category
python run_test_suite.py --category provider_search
```

### Analysis
```bash
# Generate metrics
python analyze_test_results.py

# RAG analysis
python analyze_rag_mechanics.py

# Failure patterns
python deep_failure_analysis.py
```

### Deployment
```bash
# Sync from LaunchDarkly
python fetch_ai_config_prompts.py

# Update LaunchDarkly
# (Use UI or API - see technical guide)

# Monitor production
aws cloudwatch get-metric-statistics --namespace ToggleHealth/AI
```

---

## Useful Links

| Resource | URL |
|----------|-----|
| LaunchDarkly Dashboard | https://app.launchdarkly.com |
| AWS Bedrock Console | https://console.aws.amazon.com/bedrock |
| CloudWatch Dashboards | https://console.aws.amazon.com/cloudwatch |
| Test Results | `/test_results/` |
| Documentation | `/data/markdown/` |

---

## Common Questions

### Q: Why did accuracy drop so much?
**A:** Overly defensive prompts caused 85% false negatives in provider searches. System says "not found" to avoid mistakes.

### Q: Are the models broken?
**A:** No. All models fail similarly (36-64%), indicating prompt issues not model issues. Even best model (Sonnet 4) only gets 40%.

### Q: Can we fix this quickly?
**A:** Yes. Week 1 prompt changes → 80% accuracy. Full fix (4 weeks) → 87% accuracy.

### Q: How much will it cost?
**A:** ~$400 one-time + $370/month. ROI positive in 2-3 months from reduced call volume.

### Q: What's the biggest risk?
**A:** Not fixing it. Current 40% provider accuracy is a patient safety issue.

### Q: What's the quickest win?
**A:** Remove "precision over helpfulness" instruction from provider prompt. One line change → -85% false negatives.

---

## Emergency Contacts

| Role | Contact | When to Contact |
|------|---------|----------------|
| Engineering Lead | [Email/Slack] | Deployment issues, rollback needed |
| AI/ML Lead | [Email/Slack] | Model performance, prompt issues |
| DevOps | [Email/Slack] | Infrastructure, AWS issues |
| Product Manager | [Email/Slack] | User impact, business decisions |
| On-Call Engineer | [PagerDuty] | Critical alerts, P0 incidents |

---

**Last Updated:** November 13, 2025
**Document Owner:** AI System Performance Team
**Review Frequency:** Weekly during implementation, monthly thereafter
