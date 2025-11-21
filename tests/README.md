# Tests

This directory contains test scripts for evaluating agent performance and system functionality.

## Scripts

### `test_agent_suite.py`
Comprehensive test suite that runs real agent evaluations with actual model calls. Supports modular evaluation of specific agents (policy, provider, brand).

**Usage:**
```bash
# Run full test suite (50 iterations)
make test-suite

# Run quick test (5 iterations)
make test-quick

# Evaluate specific agent
python tests/test_agent_suite.py --evaluate brand_agent --limit 10
```

### `test_agent_evaluation.py`
Focused testing for agent evaluation metrics and G-Eval integration.

### `test_evaluation_mode_demo.py`
Demonstration of evaluation modes and metric tracking for demos.

### `test_metrics_diagnostic.py`
Diagnostic tool for troubleshooting metric delivery and attribution issues.

## Test Data

Test datasets are located in `test_data/`:
- `qa_dataset.json` - Full question-answer dataset
- `qa_dataset_demo.json` - Smaller demo dataset

## Features

- **Real Model Calls**: Makes actual LLM invocations for accurate evaluation
- **G-Eval Integration**: Uses G-Eval for accuracy and coherence scoring
- **LaunchDarkly Metrics**: Sends evaluation results to LaunchDarkly for experimentation
- **Modular Evaluation**: Test individual agents or the full system
- **CSV/JSON Export**: Saves detailed results for analysis

