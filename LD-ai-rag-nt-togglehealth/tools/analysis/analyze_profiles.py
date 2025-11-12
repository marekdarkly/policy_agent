#!/usr/bin/env python3
"""
Comprehensive Analysis of ToggleBank Customer Profile Files
Identifies duplicates, variations, and quality issues for cleanup
"""
import os
import json
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import datetime

def read_profile_file(filepath):
    """Read and parse a customer profile file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            lines = content.split('\n')
            
            profile_data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    profile_data[key.strip()] = value.strip()
            
            return {
                'file': os.path.basename(filepath),
                'profile': profile_data,
                'raw_content': content
            }
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return None

def extract_first_name(full_name):
    """Extract first name from profile name"""
    # Handle formats like "Hayden X." or "Jordan E."
    parts = full_name.split()
    return parts[0] if parts else ""

def analyze_profiles():
    """Main analysis function for customer profiles"""
    profiles_dir = "samples/togglebank_profiles_txt"
    
    if not os.path.exists(profiles_dir):
        print(f"Directory {profiles_dir} not found!")
        return
    
    # Read all profile files
    profiles = []
    for filename in sorted(os.listdir(profiles_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(profiles_dir, filename)
            profile = read_profile_file(filepath)
            if profile:
                profiles.append(profile)
    
    print(f"📊 Analyzed {len(profiles)} customer profile files")
    print("="*80)
    
    # Extract all field values for analysis
    all_names = []
    all_cities = []
    all_tiers = []
    all_languages = []
    all_channels = []
    all_balances = []
    
    for profile in profiles:
        data = profile['profile']
        all_names.append(data.get('Name', ''))
        all_cities.append(data.get('City', ''))
        all_tiers.append(data.get('Account Tier', ''))
        all_languages.append(data.get('Language Preference', ''))
        all_channels.append(data.get('Preferred Channel', ''))
        all_balances.append(data.get('Average Balance', ''))
    
    # Analyze name similarities
    print("🔍 NAME SIMILARITY ANALYSIS")
    print("="*50)
    
    first_names = [extract_first_name(name) for name in all_names]
    name_counts = Counter(first_names)
    
    # Find similar names
    similar_names = []
    unique_names = list(set(first_names))
    
    for i, name1 in enumerate(unique_names):
        for j, name2 in enumerate(unique_names[i+1:], i+1):
            similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            if similarity > 0.7 and similarity < 1.0:  # Similar but not identical
                similar_names.append((name1, name2, similarity))
    
    duplicate_names = [name for name, count in name_counts.items() if count > 1]
    
    print(f"📈 Total unique first names: {len(unique_names)}")
    print(f"📈 Duplicate first names: {len(duplicate_names)}")
    print(f"📈 Similar name pairs: {len(similar_names)}")
    
    if duplicate_names:
        print(f"\n🔴 TOP DUPLICATE NAMES:")
        for name in sorted(duplicate_names, key=lambda x: name_counts[x], reverse=True)[:10]:
            print(f"  • {name}: {name_counts[name]} occurrences")
    
    if similar_names:
        print(f"\n🟡 SIMILAR NAME PAIRS:")
        for name1, name2, sim in sorted(similar_names, key=lambda x: x[2], reverse=True)[:10]:
            print(f"  • {name1} ↔ {name2} (similarity: {sim:.2f})")
    
    # Analyze data consistency
    print(f"\n🧐 DATA CONSISTENCY ANALYSIS")
    print("="*50)
    
    # Check for data format issues
    format_issues = {
        'invalid_cities': [],
        'invalid_tiers': [],
        'invalid_languages': [],
        'invalid_channels': [],
        'invalid_balances': [],
        'invalid_dates': []
    }
    
    valid_tiers = {'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'}
    valid_channels = {'mobile', 'web', 'phone', 'branch'}
    valid_languages = {'en', 'es', 'fr', 'de', 'zh'}
    valid_balance_patterns = [r'<1k', r'\d+k-\d+k', r'>\d+k']
    
    for profile in profiles:
        data = profile['profile']
        
        # Check cities (should have state)
        city = data.get('City', '')
        if city and ', ' not in city:
            format_issues['invalid_cities'].append((profile['file'], city))
        
        # Check account tiers
        tier = data.get('Account Tier', '')
        if tier and tier not in valid_tiers:
            format_issues['invalid_tiers'].append((profile['file'], tier))
        
        # Check languages (should be 2-char codes)
        lang = data.get('Language Preference', '').rstrip('.')
        if lang and lang not in valid_languages:
            format_issues['invalid_languages'].append((profile['file'], lang))
        
        # Check channels
        channel = data.get('Preferred Channel', '')
        if channel and channel not in valid_channels:
            format_issues['invalid_channels'].append((profile['file'], channel))
        
        # Check balance format
        balance = data.get('Average Balance', '')
        if balance and not any(re.match(pattern, balance) for pattern in valid_balance_patterns):
            format_issues['invalid_balances'].append((profile['file'], balance))
        
        # Check date formats
        for date_field in ['Account Since', 'Last Login']:
            date_str = data.get(date_field, '')
            if date_str:
                try:
                    datetime.datetime.strptime(date_str, '%Y-%m-%d')
                except ValueError:
                    format_issues['invalid_dates'].append((profile['file'], date_field, date_str))
    
    print("Data Format Issues:")
    for issue_type, issues in format_issues.items():
        if issues:
            print(f"  • {issue_type.replace('_', ' ').title()}: {len(issues)} files")
    
    # Analyze value distributions
    print(f"\n📊 VALUE DISTRIBUTIONS")
    print("="*50)
    
    tier_dist = Counter(all_tiers)
    lang_dist = Counter(all_languages)
    channel_dist = Counter(all_channels)
    balance_dist = Counter(all_balances)
    
    print("Account Tier Distribution:")
    for tier, count in tier_dist.most_common():
        percentage = (count / len(profiles)) * 100
        print(f"  • {tier}: {count} ({percentage:.1f}%)")
    
    print("\nLanguage Distribution:")
    for lang, count in lang_dist.most_common():
        percentage = (count / len(profiles)) * 100
        print(f"  • {lang}: {count} ({percentage:.1f}%)")
    
    print("\nChannel Distribution:")
    for channel, count in channel_dist.most_common():
        percentage = (count / len(profiles)) * 100
        print(f"  • {channel}: {count} ({percentage:.1f}%)")
    
    # Analyze geographic diversity
    print(f"\n🌍 GEOGRAPHIC DIVERSITY")
    print("="*50)
    
    states = []
    cities_only = []
    for city in all_cities:
        if ', ' in city:
            city_name, state = city.split(', ')
            states.append(state)
            cities_only.append(city_name)
        else:
            cities_only.append(city)
    
    state_dist = Counter(states)
    city_dist = Counter(cities_only)
    
    print(f"Unique states: {len(set(states))}")
    print(f"Unique cities: {len(set(cities_only))}")
    
    print("\nTop 10 States:")
    for state, count in state_dist.most_common(10):
        percentage = (count / len(states)) * 100 if states else 0
        print(f"  • {state}: {count} ({percentage:.1f}%)")
    
    # Quality assessment
    print(f"\n🏆 OVERALL QUALITY ASSESSMENT")
    print("="*50)
    
    quality_scores = {
        'name_uniqueness': len(unique_names) / len(profiles),
        'data_completeness': sum(1 for p in profiles if len(p['profile']) >= 8) / len(profiles),
        'format_consistency': 1 - sum(len(issues) for issues in format_issues.values()) / (len(profiles) * len(format_issues)),
        'geographic_diversity': len(set(states)) / max(1, len(states)) if states else 0
    }
    
    overall_quality = sum(quality_scores.values()) / len(quality_scores)
    
    print("Quality Metrics:")
    for metric, score in quality_scores.items():
        print(f"  • {metric.replace('_', ' ').title()}: {score:.3f}")
    
    print(f"\n📊 OVERALL QUALITY SCORE: {overall_quality:.3f}")
    
    if overall_quality >= 0.9:
        print("🎉 EXCELLENT - High quality profiles")
    elif overall_quality >= 0.8:
        print("✅ GOOD - Minor improvements needed") 
    elif overall_quality >= 0.7:
        print("⚠️  FAIR - Some quality issues to address")
    else:
        print("❌ POOR - Significant quality improvements needed")
    
    # Generate cleanup recommendations
    print(f"\n🛠️  CLEANUP RECOMMENDATIONS")
    print("="*50)
    
    recommendations = []
    
    if len(duplicate_names) > 0:
        recommendations.append(f"🔄 Replace {len(duplicate_names)} duplicate names with unique full names")
    
    if len(similar_names) > 10:
        recommendations.append(f"📝 Review {len(similar_names)} similar name pairs for better diversity")
    
    total_format_issues = sum(len(issues) for issues in format_issues.values())
    if total_format_issues > 0:
        recommendations.append(f"🔧 Fix {total_format_issues} data format inconsistencies")
    
    if len(set(states)) < 20:
        recommendations.append("🌎 Increase geographic diversity across more states")
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    return {
        'total_profiles': len(profiles),
        'unique_names': len(unique_names),
        'duplicate_names': len(duplicate_names),
        'similar_names': len(similar_names),
        'format_issues': format_issues,
        'quality_scores': quality_scores,
        'overall_quality': overall_quality,
        'distributions': {
            'tiers': dict(tier_dist),
            'languages': dict(lang_dist),
            'channels': dict(channel_dist),
            'states': dict(state_dist.most_common(10))
        }
    }

if __name__ == "__main__":
    results = analyze_profiles() 