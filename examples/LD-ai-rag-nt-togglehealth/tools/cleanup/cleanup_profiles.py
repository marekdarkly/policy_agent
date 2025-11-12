#!/usr/bin/env python3
"""
Comprehensive Cleanup of ToggleBank Customer Profile Files
Creates canonical, high-quality customer profiles with unique names
"""
import os
import json
import re
import random
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import itertools

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

def generate_unique_names(count):
    """Generate unique, diverse full names"""
    
    # Diverse first names (avoiding similar-sounding names)
    first_names = [
        # Traditional names
        'Alexander', 'Benjamin', 'Catherine', 'Diana', 'Edward', 'Francesca',
        'Gabriel', 'Helena', 'Isabella', 'Jonathan', 'Katherine', 'Leonardo',
        'Margaret', 'Nicholas', 'Olivia', 'Patrick', 'Rebecca', 'Sebastian',
        'Theodora', 'Victoria',
        
        # Modern names  
        'Aaliyah', 'Brandon', 'Chelsea', 'Devon', 'Elena', 'Felix',
        'Gianna', 'Harrison', 'Imara', 'Jasper', 'Keira', 'Lucian',
        'Meredith', 'Nathan', 'Ophelia', 'Phoenix', 'Quinton', 'Rhiannon',
        'Sienna', 'Tristan',
        
        # International names
        'Akira', 'Bianca', 'Carmen', 'Dmitri', 'Esperanza', 'Fatima',
        'Giuseppe', 'Hiroshi', 'Ingrid', 'Joaquin', 'Kenji', 'Lucia',
        'Mateo', 'Nadia', 'Omar', 'Priya', 'Qadir', 'Rosa',
        'Soren', 'Takeshi',
        
        # Contemporary names
        'Aria', 'Blake', 'Chloe', 'Damon', 'Eva', 'Finn',
        'Grace', 'Hunter', 'Ivy', 'Jaxon', 'Kai', 'Luna',
        'Mason', 'Nova', 'Owen', 'Piper', 'Quinn', 'River',
        'Sage', 'Zara'
    ]
    
    # Diverse last names from various origins
    last_names = [
        # Anglo-Saxon
        'Anderson', 'Brown', 'Campbell', 'Davis', 'Edwards', 'Fisher',
        'Garcia', 'Harris', 'Johnson', 'Kennedy', 'Lewis', 'Mitchell',
        'Nelson', 'Parker', 'Roberts', 'Stevens', 'Thompson', 'Wilson',
        
        # European
        'Andersson', 'Bergmann', 'Chavez', 'Dubois', 'Eriksson', 'Ferrari',
        'González', 'Hansen', 'Ivanov', 'Jankowski', 'Klein', 'Larsson',
        'Mueller', 'Nielsen', 'O\'Brien', 'Petrov', 'Rossi', 'Schmidt',
        
        # Asian
        'Chen', 'Kim', 'Lee', 'Liu', 'Nakamura', 'Patel', 'Sato', 'Singh',
        'Tanaka', 'Wang', 'Wong', 'Yamamoto', 'Zhang', 'Zhou',
        
        # Latin American
        'Castillo', 'Díaz', 'Fernández', 'Jiménez', 'López', 'Martínez',
        'Morales', 'Pérez', 'Ramírez', 'Rivera', 'Rodríguez', 'Sánchez',
        
        # African
        'Abebe', 'Adebayo', 'Asante', 'Diallo', 'Kone', 'Mensah',
        'Nkomo', 'Okafor', 'Traore', 'Wanjiku',
        
        # Middle Eastern
        'Al-Rashid', 'Hassan', 'Ibrahim', 'Khalil', 'Mansour', 'Omar',
        'Rahman', 'Said', 'Yusuf', 'Zayed'
    ]
    
    # Generate unique combinations
    used_combinations = set()
    unique_names = []
    
    # Create all possible combinations
    all_combinations = list(itertools.product(first_names, last_names))
    random.shuffle(all_combinations)
    
    for first, last in all_combinations:
        if len(unique_names) >= count:
            break
        
        # Check for similar-sounding combinations
        full_name = f"{first} {last}"
        
        # Avoid confusing combinations (same initials, rhyming, etc.)
        is_confusing = False
        for existing_name in unique_names:
            existing_first, existing_last = existing_name.split()
            
            # Check for same initials
            if first[0] == existing_first[0] and last[0] == existing_last[0]:
                is_confusing = True
                break
            
            # Check for similar sounds (basic check)
            if (first.lower().endswith(existing_first.lower()[-3:]) or 
                last.lower().endswith(existing_last.lower()[-3:])):
                is_confusing = True
                break
        
        if not is_confusing:
            unique_names.append(full_name)
    
    return unique_names

