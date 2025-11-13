#!/usr/bin/env python3
"""Generate realistic provider data files"""

providers = [
    {
        "provider_id": "SPEC-AZ-015",
        "name": "Dr. Michael R. Thompson",
        "credentials": "DPM",
        "specialty": "Podiatry",
        "practice": "Arizona Foot & Ankle Specialists",
        "address": "4545 E. Shea Boulevard, Suite 210",
        "city": "Phoenix",
        "state": "AZ",
        "zip": "85028",
        "phone": "602-555-7800",
        "fax": "602-555-7801",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English", "Spanish"],
        "board_certified": True,
        "years_practice": 15,
        "rating": 4.7,
        "reviews": 189,
        "medical_school": "Arizona College of Podiatric Medicine",
        "residency": "St. Joseph's Hospital - Podiatric Surgery",
        "subspecialties": ["Diabetic Foot Care", "Sports Injuries", "Foot & Ankle Surgery"]
    },
    {
        "provider_id": "SPEC-TX-022",
        "name": "Dr. Jennifer L. Martinez",
        "credentials": "MD",
        "specialty": "Bariatric Surgery",
        "practice": "Houston Weight Loss Surgery Center",
        "address": "6624 Fannin Street, Suite 2780",
        "city": "Houston",
        "state": "TX",
        "zip": "77030",
        "phone": "713-555-9200",
        "fax": "713-555-9201",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024", "TH-HDHP-BRONZE-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English", "Spanish"],
        "board_certified": True,
        "years_practice": 12,
        "rating": 4.9,
        "reviews": 276,
        "medical_school": "Baylor College of Medicine",
        "residency": "Methodist Hospital - General Surgery",
        "fellowship": "Cleveland Clinic - Bariatric & Metabolic Surgery",
        "subspecialties": ["Laparoscopic Surgery", "Metabolic Surgery", "Revisional Surgery"]
    },
    {
        "provider_id": "SPEC-WA-008",
        "name": "Dr. David K. Chen",
        "credentials": "MD",
        "specialty": "Radiology",
        "practice": "Seattle Medical Imaging",
        "address": "1100 Ninth Avenue",
        "city": "Seattle",
        "state": "WA",
        "zip": "98101",
        "phone": "206-555-3400",
        "fax": "206-555-3401",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English", "Mandarin"],
        "board_certified": True,
        "years_practice": 14,
        "rating": 4.6,
        "reviews": 95,
        "medical_school": "University of Washington School of Medicine",
        "residency": "Stanford Medical Center - Diagnostic Radiology",
        "subspecialties": ["Body Imaging", "MRI", "CT Imaging"]
    },
    {
        "provider_id": "SPEC-CA-031",
        "name": "Dr. Robert J. Williams",
        "credentials": "MD",
        "specialty": "Nephrology",
        "practice": "Bay Area Kidney Specialists",
        "address": "450 Sutter Street, Suite 2200",
        "city": "San Francisco",
        "state": "CA",
        "zip": "94108",
        "phone": "415-555-6700",
        "fax": "415-555-6701",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024", "TH-HDHP-BRONZE-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English"],
        "board_certified": True,
        "years_practice": 19,
        "rating": 4.8,
        "reviews": 167,
        "medical_school": "UCSF School of Medicine",
        "residency": "UCLA Medical Center - Internal Medicine",
        "fellowship": "Johns Hopkins - Nephrology",
        "subspecialties": ["Chronic Kidney Disease", "Dialysis", "Transplant Nephrology"]
    },
    {
        "provider_id": "SPEC-WA-012",
        "name": "Dr. Emily R. Patel",
        "credentials": "MD",
        "specialty": "Physical Therapy",
        "practice": "Seattle Sports Medicine & Rehab",
        "address": "1959 NE Pacific Street",
        "city": "Seattle",
        "state": "WA",
        "zip": "98195",
        "phone": "206-555-8100",
        "fax": "206-555-8101",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English", "Hindi"],
        "board_certified": True,
        "years_practice": 10,
        "rating": 4.9,
        "reviews": 203,
        "medical_school": "University of Pittsburgh - Physical Therapy",
        "subspecialties": ["Sports Rehabilitation", "Orthopedic Physical Therapy", "Manual Therapy"]
    },
    {
        "provider_id": "SPEC-WA-016",
        "name": "Dr. Amanda S. Foster",
        "credentials": "MD",
        "specialty": "Sleep Medicine",
        "practice": "Pacific Sleep Disorders Center",
        "address": "1101 Madison Street, Suite 600",
        "city": "Seattle",
        "state": "WA",
        "zip": "98104",
        "phone": "206-555-9500",
        "fax": "206-555-9501",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024", "TH-HDHP-BRONZE-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English"],
        "board_certified": True,
        "years_practice": 16,
        "rating": 4.7,
        "reviews": 142,
        "medical_school": "University of Michigan Medical School",
        "residency": "Stanford - Internal Medicine",
        "fellowship": "Stanford Sleep Medicine Center",
        "subspecialties": ["Sleep Apnea", "Insomnia", "Narcolepsy"]
    },
    {
        "provider_id": "SPEC-CO-019",
        "name": "Dr. James T. Morrison",
        "credentials": "PsyD",
        "specialty": "Clinical Psychology",
        "practice": "Denver Behavioral Health Associates",
        "address": "1780 S. Bellaire Street, Suite 310",
        "city": "Denver",
        "state": "CO",
        "zip": "80222",
        "phone": "303-555-4200",
        "fax": "303-555-4201",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English"],
        "board_certified": True,
        "years_practice": 13,
        "rating": 4.8,
        "reviews": 178,
        "degree": "University of Denver - Clinical Psychology (PsyD)",
        "subspecialties": ["Cognitive Behavioral Therapy", "Anxiety Disorders", "Depression"]
    },
    {
        "provider_id": "SPEC-CA-025",
        "name": "Dr. Maria G. Rodriguez",
        "credentials": "MD",
        "specialty": "Obstetrics and Gynecology",
        "practice": "San Diego Women's Health Center",
        "address": "3737 Moraga Avenue",
        "city": "San Diego",
        "state": "CA",
        "zip": "92117",
        "phone": "619-555-7300",
        "fax": "619-555-7301",
        "accepted_plans": ["TH-HMO-GOLD-2024", "TH-PPO-PLATINUM-2024", "TH-HDHP-BRONZE-2024"],
        "network": "In-Network",
        "accepting_new": True,
        "languages": ["English", "Spanish"],
        "board_certified": True,
        "years_practice": 17,
        "rating": 4.9,
        "reviews": 289,
        "medical_school": "UC San Diego School of Medicine",
        "residency": "Scripps Mercy Hospital - OB/GYN",
        "subspecialties": ["High-Risk Pregnancy", "Minimally Invasive Surgery", "Women's Wellness"]
    }
]

