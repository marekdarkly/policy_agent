#!/usr/bin/env python3
"""
Analyze RAG retrieval mechanics from test results
"""

import re
from collections import defaultdict
import statistics

def analyze_rag_performance(log_path):
    with open(log_path, 'r') as f:
        content = f.read()

    results = {
        'retrievals': [],
        'failures': [],
        'score_distribution': [],
        'document_counts': [],
        'by_agent': defaultdict(list)
    }

    # Find all RAG retrieval sections
    retrieval_pattern = r'✅ Retrieved (\d+) documents \(top score: ([\d.]+)\)'
    matches = re.finditer(retrieval_pattern, content)

    for match in matches:
        doc_count = int(match.group(1))
        top_score = float(match.group(2))
        results['retrievals'].append({
            'count': doc_count,
            'top_score': top_score
        })
        results['score_distribution'].append(top_score)
        results['document_counts'].append(doc_count)

    # Find catastrophic RAG failures
    failure_pattern = r'❌ CATASTROPHIC: No (\w+) documents retrieved from Bedrock Knowledge Base!'
    failures = re.finditer(failure_pattern, content)

    for failure in failures:
        doc_type = failure.group(1)
        results['failures'].append(doc_type)

    # Analyze document scores in detail
    doc_score_pattern = r'Doc \d+: Score ([\d.]+), Length (\d+) chars'
    doc_scores = re.finditer(doc_score_pattern, content)

    all_doc_scores = []
    for match in doc_scores:
        score = float(match.group(1))
        length = int(match.group(2))
        all_doc_scores.append({'score': score, 'length': length})

    results['all_doc_scores'] = all_doc_scores

    return results

def generate_rag_report(results):
    report = []
    report.append("=" * 80)
    report.append("RAG MECHANICS ANALYSIS")
    report.append("=" * 80)
    report.append("")

    # Overall stats
    report.append("## RETRIEVAL STATISTICS")
    report.append("")
    report.append(f"Total Retrievals: {len(results['retrievals'])}")
    report.append(f"Catastrophic Failures: {len(results['failures'])}")
    if results['failures']:
        report.append(f"  Failed Types: {', '.join(results['failures'])}")
    report.append("")

    # Score distribution
    if results['score_distribution']:
        scores = results['score_distribution']
        report.append("## RETRIEVAL SCORE DISTRIBUTION")
        report.append("")
        report.append(f"Mean Top Score: {statistics.mean(scores):.3f}")
        report.append(f"Median Top Score: {statistics.median(scores):.3f}")
        report.append(f"Min Score: {min(scores):.3f}")
        report.append(f"Max Score: {max(scores):.3f}")
        report.append(f"Std Dev: {statistics.stdev(scores):.3f}")
        report.append("")

        # Score ranges
        excellent = sum(1 for s in scores if s >= 0.8)
        good = sum(1 for s in scores if 0.7 <= s < 0.8)
        fair = sum(1 for s in scores if 0.6 <= s < 0.7)
        poor = sum(1 for s in scores if s < 0.6)

        total = len(scores)
        report.append("### Score Quality Breakdown")
        report.append(f"  Excellent (≥0.8): {excellent} ({excellent/total*100:.1f}%)")
        report.append(f"  Good (0.7-0.8): {good} ({good/total*100:.1f}%)")
        report.append(f"  Fair (0.6-0.7): {fair} ({fair/total*100:.1f}%)")
        report.append(f"  Poor (<0.6): {poor} ({poor/total*100:.1f}%)")
        report.append("")

    # Document count analysis
    if results['document_counts']:
        counts = results['document_counts']
        report.append("## DOCUMENT COUNT ANALYSIS")
        report.append("")
        report.append(f"Mean Documents Retrieved: {statistics.mean(counts):.1f}")
        report.append(f"Median: {statistics.median(counts):.0f}")
        report.append(f"Min: {min(counts)}")
        report.append(f"Max: {max(counts)}")
        report.append("")

    # All document scores (not just top)
    if results['all_doc_scores']:
        all_scores = [d['score'] for d in results['all_doc_scores']]
        report.append("## ALL DOCUMENT SCORES (Including Lower Ranks)")
        report.append("")
        report.append(f"Total Documents Across All Retrievals: {len(all_scores)}")
        report.append(f"Mean Score: {statistics.mean(all_scores):.3f}")
        report.append(f"Median Score: {statistics.median(all_scores):.3f}")
        report.append("")

        # Quality breakdown for all docs
        excellent = sum(1 for s in all_scores if s >= 0.8)
        good = sum(1 for s in all_scores if 0.7 <= s < 0.8)
        fair = sum(1 for s in all_scores if 0.6 <= s < 0.7)
        poor = sum(1 for s in all_scores if s < 0.6)

        total = len(all_scores)
        report.append("### Quality Distribution (All Retrieved Docs)")
        report.append(f"  Excellent (≥0.8): {excellent} ({excellent/total*100:.1f}%)")
        report.append(f"  Good (0.7-0.8): {good} ({good/total*100:.1f}%)")
        report.append(f"  Fair (0.6-0.7): {fair} ({fair/total*100:.1f}%)")
        report.append(f"  Poor (<0.6): {poor} ({poor/total*100:.1f}%)")
        report.append("")

    # Document length analysis
    if results['all_doc_scores']:
        lengths = [d['length'] for d in results['all_doc_scores']]
        report.append("## DOCUMENT LENGTH ANALYSIS")
        report.append("")
        report.append(f"Mean Length: {statistics.mean(lengths):.0f} chars")
        report.append(f"Median Length: {statistics.median(lengths):.0f} chars")
        report.append(f"Min: {min(lengths)} chars")
        report.append(f"Max: {max(lengths)} chars")
        report.append("")

        # Check for very short docs (may be incomplete)
        very_short = sum(1 for l in lengths if l < 500)
        short = sum(1 for l in lengths if 500 <= l < 2000)
        medium = sum(1 for l in lengths if 2000 <= l < 5000)
        long_docs = sum(1 for l in lengths if l >= 5000)

        total = len(lengths)
        report.append("### Length Distribution")
        report.append(f"  Very Short (<500): {very_short} ({very_short/total*100:.1f}%)")
        report.append(f"  Short (500-2000): {short} ({short/total*100:.1f}%)")
        report.append(f"  Medium (2000-5000): {medium} ({medium/total*100:.1f}%)")
        report.append(f"  Long (≥5000): {long_docs} ({long_docs/total*100:.1f}%)")
        report.append("")

    return "\n".join(report)

def main():
    log_path = 'test_results/full_run_150_updated_prompts_20251113_110625.log'

    print("Analyzing RAG retrieval mechanics...")
    results = analyze_rag_performance(log_path)

    report = generate_rag_report(results)

    # Save report
    with open('test_results/rag_mechanics_analysis.txt', 'w') as f:
        f.write(report)

    print(report)
    print("\n✅ RAG mechanics analysis saved to: test_results/rag_mechanics_analysis.txt")

if __name__ == '__main__':
    main()
