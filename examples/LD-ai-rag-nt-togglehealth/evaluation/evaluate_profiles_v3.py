#!/usr/bin/env python3
"""
EVALUATION #3: Business Utility & Analytics Value
Evaluates cleaned customer profiles for business analysis and customer insights
"""
import os
import json
import re
from collections import defaultdict, Counter
from datetime import datetime, timedelta
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

def parse_balance_range(balance_str):
    """Parse balance range string into numeric values"""
    if balance_str == '<1k':
        return 0, 1000
    elif balance_str.startswith('>'):
        min_val = int(balance_str[1:-1]) * 1000
        return min_val, min_val * 10  # Assume upper bound
    elif '-' in balance_str:
        parts = balance_str.split('-')
        min_val = int(parts[0][:-1]) * 1000
        max_val = int(parts[1][:-1]) * 1000
        return min_val, max_val
    else:
        return 0, 0

def calculate_customer_lifetime_value_potential(profile_data):
    """Estimate CLV potential based on profile data"""
    tier = profile_data.get('Account Tier', '')
    balance_str = profile_data.get('Average Balance', '')
    
    # Tier-based scoring
    tier_scores = {
        'Diamond': 1.0,
        'Platinum': 0.8,
        'Gold': 0.6,
        'Silver': 0.4,
        'Bronze': 0.2
    }
    
    tier_score = tier_scores.get(tier, 0.2)
    
    # Balance-based scoring
    min_balance, max_balance = parse_balance_range(balance_str)
    avg_balance = (min_balance + max_balance) / 2
    
    # Normalize balance score (log scale for better distribution)
    import math
    balance_score = min(1.0, math.log10(max(avg_balance, 1)) / 6)  # Assuming $1M as top
    
    # Account age factor
    account_since = profile_data.get('Account Since', '')
    if account_since:
        try:
            account_date = datetime.strptime(account_since, '%Y-%m-%d')
            years_active = (datetime.now() - account_date).days / 365.25
            age_score = min(1.0, years_active / 10)  # 10 years = max score
        except ValueError:
            age_score = 0.5
    else:
        age_score = 0.5
    
    # Combined CLV potential
    clv_potential = (tier_score * 0.4 + balance_score * 0.4 + age_score * 0.2)
    return clv_potential

