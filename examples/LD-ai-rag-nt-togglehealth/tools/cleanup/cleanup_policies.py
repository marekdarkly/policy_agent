#!/usr/bin/env python3
"""
Comprehensive Cleanup of ToggleBank Policy Files
Creates canonical, high-quality policy dataset
"""
import os
import json
import re
from collections import defaultdict
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

def fix_question_grammar(question):
    """Fix common grammatical issues in questions"""
    # Fix "What is the procedure to do I..."
    question = re.sub(r'What is the procedure to do I\s+', 'How do I ', question)
    
    # Fix "What is the procedure to can I..."
    question = re.sub(r'What is the procedure to can I\s+', 'How can I ', question)
    
    # Fix "What is the procedure to are..."
    question = re.sub(r'What is the procedure to are\s+', 'How are ', question)
    
    # Standardize "Could you explain what..."
    question = re.sub(r'^Could you explain what\s+', 'What ', question, flags=re.IGNORECASE)
    
    # Ensure question mark
    if not question.endswith('?'):
        question += '?'
    
    return question

def merge_content_variations(variations):
    """Merge multiple content variations into the best version"""
    if not variations:
        return []
    
    if len(variations) == 1:
        return variations[0]['content']
    
    # Collect all unique steps
    all_steps = []
    step_counts = defaultdict(int)
    
    for var in variations:
        for step in var['content']:
            # Clean the step
            step = step.strip()
            if step:
                all_steps.append(step)
                # Count occurrences of similar steps
                step_key = re.sub(r'^\d+\.\s*', '', step).lower()
                step_counts[step_key] += 1
    
    # Prefer steps that appear in multiple variations
    # Sort by step number and frequency
    def extract_step_number(step):
        match = re.match(r'^(\d+)\.', step)
        return int(match.group(1)) if match else 999
    
    def step_priority(step):
        step_key = re.sub(r'^\d+\.\s*', '', step).lower()
        return (extract_step_number(step), -step_counts[step_key])
    
    # Remove duplicates while preserving order
    seen_steps = set()
    merged_steps = []
    
    for step in sorted(all_steps, key=step_priority):
        step_key = re.sub(r'^\d+\.\s*', '', step).lower()
        if step_key not in seen_steps:
            seen_steps.add(step_key)
            merged_steps.append(step)
    
    # Renumber steps
    final_steps = []
    for i, step in enumerate(merged_steps, 1):
        # Remove old numbering and add new
        step_text = re.sub(r'^\d+\.\s*', '', step)
        final_steps.append(f"{i}. {step_text}")
    
    return final_steps

def enhance_content(question, content):
    """Add richer detail and context to content"""
    enhanced_content = content.copy()
    
    # Add context and helpful details based on question type
    question_lower = question.lower()
    
    # ATM withdrawal limits
    if 'atm withdrawal limits' in question_lower:
        enhanced_content.append("6. You can request temporary limit increases through the mobile app for special circumstances.")
        enhanced_content.append("7. International ATM withdrawals may have additional fees and restrictions.")
    
    # Credit limit increase
    elif 'credit limit increase' in question_lower:
        enhanced_content.append("5. Factors considered include payment history, credit score, income verification, and account standing.")
        enhanced_content.append("6. If declined, you may reapply after 60 days or after improving credit factors.")
    
    # Lost/stolen card
    elif 'lost or stolen' in question_lower and 'card' in question_lower:
        enhanced_content.append("5. Monitor your account closely for any unauthorized transactions.")
        enhanced_content.append("6. Update any automatic payments or subscriptions with your new card information once received.")
    
    # Overdraft fees
    elif 'overdraft' in question_lower:
        enhanced_content.append("5. Consider maintaining a buffer amount in your account to avoid overdrafts.")
        enhanced_content.append("6. Review your account daily using mobile banking to stay aware of your balance.")
    
    # Two-factor authentication
    elif '2fa' in question_lower or 'two-factor' in question_lower:
        enhanced_content.append("6. Backup codes are provided in case you lose access to your primary 2FA method.")
        enhanced_content.append("7. 2FA significantly improves account security and is strongly recommended.")
    
    # Balance alerts
    elif 'balance alert' in question_lower:
        enhanced_content.append("5. Multiple alerts can be set for different thresholds and accounts.")
        enhanced_content.append("6. Alerts help prevent overdrafts and monitor unusual account activity.")
    
    # Add general support contact if not present
    if not any('contact ToggleSupport' in step or '1‑800‑TOGGLE' in step for step in enhanced_content):
        enhanced_content.append("If you need further assistance, contact ToggleSupport via chat 24/7 or call 1‑800‑TOGGLE.")
    
    return enhanced_content

