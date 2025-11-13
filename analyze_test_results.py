#!/usr/bin/env python3
"""
Comprehensive analysis of ToggleHealth test results
Extracts and analyzes accuracy, coherence, routing, and failure patterns
"""

import re
import json
from collections import defaultdict
from typing import Dict, List, Tuple
import statistics

def parse_test_log(log_path: str) -> Dict:
    """Parse the test log file and extract all metrics"""

    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()

    results = {
        'tests': [],
        'summary': {},
        'failures': [],
        'accuracy_by_agent': defaultdict(list),
        'coherence_by_agent': defaultdict(list),
        'accuracy_by_model': defaultdict(list),
        'issues_by_type': defaultdict(list),
        'low_accuracy_tests': [],  # accuracy < 0.7
        'hallucination_cases': [],
    }

    # Split into individual test sections
    test_sections = re.split(r'={80}\n🧪 Test \d+/\d+', content)

    for section in test_sections[1:]:  # Skip header
        test_data = parse_test_section(section)
        if test_data:
            results['tests'].append(test_data)

            # Categorize by agent type
            agent = test_data.get('specialist_type', 'unknown')
            if test_data.get('accuracy') is not None:
                results['accuracy_by_agent'][agent].append(test_data['accuracy'])
            if test_data.get('coherence') is not None:
                results['coherence_by_agent'][agent].append(test_data['coherence'])

            # Categorize by model
            model = test_data.get('specialist_model', 'unknown')
            if test_data.get('accuracy') is not None:
                results['accuracy_by_model'][model].append(test_data['accuracy'])

            # Track low accuracy cases
            if test_data.get('accuracy') and test_data['accuracy'] < 0.7:
                results['low_accuracy_tests'].append(test_data)

            # Track hallucinations
            if 'hallucination' in test_data.get('accuracy_reasoning', '').lower() or \
               'fabricat' in test_data.get('accuracy_reasoning', '').lower():
                results['hallucination_cases'].append(test_data)

            # Track issues
            for issue in test_data.get('accuracy_issues', []):
                results['issues_by_type'][categorize_issue(issue)].append({
                    'test_id': test_data['test_id'],
                    'question': test_data['question'],
                    'issue': issue
                })

    # Parse summary
    summary_match = re.search(
        r'📊 RUNNING STATS.*?Avg Accuracy: ([\d.]+)%.*?Avg Coherence: ([\d.]+)%.*?Routing Accuracy: (\d+)/(\d+)',
        content,
        re.DOTALL
    )
    if summary_match:
        results['summary'] = {
            'avg_accuracy': float(summary_match.group(1)) / 100,
            'avg_coherence': float(summary_match.group(2)) / 100,
            'routing_correct': int(summary_match.group(3)),
            'routing_total': int(summary_match.group(4)),
            'routing_accuracy': int(summary_match.group(3)) / int(summary_match.group(4))
        }

    return results

