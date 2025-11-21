# Simulations

This directory contains scripts for simulating and testing LaunchDarkly AI Config experiments.

## Scripts

### `simulate_policy_prompts.py`
Simulates policy prompt experiments with various model configurations, sending metrics to LaunchDarkly for experimentation and A/B testing.

### `simulate_brand_agent.py`
Focused simulation for brand voice agent testing, including accuracy and coherence metrics.

### `simulate_experiments.py`
General-purpose experiment simulator for testing different AI configurations.

### `run_batched_experiments.py`
Orchestrates batch runs of simulations with configurable intervals and limits.

### `guarded_release_accuracy_simulator.py`
Specialized simulator for testing guarded release features with accuracy-based rollback triggers.

## Usage

Run simulations from the project root:

```bash
# Run policy prompt simulation
python simulations/simulate_policy_prompts.py

# Run batched experiments
python simulations/run_batched_experiments.py --limit 1000 --batch-size 20
```

## Note

These scripts generate synthetic metrics for LaunchDarkly experimentation. They do not make real model calls and are designed for testing targeting rules, metric attribution, and experiment analysis.