def create_canonical_policies():
    """Create canonical, cleaned up policy files"""
    policies_dir = "samples/togglebank_policies_txt"
    output_dir = "samples/cleaned_policies"
    
    if not os.path.exists(policies_dir):
        print(f"Directory {policies_dir} not found!")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read all policy files
    policies = []
    for filename in sorted(os.listdir(policies_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(policies_dir, filename)
            policy = read_policy_file(filepath)
            if policy:
                policies.append(policy)
    
    print(f"🔍 Processing {len(policies)} policy files...")
    
    # Group by normalized question
    question_groups = defaultdict(list)
    for policy in policies:
        normalized = normalize_question(policy['question'])
        question_groups[normalized].append(policy)
    
    print(f"📊 Found {len(question_groups)} unique question groups")
    
    # Create canonical versions
    canonical_policies = []
    policy_counter = 1
    
    for normalized_q, group in sorted(question_groups.items()):
        print(f"🔧 Processing: {normalized_q[:50]}... ({len(group)} variations)")
        
        # Pick the best question format (without grammatical errors)
        best_question = None
        for policy in group:
            if 'procedure to do I' not in policy['question']:
                best_question = policy['question']
                break
        
        # If all have errors, pick first and fix it
        if not best_question:
            best_question = group[0]['question']
        
        # Fix grammar in question
        canonical_question = fix_question_grammar(best_question)
        
        # Merge content from all variations
        merged_content = merge_content_variations(group)
        
        # Enhance content with richer details
        enhanced_content = enhance_content(canonical_question, merged_content)
        
        # Create canonical policy
        canonical_policy = {
            'id': f"policy_{policy_counter:03d}",
            'question': canonical_question,
            'content': enhanced_content,
            'source_files': [p['file'] for p in group],
            'variations_merged': len(group)
        }
        
        canonical_policies.append(canonical_policy)
        
        # Write individual file
        output_file = os.path.join(output_dir, f"policy_{policy_counter:03d}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"{canonical_question}\n\n")
            for step in enhanced_content:
                f.write(f"{step}\n")
        
        policy_counter += 1
    
    # Create metadata file
    metadata = {
        'total_canonical_policies': len(canonical_policies),
        'original_files_processed': len(policies),
        'reduction_ratio': len(policies) / len(canonical_policies),
        'policies': canonical_policies
    }
    
    metadata_file = os.path.join(output_dir, 'policy_metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ CLEANUP COMPLETE!")
    print(f"📊 Created {len(canonical_policies)} canonical policies from {len(policies)} original files")
    print(f"📉 Reduction ratio: {len(policies) / len(canonical_policies):.1f}:1")
    print(f"📁 Output directory: {output_dir}")
    
    return canonical_policies

def evaluate_cleanup_quality(canonical_policies):
    """Evaluate the quality of the cleaned up policies"""
    print(f"\n🔍 CLEANUP QUALITY EVALUATION")
    print("="*50)
    
    # Evaluation criteria 1: Question Quality
    print("1️⃣ QUESTION QUALITY:")
    grammatical_errors = 0
    unclear_questions = 0
    
    for policy in canonical_policies:
        question = policy['question']
        
        # Check for remaining grammatical issues
        if 'procedure to do I' in question or 'procedure to can I' in question:
            grammatical_errors += 1
        
        # Check for clarity
        if len(question.split()) > 15 or question.count('?') != 1:
            unclear_questions += 1
    
    print(f"   ✅ Grammatical errors: {grammatical_errors}/{len(canonical_policies)}")
    print(f"   ✅ Clear questions: {len(canonical_policies) - unclear_questions}/{len(canonical_policies)}")
    
    # Evaluation criteria 2: Content Completeness
    print("\n2️⃣ CONTENT COMPLETENESS:")
    step_counts = [len(policy['content']) for policy in canonical_policies]
    avg_steps = sum(step_counts) / len(step_counts)
    minimal_content = sum(1 for count in step_counts if count < 3)
    
    print(f"   ✅ Average steps per policy: {avg_steps:.1f}")
    print(f"   ✅ Policies with sufficient content (3+ steps): {len(canonical_policies) - minimal_content}/{len(canonical_policies)}")
    
    # Evaluation criteria 3: Consistency
    print("\n3️⃣ FORMATTING CONSISTENCY:")
    properly_numbered = 0
    has_contact_info = 0
    
    for policy in canonical_policies:
        # Check numbering
        if policy['content'] and all(re.match(r'^\d+\.', step) for step in policy['content'] if step.strip()):
            properly_numbered += 1
        
        # Check for contact information
        if any('ToggleSupport' in step or '1‑800‑TOGGLE' in step for step in policy['content']):
            has_contact_info += 1
    
    print(f"   ✅ Properly numbered: {properly_numbered}/{len(canonical_policies)}")
    print(f"   ✅ Includes contact info: {has_contact_info}/{len(canonical_policies)}")
    
    # Evaluation criteria 4: RAG Suitability
    print("\n4️⃣ RAG EVALUATION SUITABILITY:")
    unique_questions = len(set(policy['question'] for policy in canonical_policies))
    enhanced_policies = sum(1 for policy in canonical_policies if len(policy['content']) > policy['variations_merged'])
    
    print(f"   ✅ Unique questions: {unique_questions}/{len(canonical_policies)}")
    print(f"   ✅ Enhanced with additional detail: {enhanced_policies}/{len(canonical_policies)}")
    
    # Overall score
    total_checks = len(canonical_policies) * 4  # 4 criteria
    passed_checks = (
        (len(canonical_policies) - grammatical_errors) +
        (len(canonical_policies) - unclear_questions) +
        (len(canonical_policies) - minimal_content) +
        properly_numbered
    )
    
    quality_score = (passed_checks / total_checks) * 100
    
    print(f"\n📊 OVERALL QUALITY SCORE: {quality_score:.1f}%")
    
    if quality_score >= 90:
        print("🎉 EXCELLENT - Ready for RAG evaluation!")
    elif quality_score >= 80:
        print("✅ GOOD - Minor improvements needed")
    elif quality_score >= 70:
        print("⚠️  FAIR - Some issues to address")
    else:
        print("❌ POOR - Significant improvements needed")

if __name__ == "__main__":
    canonical_policies = create_canonical_policies()
    if canonical_policies:
        evaluate_cleanup_quality(canonical_policies) 