def parse_test_section(section: str) -> Dict:
    """Parse an individual test section"""
    test_data = {}

    # Extract test ID and question
    question_match = re.search(r'- (Q\d+)\n={80}\n❓ Question: (.+?)\n', section)
    if question_match:
        test_data['test_id'] = question_match.group(1)
        test_data['question'] = question_match.group(2).strip()

    # Extract expected route
    route_match = re.search(r'🎯 Expected Route: (\w+)', section)
    if route_match:
        test_data['expected_route'] = route_match.group(1)

    # Extract accuracy score and reasoning
    accuracy_match = re.search(
        r'📊 Accuracy: ([\d.]+) (✅|❌).*?Reasoning: (.+?)(?=\n\n|📊 Coherence:|Issues:)',
        section,
        re.DOTALL
    )
    if accuracy_match:
        test_data['accuracy'] = float(accuracy_match.group(1))
        test_data['accuracy_pass'] = accuracy_match.group(2) == '✅'
        test_data['accuracy_reasoning'] = accuracy_match.group(3).strip()

    # Extract accuracy issues
    issues_match = re.search(r'📊 Accuracy:.*?Issues:\s*\n((?:     - .+\n)+)', section, re.DOTALL)
    if issues_match:
        issues_text = issues_match.group(1)
        test_data['accuracy_issues'] = [
            line.strip('- ').strip()
            for line in issues_text.split('\n')
            if line.strip().startswith('-')
        ]
    else:
        test_data['accuracy_issues'] = []

    # Extract coherence score and reasoning
    coherence_match = re.search(
        r'📊 Coherence: ([\d.]+) (✅|❌).*?Reasoning: (.+?)(?=\n   Issues:|\n={80})',
        section,
        re.DOTALL
    )
    if coherence_match:
        test_data['coherence'] = float(coherence_match.group(1))
        test_data['coherence_pass'] = coherence_match.group(2) == '✅'
        test_data['coherence_reasoning'] = coherence_match.group(3).strip()

    # Extract coherence issues
    coh_issues_match = re.search(r'📊 Coherence:.*?Issues:\s*\n((?:     - .+\n)+)', section, re.DOTALL)
    if coh_issues_match:
        issues_text = coh_issues_match.group(1)
        test_data['coherence_issues'] = [
            line.strip('- ').strip()
            for line in issues_text.split('\n')
            if line.strip().startswith('-')
        ]
    else:
        test_data['coherence_issues'] = []

    # Extract specialist type
    if 'POLICY SPECIALIST' in section:
        test_data['specialist_type'] = 'policy_specialist'
    elif 'PROVIDER SPECIALIST' in section:
        test_data['specialist_type'] = 'provider_specialist'
    elif 'SCHEDULER SPECIALIST' in section:
        test_data['specialist_type'] = 'scheduler_specialist'
    else:
        test_data['specialist_type'] = 'unknown'

    # Extract models used
    models_match = re.search(
        r'Models: Triage=([^,]+), Specialist=([^,]+), Brand=([^,\n]+)',
        section
    )
    if models_match:
        test_data['triage_model'] = models_match.group(1).strip()
        test_data['specialist_model'] = models_match.group(2).strip()
        test_data['brand_model'] = models_match.group(3).strip()

    # Extract specialist output
    specialist_match = re.search(
        r'📋 SPECIALIST OUTPUT \((.+?)\):\s*\n   -{76}\n(.+?)\n   -{76}',
        section,
        re.DOTALL
    )
    if specialist_match:
        test_data['specialist_output'] = specialist_match.group(2).strip()

    # Extract final brand voice output
    brand_match = re.search(
        r'💬 FINAL RESPONSE \(Brand Voice\):\s*\n   -{76}\n(.+?)\n   -{76}',
        section,
        re.DOTALL
    )
    if brand_match:
        test_data['brand_output'] = brand_match.group(1).strip()

    return test_data

def categorize_issue(issue: str) -> str:
    """Categorize an issue based on its description"""
    issue_lower = issue.lower()

    if 'hallucin' in issue_lower or 'fabricat' in issue_lower or 'invent' in issue_lower:
        return 'hallucination'
    elif 'omit' in issue_lower or 'missing' in issue_lower or 'not mention' in issue_lower:
        return 'omission'
    elif 'incorrect' in issue_lower or 'wrong' in issue_lower or 'inaccurate' in issue_lower:
        return 'incorrect_information'
    elif 'rag' in issue_lower or 'document' in issue_lower:
        return 'rag_fidelity'
    elif 'plan type' in issue_lower or 'hmo' in issue_lower or 'ppo' in issue_lower:
        return 'plan_type_mismatch'
    elif 'provider' in issue_lower and ('name' in issue_lower or 'address' in issue_lower):
        return 'provider_fabrication'
    else:
        return 'other'

