#!/usr/bin/env python3
"""
EVALUATION #2: Diversity & Representation
Evaluates cleaned customer profiles for demographic and geographic diversity
"""
import os
import json
import re
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import statistics
import math

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

def calculate_diversity_index(values):
    """Calculate Shannon diversity index for a list of values"""
    if not values:
        return 0
    
    counter = Counter(values)
    total = len(values)
    
    # Shannon diversity index
    shannon = 0
    for count in counter.values():
        if count > 0:
            proportion = count / total
            shannon -= proportion * math.log(proportion)
    
    # Normalize to 0-1 scale
    max_shannon = math.log(len(counter)) if len(counter) > 1 else 0
    return shannon / max_shannon if max_shannon > 0 else 0

def analyze_name_origins(names):
    """Analyze the cultural/ethnic diversity of names"""
    name_origins = {
        'Western': ['Alexander', 'Benjamin', 'Catherine', 'Diana', 'Edward', 'Margaret', 'Nicholas', 'Olivia', 'Patrick', 'Rebecca', 'Sebastian', 'Victoria'],
        'Hispanic/Latino': ['Carmen', 'Esperanza', 'Joaquin', 'Lucia', 'Mateo', 'Rosa'],
        'Asian': ['Akira', 'Hiroshi', 'Kenji', 'Takeshi'],
        'Arabic/Middle Eastern': ['Fatima', 'Omar', 'Qadir'],
        'Modern/Contemporary': ['Aria', 'Blake', 'Chloe', 'Damon', 'Eva', 'Finn', 'Grace', 'Hunter', 'Ivy', 'Jaxon', 'Kai', 'Luna', 'Mason', 'Nova', 'Owen', 'Piper', 'Quinn', 'River', 'Sage', 'Zara'],
        'International': ['Bianca', 'Dmitri', 'Giuseppe', 'Ingrid', 'Nadia', 'Priya', 'Soren']
    }
    
    origin_counts = defaultdict(int)
    unclassified = 0
    
    for name in names:
        first_name = name.split()[0] if name else ''
        classified = False
        
        for origin, origin_names in name_origins.items():
            if first_name in origin_names:
                origin_counts[origin] += 1
                classified = True
                break
        
        if not classified and first_name:
            unclassified += 1
    
    return dict(origin_counts), unclassified

