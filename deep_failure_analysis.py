#!/usr/bin/env python3
"""
Deep failure pattern analysis - categorizes specific prompt/model failures
"""

import json
import re
from collections import defaultdict

def load_detailed_analysis():
    with open('test_results/detailed_analysis.json', 'r') as f:
        return json.load(f)

def analyze_provider_failures(data):
    """Analyze provider specialist failures in detail"""
    provider_failures = []

    for test in data['low_accuracy_tests']:
        if test.get('specialist_type') == 'provider_specialist':
            failure_type = categorize_provider_failure(test)
            provider_failures.append({
                'test_id': test['test_id'],
                'question': test['question'],
                'accuracy': test['accuracy'],
                'model': test.get('specialist_model'),
                'failure_type': failure_type,
                'reasoning': test.get('accuracy_reasoning', ''),
                'issues': test.get('accuracy_issues', [])
            })

    return provider_failures

def categorize_provider_failure(test):
    """Categorize the type of provider failure"""
    reasoning = test.get('accuracy_reasoning', '').lower()
    issues = ' '.join(test.get('accuracy_issues', [])).lower()
    combined = reasoning + ' ' + issues

    if 'specialty' in combined and ('wrong' in combined or 'misidentif' in combined or 'oncologist' in combined):
        return 'SPECIALTY_MISMATCH'
    elif 'no' in combined and ('found' in combined or 'available' in combined) and 'rag' in combined:
        return 'FALSE_NEGATIVE_RESULTS'
    elif 'plan type' in combined or 'hmo' in combined or 'ppo' in combined:
        return 'PLAN_TYPE_CONFUSION'
    elif 'fabricat' in combined or 'invent' in combined or 'hallucin' in combined:
        return 'PROVIDER_FABRICATION'
    elif 'pcp' in combined or 'primary care' in combined:
        return 'PCP_REQUIREMENT_ERROR'
    elif 'network' in combined:
        return 'NETWORK_STATUS_ERROR'
    else:
        return 'OTHER'

def analyze_policy_failures(data):
    """Analyze policy specialist failures in detail"""
    policy_failures = []

    for test in data['low_accuracy_tests']:
        if test.get('specialist_type') == 'policy_specialist':
            failure_type = categorize_policy_failure(test)
            policy_failures.append({
                'test_id': test['test_id'],
                'question': test['question'],
                'accuracy': test['accuracy'],
                'model': test.get('specialist_model'),
                'failure_type': failure_type,
                'reasoning': test.get('accuracy_reasoning', ''),
                'issues': test.get('accuracy_issues', [])
            })

    return policy_failures

def categorize_policy_failure(test):
    """Categorize the type of policy failure"""
    reasoning = test.get('accuracy_reasoning', '').lower()
    issues = ' '.join(test.get('accuracy_issues', [])).lower()
    combined = reasoning + ' ' + issues

    if 'plan type' in combined and ('mismatch' in combined or 'wrong' in combined):
        return 'PLAN_TYPE_MISMATCH'
    elif 'fabricat' in combined or 'hallucin' in combined:
        return 'COVERAGE_FABRICATION'
    elif 'prescription' in combined or 'drug' in combined:
        return 'PRESCRIPTION_INFO_ERROR'
    elif 'copay' in combined or 'deductible' in combined or 'coverage' in combined:
        return 'COVERAGE_DETAILS_ERROR'
    elif 'rag' in combined and 'not' in combined:
        return 'RAG_FIDELITY_VIOLATION'
    else:
        return 'OTHER'

def analyze_by_model_and_failure(provider_failures, policy_failures):
    """Analyze which models have which types of failures"""
    model_failures = defaultdict(lambda: defaultdict(int))

    for failure in provider_failures:
        model = failure['model']
        ftype = failure['failure_type']
        model_failures[model][ftype] += 1

    for failure in policy_failures:
        model = failure['model']
        ftype = failure['failure_type']
        model_failures[model][ftype] += 1

    return model_failures

def generate_deep_report(data):
    """Generate deep failure analysis report"""
    provider_failures = analyze_provider_failures(data)
    policy_failures = analyze_policy_failures(data)
    model_failures = analyze_by_model_and_failure(provider_failures, policy_failures)

    report = []
    report.append("=" * 80)
    report.append("DEEP FAILURE PATTERN ANALYSIS")
    report.append("=" * 80)
    report.append("")

    # Provider Specialist Failures
    report.append("## PROVIDER SPECIALIST FAILURE PATTERNS")
    report.append("")
    report.append(f"Total Provider Failures (accuracy < 0.7): {len(provider_failures)}")
    report.append("")

    provider_by_type = defaultdict(list)
    for f in provider_failures:
        provider_by_type[f['failure_type']].append(f)

    for ftype, failures in sorted(provider_by_type.items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"### {ftype}: {len(failures)} cases")
        report.append("")
        for f in failures[:3]:  # Show top 3 examples
            report.append(f"  - {f['test_id']}: {f['question'][:60]}...")
            report.append(f"    Model: {f['model']}")
            report.append(f"    Accuracy: {f['accuracy']:.3f}")
            report.append(f"    Why: {f['reasoning'][:100]}...")
        report.append("")

    # Policy Specialist Failures
    report.append("## POLICY SPECIALIST FAILURE PATTERNS")
    report.append("")
    report.append(f"Total Policy Failures (accuracy < 0.7): {len(policy_failures)}")
    report.append("")

    policy_by_type = defaultdict(list)
    for f in policy_failures:
        policy_by_type[f['failure_type']].append(f)

    for ftype, failures in sorted(policy_by_type.items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"### {ftype}: {len(failures)} cases")
        report.append("")
        for f in failures[:3]:  # Show top 3 examples
            report.append(f"  - {f['test_id']}: {f['question'][:60]}...")
            report.append(f"    Model: {f['model']}")
            report.append(f"    Accuracy: {f['accuracy']:.3f}")
            report.append(f"    Why: {f['reasoning'][:100]}...")
        report.append("")

    # Model-specific failure patterns
    report.append("## FAILURE PATTERNS BY MODEL")
    report.append("")
    for model, ftypes in sorted(model_failures.items()):
        report.append(f"### {model}")
        total = sum(ftypes.values())
        report.append(f"Total failures: {total}")
        for ftype, count in sorted(ftypes.items(), key=lambda x: x[1], reverse=True):
            pct = (count / total * 100) if total > 0 else 0
            report.append(f"  - {ftype}: {count} ({pct:.1f}%)")
        report.append("")

    return "\n".join(report)

def main():
    data = load_detailed_analysis()

    report = generate_deep_report(data)

    # Save report
    with open('test_results/deep_failure_analysis.txt', 'w') as f:
        f.write(report)

    print(report)
    print("\n✅ Deep failure analysis saved to: test_results/deep_failure_analysis.txt")

if __name__ == '__main__':
    main()
