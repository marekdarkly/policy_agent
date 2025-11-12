#!/usr/bin/env python3
"""
EVALUATION #2: Customer Usability & Clarity
Evaluates cleaned policies for customer experience and comprehension
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

def calculate_readability_score(text):
    """Calculate simplified readability score (based on Flesch formula principles)"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    words = re.findall(r'\b\w+\b', text)
    syllables = 0
    
    for word in words:
        # Simple syllable counting
        word = word.lower()
        syllable_count = max(1, len(re.findall(r'[aeiouAEIOU]', word)))
        syllables += syllable_count
    
    if len(sentences) == 0 or len(words) == 0:
        return 0
    
    avg_sentence_length = len(words) / len(sentences)
    avg_syllables_per_word = syllables / len(words)
    
    # Simplified Flesch-like score (higher = more readable)
    score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
    return max(0, min(100, score))

def evaluate_customer_usability_clarity():
    """Evaluate policies for customer usability and clarity"""
    policies = load_cleaned_policies()
    
    if not policies:
        print("No policies found!")
        return
    
    print("👥 EVALUATION #2: CUSTOMER USABILITY & CLARITY")
    print("="*60)
    print("Focus: How user-friendly and clear are these policies for customers?")
    print()
    
    # Criterion 1: Question Clarity & Natural Language
    print("1️⃣ QUESTION CLARITY & NATURAL LANGUAGE")
    print("-" * 40)
    
    natural_questions = 0
    clear_questions = 0
    question_issues = []
    
    natural_question_starters = [
        'how do i', 'how can i', 'what are', 'what is', 'how are', 
        'can i', 'should i', 'what should'
    ]
    
    for policy in policies:
        question = policy['question'].lower()
        
        # Check if question starts naturally
        is_natural = any(question.startswith(starter) for starter in natural_question_starters)
        if is_natural:
            natural_questions += 1
        
        # Check clarity factors
        word_count = len(question.split())
        has_jargon = any(word in question for word in [
            'procedure', 'protocol', 'methodology', 'pursuant', 'aforementioned'
        ])
        
        is_clear = word_count <= 12 and not has_jargon and '?' in question
        if is_clear:
            clear_questions += 1
        
        if not is_natural or not is_clear:
            question_issues.append({
                'file': policy['file'],
                'question': policy['question'],
                'issues': {
                    'unnatural': not is_natural,
                    'too_long': word_count > 12,
                    'has_jargon': has_jargon,
                    'missing_question_mark': '?' not in question
                }
            })
    
    natural_score = natural_questions / len(policies)
    clarity_score = clear_questions / len(policies)
    
    print(f"   📊 Natural language questions: {natural_questions}/{len(policies)} ({natural_score:.3f})")
    print(f"   📊 Clear questions: {clear_questions}/{len(policies)} ({clarity_score:.3f})")
    
    if question_issues:
        print(f"   ⚠️  Found {len(question_issues)} question clarity issues:")
        for issue in question_issues[:3]:
            problems = [k for k, v in issue['issues'].items() if v]
            print(f"      • {issue['file']}: {', '.join(problems)}")
            print(f"        '{issue['question']}'")
    
    # Criterion 2: Step-by-Step Clarity
    print("\n2️⃣ STEP-BY-STEP CLARITY")
    print("-" * 40)
    
    step_clarity_scores = []
    confusing_steps = []
    
    for policy in policies:
        clear_steps = 0
        total_steps = len(policy['content'])
        
        for step in policy['content']:
            # Remove step number for analysis
            step_text = re.sub(r'^\d+\.\s*', '', step)
            
            # Clarity indicators
            word_count = len(step_text.split())
            has_action_verb = any(step_text.lower().startswith(verb) for verb in [
                'go to', 'click', 'tap', 'enter', 'call', 'download', 'visit',
                'select', 'choose', 'navigate', 'open', 'log in', 'sign'
            ])
            
            has_specific_details = any(marker in step_text for marker in [
                '▸', '$', '%', '1‑800', 'app', 'Settings', 'Account'
            ])
            
            # Too complex if over 25 words or contains multiple sentences
            too_complex = word_count > 25 or step_text.count('.') > 1
            
            if has_action_verb and has_specific_details and not too_complex:
                clear_steps += 1
            elif too_complex or word_count > 30:
                confusing_steps.append({
                    'file': policy['file'],
                    'step': step,
                    'word_count': word_count,
                    'question': policy['question'][:30]
                })
        
        if total_steps > 0:
            step_clarity_scores.append(clear_steps / total_steps)
    
    avg_step_clarity = statistics.mean(step_clarity_scores) if step_clarity_scores else 0
    
    print(f"   📊 Average step clarity score: {avg_step_clarity:.3f}")
    print(f"   📊 Policies with clear steps (≥0.8): {len([s for s in step_clarity_scores if s >= 0.8])}/{len(policies)}")
    
    if confusing_steps:
        print(f"   ⚠️  Found {len(confusing_steps)} confusing steps:")
        for step in confusing_steps[:3]:
            print(f"      • {step['file']}: {step['word_count']} words - '{step['question']}...'")
    
    # Criterion 3: Readability & Comprehension Level
    print("\n3️⃣ READABILITY & COMPREHENSION LEVEL")
    print("-" * 40)
    
    readability_scores = []
    difficult_policies = []
    
    for policy in policies:
        all_text = policy['question'] + ' ' + ' '.join(policy['content'])
        readability = calculate_readability_score(all_text)
        readability_scores.append(readability)
        
        if readability < 60:  # Below acceptable readability
            difficult_policies.append({
                'file': policy['file'],
                'readability': readability,
                'question': policy['question'][:50]
            })
    
    avg_readability = statistics.mean(readability_scores) if readability_scores else 0
    
    print(f"   📊 Average readability score: {avg_readability:.1f}")
    print(f"   📊 Easily readable policies (≥60): {len([s for s in readability_scores if s >= 60])}/{len(policies)}")
    
    # Readability scale
    if avg_readability >= 90:
        readability_level = "Very Easy (5th grade)"
    elif avg_readability >= 80:
        readability_level = "Easy (6th grade)"
    elif avg_readability >= 70:
        readability_level = "Fairly Easy (7th grade)"
    elif avg_readability >= 60:
        readability_level = "Standard (8th-9th grade)"
    elif avg_readability >= 50:
        readability_level = "Fairly Difficult (10th-12th grade)"
    else:
        readability_level = "Difficult (College level)"
    
    print(f"   📚 Reading level: {readability_level}")
    
    if difficult_policies:
        print(f"   ⚠️  Difficult to read policies:")
        for policy in difficult_policies[:3]:
            print(f"      • {policy['file']}: {policy['readability']:.1f} - '{policy['question']}...'")
    
    # Criterion 4: Customer Service Integration
    print("\n4️⃣ CUSTOMER SERVICE INTEGRATION")
    print("-" * 40)
    
    service_integration_scores = []
    missing_support = []
    
    for policy in policies:
        content_text = ' '.join(policy['content']).lower()
        
        # Check support options mentioned
        has_phone = '1‑800‑toggle' in content_text or 'call' in content_text
        has_chat = 'chat' in content_text or 'togglesupport' in content_text
        has_app_support = 'mobile app' in content_text or 'app' in content_text
        has_specific_hours = '24/7' in content_text or 'business day' in content_text
        
        support_score = 0
        if has_phone: support_score += 0.3
        if has_chat: support_score += 0.3
        if has_app_support: support_score += 0.2
        if has_specific_hours: support_score += 0.2
        
        service_integration_scores.append(support_score)
        
        if support_score < 0.5:
            missing_support.append({
                'file': policy['file'],
                'score': support_score,
                'question': policy['question'][:50],
                'missing': {
                    'phone': not has_phone,
                    'chat': not has_chat,
                    'app': not has_app_support,
                    'hours': not has_specific_hours
                }
            })
    
    avg_service_integration = statistics.mean(service_integration_scores) if service_integration_scores else 0
    
    print(f"   📊 Average service integration: {avg_service_integration:.3f}")
    print(f"   📊 Well-integrated policies (≥0.5): {len([s for s in service_integration_scores if s >= 0.5])}/{len(policies)}")
    
    if missing_support:
        print(f"   ⚠️  Poor service integration:")
        for policy in missing_support[:3]:
            missing_items = [k for k, v in policy['missing'].items() if v]
            print(f"      • {policy['file']}: Missing {', '.join(missing_items)}")
    
    # Criterion 5: Actionability & User Empowerment
    print("\n5️⃣ ACTIONABILITY & USER EMPOWERMENT")
    print("-" * 40)
    
    actionability_scores = []
    passive_policies = []
    
    for policy in policies:
        content_text = ' '.join(policy['content']).lower()
        
        # Count action words
        action_words = [
            'click', 'tap', 'select', 'choose', 'enter', 'call', 'go to',
            'navigate', 'open', 'download', 'upload', 'set', 'enable',
            'verify', 'confirm', 'review', 'check', 'visit'
        ]
        
        action_count = sum(content_text.count(word) for word in action_words)
        
        # Check for empowering language
        empowering_phrases = [
            'you can', 'you may', 'you have the option', 'choose', 'customize',
            'your preference', 'in-app', 'instantly', 'immediately'
        ]
        
        empowerment_count = sum(content_text.count(phrase) for phrase in empowering_phrases)
        
        # Check for negative/passive language
        passive_phrases = [
            'must wait', 'contact us to', 'you cannot', 'not possible',
            'restrictions apply', 'pending approval'
        ]
        
        passive_count = sum(content_text.count(phrase) for phrase in passive_phrases)
        
        # Calculate actionability (higher is better)
        total_words = len(content_text.split())
        if total_words > 0:
            action_density = action_count / total_words
            empowerment_density = empowerment_count / total_words
            passive_penalty = passive_count / total_words
            
            actionability = min(1.0, (action_density * 10) + (empowerment_density * 5) - (passive_penalty * 3))
        else:
            actionability = 0
        
        actionability_scores.append(actionability)
        
        if actionability < 0.3:
            passive_policies.append({
                'file': policy['file'],
                'score': actionability,
                'question': policy['question'][:50],
                'action_count': action_count,
                'passive_count': passive_count
            })
    
    avg_actionability = statistics.mean(actionability_scores) if actionability_scores else 0
    
    print(f"   📊 Average actionability score: {avg_actionability:.3f}")
    print(f"   📊 Highly actionable policies (≥0.5): {len([s for s in actionability_scores if s >= 0.5])}/{len(policies)}")
    
    if passive_policies:
        print(f"   ⚠️  Low actionability policies:")
        for policy in passive_policies[:3]:
            print(f"      • {policy['file']}: {policy['score']:.2f} - '{policy['question']}...'")
    
    # Overall Customer Usability Score
    print("\n📊 OVERALL CUSTOMER USABILITY & CLARITY SCORE")
    print("="*50)
    
    component_scores = {
        'Question Clarity': (natural_score + clarity_score) / 2 * 0.25,
        'Step Clarity': avg_step_clarity * 0.25,
        'Readability': min(avg_readability / 80, 1.0) * 0.20,  # Scale to 0-1 (80+ is good)
        'Service Integration': avg_service_integration * 0.15,
        'Actionability': avg_actionability * 0.15
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n👥 FINAL CUSTOMER USABILITY SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🌟 OUTSTANDING - Exceptional customer experience")
    elif total_score >= 0.8:
        print("😊 EXCELLENT - Very user-friendly")
    elif total_score >= 0.7:
        print("👍 GOOD - Generally clear and usable")
    elif total_score >= 0.6:
        print("👌 ACCEPTABLE - Some usability improvements needed")
    else:
        print("😕 NEEDS IMPROVEMENT - Significant usability issues")
    
    print("\n💡 KEY RECOMMENDATIONS FOR CUSTOMER EXPERIENCE:")
    if (natural_score + clarity_score) / 2 < 0.8:
        print("  • Improve question clarity and use more natural language")
    if avg_step_clarity < 0.8:
        print("  • Simplify steps and add more specific action words")
    if avg_readability < 70:
        print("  • Reduce complexity for better readability")
    if avg_service_integration < 0.6:
        print("  • Better integrate customer support options")
    if avg_actionability < 0.5:
        print("  • Make instructions more actionable and empowering")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'policies_analyzed': len(policies),
        'readability_level': readability_level,
        'issues_found': {
            'question_issues': len(question_issues),
            'confusing_steps': len(confusing_steps),
            'difficult_policies': len(difficult_policies),
            'missing_support': len(missing_support),
            'passive_policies': len(passive_policies)
        }
    }

if __name__ == "__main__":
    results = evaluate_customer_usability_clarity() 