def evaluate_diversity_representation():
    """Evaluate customer profiles for diversity and representation"""
    profiles = load_cleaned_profiles()
    
    if not profiles:
        print("No profiles found!")
        return
    
    print("🌍 EVALUATION #2: DIVERSITY & REPRESENTATION")
    print("="*60)
    print("Focus: How well do these profiles represent a diverse customer base?")
    print()
    
    # Criterion 1: Name/Cultural Diversity
    print("1️⃣ NAME & CULTURAL DIVERSITY")
    print("-" * 40)
    
    names = [profile['profile'].get('Name', '') for profile in profiles]
    first_names = [name.split()[0] for name in names if name]
    last_names = [name.split()[-1] for name in names if name and len(name.split()) > 1]
    
    # Analyze name origins
    origin_counts, unclassified = analyze_name_origins(names)
    
    # Calculate name diversity indices
    first_name_diversity = calculate_diversity_index(first_names)
    last_name_diversity = calculate_diversity_index(last_names)
    
    print(f"   📊 Total profiles: {len(profiles)}")
    print(f"   📊 Unique first names: {len(set(first_names))}")
    print(f"   📊 Unique last names: {len(set(last_names))}")
    print(f"   📊 First name diversity index: {first_name_diversity:.3f}")
    print(f"   📊 Last name diversity index: {last_name_diversity:.3f}")
    
    print("\n   Cultural Name Distribution:")
    total_classified = sum(origin_counts.values())
    for origin, count in sorted(origin_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {origin}: {count} ({percentage:.1f}%)")
    
    if unclassified > 0:
        percentage = (unclassified / len(profiles)) * 100
        print(f"     • Unclassified: {unclassified} ({percentage:.1f}%)")
    
    # Calculate cultural diversity score
    cultural_diversity = calculate_diversity_index(list(origin_counts.keys()) * len(profiles))
    
    # Criterion 2: Geographic Diversity
    print("\n2️⃣ GEOGRAPHIC DIVERSITY")
    print("-" * 40)
    
    cities = [profile['profile'].get('City', '') for profile in profiles]
    states = [city.split(', ')[1] if ', ' in city else '' for city in cities]
    regions = []
    
    # Classify states into regions
    state_regions = {
        'Northeast': ['NY', 'PA', 'MA', 'CT', 'RI', 'VT', 'NH', 'ME', 'NJ'],
        'Southeast': ['FL', 'GA', 'NC', 'SC', 'VA', 'WV', 'KY', 'TN', 'AL', 'MS', 'AR', 'LA'],
        'Midwest': ['OH', 'IN', 'IL', 'MI', 'WI', 'MN', 'IA', 'MO', 'ND', 'SD', 'NE', 'KS'],
        'Southwest': ['TX', 'OK', 'NM', 'AZ'],
        'West': ['CA', 'NV', 'UT', 'CO', 'WY', 'MT', 'ID', 'WA', 'OR'],
        'Pacific': ['HI', 'AK']
    }
    
    for state in states:
        if state:
            for region, region_states in state_regions.items():
                if state in region_states:
                    regions.append(region)
                    break
    
    # Calculate geographic diversity metrics
    state_diversity = calculate_diversity_index(states)
    city_diversity = calculate_diversity_index(cities)
    region_diversity = calculate_diversity_index(regions)
    
    unique_states = len(set(state for state in states if state))
    unique_cities = len(set(city for city in cities if city))
    unique_regions = len(set(regions))
    
    print(f"   📊 Unique states: {unique_states}")
    print(f"   📊 Unique cities: {unique_cities}")
    print(f"   📊 Unique regions: {unique_regions}")
    print(f"   📊 State diversity index: {state_diversity:.3f}")
    print(f"   📊 City diversity index: {city_diversity:.3f}")
    print(f"   📊 Regional diversity index: {region_diversity:.3f}")
    
    # Show regional distribution
    region_counts = Counter(regions)
    print("\n   Regional Distribution:")
    for region, count in region_counts.most_common():
        percentage = (count / len(regions)) * 100 if regions else 0
        print(f"     • {region}: {count} ({percentage:.1f}%)")
    
    # Criterion 3: Socioeconomic Diversity
    print("\n3️⃣ SOCIOECONOMIC DIVERSITY")
    print("-" * 40)
    
    tiers = [profile['profile'].get('Account Tier', '') for profile in profiles]
    balances = [profile['profile'].get('Average Balance', '') for profile in profiles]
    
    # Analyze tier distribution
    tier_counts = Counter(tiers)
    tier_diversity = calculate_diversity_index(tiers)
    
    # Analyze balance distribution
    balance_counts = Counter(balances)
    balance_diversity = calculate_diversity_index(balances)
    
    print(f"   📊 Account tier diversity: {tier_diversity:.3f}")
    print(f"   📊 Balance range diversity: {balance_diversity:.3f}")
    
    print("\n   Account Tier Distribution:")
    for tier, count in tier_counts.most_common():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {tier}: {count} ({percentage:.1f}%)")
    
    print("\n   Balance Range Distribution:")
    for balance, count in balance_counts.most_common():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {balance}: {count} ({percentage:.1f}%)")
    
    # Check for realistic tier distribution (should be pyramid-like)
    expected_tier_order = ['Bronze', 'Silver', 'Gold', 'Platinum', 'Diamond']
    tier_distribution_score = 0
    
    for i in range(len(expected_tier_order) - 1):
        current_tier = expected_tier_order[i]
        next_tier = expected_tier_order[i + 1]
        
        current_count = tier_counts.get(current_tier, 0)
        next_count = tier_counts.get(next_tier, 0)
        
        if current_count >= next_count:
            tier_distribution_score += 1
    
    tier_distribution_score = tier_distribution_score / (len(expected_tier_order) - 1)
    
    # Criterion 4: Behavioral/Preference Diversity
    print("\n4️⃣ BEHAVIORAL & PREFERENCE DIVERSITY")
    print("-" * 40)
    
    channels = [profile['profile'].get('Preferred Channel', '') for profile in profiles]
    languages = [profile['profile'].get('Language Preference', '') for profile in profiles]
    
    # Calculate behavioral diversity
    channel_diversity = calculate_diversity_index(channels)
    language_diversity = calculate_diversity_index(languages)
    
    channel_counts = Counter(channels)
    language_counts = Counter(languages)
    
    print(f"   📊 Channel preference diversity: {channel_diversity:.3f}")
    print(f"   📊 Language preference diversity: {language_diversity:.3f}")
    
    print("\n   Channel Distribution:")
    for channel, count in channel_counts.most_common():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {channel}: {count} ({percentage:.1f}%)")
    
    print("\n   Language Distribution:")
    for language, count in language_counts.most_common():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {language}: {count} ({percentage:.1f}%)")
    
    # Criterion 5: Temporal Diversity
    print("\n5️⃣ TEMPORAL DIVERSITY")
    print("-" * 40)
    
    account_years = []
    login_years = []
    
    for profile in profiles:
        data = profile['profile']
        
        account_since = data.get('Account Since', '')
        last_login = data.get('Last Login', '')
        
        if account_since:
            try:
                year = int(account_since.split('-')[0])
                account_years.append(year)
            except (ValueError, IndexError):
                pass
        
        if last_login:
            try:
                year = int(last_login.split('-')[0])
                login_years.append(year)
            except (ValueError, IndexError):
                pass
    
    # Calculate temporal diversity
    account_year_diversity = calculate_diversity_index(account_years)
    login_year_diversity = calculate_diversity_index(login_years)
    
    account_year_range = max(account_years) - min(account_years) if account_years else 0
    login_year_range = max(login_years) - min(login_years) if login_years else 0
    
    print(f"   📊 Account creation year diversity: {account_year_diversity:.3f}")
    print(f"   📊 Last login year diversity: {login_year_diversity:.3f}")
    print(f"   📊 Account creation year range: {account_year_range} years")
    print(f"   📊 Login activity year range: {login_year_range} years")
    
    if account_years:
        account_year_counts = Counter(account_years)
        print("\n   Account Creation Year Distribution:")
        for year, count in sorted(account_year_counts.items()):
            percentage = (count / len(account_years)) * 100
            print(f"     • {year}: {count} ({percentage:.1f}%)")
    
    # Overall Diversity & Representation Score
    print("\n📊 OVERALL DIVERSITY & REPRESENTATION SCORE")
    print("="*50)
    
    component_scores = {
        'Cultural Diversity': (first_name_diversity + last_name_diversity + cultural_diversity) / 3 * 0.25,
        'Geographic Diversity': (state_diversity + region_diversity) / 2 * 0.25,
        'Socioeconomic Diversity': (tier_diversity + balance_diversity + tier_distribution_score) / 3 * 0.25,
        'Behavioral Diversity': (channel_diversity + language_diversity) / 2 * 0.15,
        'Temporal Diversity': (account_year_diversity + login_year_diversity) / 2 * 0.10
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n🌍 FINAL DIVERSITY & REPRESENTATION SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🌟 EXCEPTIONAL - Outstanding diversity and representation")
    elif total_score >= 0.8:
        print("⭐ EXCELLENT - Very diverse and representative")
    elif total_score >= 0.7:
        print("✅ GOOD - Well-balanced diversity")
    elif total_score >= 0.6:
        print("👍 ACCEPTABLE - Moderate diversity")
    else:
        print("⚠️  NEEDS IMPROVEMENT - Limited diversity")
    
    print("\n🎯 KEY RECOMMENDATIONS FOR DIVERSITY:")
    if (first_name_diversity + last_name_diversity + cultural_diversity) / 3 < 0.8:
        print("  • Increase cultural and ethnic name diversity")
    if (state_diversity + region_diversity) / 2 < 0.8:
        print("  • Expand geographic representation across more regions")
    if (tier_diversity + balance_diversity) / 2 < 0.8:
        print("  • Balance socioeconomic representation")
    if (channel_diversity + language_diversity) / 2 < 0.8:
        print("  • Diversify behavioral preferences and languages")
    if (account_year_diversity + login_year_diversity) / 2 < 0.7:
        print("  • Include customers from broader time ranges")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'profiles_analyzed': len(profiles),
        'diversity_metrics': {
            'cultural_origins': origin_counts,
            'geographic_distribution': dict(region_counts),
            'tier_distribution': dict(tier_counts),
            'channel_distribution': dict(channel_counts),
            'language_distribution': dict(language_counts)
        },
        'diversity_indices': {
            'name_diversity': (first_name_diversity + last_name_diversity) / 2,
            'geographic_diversity': (state_diversity + region_diversity) / 2,
            'socioeconomic_diversity': (tier_diversity + balance_diversity) / 2,
            'behavioral_diversity': (channel_diversity + language_diversity) / 2
        }
    }

if __name__ == "__main__":
    results = evaluate_diversity_representation() 