def generate_diverse_locations():
    """Generate diverse geographic locations"""
    locations = [
        # Major metropolitan areas
        'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
        'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
        'Dallas, TX', 'San Jose, CA', 'Austin, TX', 'Jacksonville, FL',
        'Fort Worth, TX', 'Columbus, OH', 'Indianapolis, IN', 'Charlotte, NC',
        'San Francisco, CA', 'Seattle, WA', 'Denver, CO', 'Boston, MA',
        
        # Secondary cities
        'El Paso, TX', 'Nashville, TN', 'Detroit, MI', 'Oklahoma City, OK',
        'Portland, OR', 'Las Vegas, NV', 'Memphis, TN', 'Louisville, KY',
        'Baltimore, MD', 'Milwaukee, WI', 'Albuquerque, NM', 'Tucson, AZ',
        'Fresno, CA', 'Sacramento, CA', 'Kansas City, MO', 'Mesa, AZ',
        'Virginia Beach, VA', 'Atlanta, GA', 'Colorado Springs, CO', 'Omaha, NE',
        
        # Smaller cities for diversity
        'Raleigh, NC', 'Miami, FL', 'Tampa, FL', 'New Orleans, LA',
        'Cleveland, OH', 'Wichita, KS', 'Arlington, TX', 'Bakersfield, CA',
        'Aurora, CO', 'Anaheim, CA', 'Honolulu, HI', 'Santa Ana, CA',
        'Riverside, CA', 'Corpus Christi, TX', 'Lexington, KY', 'Henderson, NV',
        'Stockton, CA', 'Saint Paul, MN', 'Cincinnati, OH', 'Pittsburgh, PA'
    ]
    
    return locations

def fix_balance_format(balance):
    """Fix invalid balance formats"""
    if not balance or balance == '':
        return '<1k'
    
    # Handle various invalid formats
    balance = balance.strip()
    
    # If it's already valid, return as-is
    valid_patterns = [r'<1k', r'\d+k-\d+k', r'>\d+k']
    if any(re.match(pattern, balance) for pattern in valid_patterns):
        return balance
    
    # Try to extract numbers and fix format
    numbers = re.findall(r'\d+', balance)
    
    if not numbers:
        return '<1k'
    
    num = int(numbers[0])
    
    if num < 1:
        return '<1k'
    elif num < 10:
        return f'{num}k-{num + 5}k'
    elif num < 100:
        return f'{num}k-{num + 10}k'
    else:
        return f'>{num}k'

def create_canonical_profiles():
    """Create canonical, cleaned up customer profiles"""
    profiles_dir = "samples/togglebank_profiles_txt"
    output_dir = "samples/cleaned_profiles"
    
    if not os.path.exists(profiles_dir):
        print(f"Directory {profiles_dir} not found!")
        return
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Read all profile files
    profiles = []
    for filename in sorted(os.listdir(profiles_dir)):
        if filename.endswith('.txt'):
            filepath = os.path.join(profiles_dir, filename)
            profile = read_profile_file(filepath)
            if profile:
                profiles.append(profile)
    
    print(f"🔍 Processing {len(profiles)} customer profiles...")
    
    # Determine how many unique profiles to create (reduce redundancy)
    target_count = min(500, len(profiles))  # Create 500 unique profiles
    
    # Generate unique names and locations
    unique_names = generate_unique_names(target_count)
    locations = generate_diverse_locations()
    
    print(f"📊 Generated {len(unique_names)} unique names")
    print(f"📊 Using {len(locations)} diverse locations")
    
    # Create canonical profiles
    canonical_profiles = []
    
    # Sample original profiles to get diverse characteristics
    sampled_profiles = random.sample(profiles, target_count)
    
    for i, original_profile in enumerate(sampled_profiles):
        if i >= len(unique_names):
            break
        
        original_data = original_profile['profile']
        
        # Create enhanced profile
        canonical_profile = {
            'id': f"customer_{i+1:03d}",
            'name': unique_names[i],
            'city': random.choice(locations),
            'account_tier': original_data.get('Account Tier', 'Bronze'),
            'account_since': original_data.get('Account Since', '2020-01-01'),
            'last_login': original_data.get('Last Login', '2024-01-01'),
            'average_balance': fix_balance_format(original_data.get('Average Balance', '<1k')),
            'rewards_points': original_data.get('Rewards Points', '0'),
            'preferred_channel': original_data.get('Preferred Channel', 'mobile'),
            'language_preference': original_data.get('Language Preference', 'en').rstrip('.'),
            'source_files': [original_profile['file']]
        }
        
        canonical_profiles.append(canonical_profile)
        
        # Write individual profile file
        output_file = os.path.join(output_dir, f"customer_{i+1:03d}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Name: {canonical_profile['name']}\n")
            f.write(f"City: {canonical_profile['city']}\n")
            f.write(f"Account Tier: {canonical_profile['account_tier']}\n")
            f.write(f"Account Since: {canonical_profile['account_since']}\n")
            f.write(f"Last Login: {canonical_profile['last_login']}\n")
            f.write(f"Average Balance: {canonical_profile['average_balance']}\n")
            f.write(f"Rewards Points: {canonical_profile['rewards_points']}\n")
            f.write(f"Preferred Channel: {canonical_profile['preferred_channel']}\n")
            f.write(f"Language Preference: {canonical_profile['language_preference']}\n")
    
    # Create metadata file
    metadata = {
        'total_canonical_profiles': len(canonical_profiles),
        'original_files_processed': len(profiles),
        'reduction_ratio': len(profiles) / len(canonical_profiles),
        'unique_names_generated': len(unique_names),
        'locations_used': len(set(profile['city'] for profile in canonical_profiles)),
        'profiles': canonical_profiles
    }
    
    metadata_file = os.path.join(output_dir, 'profile_metadata.json')
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ CLEANUP COMPLETE!")
    print(f"📊 Created {len(canonical_profiles)} canonical profiles from {len(profiles)} original files")
    print(f"📉 Reduction ratio: {len(profiles) / len(canonical_profiles):.1f}:1")
    print(f"📁 Output directory: {output_dir}")
    
    return canonical_profiles