def evaluate_business_utility_analytics():
    """Evaluate customer profiles for business utility and analytics value"""
    profiles = load_cleaned_profiles()
    
    if not profiles:
        print("No profiles found!")
        return
    
    print("💼 EVALUATION #3: BUSINESS UTILITY & ANALYTICS VALUE")
    print("="*60)
    print("Focus: How useful are these profiles for business analysis and insights?")
    print()
    
    # Criterion 1: Customer Segmentation Capability
    print("1️⃣ CUSTOMER SEGMENTATION CAPABILITY")
    print("-" * 40)
    
    # Analyze segmentation dimensions
    tiers = [profile['profile'].get('Account Tier', '') for profile in profiles]
    balances = [profile['profile'].get('Average Balance', '') for profile in profiles]
    channels = [profile['profile'].get('Preferred Channel', '') for profile in profiles]
    languages = [profile['profile'].get('Language Preference', '') for profile in profiles]
    
    # Geographic segmentation
    cities = [profile['profile'].get('City', '') for profile in profiles]
    states = [city.split(', ')[1] if ', ' in city else '' for city in cities]
    
    # Calculate segmentation quality
    tier_segments = len(set(tiers))
    balance_segments = len(set(balances))
    channel_segments = len(set(channels))
    language_segments = len(set(languages))
    geographic_segments = len(set(states))
    
    # Check for meaningful distribution in each segment
    tier_counts = Counter(tiers)
    min_tier_size = min(tier_counts.values()) if tier_counts else 0
    max_tier_size = max(tier_counts.values()) if tier_counts else 0
    tier_balance = min_tier_size / max_tier_size if max_tier_size > 0 else 0
    
    balance_counts = Counter(balances)
    min_balance_size = min(balance_counts.values()) if balance_counts else 0
    max_balance_size = max(balance_counts.values()) if balance_counts else 0
    balance_balance = min_balance_size / max_balance_size if max_balance_size > 0 else 0
    
    print(f"   📊 Available tier segments: {tier_segments}")
    print(f"   📊 Available balance segments: {balance_segments}")
    print(f"   📊 Available channel segments: {channel_segments}")
    print(f"   📊 Available language segments: {language_segments}")
    print(f"   📊 Available geographic segments: {geographic_segments}")
    print(f"   📊 Tier segment balance: {tier_balance:.3f}")
    print(f"   📊 Balance segment balance: {balance_balance:.3f}")
    
    # Multi-dimensional segmentation capability
    segment_combinations = set()
    for profile in profiles:
        data = profile['profile']
        tier = data.get('Account Tier', '')
        balance = data.get('Average Balance', '')
        channel = data.get('Preferred Channel', '')
        state = data.get('City', '').split(', ')[1] if ', ' in data.get('City', '') else ''
        
        segment_combinations.add((tier, balance, channel, state))
    
    segmentation_score = len(segment_combinations) / len(profiles) if profiles else 0
    
    print(f"   📊 Unique customer segments: {len(segment_combinations)}")
    print(f"   📊 Segmentation granularity: {segmentation_score:.3f}")
    
    # Criterion 2: Customer Lifetime Value Analysis
    print("\n2️⃣ CUSTOMER LIFETIME VALUE ANALYSIS")
    print("-" * 40)
    
    clv_potentials = []
    clv_distribution = defaultdict(int)
    
    for profile in profiles:
        data = profile['profile']
        clv_potential = calculate_customer_lifetime_value_potential(data)
        clv_potentials.append(clv_potential)
        
        # Categorize CLV potential
        if clv_potential >= 0.8:
            clv_distribution['High'] += 1
        elif clv_potential >= 0.6:
            clv_distribution['Medium-High'] += 1
        elif clv_potential >= 0.4:
            clv_distribution['Medium'] += 1
        elif clv_potential >= 0.2:
            clv_distribution['Low-Medium'] += 1
        else:
            clv_distribution['Low'] += 1
    
    avg_clv_potential = statistics.mean(clv_potentials) if clv_potentials else 0
    clv_variance = statistics.variance(clv_potentials) if len(clv_potentials) > 1 else 0
    
    print(f"   📊 Average CLV potential: {avg_clv_potential:.3f}")
    print(f"   📊 CLV potential variance: {clv_variance:.3f}")
    
    print("\n   CLV Distribution:")
    for category, count in clv_distribution.items():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {category}: {count} ({percentage:.1f}%)")
    
    # Criterion 3: Customer Journey Analytics
    print("\n3️⃣ CUSTOMER JOURNEY ANALYTICS")
    print("-" * 40)
    
    # Analyze customer tenure and activity patterns
    account_ages = []
    login_recency = []
    journey_stages = defaultdict(int)
    
    for profile in profiles:
        data = profile['profile']
        
        # Calculate account age
        account_since = data.get('Account Since', '')
        if account_since:
            try:
                account_date = datetime.strptime(account_since, '%Y-%m-%d')
                age_years = (datetime.now() - account_date).days / 365.25
                account_ages.append(age_years)
                
                # Classify journey stage
                if age_years < 0.5:
                    journey_stages['New'] += 1
                elif age_years < 2:
                    journey_stages['Growing'] += 1
                elif age_years < 5:
                    journey_stages['Established'] += 1
                else:
                    journey_stages['Mature'] += 1
                    
            except ValueError:
                pass
        
        # Calculate login recency
        last_login = data.get('Last Login', '')
        if last_login:
            try:
                login_date = datetime.strptime(last_login, '%Y-%m-%d')
                days_since_login = (datetime.now() - login_date).days
                login_recency.append(days_since_login)
            except ValueError:
                pass
    
    avg_account_age = statistics.mean(account_ages) if account_ages else 0
    avg_login_recency = statistics.mean(login_recency) if login_recency else 0
    
    print(f"   📊 Average account age: {avg_account_age:.1f} years")
    print(f"   📊 Average login recency: {avg_login_recency:.1f} days")
    
    print("\n   Customer Journey Stages:")
    for stage, count in journey_stages.items():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {stage}: {count} ({percentage:.1f}%)")
    
    # Engagement analysis
    engagement_scores = []
    for profile in profiles:
        data = profile['profile']
        
        # Simple engagement scoring
        score = 0
        
        # Recent login activity
        last_login = data.get('Last Login', '')
        if last_login:
            try:
                login_date = datetime.strptime(last_login, '%Y-%m-%d')
                days_since = (datetime.now() - login_date).days
                if days_since <= 30:
                    score += 0.4
                elif days_since <= 90:
                    score += 0.3
                elif days_since <= 180:
                    score += 0.2
                else:
                    score += 0.1
            except ValueError:
                score += 0.2
        
        # Tier-based engagement
        tier = data.get('Account Tier', '')
        tier_engagement = {
            'Diamond': 0.6, 'Platinum': 0.5, 'Gold': 0.4, 
            'Silver': 0.3, 'Bronze': 0.2
        }
        score += tier_engagement.get(tier, 0.2)
        
        engagement_scores.append(min(1.0, score))
    
    avg_engagement = statistics.mean(engagement_scores) if engagement_scores else 0
    
    print(f"   📊 Average engagement score: {avg_engagement:.3f}")
    
    # Criterion 4: Risk Assessment Capability
    print("\n4️⃣ RISK ASSESSMENT CAPABILITY")
    print("-" * 40)
    
    risk_factors = []
    risk_distribution = defaultdict(int)
    
    for profile in profiles:
        data = profile['profile']
        risk_score = 0
        
        # Account age risk (very new or very old accounts)
        account_since = data.get('Account Since', '')
        if account_since:
            try:
                account_date = datetime.strptime(account_since, '%Y-%m-%d')
                age_years = (datetime.now() - account_date).days / 365.25
                
                if age_years < 0.25:  # Very new
                    risk_score += 0.3
                elif age_years > 10:  # Very old, might be inactive
                    risk_score += 0.2
            except ValueError:
                risk_score += 0.2
        
        # Login recency risk
        last_login = data.get('Last Login', '')
        if last_login:
            try:
                login_date = datetime.strptime(last_login, '%Y-%m-%d')
                days_since = (datetime.now() - login_date).days
                
                if days_since > 365:  # Inactive for over a year
                    risk_score += 0.4
                elif days_since > 180:  # Inactive for 6+ months
                    risk_score += 0.3
                elif days_since > 90:  # Inactive for 3+ months
                    risk_score += 0.2
            except ValueError:
                risk_score += 0.2
        
        # Tier-balance mismatch risk
        tier = data.get('Account Tier', '')
        balance_str = data.get('Average Balance', '')
        
        if tier == 'Diamond' and balance_str == '<1k':
            risk_score += 0.3
        elif tier == 'Bronze' and balance_str.startswith('>'):
            risk_score += 0.2
        
        risk_factors.append(min(1.0, risk_score))
        
        # Categorize risk
        if risk_score >= 0.7:
            risk_distribution['High'] += 1
        elif risk_score >= 0.5:
            risk_distribution['Medium-High'] += 1
        elif risk_score >= 0.3:
            risk_distribution['Medium'] += 1
        elif risk_score >= 0.1:
            risk_distribution['Low-Medium'] += 1
        else:
            risk_distribution['Low'] += 1
    
    avg_risk = statistics.mean(risk_factors) if risk_factors else 0
    
    print(f"   📊 Average risk score: {avg_risk:.3f}")
    
    print("\n   Risk Distribution:")
    for category, count in risk_distribution.items():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {category}: {count} ({percentage:.1f}%)")
    
    # Criterion 5: Marketing & Personalization Potential
    print("\n5️⃣ MARKETING & PERSONALIZATION POTENTIAL")
    print("-" * 40)
    
    # Channel preference analysis
    channel_counts = Counter(channels)
    channel_coverage = len(set(channels)) / 4  # Assuming 4 main channels
    
    # Language preference analysis
    language_counts = Counter(languages)
    language_coverage = len(set(languages)) / 5  # Assuming 5 main languages
    
    # Geographic targeting potential
    state_counts = Counter(states)
    geographic_coverage = len(set(state for state in states if state)) / 50  # 50 US states
    
    # Demographic segmentation for marketing
    marketing_segments = set()
    for profile in profiles:
        data = profile['profile']
        tier = data.get('Account Tier', '')
        balance = data.get('Average Balance', '')
        channel = data.get('Preferred Channel', '')
        language = data.get('Language Preference', '')
        state = data.get('City', '').split(', ')[1] if ', ' in data.get('City', '') else ''
        
        # Create marketing personas
        persona = f"{tier}_{balance}_{channel}_{language}_{state}"
        marketing_segments.add(persona)
    
    personalization_potential = len(marketing_segments) / len(profiles) if profiles else 0
    
    print(f"   📊 Channel coverage: {channel_coverage:.3f}")
    print(f"   📊 Language coverage: {language_coverage:.3f}")
    print(f"   📊 Geographic coverage: {geographic_coverage:.3f}")
    print(f"   📊 Marketing personas: {len(marketing_segments)}")
    print(f"   📊 Personalization potential: {personalization_potential:.3f}")
    
    print("\n   Channel Distribution for Targeting:")
    for channel, count in channel_counts.most_common():
        percentage = (count / len(profiles)) * 100 if profiles else 0
        print(f"     • {channel}: {count} ({percentage:.1f}%)")
    
    # Overall Business Utility Score
    print("\n📊 OVERALL BUSINESS UTILITY & ANALYTICS VALUE SCORE")
    print("="*50)
    
    component_scores = {
        'Segmentation Capability': segmentation_score * 0.25,
        'CLV Analysis': (avg_clv_potential + (1 - clv_variance)) / 2 * 0.25,
        'Journey Analytics': (avg_engagement + (1 - avg_risk)) / 2 * 0.20,
        'Risk Assessment': (1 - avg_risk) * 0.15,
        'Marketing Potential': (channel_coverage + language_coverage + geographic_coverage + personalization_potential) / 4 * 0.15
    }
    
    total_score = sum(component_scores.values())
    
    print("Component Scores:")
    for component, score in component_scores.items():
        print(f"  • {component}: {score:.3f}")
    
    print(f"\n💼 FINAL BUSINESS UTILITY SCORE: {total_score:.3f}")
    
    if total_score >= 0.9:
        print("🚀 EXCEPTIONAL - Outstanding business value and analytics potential")
    elif total_score >= 0.8:
        print("⭐ EXCELLENT - High business utility and analytics value")
    elif total_score >= 0.7:
        print("✅ GOOD - Strong business insights potential")
    elif total_score >= 0.6:
        print("👍 ACCEPTABLE - Adequate for basic business analysis")
    else:
        print("⚠️  LIMITED - Needs improvement for meaningful business insights")
    
    print("\n🎯 KEY RECOMMENDATIONS FOR BUSINESS UTILITY:")
    if segmentation_score < 0.8:
        print("  • Improve customer segmentation granularity")
    if avg_clv_potential < 0.6:
        print("  • Enhance CLV analysis with more high-value customers")
    if avg_engagement < 0.7:
        print("  • Include more engagement indicators")
    if avg_risk > 0.4:
        print("  • Address high-risk customer profiles")
    if personalization_potential < 0.8:
        print("  • Increase diversity for better personalization opportunities")
    
    return {
        'total_score': total_score,
        'component_scores': component_scores,
        'profiles_analyzed': len(profiles),
        'business_metrics': {
            'segmentation_quality': segmentation_score,
            'avg_clv_potential': avg_clv_potential,
            'avg_engagement': avg_engagement,
            'avg_risk': avg_risk,
            'personalization_potential': personalization_potential
        },
        'distributions': {
            'clv_distribution': dict(clv_distribution),
            'journey_stages': dict(journey_stages),
            'risk_distribution': dict(risk_distribution),
            'channel_distribution': dict(channel_counts),
            'language_distribution': dict(language_counts)
        }
    }

if __name__ == "__main__":
    results = evaluate_business_utility_analytics() 