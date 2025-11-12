#!/usr/bin/env python3
"""
EVALUATION #4: RAG Performance Optimization
Evaluates cleaned customer profiles for RAG-based customer service applications
"""
import os
import json
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import statistics

def load_cleaned_profiles():
    """Load cleaned customer profile files"""
    profiles = []
    profiles_dir = "samples/cleaned_profiles"
    
    if not os.path.exists(profiles_dir):
        print(f"Directory {profiles_dir} not found!")
        return []
    
    for filename in sorted(os.listdir(profiles_dir)):
        if filename.endswith('.txt') and filename.startswith('customer_'):
            filepath = os.path.join(profiles_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    lines = content.split('\n')
                    
                    profile_data = {}
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            profile_data[key.strip()] = value.strip()
                    
                    profiles.append({
                        'file': filename,
                        'profile': profile_data,
                        'raw_content': content
                    })
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return profiles

def calculate_retrieval_keywords_density(content):
    """Calculate density of customer service relevant keywords"""
    customer_service_keywords = {
        'account', 'customer', 'balance', 'tier', 'login', 'since', 'rewards',
        'points', 'channel', 'language', 'preference', 'mobile', 'web', 'phone',
        'branch', 'bronze', 'silver', 'gold', 'platinum', 'diamond', 'city',
        'state', 'profile', 'information', 'data', 'service'
    }
    
    words = re.findall(r'\w+', content.lower())
    if not words:
        return 0
    
    keyword_count = sum(1 for word in words if word in customer_service_keywords)
    return keyword_count / len(words)

def evaluate_rag_performance_optimization():
    """Evaluate customer profiles for RAG performance optimization"""
    profiles = load_cleaned_profiles()
    
    if not profiles:
        print("No profiles found!")
        return
    
    print("🔧 EVALUATION #4: RAG PERFORMANCE OPTIMIZATION")
    print("="*60)
    print("Focus: How well do these profiles support RAG-based customer service?")
    print()
    
    # Criterion 1: Query Matching & Retrieval Precision
    print("1️⃣ QUERY MATCHING & RETRIEVAL PRECISION")
    print("-" * 40)
    
    # Analyze profile uniqueness for precise retrieval
    names = [profile['profile'].get('Name', '') for profile in profiles]
    unique_identifiers = set(names)
    name_uniqueness = len(unique_identifiers) / len(profiles) if profiles else 0
    
    # Check for ambiguous identifiers
    ambiguous_cases = []
    name_parts = defaultdict(list)
    
    for i, name in enumerate(names):
        if name:
            first_name = name.split()[0]
            last_name = name.split()[-1] if len(name.split()) > 1 else ''
            
            name_parts[first_name].append(i)
            if last_name:
                name_parts[last_name].append(i)
    
    # Find potentially ambiguous name parts
    ambiguous_count = 0
    for part, indices in name_parts.items():
        if len(indices) > 1 and len(part) > 2:  # Common name parts
            ambiguous_count += 1
    
    # Analyze keyword density for better retrieval
    keyword_densities = []
    for profile in profiles:
        content = profile['raw_content']
        density = calculate_retrieval_keywords_density(content)
        keyword_densities.append(density)
    
    avg_keyword_density = statistics.mean(keyword_densities) if keyword_densities else 0
    
    print(f"   📊 Name uniqueness: {name_uniqueness:.3f}")
    print(f"   📊 Ambiguous name parts: {ambiguous_count}")
    print(f"   📊 Average keyword density: {avg_keyword_density:.3f}")
    print(f"   📊 Profiles with good density (>0.3): {len([d for d in keyword_densities if d > 0.3])}/{len(profiles)}")
    
    # Query precision score
    precision_score = (name_uniqueness + min(avg_keyword_density * 3, 1.0)) / 2
    
    # Criterion 2: Information Completeness for Context
    print("\n2️⃣ INFORMATION COMPLETENESS FOR CONTEXT")
    print("-" * 40)
    
    required_fields = ['Name', 'City', 'Account Tier', 'Account Since', 'Last Login', 
                      'Average Balance', 'Rewards Points', 'Preferred Channel', 'Language Preference']
    
    completeness_scores = []
    incomplete_profiles = []
    field_coverage = defaultdict(int)
    
    for profile in profiles:
        data = profile['profile']
        complete_fields = 0
        
        for field in required_fields:
            if field in data and data[field].strip():
                complete_fields += 1
                field_coverage[field] += 1
        
        completeness = complete_fields / len(required_fields)
        completeness_scores.append(completeness)
        
        if completeness < 0.9:
            missing_fields = [field for field in required_fields 
                            if field not in data or not data[field].strip()]
            incomplete_profiles.append((profile['file'], missing_fields))
    
    avg_completeness = statistics.mean(completeness_scores) if completeness_scores else 0
    
    print(f"   📊 Average completeness: {avg_completeness:.3f}")
    print(f"   📊 Fully complete profiles (100%): {len([s for s in completeness_scores if s == 1.0])}/{len(profiles)}")
    
    if incomplete_profiles:
        print(f"   ⚠️  Incomplete profiles: {len(incomplete_profiles)}")
        for file, missing in incomplete_profiles[:3]:
            print(f"      • {file}: Missing {', '.join(missing[:3])}")
    
    print("\n   Field Coverage:")
    for field in required_fields:
        coverage = (field_coverage[field] / len(profiles)) * 100 if profiles else 0
        print(f"     • {field}: {field_coverage[field]}/{len(profiles)} ({coverage:.1f}%)")
    
    # Criterion 3: Response Generation Support
    print("\n3️⃣ RESPONSE GENERATION SUPPORT")
    print("-" * 40)
    
    # Analyze content richness for generating helpful responses
    generation_quality_scores = []
    insufficient_content = []
    
    for profile in profiles:
        data = profile['profile']
        content = profile['raw_content']
        
        # Content richness indicators
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        # Check for specific data that helps response generation
        has_specific_data = 0
        
        # Date information
        if data.get('Account Since') and data.get('Last Login'):
            has_specific_data += 0.2
        
        # Tier information
        if data.get('Account Tier') in ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']:
            has_specific_data += 0.2
        
        # Balance information
        if data.get('Average Balance') and re.match(r'(<1k|\d+k-\d+k|>\d+k)', data.get('Average Balance', '')):
            has_specific_data += 0.2
        
        # Contact preferences
        if data.get('Preferred Channel') and data.get('Language Preference'):
            has_specific_data += 0.2
        
        # Geographic information
        if data.get('City') and ', ' in data.get('City', ''):
            has_specific_data += 0.2
        
        # Content structure quality
        structure_score = 0
        if word_count >= 20:  # Minimum content
            structure_score += 0.3
        if line_count >= 8:  # Well-structured
            structure_score += 0.3
        if word_count <= 100:  # Not too verbose
            structure_score += 0.4
        
        generation_score = (has_specific_data + structure_score) / 2
        generation_quality_scores.append(generation_score)
        
        if generation_score < 0.7:
            insufficient_content.append((profile['file'], generation_score, word_count))
    
    avg_generation_quality = statistics.mean(generation_quality_scores) if generation_quality_scores else 0
    
    print(f"   📊 Average generation quality: {avg_generation_quality:.3f}")
    print(f"   📊 High-quality profiles (≥0.8): {len([s for s in generation_quality_scores if s >= 0.8])}/{len(profiles)}")
    
    if insufficient_content:
        print(f"   ⚠️  Insufficient content quality: {len(insufficient_content)} profiles")
        for file, score, words in insufficient_content[:3]:
            print(f"      • {file}: {score:.2f} ({words} words)")
    
    # Criterion 4: Personalization Context Support
    print("\n4️⃣ PERSONALIZATION CONTEXT SUPPORT")
    print("-" * 40)
    
    # Analyze how well profiles support personalized responses
    personalization_scores = []
    limited_personalization = []
    
    for profile in profiles:
        data = profile['profile']
        
        personalization_factors = 0
        
        # Language-based personalization
        language = data.get('Language Preference', '')
        if language and language in ['en', 'es', 'fr', 'de', 'zh']:
            personalization_factors += 0.25
        
        # Channel-based personalization
        channel = data.get('Preferred Channel', '')
        if channel and channel in ['mobile', 'web', 'phone', 'branch']:
            personalization_factors += 0.25
        
        # Tier-based personalization
        tier = data.get('Account Tier', '')
        if tier and tier in ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']:
            personalization_factors += 0.25
        
        # Geographic personalization
        city = data.get('City', '')
        if city and ', ' in city:
            personalization_factors += 0.25
        
        personalization_scores.append(personalization_factors)
        
        if personalization_factors < 0.75:
            missing_factors = []
            if not language or language not in ['en', 'es', 'fr', 'de', 'zh']:
                missing_factors.append('language')
            if not channel or channel not in ['mobile', 'web', 'phone', 'branch']:
                missing_factors.append('channel')
            if not tier or tier not in ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']:
                missing_factors.append('tier')
            if not city or ', ' not in city:
                missing_factors.append('geography')
                
            limited_personalization.append((profile['file'], missing_factors))
    
    avg_personalization = statistics.mean(personalization_scores) if personalization_scores else 0
    
    print(f"   📊 Average personalization support: {avg_personalization:.3f}")
    print(f"   📊 Full personalization support: {len([s for s in personalization_scores if s >= 1.0])}/{len(profiles)}")
    
    if limited_personalization:
        print(f"   ⚠️  Limited personalization: {len(limited_personalization)} profiles")
        for file, missing in limited_personalization[:3]:
            print(f"      • {file}: Missing {', '.join(missing)}")
    
    # Criterion 5: Error Prevention & Data Consistency
    print("\n5️⃣ ERROR PREVENTION & DATA CONSISTENCY")
    print("-" * 40)
    
    # Analyze data consistency to prevent hallucination
    consistency_scores = []
    consistency_issues = []
    
    for profile in profiles:
        data = profile['profile']
        issues = []
        
        # Date consistency
        account_since = data.get('Account Since', '')
        last_login = data.get('Last Login', '')
        
        if account_since and last_login:
            try:
                from datetime import datetime
                since_date = datetime.strptime(account_since, '%Y-%m-%d')
                login_date = datetime.strptime(last_login, '%Y-%m-%d')
                
                if since_date > login_date:
                    issues.append('Account Since after Last Login')
                
                # Check for reasonable date ranges
                now = datetime.now()
                if (now - since_date).days < 0:
                    issues.append('Future account creation')
                if (now - login_date).days < 0:
                    issues.append('Future login date')
                    
            except ValueError:
                issues.append('Invalid date format')
        
        # Tier-balance consistency
        tier = data.get('Account Tier', '')
        balance = data.get('Average Balance', '')
        
        if tier and balance:
            # Check for obvious mismatches
            if tier == 'Diamond' and balance == '<1k':
                issues.append('Diamond tier with minimal balance')
            elif tier == 'Bronze' and balance.startswith('>100k'):
                issues.append('Bronze tier with very high balance')
        
        # Rewards points consistency
        points = data.get('Rewards Points', '')
        if points:
            try:
                points_val = int(points)
                if points_val < 0:
                    issues.append('Negative rewards points')
                elif points_val > 1000000:
                    issues.append('Unrealistic rewards points')
            except ValueError:
                issues.append('Invalid rewards points format')
        
        # Geographic consistency
        city = data.get('City', '')
        if city:
            if ', ' not in city:
                issues.append('Missing state in city field')
            elif len(city.split(', ')[1]) != 2:
                issues.append('Invalid state code format')
        
        consistency_score = max(0, 1 - (len(issues) * 0.2))  # Penalize each issue
        consistency_scores.append(consistency_score)
        
        if issues:
            consistency_issues.append((profile['file'], issues))
    
    avg_consistency = statistics.mean(consistency_scores) if consistency_scores else 0
    
    print(f"   📊 Average data consistency: {avg_consistency:.3f}")
    print(f"   📊 Fully consistent profiles: {len([s for s in consistency_scores if s >= 1.0])}/{len(profiles)}")
    
    if consistency_issues:
        print(f"   ⚠️  Data consistency issues: {len(consistency_issues)} profiles")
        for file, issues in consistency_issues[:3]:
            print(f"      • {file}: {', '.join(issues[:3])}")
    
    # Criterion 6: RAG Chunking Optimization
    print("\n6️⃣ RAG CHUNKING OPTIMIZATION")
    print("-" * 40)
    
    # Analyze how well profiles work as RAG chunks
    chunk_quality_scores = []
    suboptimal_chunks = []
    
    for profile in profiles:
        content = profile['raw_content']
        
        # Optimal chunk characteristics
        word_count = len(content.split())
        line_count = len(content.split('\n'))
        
        # Size optimization (not too small, not too large)
        size_score = 0
        if 20 <= word_count <= 150:  # Optimal range for customer profiles
            size_score = 1.0
        elif 15 <= word_count <= 200:  # Acceptable range
            size_score = 0.8
        elif word_count < 15:  # Too small
            size_score = 0.3
        else:  # Too large
            size_score = 0.5
        
        # Structure optimization
        structure_score = 0
        if line_count >= 8:  # Well-structured with clear fields
            structure_score += 0.5
        if line_count <= 12:  # Not overly complex
            structure_score += 0.5
        
        # Information density
        data = profile['profile']
        info_density = len([v for v in data.values() if v.strip()]) / 9  # 9 expected fields
        
        chunk_quality = (size_score * 0.4 + structure_score * 0.3 + info_density * 0.3)
        chunk_quality_scores.append(chunk_quality)
        
        if chunk_quality < 0.8:
            suboptimal_chunks.append((profile['file'], chunk_quality, word_count, line_count))
    
    avg_chunk_quality = statistics.mean(chunk_quality_scores) if chunk_quality_scores else 0
    
    print(f"   📊 Average chunk quality: {avg_chunk_quality:.3f}")
    print(f"   📊 Optimal chunks (≥0.9): {len([s for s in chunk_quality_scores if s >= 0.9])}/{len(profiles)}")
    
    if suboptimal_chunks:
        print(f"   ⚠️  Suboptimal chunks: {len(suboptimal_chunks)} profiles")
        for file, quality, words, lines in suboptimal_chunks[:3]:
            print(f"      • {file}: {quality:.2f} ({words} words, {lines} lines)")
    
    # Overall RAG Performance Score
    print("\n📊 OVERALL RAG PERFORMANCE OPTIMIZATION SCORE")
    print("="*50)
    
    component_scores = {
        'Query Matching Precision': precision_score * 0.20,
        'Information Completeness': avg_completeness * 0.20,
        'Response Generation Support': avg_generation_quality * 0.20,
        'Personalization Context': avg_personalization * 0.15,
        'Data Consistency': avg_consistency * 0.15,
        'Chunk Optimization': avg_chunk_quality * 0.10
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n🔧 FINAL RAG PERFORMANCE SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🚀 EXCEPTIONAL - Perfectly optimized for RAG applications")
    elif total_score >= 0.8:
        print("⭐ EXCELLENT - Very well suited for RAG systems")
    elif total_score >= 0.7:
        print("✅ GOOD - Solid RAG performance with minor optimizations needed")
    elif total_score >= 0.6:
        print("👍 ACCEPTABLE - Adequate for RAG with some improvements")
    else:
        print("⚠️  NEEDS OPTIMIZATION - Significant RAG improvements required")
    
    print("\n🎯 KEY RECOMMENDATIONS FOR RAG OPTIMIZATION:")
    if precision_score < 0.8:
        print("  • Improve query matching precision with better keywords and unique identifiers")
    if avg_completeness < 0.9:
        print("  • Ensure all profiles have complete information for better context")
    if avg_generation_quality < 0.8:
        print("  • Enhance content richness to support better response generation")
    if avg_personalization < 0.8:
        print("  • Add more personalization context (language, channel, geography)")
    if avg_consistency < 0.9:
        print("  • Fix data consistency issues to prevent hallucination")
    if avg_chunk_quality < 0.8:
        print("  • Optimize profile structure and size for better chunking")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'profiles_analyzed': len(profiles),
        'rag_metrics': {
            'query_precision': precision_score,
            'completeness': avg_completeness,
            'generation_quality': avg_generation_quality,
            'personalization_support': avg_personalization,
            'data_consistency': avg_consistency,
            'chunk_quality': avg_chunk_quality
        },
        'issues_found': {
            'ambiguous_names': ambiguous_count,
            'incomplete_profiles': len(incomplete_profiles),
            'insufficient_content': len(insufficient_content),
            'limited_personalization': len(limited_personalization),
            'consistency_issues': len(consistency_issues),
            'suboptimal_chunks': len(suboptimal_chunks)
        }
    }

if __name__ == "__main__":
    results = evaluate_rag_performance_optimization() 