def evaluate_cleanup_quality(canonical_profiles):
    """Evaluate the quality of the cleaned up profiles"""
    print(f"\n🔍 CLEANUP QUALITY EVALUATION")
    print("="*50)
    
    # Evaluation criteria 1: Name Uniqueness
    print("1️⃣ NAME UNIQUENESS:")
    names = [profile['name'] for profile in canonical_profiles]
    unique_names = set(names)
    first_names = [name.split()[0] for name in names]
    unique_first_names = set(first_names)
    
    print(f"   ✅ Total unique full names: {len(unique_names)}/{len(canonical_profiles)}")
    print(f"   ✅ Unique first names: {len(unique_first_names)}/{len(canonical_profiles)}")
    print(f"   ✅ Name uniqueness score: {len(unique_names) / len(canonical_profiles):.3f}")
    
    # Evaluation criteria 2: Geographic Diversity
    print("\n2️⃣ GEOGRAPHIC DIVERSITY:")
    cities = [profile['city'] for profile in canonical_profiles]
    states = [city.split(', ')[1] if ', ' in city else '' for city in cities]
    unique_cities = set(cities)
    unique_states = set(state for state in states if state)
    
    print(f"   ✅ Unique cities: {len(unique_cities)}")
    print(f"   ✅ Unique states: {len(unique_states)}")
    print(f"   ✅ Geographic diversity score: {len(unique_states) / 50:.3f}")  # US has 50 states
    
    # Evaluation criteria 3: Data Quality
    print("\n3️⃣ DATA QUALITY:")
    valid_balances = 0
    valid_dates = 0
    complete_profiles = 0
    
    for profile in canonical_profiles:
        # Check balance format
        balance = profile['average_balance']
        if re.match(r'(<1k|\d+k-\d+k|>\d+k)', balance):
            valid_balances += 1
        
        # Check date formats
        try:
            datetime.strptime(profile['account_since'], '%Y-%m-%d')
            datetime.strptime(profile['last_login'], '%Y-%m-%d')
            valid_dates += 1
        except ValueError:
            pass
        
        # Check completeness
        if all(profile[key] for key in ['name', 'city', 'account_tier', 'account_since']):
            complete_profiles += 1
    
    print(f"   ✅ Valid balance formats: {valid_balances}/{len(canonical_profiles)}")
    print(f"   ✅ Valid date formats: {valid_dates}/{len(canonical_profiles)}")
    print(f"   ✅ Complete profiles: {complete_profiles}/{len(canonical_profiles)}")
    
    # Evaluation criteria 4: Diversity in Characteristics
    print("\n4️⃣ CHARACTERISTIC DIVERSITY:")
    tiers = [profile['account_tier'] for profile in canonical_profiles]
    channels = [profile['preferred_channel'] for profile in canonical_profiles]
    languages = [profile['language_preference'] for profile in canonical_profiles]
    
    tier_diversity = len(set(tiers)) / len(tiers) if tiers else 0
    channel_diversity = len(set(channels)) / len(channels) if channels else 0
    language_diversity = len(set(languages)) / len(languages) if languages else 0
    
    print(f"   ✅ Account tier diversity: {len(set(tiers))} tiers")
    print(f"   ✅ Channel diversity: {len(set(channels))} channels")
    print(f"   ✅ Language diversity: {len(set(languages))} languages")
    
    # Overall score
    name_score = len(unique_names) / len(canonical_profiles)
    geo_score = len(unique_states) / 50
    data_score = (valid_balances + valid_dates + complete_profiles) / (3 * len(canonical_profiles))
    diversity_score = (tier_diversity + channel_diversity + language_diversity) / 3
    
    overall_score = (name_score + geo_score + data_score + diversity_score) / 4
    
    print(f"\n📊 OVERALL CLEANUP QUALITY SCORE: {overall_score:.3f}")
    
    if overall_score >= 0.9:
        print("🎉 EXCEPTIONAL - Outstanding profile quality!")
    elif overall_score >= 0.8:
        print("⭐ EXCELLENT - High quality profiles")
    elif overall_score >= 0.7:
        print("✅ GOOD - Solid profile quality")
    elif overall_score >= 0.6:
        print("👍 ACCEPTABLE - Decent quality with room for improvement")
    else:
        print("⚠️  NEEDS WORK - Quality improvements needed")

if __name__ == "__main__":
    canonical_profiles = create_canonical_profiles()
    if canonical_profiles:
        evaluate_cleanup_quality(canonical_profiles) 