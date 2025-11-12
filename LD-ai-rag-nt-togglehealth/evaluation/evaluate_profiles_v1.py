#!/usr/bin/env python3
"""
EVALUATION #1: Customer Data Accuracy & Consistency
Evaluates cleaned customer profiles for data reliability and quality
"""
import os
import json
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher
from datetime import datetime
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
                        'profile': profile_data
                    })
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return profiles

def calculate_name_diversity(profiles):
    """Calculate diversity of customer names"""
    full_names = [profile['profile'].get('Name', '') for profile in profiles]
    first_names = [name.split()[0] for name in full_names if name]
    last_names = [name.split()[-1] for name in full_names if name and len(name.split()) > 1]
    
    return {
        'total_names': len(full_names),
        'unique_full_names': len(set(full_names)),
        'unique_first_names': len(set(first_names)),
        'unique_last_names': len(set(last_names)),
        'full_name_uniqueness': len(set(full_names)) / len(full_names) if full_names else 0,
        'first_name_diversity': len(set(first_names)) / len(first_names) if first_names else 0
    }

def evaluate_customer_data_accuracy_consistency():
    """Evaluate customer profiles for data accuracy and consistency"""
    profiles = load_cleaned_profiles()
    
    if not profiles:
        print("No profiles found!")
        return
    
    print("🎯 EVALUATION #1: CUSTOMER DATA ACCURACY & CONSISTENCY")
    print("="*60)
    print("Focus: How reliable and consistent is the customer profile data?")
    print()
    
    # Criterion 1: Name Quality & Uniqueness
    print("1️⃣ NAME QUALITY & UNIQUENESS")
    print("-" * 40)
    
    name_stats = calculate_name_diversity(profiles)
    
    # Check for name format consistency
    names = [profile['profile'].get('Name', '') for profile in profiles]
    name_format_issues = []
    similar_names = []
    
    for i, name1 in enumerate(names):
        # Check format (should be "First Last")
        if not re.match(r'^[A-Z][a-z]+ [A-Z][a-z\']+(-[A-Z][a-z\']+)*$', name1):
            if name1:  # Only count non-empty names
                name_format_issues.append((profiles[i]['file'], name1))
        
        # Check for similar names
        for j, name2 in enumerate(names[i+1:], i+1):
            if name1 and name2:
                similarity = SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
                if similarity > 0.8 and similarity < 1.0:
                    similar_names.append((name1, name2, similarity))
    
    print(f"   📊 Total profiles: {len(profiles)}")
    print(f"   📊 Unique full names: {name_stats['unique_full_names']}/{name_stats['total_names']}")
    print(f"   📊 Name uniqueness score: {name_stats['full_name_uniqueness']:.3f}")
    print(f"   📊 First name diversity: {name_stats['first_name_diversity']:.3f}")
    
    if name_format_issues:
        print(f"   ⚠️  Name format issues: {len(name_format_issues)} profiles")
        for file, name in name_format_issues[:3]:
            print(f"      • {file}: '{name}'")
    else:
        print("   ✅ All names properly formatted")
    
    if similar_names:
        print(f"   ⚠️  Similar names found: {len(similar_names)} pairs")
        for name1, name2, sim in similar_names[:3]:
            print(f"      • '{name1}' ↔ '{name2}' (similarity: {sim:.2f})")
    else:
        print("   ✅ No confusingly similar names")
    
    # Criterion 2: Geographic Data Consistency
    print("\n2️⃣ GEOGRAPHIC DATA CONSISTENCY")
    print("-" * 40)
    
    cities = [profile['profile'].get('City', '') for profile in profiles]
    geographic_issues = []
    valid_city_formats = 0
    
    states = []
    city_names = []
    
    for i, city in enumerate(cities):
        if city:
            # Check format (should be "City, ST")
            if re.match(r'^[A-Za-z\s\'-]+, [A-Z]{2}$', city):
                valid_city_formats += 1
                city_name, state = city.split(', ')
                states.append(state)
                city_names.append(city_name)
            else:
                geographic_issues.append((profiles[i]['file'], city))
    
    state_counts = Counter(states)
    city_counts = Counter(cities)
    
    # Check for geographic diversity
    unique_states = len(set(states))
    unique_cities = len(set(cities))
    geographic_concentration = max(state_counts.values()) / len(states) if states else 0
    
    print(f"   📊 Valid city formats: {valid_city_formats}/{len(profiles)}")
    print(f"   📊 Unique states: {unique_states}")
    print(f"   📊 Unique cities: {unique_cities}")
    print(f"   📊 Geographic concentration: {geographic_concentration:.3f}")
    
    if geographic_issues:
        print(f"   ⚠️  Geographic format issues: {len(geographic_issues)} profiles")
        for file, city in geographic_issues[:3]:
            print(f"      • {file}: '{city}'")
    else:
        print("   ✅ All geographic data properly formatted")
    
    # Criterion 3: Data Type Validation
    print("\n3️⃣ DATA TYPE VALIDATION")
    print("-" * 40)
    
    validation_scores = {
        'valid_tiers': 0,
        'valid_dates': 0,
        'valid_balances': 0,
        'valid_points': 0,
        'valid_channels': 0,
        'valid_languages': 0
    }
    
    validation_issues = defaultdict(list)
    
    valid_tiers = {'Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond'}
    valid_channels = {'mobile', 'web', 'phone', 'branch'}
    valid_languages = {'en', 'es', 'fr', 'de', 'zh'}
    
    for profile in profiles:
        data = profile['profile']
        file = profile['file']
        
        # Check account tier
        tier = data.get('Account Tier', '')
        if tier in valid_tiers:
            validation_scores['valid_tiers'] += 1
        elif tier:
            validation_issues['invalid_tiers'].append((file, tier))
        
        # Check dates
        valid_date_count = 0
        for date_field in ['Account Since', 'Last Login']:
            date_str = data.get(date_field, '')
            if date_str:
                try:
                    datetime.strptime(date_str, '%Y-%m-%d')
                    valid_date_count += 1
                except ValueError:
                    validation_issues['invalid_dates'].append((file, date_field, date_str))
        
        if valid_date_count == 2:
            validation_scores['valid_dates'] += 1
        
        # Check balance format
        balance = data.get('Average Balance', '')
        if balance and re.match(r'^(<1k|\d+k-\d+k|>\d+k)$', balance):
            validation_scores['valid_balances'] += 1
        elif balance:
            validation_issues['invalid_balances'].append((file, balance))
        
        # Check rewards points (should be numeric)
        points = data.get('Rewards Points', '')
        if points and points.isdigit():
            validation_scores['valid_points'] += 1
        elif points:
            validation_issues['invalid_points'].append((file, points))
        
        # Check preferred channel
        channel = data.get('Preferred Channel', '')
        if channel in valid_channels:
            validation_scores['valid_channels'] += 1
        elif channel:
            validation_issues['invalid_channels'].append((file, channel))
        
        # Check language preference
        language = data.get('Language Preference', '')
        if language in valid_languages:
            validation_scores['valid_languages'] += 1
        elif language:
            validation_issues['invalid_languages'].append((file, language))
    
    total_profiles = len(profiles)
    
    print("   Data Type Validation Scores:")
    for validation_type, score in validation_scores.items():
        percentage = (score / total_profiles) * 100 if total_profiles > 0 else 0
        print(f"     • {validation_type.replace('_', ' ').title()}: {score}/{total_profiles} ({percentage:.1f}%)")
    
    if validation_issues:
        print("   ⚠️  Validation Issues Found:")
        for issue_type, issues in validation_issues.items():
            if issues:
                print(f"     • {issue_type.replace('_', ' ').title()}: {len(issues)} cases")
    
    # Criterion 4: Logical Data Consistency
    print("\n4️⃣ LOGICAL DATA CONSISTENCY")
    print("-" * 40)
    
    logical_issues = []
    logical_consistency_score = 0
    
    for profile in profiles:
        data = profile['profile']
        file = profile['file']
        
        issues_found = []
        
        # Check date logic (Account Since should be before Last Login)
        account_since = data.get('Account Since', '')
        last_login = data.get('Last Login', '')
        
        if account_since and last_login:
            try:
                since_date = datetime.strptime(account_since, '%Y-%m-%d')
                login_date = datetime.strptime(last_login, '%Y-%m-%d')
                
                if since_date > login_date:
                    issues_found.append("Account Since after Last Login")
                
                # Check if dates are reasonable (not in far future)
                now = datetime.now()
                if since_date > now or login_date > now:
                    issues_found.append("Future dates")
                    
                # Check if account is too old (before 2010)
                if since_date.year < 2010:
                    issues_found.append("Account too old")
                    
            except ValueError:
                pass  # Already caught in data type validation
        
        # Check tier vs balance consistency
        tier = data.get('Account Tier', '')
        balance = data.get('Average Balance', '')
        
        if tier and balance:
            # Basic tier-balance consistency check
            if tier == 'Diamond' and balance == '<1k':
                issues_found.append("Diamond tier with low balance")
            elif tier == 'Bronze' and balance.startswith('>'):
                issues_found.append("Bronze tier with very high balance")
        
        # Check rewards points reasonableness
        points = data.get('Rewards Points', '')
        if points and points.isdigit():
            points_val = int(points)
            if points_val > 1000000:  # Unreasonably high
                issues_found.append("Unreasonably high rewards points")
            elif points_val < 0:
                issues_found.append("Negative rewards points")
        
        if not issues_found:
            logical_consistency_score += 1
        else:
            logical_issues.append((file, issues_found))
    
    logical_score = logical_consistency_score / total_profiles if total_profiles > 0 else 0
    
    print(f"   📊 Logically consistent profiles: {logical_consistency_score}/{total_profiles} ({logical_score:.3f})")
    
    if logical_issues:
        print(f"   ⚠️  Logical inconsistencies found: {len(logical_issues)} profiles")
        for file, issues in logical_issues[:3]:
            print(f"      • {file}: {', '.join(issues)}")
    else:
        print("   ✅ All profiles logically consistent")
    
    # Overall Customer Data Accuracy Score
    print("\n📊 OVERALL CUSTOMER DATA ACCURACY & CONSISTENCY SCORE")
    print("="*50)
    
    component_scores = {
        'Name Quality': name_stats['full_name_uniqueness'] * 0.25,
        'Geographic Consistency': (valid_city_formats / total_profiles) * 0.25,
        'Data Type Validation': (sum(validation_scores.values()) / (len(validation_scores) * total_profiles)) * 0.25,
        'Logical Consistency': logical_score * 0.25
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n🎯 FINAL DATA ACCURACY SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🏆 EXCEPTIONAL - Outstanding data quality")
    elif total_score >= 0.8:
        print("⭐ EXCELLENT - High quality customer data")
    elif total_score >= 0.7:
        print("✅ GOOD - Reliable data with minor issues")
    elif total_score >= 0.6:
        print("👍 ACCEPTABLE - Generally reliable data")
    else:
        print("⚠️  NEEDS IMPROVEMENT - Data quality concerns")
    
    print("\n🔧 KEY RECOMMENDATIONS FOR DATA QUALITY:")
    if name_stats['full_name_uniqueness'] < 0.95:
        print("  • Ensure all customer names are completely unique")
    if (valid_city_formats / total_profiles) < 0.95:
        print("  • Standardize geographic data formatting")
    if (sum(validation_scores.values()) / (len(validation_scores) * total_profiles)) < 0.9:
        print("  • Fix data type validation issues")
    if logical_score < 0.9:
        print("  • Resolve logical data inconsistencies")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'profiles_analyzed': len(profiles),
        'name_stats': name_stats,
        'validation_scores': validation_scores,
        'issues_found': {
            'name_format_issues': len(name_format_issues),
            'similar_names': len(similar_names),
            'geographic_issues': len(geographic_issues),
            'validation_issues': sum(len(issues) for issues in validation_issues.values()),
            'logical_issues': len(logical_issues)
        }
    }

if __name__ == "__main__":
    results = evaluate_customer_data_accuracy_consistency() 