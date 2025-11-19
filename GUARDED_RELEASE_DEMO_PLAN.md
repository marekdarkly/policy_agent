# Guarded Release Demo Plan - Accuracy-Based Rollback

## 🎯 Goal
Demo an automated rollback when accuracy drops below 95%, completing within 5 minutes.

## 📋 Prerequisites

### LaunchDarkly Setup
1. **AI Config**: `policy_agent`
2. **Control Variation**: `llama-4-concise-prompt` (good, accurate)
3. **Treatment Variation**: `llama-4-bad-hallucinating-prompt` (will fail)
4. **Metric**: `$ld:ai:hallucinations` (0.0-1.0 where 1.0 = passed, 0.0 = failed)
5. **Guardrail Rule**: Rollback if accuracy < 0.95 (hallucination rate > 5%)

### Files Created
- ✅ `llama-4-bad-hallucinating-prompt.txt` - Bad prompt that encourages hallucinations
- 🔜 `guarded_release_accuracy_simulator.py` - Custom simulator for accuracy metric

---

## 🏗️ Architecture

### How GE Simulator Works (Current)
```python
# Tracks 3 metrics:
1. Latency (numeric) - random values in range
2. Error Rate (binary) - conversion % chance  
3. Business (binary) - conversion % chance
```

### What We Need (Modified)
```python
# Track 1 accuracy metric:
1. Accuracy ($ld:ai:hallucinations) - 0.0 to 1.0
   - Control (concise): High accuracy ~0.95 (good)
   - Treatment (bad): Low accuracy ~0.30-0.60 (fails)
```

---

## 🎬 Demo Flow (5 Minutes)

### **Minute 0-1: Setup**
1. Create `llama-4-bad-hallucinating-prompt` variation in LaunchDarkly UI
2. Set up Guarded Release from `concise` → `bad` with:
   - Start at 0% → ramp to 100%
   - Guardrail: `$ld:ai:hallucinations` < 0.95 triggers rollback
   - Sample period: 30 seconds
3. Start simulator: `python guarded_release_accuracy_simulator.py`

### **Minute 1-2: Ramp Up**
- Simulator generates traffic
- Control (concise): accuracy ~0.92-0.95 ✅
- LD gradually increases % to treatment
- Both variations look good initially

### **Minute 2-3: Treatment Gets Traffic**
- More users bucketed to treatment (bad prompt)
- Treatment (bad): accuracy ~0.30-0.60 ❌
- Metrics start showing disparity
- Aggregate accuracy begins dropping

### **Minute 3-4: Trigger Rollback**
- Aggregate accuracy drops below 0.95
- LaunchDarkly detects guardrail breach
- **Automatic rollback initiated** 🚨
- Traffic redirected back to control (concise)

### **Minute 4-5: Recovery**
- All traffic back on control
- Accuracy recovers to ~0.95
- Show LD dashboard with rollback event
- **Demo complete!** ✅

---

## 🔧 Implementation Options

### **Option 1: Modify Existing GE Simulator**
**Pros**: Full UI, websockets, real-time monitoring  
**Cons**: Requires backend changes, more complex

**Changes Needed**:
```python
# In simulation.py around line 424-467:
# Replace latency/error/business tracking with:

if flag_variation:
    # Treatment (bad prompt) - LOW accuracy
    accuracy = random.uniform(0.30, 0.60)  # Fails often
    client.track("$ld:ai:hallucinations", context, metric_value=accuracy)
else:
    # Control (concise prompt) - HIGH accuracy  
    accuracy = random.uniform(0.92, 0.98)  # Usually passes
    client.track("$ld:ai:hallucinations", context, metric_value=accuracy)
```

### **Option 2: Standalone Simulator Script** ⭐ **RECOMMENDED**
**Pros**: Quick to build, easy to run, focused on accuracy  
**Cons**: No fancy UI (but you can watch LD dashboard)

**Script Structure**:
```python
# guarded_release_accuracy_simulator.py

1. Init LD client with SDK key
2. Loop:
   - Create unique user context
   - Evaluate policy_agent AI Config
   - Get served variation (control or treatment)
   - Generate accuracy based on variation:
     * concise (control): 0.92-0.98
     * bad (treatment): 0.30-0.60
   - Track $ld:ai:hallucinations metric
   - Sleep 0.1s (10 evals/sec)
3. Watch LD dashboard for rollback
```

---