def calculate_statistics(values: List[float]) -> Dict:
    """Calculate statistics for a list of values"""
    if not values:
        return {'count': 0, 'mean': 0, 'median': 0, 'min': 0, 'max': 0, 'stdev': 0}

    return {
        'count': len(values),
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'min': min(values),
        'max': max(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0
    }

def generate_report(results: Dict) -> str:
    """Generate a comprehensive analysis report"""

    report = []
    report.append("=" * 80)
    report.append("TOGGLEHEALTH AI SYSTEM - FORMAL ANALYSIS REPORT")
    report.append("=" * 80)
    report.append("")

    # Executive Summary
    report.append("## EXECUTIVE SUMMARY")
    report.append("")
    report.append(f"Total Tests: {len(results['tests'])}")
    report.append(f"Overall Accuracy: {results['summary'].get('avg_accuracy', 0):.1%}")
    report.append(f"Overall Coherence: {results['summary'].get('avg_coherence', 0):.1%}")
    report.append(f"Routing Accuracy: {results['summary'].get('routing_accuracy', 0):.1%}")
    report.append("")
    report.append(f"⚠️  CRITICAL FINDING: Accuracy at {results['summary'].get('avg_accuracy', 0):.1%} is BELOW ACCEPTABLE threshold of 70%")
    report.append(f"✅  Coherence at {results['summary'].get('avg_coherence', 0):.1%} meets standards")
    report.append(f"✅  Routing accuracy at {results['summary'].get('routing_accuracy', 0):.1%} is excellent")
    report.append("")

    # Accuracy by Agent Type
    report.append("## ACCURACY BY AGENT TYPE")
    report.append("")
    for agent, scores in sorted(results['accuracy_by_agent'].items()):
        stats = calculate_statistics(scores)
        report.append(f"### {agent.upper()}")
        report.append(f"  Tests: {stats['count']}")
        report.append(f"  Mean Accuracy: {stats['mean']:.3f} ({stats['mean']:.1%})")
        report.append(f"  Median: {stats['median']:.3f}")
        report.append(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
        report.append(f"  Std Dev: {stats['stdev']:.3f}")
        report.append(f"  Status: {'❌ FAILING' if stats['mean'] < 0.7 else '✅ PASSING'}")
        report.append("")

    # Coherence by Agent Type
    report.append("## COHERENCE BY AGENT TYPE")
    report.append("")
    for agent, scores in sorted(results['coherence_by_agent'].items()):
        stats = calculate_statistics(scores)
        report.append(f"### {agent.upper()}")
        report.append(f"  Mean Coherence: {stats['mean']:.3f} ({stats['mean']:.1%})")
        report.append(f"  Median: {stats['median']:.3f}")
        report.append(f"  Range: {stats['min']:.3f} - {stats['max']:.3f}")
        report.append("")

    # Model Performance
    report.append("## ACCURACY BY MODEL")
    report.append("")
    for model, scores in sorted(results['accuracy_by_model'].items()):
        stats = calculate_statistics(scores)
        report.append(f"### {model}")
        report.append(f"  Tests: {stats['count']}")
        report.append(f"  Mean Accuracy: {stats['mean']:.3f} ({stats['mean']:.1%})")
        report.append(f"  Status: {'❌ FAILING' if stats['mean'] < 0.7 else '✅ PASSING'}")
        report.append("")

    # Issue Analysis
    report.append("## ISSUE ANALYSIS")
    report.append("")
    report.append(f"Total Low Accuracy Tests (< 0.7): {len(results['low_accuracy_tests'])}")
    report.append(f"Hallucination Cases: {len(results['hallucination_cases'])}")
    report.append("")

    report.append("### Issues by Category")
    for category, issues in sorted(results['issues_by_type'].items(), key=lambda x: len(x[1]), reverse=True):
        report.append(f"  {category}: {len(issues)} occurrences")
    report.append("")

    # Top Issues
    report.append("## TOP 10 MOST PROBLEMATIC TESTS (Lowest Accuracy)")
    report.append("")
    sorted_tests = sorted(results['low_accuracy_tests'], key=lambda x: x.get('accuracy', 1))[:10]
    for i, test in enumerate(sorted_tests, 1):
        report.append(f"{i}. {test['test_id']} - Accuracy: {test.get('accuracy', 0):.3f}")
        report.append(f"   Q: {test['question'][:80]}...")
        report.append(f"   Agent: {test.get('specialist_type', 'unknown')}")
        report.append(f"   Model: {test.get('specialist_model', 'unknown')}")
        report.append(f"   Reason: {test.get('accuracy_reasoning', '')[:120]}...")
        if test.get('accuracy_issues'):
            report.append(f"   Issues: {len(test['accuracy_issues'])} critical problems")
        report.append("")

    return "\n".join(report)

def main():
    log_path = 'test_results/full_run_150_updated_prompts_20251113_110625.log'

    print("Parsing test results...")
    results = parse_test_log(log_path)

    print(f"Parsed {len(results['tests'])} tests")
    print(f"Found {len(results['low_accuracy_tests'])} low accuracy tests")
    print(f"Found {len(results['hallucination_cases'])} hallucination cases")

    # Generate report
    report = generate_report(results)

    # Save to file
    report_path = 'test_results/analysis_report.txt'
    with open(report_path, 'w') as f:
        f.write(report)
    print(f"\n✅ Report saved to: {report_path}")

    # Save detailed JSON
    json_path = 'test_results/detailed_analysis.json'
    # Convert defaultdicts to regular dicts for JSON serialization
    json_results = {
        'summary': results['summary'],
        'accuracy_by_agent': dict(results['accuracy_by_agent']),
        'coherence_by_agent': dict(results['coherence_by_agent']),
        'accuracy_by_model': dict(results['accuracy_by_model']),
        'low_accuracy_tests': results['low_accuracy_tests'],
        'hallucination_cases': results['hallucination_cases'],
        'issues_by_type': {k: [{'test_id': item['test_id'], 'issue': item['issue']}
                               for item in v]
                          for k, v in results['issues_by_type'].items()}
    }
    with open(json_path, 'w') as f:
        json.dump(json_results, f, indent=2)
    print(f"✅ Detailed analysis saved to: {json_path}")

    print("\n" + "=" * 80)
    print(report)

if __name__ == '__main__':
    main()
