#!/usr/bin/env python3
"""
EVALUATION #3: Completeness & Information Quality
Evaluates cleaned policies for comprehensive and accurate information
"""
import os
import json
import re
from collections import defaultdict, Counter
import statistics

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

def extract_specific_data(text):
    """Extract specific data points like amounts, percentages, timeframes"""
    data_points = {
        'monetary_amounts': re.findall(r'\$[\d,]+', text),
        'percentages': re.findall(r'\d+%', text),
        'timeframes': re.findall(r'\d+\s*(?:minutes?|hours?|days?|weeks?|months?|years?)', text, re.IGNORECASE),
        'phone_numbers': re.findall(r'1‑800‑\w+', text),
        'times': re.findall(r'\d{1,2}:\d{2}\s*(?:AM|PM)', text, re.IGNORECASE),
        'dates': re.findall(r'(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}', text, re.IGNORECASE),
        'navigation_paths': re.findall(r'[\w\s]+▸[\w\s▸]+', text)
    }
    return data_points

def evaluate_completeness_information_quality():
    """Evaluate policies for completeness and information quality"""
    policies = load_cleaned_policies()
    
    if not policies:
        print("No policies found!")
        return
    
    print("📋 EVALUATION #3: COMPLETENESS & INFORMATION QUALITY")
    print("="*60)
    print("Focus: How comprehensive and accurate is the policy information?")
    print()
    
    # Criterion 1: Information Depth & Coverage
    print("1️⃣ INFORMATION DEPTH & COVERAGE")
    print("-" * 40)
    
    depth_scores = []
    shallow_policies = []
    
    for policy in policies:
        all_text = policy['question'] + ' ' + ' '.join(policy['content'])
        
        # Extract specific data points
        data_points = extract_specific_data(all_text)
        total_data_points = sum(len(points) for points in data_points.values())
        
        # Content depth indicators
        word_count = len(all_text.split())
        step_count = len(policy['content'])
        
        # Check for comprehensive coverage
        has_prerequisites = any(word in all_text.lower() for word in [
            'before', 'first', 'ensure', 'make sure', 'verify'
        ])
        
        has_alternatives = any(phrase in all_text.lower() for phrase in [
            'alternatively', 'you can also', 'another option', 'or you can'
        ])
        
        has_conditions = any(word in all_text.lower() for word in [
            'if', 'when', 'unless', 'provided', 'depending'
        ])
        
        has_warnings = any(phrase in all_text.lower() for phrase in [
            'note:', 'important:', 'warning:', 'caution:', 'remember:'
        ])
        
        # Calculate depth score
        depth_indicators = {
            'sufficient_length': word_count >= 50,
            'adequate_steps': step_count >= 3,
            'specific_data': total_data_points >= 2,
            'has_prerequisites': has_prerequisites,
            'has_alternatives': has_alternatives,
            'has_conditions': has_conditions,
            'has_warnings': has_warnings
        }
        
        depth_score = sum(depth_indicators.values()) / len(depth_indicators)
        depth_scores.append(depth_score)
        
        if depth_score < 0.6:
            shallow_policies.append({
                'file': policy['file'],
                'score': depth_score,
                'question': policy['question'][:50],
                'word_count': word_count,
                'data_points': total_data_points,
                'missing': [k for k, v in depth_indicators.items() if not v]
            })
    
    avg_depth = statistics.mean(depth_scores) if depth_scores else 0
    
    print(f"   📊 Average information depth: {avg_depth:.3f}")
    print(f"   📊 Comprehensive policies (≥0.7): {len([s for s in depth_scores if s >= 0.7])}/{len(policies)}")
    
    if shallow_policies:
        print(f"   ⚠️  Shallow information policies:")
        for policy in shallow_policies[:3]:
            print(f"      • {policy['file']}: {policy['score']:.2f} - Missing: {', '.join(policy['missing'][:3])}")
    
    # Criterion 2: Factual Accuracy & Specificity
    print("\n2️⃣ FACTUAL ACCURACY & SPECIFICITY")
    print("-" * 40)
    
    accuracy_scores = []
    vague_policies = []
    
    for policy in policies:
        all_text = policy['question'] + ' ' + ' '.join(policy['content'])
        
        # Extract and validate specific data
        data_points = extract_specific_data(all_text)
        
        # Check for vague language
        vague_terms = [
            'may', 'might', 'possibly', 'approximately', 'around', 'about',
            'usually', 'typically', 'generally', 'often', 'sometimes'
        ]
        
        vague_count = sum(all_text.lower().count(term) for term in vague_terms)
        
        # Check for specific indicators
        has_exact_amounts = len(data_points['monetary_amounts']) > 0
        has_exact_times = len(data_points['timeframes']) > 0 or len(data_points['times']) > 0
        has_navigation_paths = len(data_points['navigation_paths']) > 0
        has_contact_info = len(data_points['phone_numbers']) > 0
        
        # Banking-specific accuracy checks
        banking_specific_terms = {
            'tier_mentions': len(re.findall(r'(?:bronze|silver|gold|platinum|diamond)\s*tier', all_text.lower())),
            'fee_amounts': len(re.findall(r'\$\d+.*(?:fee|charge)', all_text.lower())),
            'limit_amounts': len(re.findall(r'\$[\d,]+.*limit', all_text.lower())),
            'business_days': len(re.findall(r'\d+\s*business\s*days?', all_text.lower())),
            'routing_info': len(re.findall(r'routing', all_text.lower()))
        }
        
        total_banking_specifics = sum(banking_specific_terms.values())
        
        # Calculate accuracy score
        specificity_indicators = {
            'exact_amounts': has_exact_amounts,
            'exact_times': has_exact_times,
            'navigation_paths': has_navigation_paths,
            'contact_info': has_contact_info,
            'low_vague_language': vague_count <= 2,
            'banking_specifics': total_banking_specifics >= 1
        }
        
        accuracy_score = sum(specificity_indicators.values()) / len(specificity_indicators)
        accuracy_scores.append(accuracy_score)
        
        if accuracy_score < 0.6:
            vague_policies.append({
                'file': policy['file'],
                'score': accuracy_score,
                'question': policy['question'][:50],
                'vague_count': vague_count,
                'banking_specifics': total_banking_specifics,
                'missing': [k for k, v in specificity_indicators.items() if not v]
            })
    
    avg_accuracy = statistics.mean(accuracy_scores) if accuracy_scores else 0
    
    print(f"   📊 Average factual specificity: {avg_accuracy:.3f}")
    print(f"   📊 Highly specific policies (≥0.7): {len([s for s in accuracy_scores if s >= 0.7])}/{len(policies)}")
    
    if vague_policies:
        print(f"   ⚠️  Vague or unspecific policies:")
        for policy in vague_policies[:3]:
            print(f"      • {policy['file']}: {policy['score']:.2f} - {policy['vague_count']} vague terms")
    
    # Criterion 3: Process Completeness
    print("\n3️⃣ PROCESS COMPLETENESS")
    print("-" * 40)
    
    process_scores = []
    incomplete_processes = []
    
    for policy in policies:
        content_text = ' '.join(policy['content']).lower()
        
        # Check for complete process elements
        has_initiation = any(word in content_text for word in [
            'first', 'start', 'begin', 'open', 'log in', 'go to', 'navigate'
        ])
        
        has_middle_steps = len(policy['content']) >= 3
        
        has_completion = any(phrase in content_text for phrase in [
            'complete', 'finish', 'done', 'confirmation', 'receive', 'you\'ll get'
        ])
        
        has_verification = any(word in content_text for word in [
            'verify', 'confirm', 'check', 'review', 'ensure'
        ])
        
        has_timeframe = any(word in content_text for word in [
            'within', 'day', 'hour', 'minute', 'immediately', 'instantly'
        ])
        
        has_next_steps = any(phrase in content_text for phrase in [
            'next', 'then', 'after', 'once you', 'following'
        ])
        
        # Error handling and edge cases
        has_error_handling = any(phrase in content_text for phrase in [
            'if you', 'error', 'problem', 'issue', 'unable', 'cannot', 'fails'
        ])
        
        process_elements = {
            'initiation': has_initiation,
            'middle_steps': has_middle_steps,
            'completion': has_completion,
            'verification': has_verification,
            'timeframe': has_timeframe,
            'next_steps': has_next_steps,
            'error_handling': has_error_handling
        }
        
        process_score = sum(process_elements.values()) / len(process_elements)
        process_scores.append(process_score)
        
        if process_score < 0.6:
            incomplete_processes.append({
                'file': policy['file'],
                'score': process_score,
                'question': policy['question'][:50],
                'missing': [k for k, v in process_elements.items() if not v]
            })
    
    avg_process_completeness = statistics.mean(process_scores) if process_scores else 0
    
    print(f"   📊 Average process completeness: {avg_process_completeness:.3f}")
    print(f"   📊 Complete processes (≥0.7): {len([s for s in process_scores if s >= 0.7])}/{len(policies)}")
    
    if incomplete_processes:
        print(f"   ⚠️  Incomplete processes:")
        for process in incomplete_processes[:3]:
            print(f"      • {process['file']}: Missing {', '.join(process['missing'][:3])}")
    
    # Criterion 4: Cross-Reference Consistency
    print("\n4️⃣ CROSS-REFERENCE CONSISTENCY")
    print("-" * 40)
    
    # Analyze consistency across similar policy types
    policy_categories = defaultdict(list)
    
    for policy in policies:
        question_lower = policy['question'].lower()
        
        # Categorize policies
        if 'atm' in question_lower and 'withdrawal' in question_lower:
            policy_categories['atm_withdrawal'].append(policy)
        elif 'credit limit' in question_lower:
            policy_categories['credit_limit'].append(policy)
        elif 'card' in question_lower and ('lost' in question_lower or 'stolen' in question_lower):
            policy_categories['lost_card'].append(policy)
        elif 'overdraft' in question_lower:
            policy_categories['overdraft'].append(policy)
        elif 'two-factor' in question_lower or '2fa' in question_lower:
            policy_categories['2fa'].append(policy)
        elif 'balance alert' in question_lower:
            policy_categories['balance_alerts'].append(policy)
        else:
            policy_categories['general'].append(policy)
    
    consistency_issues = []
    category_consistency_scores = []
    
    for category, category_policies in policy_categories.items():
        if len(category_policies) > 1:
            # Check for consistency in data points
            all_data = []
            for policy in category_policies:
                all_text = ' '.join(policy['content'])
                data_points = extract_specific_data(all_text)
                all_data.append(data_points)
            
            # Look for conflicts in monetary amounts, timeframes, etc.
            monetary_amounts = set()
            timeframes = set()
            
            for data in all_data:
                monetary_amounts.update(data['monetary_amounts'])
                timeframes.update(data['timeframes'])
            
            # If there are multiple different values, check for conflicts
            if len(monetary_amounts) > 1:
                consistency_issues.append({
                    'category': category,
                    'type': 'monetary_conflicts',
                    'values': list(monetary_amounts)
                })
            
            if len(timeframes) > 1:
                # Some variation is normal, but significant differences are concerning
                timeframe_numbers = []
                for tf in timeframes:
                    numbers = re.findall(r'\d+', tf)
                    if numbers:
                        timeframe_numbers.extend([int(n) for n in numbers])
                
                if timeframe_numbers and max(timeframe_numbers) > min(timeframe_numbers) * 3:
                    consistency_issues.append({
                        'category': category,
                        'type': 'timeframe_conflicts',
                        'values': list(timeframes)
                    })
        
        # Calculate consistency score for this category
        if len(category_policies) > 1:
            consistency_score = 1.0 - (len([issue for issue in consistency_issues 
                                          if issue['category'] == category]) / 2)  # Max 2 types of conflicts
            category_consistency_scores.append(max(0, consistency_score))
    
    avg_consistency = statistics.mean(category_consistency_scores) if category_consistency_scores else 1.0
    
    print(f"   📊 Cross-reference consistency: {avg_consistency:.3f}")
    print(f"   📊 Policy categories analyzed: {len(policy_categories)}")
    print(f"   📊 Consistency conflicts found: {len(consistency_issues)}")
    
    if consistency_issues:
        print(f"   ⚠️  Consistency issues:")
        for issue in consistency_issues[:3]:
            print(f"      • {issue['category']}: {issue['type']} - {issue['values']}")
    
    # Criterion 5: Regulatory & Compliance Coverage
    print("\n5️⃣ REGULATORY & COMPLIANCE COVERAGE")
    print("-" * 40)
    
    compliance_scores = []
    weak_compliance = []
    
    for policy in policies:
        all_text = (policy['question'] + ' ' + ' '.join(policy['content'])).lower()
        
        # Banking compliance indicators
        compliance_elements = {
            'security_mentions': any(word in all_text for word in [
                'secure', 'encryption', 'protect', 'privacy', 'confidential'
            ]),
            'verification_required': any(phrase in all_text for phrase in [
                'verify', 'authentication', 'confirm identity', 'last 4 digits'
            ]),
            'fraud_protection': any(word in all_text for word in [
                'fraud', 'unauthorized', 'dispute', 'protect', 'monitor'
            ]),
            'time_limits': any(phrase in all_text for phrase in [
                'within', 'business days', 'hours', 'immediately'
            ]),
            'fee_disclosure': any(word in all_text for word in [
                'fee', 'charge', 'cost', 'free', 'waived'
            ]),
            'customer_rights': any(phrase in all_text for phrase in [
                'you can', 'you may', 'you have the right', 'option to'
            ]),
            'contact_info': any(phrase in all_text for phrase in [
                'contact', 'support', 'call', 'chat', '1‑800'
            ])
        }
        
        compliance_score = sum(compliance_elements.values()) / len(compliance_elements)
        compliance_scores.append(compliance_score)
        
        if compliance_score < 0.5:
            weak_compliance.append({
                'file': policy['file'],
                'score': compliance_score,
                'question': policy['question'][:50],
                'missing': [k for k, v in compliance_elements.items() if not v]
            })
    
    avg_compliance = statistics.mean(compliance_scores) if compliance_scores else 0
    
    print(f"   📊 Average compliance coverage: {avg_compliance:.3f}")
    print(f"   📊 Strong compliance policies (≥0.7): {len([s for s in compliance_scores if s >= 0.7])}/{len(policies)}")
    
    if weak_compliance:
        print(f"   ⚠️  Weak compliance coverage:")
        for policy in weak_compliance[:3]:
            print(f"      • {policy['file']}: Missing {', '.join(policy['missing'][:3])}")
    
    # Overall Completeness & Information Quality Score
    print("\n📊 OVERALL COMPLETENESS & INFORMATION QUALITY SCORE")
    print("="*50)
    
    component_scores = {
        'Information Depth': avg_depth * 0.25,
        'Factual Specificity': avg_accuracy * 0.25,
        'Process Completeness': avg_process_completeness * 0.25,
        'Cross-Reference Consistency': avg_consistency * 0.15,
        'Compliance Coverage': avg_compliance * 0.10
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n📋 FINAL COMPLETENESS & QUALITY SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🏆 EXCEPTIONAL - Comprehensive and highly accurate")
    elif total_score >= 0.8:
        print("⭐ EXCELLENT - Very complete and reliable information")
    elif total_score >= 0.7:
        print("✅ GOOD - Generally complete with minor gaps")
    elif total_score >= 0.6:
        print("📝 ADEQUATE - Acceptable but could be more comprehensive")
    else:
        print("📉 NEEDS WORK - Significant information gaps")
    
    print("\n🔧 KEY RECOMMENDATIONS FOR INFORMATION QUALITY:")
    if avg_depth < 0.7:
        print("  • Add more comprehensive coverage and prerequisites")
    if avg_accuracy < 0.7:
        print("  • Include more specific data points and reduce vague language")
    if avg_process_completeness < 0.7:
        print("  • Complete process flows from start to finish")
    if avg_consistency < 0.8:
        print("  • Review and resolve cross-reference inconsistencies")
    if avg_compliance < 0.7:
        print("  • Strengthen regulatory and compliance coverage")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'policies_analyzed': len(policies),
        'categories_identified': len(policy_categories),
        'issues_found': {
            'shallow_policies': len(shallow_policies),
            'vague_policies': len(vague_policies),
            'incomplete_processes': len(incomplete_processes),
            'consistency_issues': len(consistency_issues),
            'weak_compliance': len(weak_compliance)
        }
    }

if __name__ == "__main__":
    results = evaluate_completeness_information_quality() 