## 📝 Standalone Simulator (Recommended Implementation)

### Key Features
- **Simple**: ~100 lines of Python
- **Fast**: 10 evaluations/second
- **Focused**: Only tracks accuracy metric
- **Clean**: Console output shows what's happening
- **Observable**: Watch LaunchDarkly dashboard in real-time

### Output Example
```
🚀 Starting Guarded Release Accuracy Simulator
================================================
Config: policy_agent
Control: llama-4-concise-prompt (good)
Treatment: llama-4-bad-hallucinating-prompt (bad)
Metric: $ld:ai:hallucinations

✅ User-001 → concise-prompt    | accuracy: 0.94 ✓
✅ User-002 → concise-prompt    | accuracy: 0.96 ✓
✅ User-003 → bad-prompt        | accuracy: 0.42 ✗ HALLUCINATING!
⚠️  User-004 → bad-prompt        | accuracy: 0.55 ✗ HALLUCINATING!
✅ User-005 → concise-prompt    | accuracy: 0.93 ✓
...

📊 Stats (30s):
   Control:   Avg Accuracy: 0.948 (150 evals)
   Treatment: Avg Accuracy: 0.478 (50 evals)  ⚠️  BELOW THRESHOLD!
   
🚨 ROLLBACK EXPECTED - Check LaunchDarkly Dashboard!
```

---

## 🚀 Quick Start Commands

### 1. Create Bad Variation in LaunchDarkly
```bash
# Upload bad prompt to LaunchDarkly AI Config
# Variation key: llama-4-bad-hallucinating-prompt
# Use contents from: llama-4-bad-hallucinating-prompt.txt
```

### 2. Set Up Guarded Release
```
LaunchDarkly UI:
1. Go to policy_agent AI Config
2. Enable Guarded Release
3. From: llama-4-concise-prompt → To: llama-4-bad-hallucinating-prompt
4. Add Guardrail: $ld:ai:hallucinations < 0.95 → Rollback
5. Sample period: 30 seconds
6. Start at 0%, ramp to 100%
```

### 3. Run Simulator
```bash
python guarded_release_accuracy_simulator.py --sdk-key YOUR_SDK_KEY
```

### 4. Watch Dashboard
- Open LaunchDarkly Experiments/Guarded Release view
- Watch treatment % increase
- See accuracy drop in treatment
- **Observe automatic rollback!**

---

## ✅ Success Criteria

- [ ] Control maintains ~95% accuracy
- [ ] Treatment shows ~30-60% accuracy (hallucinating!)
- [ ] LaunchDarkly detects guardrail breach
- [ ] Automatic rollback occurs within 5 minutes
- [ ] All traffic returns to control
- [ ] Demo shows clear before/after in LD dashboard

---

## 🎯 Next Steps

1. **Create standalone simulator script** (`guarded_release_accuracy_simulator.py`)
2. **Test locally** to verify it works
3. **Upload bad prompt** to LaunchDarkly as new variation
4. **Configure guarded release** with guardrails
5. **Practice run** to ensure 5-minute timing
6. **Demo day!** 🎉

---

## 📊 Expected Metrics in LaunchDarkly

### Before Rollback
```
Variation              | Accuracy | Status
-----------------------|----------|--------
llama-4-concise        | 94.8%    | ✅ Good
llama-4-bad-hallucinate| 47.2%    | ❌ FAILING
-----------------------|----------|--------
Overall                | 82.3%    | 🚨 BELOW 95%
```

### After Rollback
```
Variation              | Accuracy | Status
-----------------------|----------|--------
llama-4-concise        | 94.8%    | ✅ Good
llama-4-bad-hallucinate| (rolled back)
-----------------------|----------|--------
Overall                | 94.8%    | ✅ Recovered
```

---

## 🔍 Troubleshooting

**Q: Rollback not triggering?**
- Check guardrail threshold (should be < 0.95)
- Verify sample period (30s minimum)
- Ensure enough treatment traffic (>20% for statistical significance)

**Q: Accuracy not dropping enough?**
- Increase bad prompt failure rate (lower the random range)
- Ensure treatment is actually serving bad prompt

**Q: Demo taking too long?**
- Increase evaluations/second in simulator (currently 10/sec)
- Reduce sample period to minimum (30s)
- Start ramp at higher % (e.g., 20% instead of 0%)

---

**Ready to build the simulator script?** Let me know and I'll create `guarded_release_accuracy_simulator.py`!

