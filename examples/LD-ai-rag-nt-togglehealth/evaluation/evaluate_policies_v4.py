#!/usr/bin/env python3
"""
EVALUATION #4: RAG-Specific Optimization
Evaluates cleaned policies specifically for RAG system performance
"""
import os
import json
import re
from collections import defaultdict, Counter
import statistics
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

def calculate_semantic_diversity(policies):
    """Calculate semantic diversity of questions for better retrieval"""
    questions = [policy['question'] for policy in policies]
    
    # Calculate pairwise similarities
    similarities = []
    for i in range(len(questions)):
        for j in range(i+1, len(questions)):
            sim = SequenceMatcher(None, questions[i].lower(), questions[j].lower()).ratio()
            similarities.append(sim)
    
    # Diversity is inverse of average similarity
    avg_similarity = statistics.mean(similarities) if similarities else 0
    diversity = 1 - avg_similarity
    
    return diversity, similarities

def evaluate_rag_specific_optimization():
    """Evaluate policies specifically for RAG system optimization"""
    policies = load_cleaned_policies()
    
    if not policies:
        print("No policies found!")
        return
    
    print("🔧 EVALUATION #4: RAG-SPECIFIC OPTIMIZATION")
    print("="*60)
    print("Focus: How well optimized are these policies for RAG systems?")
    print()
    
    # Criterion 1: Semantic Diversity for Retrieval
    print("1️⃣ SEMANTIC DIVERSITY FOR RETRIEVAL")
    print("-" * 40)
    
    diversity, similarities = calculate_semantic_diversity(policies)
    
    # Identify highly similar question pairs that could confuse retrieval
    similar_pairs = []
    for i, policy1 in enumerate(policies):
        for j, policy2 in enumerate(policies[i+1:], i+1):
            sim = SequenceMatcher(None, policy1['question'].lower(), policy2['question'].lower()).ratio()
            if sim > 0.8:  # Very similar questions
                similar_pairs.append((policy1['file'], policy2['file'], sim, 
                                    policy1['question'][:40], policy2['question'][:40]))
    
    print(f"   📊 Semantic diversity score: {diversity:.3f}")
    print(f"   📊 Average question similarity: {statistics.mean(similarities):.3f}")
    print(f"   📊 Highly similar pairs (>0.8): {len(similar_pairs)}")
    
    if similar_pairs:
        print(f"   ⚠️  Potentially confusing question pairs:")
        for file1, file2, sim, q1, q2 in similar_pairs[:3]:
            print(f"      • {file1} vs {file2} (sim: {sim:.2f})")
            print(f"        '{q1}...' vs '{q2}...'")
    
    # Criterion 2: Chunk Quality & Coherence
    print("\n2️⃣ CHUNK QUALITY & COHERENCE")
    print("-" * 40)
    
    chunk_quality_scores = []
    poor_chunks = []
    
    for policy in policies:
        # Combine question and content as a single chunk
        full_chunk = policy['question'] + '\n\n' + '\n'.join(policy['content'])
        
        # Quality indicators
        word_count = len(full_chunk.split())
        sentence_count = len(re.split(r'[.!?]+', full_chunk))
        
        # Check for self-contained information
        has_context = policy['question'] in full_chunk
        has_complete_answer = len(policy['content']) >= 3
        
        # Check for proper structure
        has_numbered_steps = any(re.match(r'^\d+\.', step) for step in policy['content'])
        
        # Check for specific banking information
        has_specific_info = any(marker in full_chunk for marker in ['$', '▸', '%', '1‑800'])
        
        # Optimal chunk size (not too short, not too long)
        optimal_size = 50 <= word_count <= 300
        
        # Calculate chunk quality
        quality_indicators = {
            'has_context': has_context,
            'complete_answer': has_complete_answer,
            'numbered_steps': has_numbered_steps,
            'specific_info': has_specific_info,
            'optimal_size': optimal_size
        }
        
        quality_score = sum(quality_indicators.values()) / len(quality_indicators)
        chunk_quality_scores.append(quality_score)
        
        if quality_score < 0.7:
            poor_chunks.append({
                'file': policy['file'],
                'score': quality_score,
                'word_count': word_count,
                'question': policy['question'][:40],
                'missing': [k for k, v in quality_indicators.items() if not v]
            })
    
    avg_chunk_quality = statistics.mean(chunk_quality_scores) if chunk_quality_scores else 0
    
    print(f"   📊 Average chunk quality: {avg_chunk_quality:.3f}")
    print(f"   📊 High-quality chunks (≥0.8): {len([s for s in chunk_quality_scores if s >= 0.8])}/{len(policies)}")
    
    if poor_chunks:
        print(f"   ⚠️  Poor quality chunks:")
        for chunk in poor_chunks[:3]:
            print(f"      • {chunk['file']}: {chunk['score']:.2f} ({chunk['word_count']} words)")
            print(f"        Missing: {', '.join(chunk['missing'][:3])}")
    
    # Criterion 3: Answer Generation Suitability
    print("\n3️⃣ ANSWER GENERATION SUITABILITY")
    print("-" * 40)
    
    generation_scores = []
    poor_generation = []
    
    for policy in policies:
        content_text = ' '.join(policy['content'])
        
        # Check for clear, actionable instructions
        action_verbs = ['go', 'click', 'tap', 'enter', 'call', 'select', 'navigate', 'open']
        action_count = sum(content_text.lower().count(verb) for verb in action_verbs)
        
        # Check for complete information flow
        has_beginning = any(word in content_text.lower() for word in ['first', 'start', 'begin'])
        has_middle = len(policy['content']) >= 3
        has_end = any(word in content_text.lower() for word in ['complete', 'finish', 'done'])
        
        # Check for helpful context
        has_examples = any(marker in content_text for marker in ['e.g.', 'for example', 'such as'])
        has_warnings = any(phrase in content_text.lower() for phrase in ['note:', 'important:', 'remember:'])
        
        # Check for customer support integration
        has_support = any(phrase in content_text.lower() for phrase in ['contact', 'support', 'help'])
        
        # Generation suitability indicators
        generation_indicators = {
            'actionable_steps': action_count >= 2,
            'complete_flow': has_beginning and has_middle and has_end,
            'helpful_context': has_examples or has_warnings,
            'support_integration': has_support,
            'sufficient_detail': len(content_text.split()) >= 30
        }
        
        generation_score = sum(generation_indicators.values()) / len(generation_indicators)
        generation_scores.append(generation_score)
        
        if generation_score < 0.6:
            poor_generation.append({
                'file': policy['file'],
                'score': generation_score,
                'question': policy['question'][:40],
                'action_count': action_count,
                'missing': [k for k, v in generation_indicators.items() if not v]
            })
    
    avg_generation = statistics.mean(generation_scores) if generation_scores else 0
    
    print(f"   📊 Average generation suitability: {avg_generation:.3f}")
    print(f"   📊 Generation-ready policies (≥0.7): {len([s for s in generation_scores if s >= 0.7])}/{len(policies)}")
    
    if poor_generation:
        print(f"   ⚠️  Poor generation suitability:")
        for policy in poor_generation[:3]:
            print(f"      • {policy['file']}: {policy['score']:.2f} ({policy['action_count']} actions)")
            print(f"        Missing: {', '.join(policy['missing'][:3])}")
    
    # Criterion 4: Retrieval Precision Optimization
    print("\n4️⃣ RETRIEVAL PRECISION OPTIMIZATION")
    print("-" * 40)
    
    precision_scores = []
    low_precision = []
    
    # Banking domain keywords for better retrieval
    banking_keywords = {
        'core': ['account', 'card', 'payment', 'transfer', 'deposit', 'withdrawal'],
        'services': ['mobile', 'app', 'online', 'banking', 'support', 'customer'],
        'financial': ['fee', 'limit', 'balance', 'credit', 'debit', 'overdraft'],
        'security': ['password', 'login', 'authentication', 'secure', 'verify']
    }
    
    all_banking_keywords = set()
    for category in banking_keywords.values():
        all_banking_keywords.update(category)
    
    for policy in policies:
        full_text = (policy['question'] + ' ' + ' '.join(policy['content'])).lower()
        words = re.findall(r'\w+', full_text)
        
        if not words:
            precision_scores.append(0)
            continue
        
        # Calculate keyword density by category
        category_densities = {}
        for category, keywords in banking_keywords.items():
            keyword_count = sum(words.count(keyword) for keyword in keywords)
            category_densities[category] = keyword_count / len(words)
        
        # Overall banking keyword density
        banking_keyword_count = sum(words.count(keyword) for keyword in all_banking_keywords)
        overall_density = banking_keyword_count / len(words)
        
        # Check for specific identifiers that help retrieval
        has_specific_amounts = bool(re.search(r'\$\d+', full_text))
        has_navigation_paths = bool(re.search(r'▸', full_text))
        has_timeframes = bool(re.search(r'\d+\s*(?:day|hour|minute)', full_text))
        
        # Precision indicators
        precision_indicators = {
            'good_keyword_density': overall_density >= 0.15,
            'balanced_categories': len([d for d in category_densities.values() if d > 0]) >= 2,
            'specific_amounts': has_specific_amounts,
            'navigation_paths': has_navigation_paths,
            'timeframes': has_timeframes
        }
        
        precision_score = sum(precision_indicators.values()) / len(precision_indicators)
        precision_scores.append(precision_score)
        
        if precision_score < 0.6:
            low_precision.append({
                'file': policy['file'],
                'score': precision_score,
                'density': overall_density,
                'question': policy['question'][:40],
                'missing': [k for k, v in precision_indicators.items() if not v]
            })
    
    avg_precision = statistics.mean(precision_scores) if precision_scores else 0
    
    print(f"   📊 Average retrieval precision: {avg_precision:.3f}")
    print(f"   📊 High-precision policies (≥0.7): {len([s for s in precision_scores if s >= 0.7])}/{len(policies)}")
    
    if low_precision:
        print(f"   ⚠️  Low retrieval precision:")
        for policy in low_precision[:3]:
            print(f"      • {policy['file']}: {policy['score']:.2f} (density: {policy['density']:.3f})")
            print(f"        Missing: {', '.join(policy['missing'][:3])}")
    
    # Criterion 5: Hallucination Prevention
    print("\n5️⃣ HALLUCINATION PREVENTION")
    print("-" * 40)
    
    hallucination_scores = []
    hallucination_risks = []
    
    for policy in policies:
        content_text = ' '.join(policy['content'])
        
        # Check for factual grounding
        has_specific_data = bool(re.search(r'\$\d+|1‑800‑\w+|\d+%|\d+\s*(?:day|hour)', content_text))
        
        # Check for clear attribution
        has_clear_source = 'ToggleBank' in content_text or 'Toggle' in content_text
        
        # Check for definitive statements vs vague language
        vague_terms = ['may', 'might', 'possibly', 'usually', 'typically', 'generally']
        vague_count = sum(content_text.lower().count(term) for term in vague_terms)
        low_vagueness = vague_count <= 2
        
        # Check for verifiable information
        has_contact_info = bool(re.search(r'1‑800‑\w+|chat|support', content_text.lower()))
        has_specific_procedures = any(marker in content_text for marker in ['▸', 'Settings', 'Account'])
        
        # Check for completeness (reduces need for model to fill gaps)
        word_count = len(content_text.split())
        sufficient_detail = word_count >= 40
        
        # Hallucination prevention indicators
        prevention_indicators = {
            'specific_data': has_specific_data,
            'clear_source': has_clear_source,
            'low_vagueness': low_vagueness,
            'verifiable_info': has_contact_info and has_specific_procedures,
            'sufficient_detail': sufficient_detail
        }
        
        prevention_score = sum(prevention_indicators.values()) / len(prevention_indicators)
        hallucination_scores.append(prevention_score)
        
        if prevention_score < 0.6:
            hallucination_risks.append({
                'file': policy['file'],
                'score': prevention_score,
                'vague_count': vague_count,
                'word_count': word_count,
                'question': policy['question'][:40],
                'missing': [k for k, v in prevention_indicators.items() if not v]
            })
    
    avg_hallucination_prevention = statistics.mean(hallucination_scores) if hallucination_scores else 0
    
    print(f"   📊 Average hallucination prevention: {avg_hallucination_prevention:.3f}")
    print(f"   📊 Low-risk policies (≥0.7): {len([s for s in hallucination_scores if s >= 0.7])}/{len(policies)}")
    
    if hallucination_risks:
        print(f"   ⚠️  Hallucination risk policies:")
        for policy in hallucination_risks[:3]:
            print(f"      • {policy['file']}: {policy['score']:.2f} ({policy['vague_count']} vague terms)")
            print(f"        Missing: {', '.join(policy['missing'][:3])}")
    
    # Overall RAG-Specific Optimization Score
    print("\n📊 OVERALL RAG-SPECIFIC OPTIMIZATION SCORE")
    print("="*50)
    
    component_scores = {
        'Semantic Diversity': diversity * 0.20,
        'Chunk Quality': avg_chunk_quality * 0.25,
        'Generation Suitability': avg_generation * 0.25,
        'Retrieval Precision': avg_precision * 0.15,
        'Hallucination Prevention': avg_hallucination_prevention * 0.15
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n🔧 FINAL RAG OPTIMIZATION SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🚀 EXCEPTIONAL - Perfectly optimized for RAG")
    elif total_score >= 0.8:
        print("⭐ EXCELLENT - Very well optimized for RAG")
    elif total_score >= 0.7:
        print("✅ GOOD - Well suited for RAG with minor tweaks")
    elif total_score >= 0.6:
        print("👍 ACCEPTABLE - RAG-ready with some optimization")
    else:
        print("⚠️  NEEDS OPTIMIZATION - Significant RAG improvements needed")
    
    print("\n🎯 KEY RECOMMENDATIONS FOR RAG OPTIMIZATION:")
    if diversity < 0.7:
        print("  • Increase semantic diversity between questions")
    if avg_chunk_quality < 0.8:
        print("  • Improve chunk structure and self-containment")
    if avg_generation < 0.7:
        print("  • Enhance answer generation suitability with more actionable content")
    if avg_precision < 0.7:
        print("  • Optimize for better retrieval precision with more banking keywords")
    if avg_hallucination_prevention < 0.7:
        print("  • Strengthen hallucination prevention with more specific, verifiable data")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'policies_analyzed': len(policies),
        'semantic_diversity': diversity,
        'issues_found': {
            'similar_pairs': len(similar_pairs),
            'poor_chunks': len(poor_chunks),
            'poor_generation': len(poor_generation),
            'low_precision': len(low_precision),
            'hallucination_risks': len(hallucination_risks)
        }
    }

if __name__ == "__main__":
    results = evaluate_rag_specific_optimization() 