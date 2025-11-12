#!/usr/bin/env python3
"""
EVALUATION #1: RAG Accuracy & Consistency
Evaluates cleaned policies for RAG-based retrieval effectiveness
"""
import os
import json
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher

def load_cleaned_policies():
    """Load cleaned policy files"""
    policies = []
    policies_dir = "samples/cleaned_policies"
    
    if not os.path.exists(policies_dir):
        print(f"Directory {policies_dir} not found!")
        return []
    
    for filename in sorted(os.listdir(policies_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(policies_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    lines = content.split('\n')
                    
                    question = lines[0].strip() if lines else ""
                    content_lines = [line.strip() for line in lines[2:] if line.strip()]
                    
                    policies.append({
                        'file': filename,
                        'question': question,
                        'content': content_lines
                    })
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return policies

def evaluate_rag_accuracy_consistency():
    """Evaluate policies for RAG accuracy and consistency"""
    policies = load_cleaned_policies()
    
    if not policies:
        print("No policies found!")
        return
    
    print("🎯 EVALUATION #1: RAG ACCURACY & CONSISTENCY")
    print("="*60)
    print("Focus: How well do these policies support accurate RAG retrieval?")
    print()
    
    # Criterion 1: Question Uniqueness (prevents retrieval confusion)
    print("1️⃣ QUESTION UNIQUENESS & DISAMBIGUATION")
    print("-" * 40)
    
    question_similarities = []
    unique_questions = set()
    similar_pairs = []
    
    for i, policy1 in enumerate(policies):
        q1 = policy1['question'].lower()
        unique_questions.add(q1)
        
        for j, policy2 in enumerate(policies[i+1:], i+1):
            q2 = policy2['question'].lower()
            similarity = SequenceMatcher(None, q1, q2).ratio()
            question_similarities.append(similarity)
            
            if similarity > 0.7 and similarity < 1.0:  # Similar but not identical
                similar_pairs.append((policy1['file'], policy2['file'], similarity, q1[:50], q2[:50]))
    
    avg_uniqueness = 1 - (sum(question_similarities) / len(question_similarities))
    unique_question_ratio = len(unique_questions) / len(policies)
    
    print(f"   📊 Question uniqueness score: {avg_uniqueness:.3f}")
    print(f"   📊 Unique questions ratio: {unique_question_ratio:.3f}")
    
    if similar_pairs:
        print(f"   ⚠️  Found {len(similar_pairs)} potentially confusing question pairs:")
        for file1, file2, sim, q1, q2 in similar_pairs[:3]:
            print(f"      • {file1} vs {file2} (similarity: {sim:.2f})")
            print(f"        '{q1}...' vs '{q2}...'")
    else:
        print("   ✅ No confusingly similar questions found")
    
    # Criterion 2: Content Consistency (logical step ordering)
    print("\n2️⃣ CONTENT LOGICAL CONSISTENCY")
    print("-" * 40)
    
    logical_issues = []
    step_numbering_issues = []
    
    for policy in policies:
        content = policy['content']
        
        # Check step numbering
        expected_numbers = list(range(1, len(content) + 1))
        actual_numbers = []
        
        for step in content:
            match = re.match(r'^(\d+)\.', step)
            if match:
                actual_numbers.append(int(match.group(1)))
            else:
                actual_numbers.append(None)
        
        if actual_numbers != expected_numbers:
            step_numbering_issues.append({
                'file': policy['file'],
                'expected': expected_numbers,
                'actual': actual_numbers,
                'question': policy['question'][:50]
            })
        
        # Check logical flow (contact info should be last)
        contact_steps = [i for i, step in enumerate(content) 
                        if 'contact' in step.lower() or 'togglesupport' in step.lower()]
        
        if contact_steps and max(contact_steps) != len(content) - 1:
            logical_issues.append({
                'file': policy['file'],
                'issue': 'Contact info not at end',
                'question': policy['question'][:50]
            })
    
    logical_score = 1 - (len(logical_issues) / len(policies))
    numbering_score = 1 - (len(step_numbering_issues) / len(policies))
    
    print(f"   📊 Logical flow score: {logical_score:.3f}")
    print(f"   📊 Step numbering score: {numbering_score:.3f}")
    
    if step_numbering_issues:
        print(f"   ⚠️  Found {len(step_numbering_issues)} numbering issues:")
        for issue in step_numbering_issues[:3]:
            print(f"      • {issue['file']}: expected {issue['expected']} got {issue['actual']}")
    
    # Criterion 3: Retrieval Keyword Density
    print("\n3️⃣ RETRIEVAL KEYWORD DENSITY")
    print("-" * 40)
    
    banking_keywords = {
        'account', 'card', 'payment', 'transfer', 'deposit', 'withdrawal', 
        'balance', 'fee', 'limit', 'customer', 'bank', 'mobile', 'app',
        'security', 'password', 'login', 'authentication', 'support'
    }
    
    keyword_densities = []
    low_density_policies = []
    
    for policy in policies:
        all_text = (policy['question'] + ' ' + ' '.join(policy['content'])).lower()
        words = re.findall(r'\w+', all_text)
        
        if words:
            keyword_count = sum(1 for word in words if word in banking_keywords)
            density = keyword_count / len(words)
            keyword_densities.append(density)
            
            if density < 0.1:  # Less than 10% banking keywords
                low_density_policies.append({
                    'file': policy['file'],
                    'density': density,
                    'question': policy['question'][:50]
                })
    
    avg_keyword_density = sum(keyword_densities) / len(keyword_densities) if keyword_densities else 0
    
    print(f"   📊 Average keyword density: {avg_keyword_density:.3f}")
    print(f"   📊 Policies with good keyword density (>0.1): {len([d for d in keyword_densities if d >= 0.1])}/{len(policies)}")
    
    if low_density_policies:
        print(f"   ⚠️  Low keyword density policies:")
        for policy in low_density_policies[:3]:
            print(f"      • {policy['file']}: {policy['density']:.3f} - '{policy['question']}...'")
    
    # Criterion 4: Answer Completeness for RAG
    print("\n4️⃣ RAG ANSWER COMPLETENESS")
    print("-" * 40)
    
    incomplete_answers = []
    self_contained_scores = []
    
    for policy in policies:
        content_text = ' '.join(policy['content']).lower()
        
        # Check if answer is self-contained
        has_prerequisites = any(phrase in content_text for phrase in [
            'see above', 'as mentioned', 'refer to', 'check previous', 'following steps'
        ])
        
        # Check completeness indicators
        has_contact_info = any(phrase in content_text for phrase in [
            'contact', 'support', 'call', 'chat'
        ])
        
        has_specific_details = any(char in content_text for char in ['$', '%', '▸'])
        
        completeness_score = 0
        if not has_prerequisites: completeness_score += 0.4
        if has_contact_info: completeness_score += 0.3
        if has_specific_details: completeness_score += 0.3
        
        self_contained_scores.append(completeness_score)
        
        if completeness_score < 0.7:
            incomplete_answers.append({
                'file': policy['file'],
                'score': completeness_score,
                'question': policy['question'][:50],
                'issues': {
                    'has_prerequisites': has_prerequisites,
                    'missing_contact': not has_contact_info,
                    'lacks_specifics': not has_specific_details
                }
            })
    
    avg_completeness = sum(self_contained_scores) / len(self_contained_scores)
    
    print(f"   📊 Average completeness score: {avg_completeness:.3f}")
    print(f"   📊 Complete answers (≥0.7): {len([s for s in self_contained_scores if s >= 0.7])}/{len(policies)}")
    
    if incomplete_answers:
        print(f"   ⚠️  Incomplete answers found:")
        for answer in incomplete_answers[:3]:
            print(f"      • {answer['file']}: {answer['score']:.2f} - '{answer['question']}...'")
    
    # Overall RAG Accuracy Score
    print("\n📊 OVERALL RAG ACCURACY & CONSISTENCY SCORE")
    print("="*50)
    
    component_scores = {
        'Question Uniqueness': avg_uniqueness * 0.25,
        'Logical Consistency': (logical_score + numbering_score) / 2 * 0.25,
        'Keyword Density': min(avg_keyword_density * 10, 1.0) * 0.25,  # Scale to 0-1
        'Answer Completeness': avg_completeness * 0.25
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n🎯 FINAL RAG ACCURACY SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🏆 EXCELLENT - Optimal for RAG evaluation")
    elif total_score >= 0.8:
        print("✅ VERY GOOD - Suitable for RAG with minor optimization")
    elif total_score >= 0.7:
        print("👍 GOOD - RAG-ready with some improvements needed")
    elif total_score >= 0.6:
        print("⚠️  FAIR - Moderate RAG suitability, optimization recommended")
    else:
        print("❌ POOR - Significant RAG optimization needed")
    
    print("\n🔍 KEY RECOMMENDATIONS FOR RAG OPTIMIZATION:")
    if avg_uniqueness < 0.8:
        print("  • Improve question disambiguation to reduce retrieval confusion")
    if numbering_score < 0.9:
        print("  • Fix step numbering issues for better content parsing")
    if avg_keyword_density < 0.15:
        print("  • Increase banking keyword density for better retrieval")
    if avg_completeness < 0.8:
        print("  • Enhance answer completeness and self-containment")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'policies_analyzed': len(policies),
        'issues_found': {
            'similar_questions': len(similar_pairs),
            'logical_issues': len(logical_issues),
            'numbering_issues': len(step_numbering_issues),
            'incomplete_answers': len(incomplete_answers)
        }
    }

if __name__ == "__main__":
    results = evaluate_rag_accuracy_consistency() 