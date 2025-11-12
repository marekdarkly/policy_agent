#!/usr/bin/env python3
"""
Comprehensive Analysis of ToggleBank Policy Files
Identifies duplicates, variations, and issues for cleanup
"""
import os
import json
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import hashlib

def read_policy_file(filepath):
    """Read and parse a policy file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            lines = content.split('\n')
            
            # Extract question (first non-empty line)
            question = lines[0].strip() if lines else ""
            
            # Extract content (everything after the duplicate question)
            content_lines = []
            found_duplicate = False
            for line in lines[1:]:
                if line.strip() == question and not found_duplicate:
                    found_duplicate = True
                    continue
                if line.strip():
                    content_lines.append(line.strip())
            
            return {
                'file': os.path.basename(filepath),
                'question': question,
                'content': content_lines,
                'raw_content': content
            }
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def normalize_question(question):
    """Normalize question for comparison"""
    # Remove "Could you explain what" prefix
    question = re.sub(r'^Could you explain what\s+', '', question, flags=re.IGNORECASE)
    # Remove "What is the procedure to" prefix variations
    question = re.sub(r'^What is the procedure to\s+(do\s+)?', '', question, flags=re.IGNORECASE)
    # Remove extra spaces and normalize
    question = re.sub(r'\s+', ' ', question).strip()
    # Remove question mark for comparison
    question = question.rstrip('?')
    return question.lower()

def content_similarity(content1, content2):
    """Calculate similarity between two content lists"""
    str1 = ' '.join(content1)
    str2 = ' '.join(content2)
    return SequenceMatcher(None, str1, str2).ratio()

def analyze_policies():
    """Main analysis function"""
    policies_dir = "samples/togglebank_policies_txt"
    
    if not os.path.exists(policies_dir):
        print(f"Directory {policies_dir} not found!")
        return
    
    # Read all policy files
    policies = []
    for filename in sorted(os.listdir(policies_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(policies_dir, filename)
            policy = read_policy_file(filepath)
            if policy:
                policies.append(policy)
    
    print(f"📊 Analyzed {len(policies)} policy files")
    print("="*80)
    
    # Group by normalized question
    question_groups = defaultdict(list)
    for policy in policies:
        normalized = normalize_question(policy['question'])
        question_groups[normalized].append(policy)
    
    # Analyze duplicates and variations
    print("🔍 DUPLICATE ANALYSIS")
    print("="*50)
    
    duplicates = []
    total_duplicates = 0
    
    for normalized_q, group in question_groups.items():
        if len(group) > 1:
            total_duplicates += len(group) - 1  # Count extras
            duplicates.append({
                'normalized_question': normalized_q,
                'count': len(group),
                'variations': group
            })
    
    # Sort by frequency
    duplicates.sort(key=lambda x: x['count'], reverse=True)
    
    print(f"📈 Found {len(duplicates)} duplicate question types")
    print(f"📈 Total duplicate files: {total_duplicates}")
    print(f"📈 Unique questions: {len(question_groups) - len(duplicates)}")
    
    # Show top duplicates
    print("\n🔝 TOP 10 MOST DUPLICATED QUESTIONS:")
    for i, dup in enumerate(duplicates[:10], 1):
        print(f"{i:2d}. {dup['normalized_question'][:60]}... ({dup['count']} versions)")
    
    # Analyze content variations in duplicates
    print("\n🧐 CONTENT VARIATION ANALYSIS:")
    print("="*50)
    
    high_variation_groups = []
    for dup in duplicates:
        if dup['count'] > 2:  # Only analyze groups with 3+ versions
            group = dup['variations']
            
            # Compare content similarities
            similarities = []
            for i in range(len(group)):
                for j in range(i+1, len(group)):
                    sim = content_similarity(group[i]['content'], group[j]['content'])
                    similarities.append(sim)
            
            avg_similarity = sum(similarities) / len(similarities) if similarities else 1.0
            
            if avg_similarity < 0.9:  # High variation
                high_variation_groups.append({
                    'question': dup['normalized_question'],
                    'count': dup['count'],
                    'avg_similarity': avg_similarity,
                    'variations': group
                })
    
    high_variation_groups.sort(key=lambda x: x['avg_similarity'])
    
    print(f"Found {len(high_variation_groups)} question groups with significant content variations")
    
    # Show examples of problematic variations
    if high_variation_groups:
        print(f"\n🚨 MOST PROBLEMATIC VARIATIONS:")
        problem_group = high_variation_groups[0]
        print(f"Question: {problem_group['question']}")
        print(f"Similarity: {problem_group['avg_similarity']:.2f}")
        print("Versions:")
        for i, var in enumerate(problem_group['variations'][:3], 1):
            print(f"  {i}. File: {var['file']}")
            print(f"     Original: {var['question']}")
            print(f"     Content: {' | '.join(var['content'][:3])}...")
            print()
    
    # Analyze question quality issues
    print("🧹 QUALITY ISSUES ANALYSIS:")
    print("="*50)
    
    quality_issues = {
        'grammatical_errors': [],
        'missing_content': [],
        'duplicate_titles': [],
        'inconsistent_formatting': []
    }
    
    for policy in policies:
        # Check for grammatical issues
        if 'procedure to do I' in policy['question']:
            quality_issues['grammatical_errors'].append(policy)
        
        # Check for missing content
        if len(policy['content']) == 0:
            quality_issues['missing_content'].append(policy)
        
        # Check for duplicate titles in content
        lines = policy['raw_content'].split('\n')
        if len(lines) > 1 and lines[0].strip() == lines[1].strip():
            quality_issues['duplicate_titles'].append(policy)
        
        # Check formatting consistency
        if policy['content'] and not any(line.startswith(('1.', '2.', '3.')) for line in policy['content']):
            if len(policy['content']) > 1:  # Multi-line content should be numbered
                quality_issues['inconsistent_formatting'].append(policy)
    
    for issue_type, issues in quality_issues.items():
        if issues:
            print(f"  {issue_type.replace('_', ' ').title()}: {len(issues)} files")
    
    # Generate cleanup recommendations
    print("\n🛠️  CLEANUP RECOMMENDATIONS:")
    print("="*50)
    
    print(f"1. 🗑️  Remove {total_duplicates} duplicate files")
    print(f"2. 🔧 Fix {len(quality_issues['grammatical_errors'])} grammatical errors")
    print(f"3. 📝 Standardize {len(quality_issues['inconsistent_formatting'])} formatting issues")
    print(f"4. 🧹 Clean up {len(quality_issues['duplicate_titles'])} duplicate titles")
    print(f"5. 🔍 Resolve {len(high_variation_groups)} content variation conflicts")
    
    return {
        'total_files': len(policies),
        'unique_questions': len(question_groups),
        'duplicates': duplicates,
        'quality_issues': quality_issues,
        'high_variation_groups': high_variation_groups
    }

if __name__ == "__main__":
    results = analyze_policies() 