# Generate markdown files
for provider in providers:
    filename = f"/home/user/policy_agent/data/markdown/providers/{provider['provider_id']}.md"

    content = f"""# Provider: {provider['name']}, {provider['credentials']}

## Specialty
{provider['specialty']}

## Practice Information
**Practice Name:** {provider['practice']}
**Address:** {provider['address']}
**City:** {provider['city']}
**State:** {provider['state']}
**ZIP Code:** {provider['zip']}
**Phone:** {provider['phone']}
**Fax:** {provider['fax']}

## Network Information
**Provider ID:** {provider['provider_id']}
**Network Type:** {provider['network']}
**Accepted Insurance Plans:**
"""
    
    for plan in provider['accepted_plans']:
        content += f"- {plan}\n"
    
    content += f"""
## Patient Information
**Accepting New Patients:** {'Yes' if provider['accepting_new'] else 'No'}
**Languages Spoken:** {', '.join(provider['languages'])}
**Board Certified:** {'Yes' if provider['board_certified'] else 'No'}
**Years in Practice:** {provider['years_practice']}

## Patient Reviews
**Average Rating:** {provider['rating']}/5.0
**Total Reviews:** {provider['reviews']}

## Medical Credentials
"""
    
    if 'medical_school' in provider:
        content += f"**Medical School:** {provider['medical_school']}\n"
    elif 'degree' in provider:
        content += f"**Degree:** {provider['degree']}\n"
    
    if 'residency' in provider:
        content += f"**Residency:** {provider['residency']}\n"
    
    if 'fellowship' in provider:
        content += f"**Fellowship:** {provider['fellowship']}\n"
    
    if provider.get('board_certified'):
        content += f"\n## Subspecialties\n"
        for sub in provider['subspecialties']:
            content += f"- {sub}\n"
    
    with open(filename, 'w') as f:
        f.write(content)
    
    print(f"Created: {provider['provider_id']}.md ({len(content)} chars)")

print(f"\n✅ Generated {len(providers)} provider files")
