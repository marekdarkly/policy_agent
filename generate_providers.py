#!/usr/bin/env python3
"""
Generate comprehensive ToggleHealth provider database with 300+ providers
across 20 major US cities with proper network affiliations.
"""

import json
import random

# City data with state codes
CITIES = [
    {"city": "Seattle", "state": "WA", "zip_base": "98", "area_code": "206"},
    {"city": "Portland", "state": "OR", "zip_base": "97", "area_code": "503"},
    {"city": "San Francisco", "state": "CA", "zip_base": "94", "area_code": "415"},
    {"city": "Los Angeles", "state": "CA", "zip_base": "90", "area_code": "213"},
    {"city": "San Diego", "state": "CA", "zip_base": "92", "area_code": "619"},
    {"city": "Boston", "state": "MA", "zip_base": "02", "area_code": "617"},
    {"city": "New York", "state": "NY", "zip_base": "10", "area_code": "212"},
    {"city": "Philadelphia", "state": "PA", "zip_base": "19", "area_code": "215"},
    {"city": "Washington", "state": "DC", "zip_base": "20", "area_code": "202"},
    {"city": "Chicago", "state": "IL", "zip_base": "60", "area_code": "312"},
    {"city": "Detroit", "state": "MI", "zip_base": "48", "area_code": "313"},
    {"city": "Minneapolis", "state": "MN", "zip_base": "55", "area_code": "612"},
    {"city": "Dallas", "state": "TX", "zip_base": "75", "area_code": "214"},
    {"city": "Houston", "state": "TX", "zip_base": "77", "area_code": "713"},
    {"city": "Austin", "state": "TX", "zip_base": "78", "area_code": "512"},
    {"city": "Phoenix", "state": "AZ", "zip_base": "85", "area_code": "602"},
    {"city": "Denver", "state": "CO", "zip_base": "80", "area_code": "303"},
    {"city": "Atlanta", "state": "GA", "zip_base": "30", "area_code": "404"},
    {"city": "Miami", "state": "FL", "zip_base": "33", "area_code": "305"},
    {"city": "Charlotte", "state": "NC", "zip_base": "28", "area_code": "704"},
]

# Network distribution logic
# TH-PPO-PREMIER: 100% of providers (widest network)
# TH-EPO-SELECT: ~80% of providers
# TH-HMO-PRIMARY: ~60% of providers (more restrictive)
# TH-HDHP-CORE: ~70% of providers

def get_network_affiliations(provider_index, total_providers):
    """Determine network affiliations based on distribution logic"""
    networks = ["TH-PPO-PREMIER"]  # All providers in PPO

    # 80% in EPO
    if provider_index % 5 != 0:
        networks.append("TH-EPO-SELECT")

    # 60% in HMO
    if provider_index % 5 < 3:
        networks.append("TH-HMO-PRIMARY")

    # 70% in HDHP
    if provider_index % 10 < 7:
        networks.append("TH-HDHP-CORE")

    return sorted(networks)

def get_accepted_plans(networks):
    """Convert network affiliations to accepted plans"""
    plan_map = {
        "TH-HMO-PRIMARY": "TH-HMO-GOLD-2024",
        "TH-PPO-PREMIER": "TH-PPO-PLATINUM-2024",
        "TH-EPO-SELECT": "TH-EPO-SILVER-2024",
        "TH-HDHP-CORE": "TH-HDHP-BRONZE-2024"
    }
    return [plan_map[network] for network in networks]

# First and last names for diversity
FIRST_NAMES = {
    "M": ["James", "Michael", "Robert", "David", "William", "Richard", "Joseph", "Thomas", "Christopher", "Daniel", "Andrew", "Mark", "Steven", "Kevin", "Brian", "Jason", "Matthew", "Gary"],
    "F": ["Mary", "Jennifer", "Linda", "Patricia", "Susan", "Jessica", "Sarah", "Karen", "Nancy", "Lisa", "Betty", "Margaret", "Sandra", "Ashley", "Kimberly", "Emily", "Donna", "Michelle"]
}

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Martinez", "Rodriguez", "Miller", "Davis", "Wilson", "Moore", "Taylor", "Anderson", "Thomas", "Jackson", "White", "Harris", "Martin", "Thompson", "Lee", "Patel", "Chen", "Kim", "Nguyen", "Cohen", "O'Brien", "Murphy", "Singh"]

SPECIALTIES = [
    "Cardiology", "Dermatology", "Endocrinology", "Gastroenterology",
    "Oncology", "Orthopedic Surgery", "Neurology", "Pulmonology",
    "Rheumatology", "Urology", "Pediatrics", "Obstetrics and Gynecology"
]

def generate_providers():
    """Generate complete provider database"""
    providers = {
        "network_overview": {
            "last_updated": "2024-01-01",
            "total_providers": 19342,
            "total_facilities": 391,
            "total_pharmacies": 1876,
            "coverage_cities": [f"{c['city']}, {c['state']}" for c in CITIES],
            "networks": ["TH-HMO-PRIMARY", "TH-PPO-PREMIER", "TH-EPO-SELECT", "TH-HDHP-CORE"],
            "network_sizes": {
                "TH-HMO-PRIMARY": "12,450 providers - More restrictive network, requires PCP and referrals",
                "TH-PPO-PREMIER": "19,342 providers - Widest network, includes out-of-network coverage",
                "TH-EPO-SELECT": "16,200 providers - Good coverage, in-network only",
                "TH-HDHP-CORE": "14,800 providers - Comprehensive network for HDHP plan"
            }
        },
        "hospitals": [],
        "primary_care_physicians": [],
        "specialists": [],
        "mental_health_providers": [],
        "urgent_care_centers": [],
        "pharmacies": []
    }

    provider_counter = 0

    # Generate providers for each city
    for city_idx, city in enumerate(CITIES):
        city_name = city["city"]
        state = city["state"]
        zip_base = city["zip_base"]
        area_code = city["area_code"]

        # Generate 2 hospitals per city
        for hosp_num in range(1, 3):
            provider_counter += 1
            hosp_id = f"HOSP-{state}-{city_idx * 10 + hosp_num:03d}"
            networks = get_network_affiliations(provider_counter, 400)

            hospital = {
                "provider_id": hosp_id,
                "facility_name": f"{city_name} {'General' if hosp_num == 1 else 'Regional'} Hospital",
                "facility_type": "General Acute Care Hospital",
                "network_affiliations": networks,
                "accepted_plans": get_accepted_plans(networks),
                "address": {
                    "street": f"{1000 + hosp_num * 500} Medical Center Drive",
                    "city": city_name,
                    "state": state,
                    "zip": f"{zip_base}{101 + hosp_num:03d}",
                    "county": city_name
                },
                "contact": {
                    "phone": f"{area_code}-555-{1000 + provider_counter:04d}",
                    "fax": f"{area_code}-555-{2000 + provider_counter:04d}",
                    "email": f"info@{city_name.lower().replace(' ', '')}hosp{hosp_num}.org"
                },
                "services": ["Emergency Services", "Inpatient Surgery", "Cardiac Care", "Oncology", "Diagnostic Imaging", "Laboratory Services"],
                "beds": 200 + hosp_num * 100 + city_idx * 20,
                "trauma_level": "Level I" if hosp_num == 1 else "Level II",
                "accreditation": "Joint Commission Accredited",
                "accepts_emergency": True,
                "quality_ratings": {
                    "cms_star_rating": 4 if provider_counter % 3 == 0 else 5,
                    "leapfrog_grade": "A" if provider_counter % 5 < 4 else "B",
                    "patient_satisfaction": round(4.3 + (provider_counter % 6) * 0.1, 1)
                }
            }
            providers["hospitals"].append(hospital)

        # Generate 4 PCPs per city
        for pcp_num in range(1, 5):
            provider_counter += 1
            gender = "F" if pcp_num % 2 == 0 else "M"
            first_name = random.choice(FIRST_NAMES[gender])
            last_name = random.choice(LAST_NAMES)
            networks = get_network_affiliations(provider_counter, 400)

            pcp = {
                "provider_id": f"PCP-{state}-{city_idx * 10 + pcp_num:03d}",
                "provider_type": "Primary Care Physician",
                "name": {
                    "first": first_name,
                    "middle": chr(65 + pcp_num),
                    "last": last_name,
                    "credentials": "MD" if pcp_num % 3 != 0 else "DO"
                },
                "specialty": "Family Medicine" if pcp_num % 2 == 0 else "Internal Medicine",
                "network_affiliations": networks,
                "accepted_plans": get_accepted_plans(networks),
                "practice_name": f"{city_name} {'Family' if pcp_num % 2 == 0 else 'Internal'} Medicine",
                "practice_address": {
                    "street": f"{1200 + pcp_num * 100} Main Street, Suite {100 + pcp_num * 100}",
                    "city": city_name,
                    "state": state,
                    "zip": f"{zip_base}{102 + pcp_num:03d}",
                    "county": city_name
                },
                "contact": {
                    "phone": f"{area_code}-555-{3000 + provider_counter:04d}",
                    "fax": f"{area_code}-555-{4000 + provider_counter:04d}"
                },
                "hospital_affiliations": [f"HOSP-{state}-{city_idx * 10 + 1:03d}", f"HOSP-{state}-{city_idx * 10 + 2:03d}"],
                "languages": ["English", "Spanish"] if pcp_num % 3 == 0 else ["English"],
                "gender": "Female" if gender == "F" else "Male",
                "accepting_new_patients": True,
                "board_certified": True,
                "years_in_practice": 10 + pcp_num * 3,
                "patient_ratings": {
                    "average_rating": round(4.5 + (provider_counter % 5) * 0.1, 1),
                    "total_reviews": 100 + provider_counter * 5,
                    "bedside_manner": round(4.6 + (provider_counter % 4) * 0.1, 1),
                    "wait_time": round(4.2 + (provider_counter % 6) * 0.1, 1)
                }
            }
            providers["primary_care_physicians"].append(pcp)

        # Generate 6 specialists per city
        for spec_num in range(1, 7):
            provider_counter += 1
            gender = "F" if spec_num % 2 == 0 else "M"
            first_name = random.choice(FIRST_NAMES[gender])
            last_name = random.choice(LAST_NAMES)
            specialty = SPECIALTIES[spec_num % len(SPECIALTIES)]
            networks = get_network_affiliations(provider_counter, 400)

            specialist = {
                "provider_id": f"SPEC-{state}-{city_idx * 10 + spec_num:03d}",
                "provider_type": "Specialist",
                "name": {
                    "first": first_name,
                    "middle": chr(65 + spec_num),
                    "last": last_name,
                    "credentials": "MD"
                },
                "specialty": specialty,
                "network_affiliations": networks,
                "accepted_plans": get_accepted_plans(networks),
                "practice_name": f"{city_name} {specialty} Center",
                "practice_address": {
                    "street": f"{2000 + spec_num * 100} Specialty Drive, Suite {200 + spec_num * 50}",
                    "city": city_name,
                    "state": state,
                    "zip": f"{zip_base}{110 + spec_num:03d}",
                    "county": city_name
                },
                "contact": {
                    "phone": f"{area_code}-555-{5000 + provider_counter:04d}",
                    "fax": f"{area_code}-555-{6000 + provider_counter:04d}"
                },
                "hospital_affiliations": [f"HOSP-{state}-{city_idx * 10 + 1:03d}"],
                "languages": ["English"],
                "gender": "Female" if gender == "F" else "Male",
                "accepting_new_patients": True,
                "board_certified": True,
                "years_in_practice": 12 + spec_num * 2,
                "patient_ratings": {
                    "average_rating": round(4.5 + (provider_counter % 5) * 0.1, 1),
                    "total_reviews": 80 + provider_counter * 3,
                    "bedside_manner": round(4.6 + (provider_counter % 4) * 0.1, 1),
                    "wait_time": round(4.3 + (provider_counter % 5) * 0.1, 1)
                }
            }
            providers["specialists"].append(specialist)

        # Generate 2 mental health providers per city
        for mh_num in range(1, 3):
            provider_counter += 1
            gender = "F" if mh_num % 2 == 0 else "M"
            first_name = random.choice(FIRST_NAMES[gender])
            last_name = random.choice(LAST_NAMES)
            networks = get_network_affiliations(provider_counter, 400)
            credential = "PhD, Licensed Psychologist" if mh_num == 1 else "MD, Psychiatrist"

            mh_provider = {
                "provider_id": f"MH-{state}-{city_idx * 10 + mh_num:03d}",
                "provider_type": "Mental Health Provider",
                "name": {
                    "first": first_name,
                    "middle": chr(65 + mh_num),
                    "last": last_name,
                    "credentials": credential
                },
                "specialty": "Clinical Psychology" if mh_num == 1 else "Psychiatry",
                "network_affiliations": networks,
                "accepted_plans": get_accepted_plans(networks),
                "practice_name": f"{city_name} {'Psychology' if mh_num == 1 else 'Psychiatry'} Associates",
                "practice_address": {
                    "street": f"{3000 + mh_num * 200} Mental Health Boulevard, Suite {300 + mh_num * 20}",
                    "city": city_name,
                    "state": state,
                    "zip": f"{zip_base}{120 + mh_num:03d}",
                    "county": city_name
                },
                "contact": {
                    "phone": f"{area_code}-555-{7000 + provider_counter:04d}",
                    "fax": f"{area_code}-555-{8000 + provider_counter:04d}"
                },
                "languages": ["English"],
                "gender": "Female" if gender == "F" else "Male",
                "accepting_new_patients": True,
                "years_in_practice": 15 + mh_num * 3,
                "patient_ratings": {
                    "average_rating": round(4.6 + (provider_counter % 4) * 0.1, 1),
                    "total_reviews": 60 + provider_counter * 2,
                    "therapeutic_relationship": round(4.7 + (provider_counter % 3) * 0.1, 1)
                }
            }
            providers["mental_health_providers"].append(mh_provider)

        # Generate 1 urgent care center per city
        provider_counter += 1
        networks = get_network_affiliations(provider_counter, 400)

        urgent_care = {
            "provider_id": f"UC-{state}-{city_idx * 10 + 1:03d}",
            "facility_name": f"ToggleHealth Urgent Care - {city_name}",
            "facility_type": "Urgent Care Center",
            "network_affiliations": networks,
            "accepted_plans": get_accepted_plans(networks),
            "address": {
                "street": f"{600 + city_idx * 100} Urgent Care Avenue",
                "city": city_name,
                "state": state,
                "zip": f"{zip_base}{130:03d}",
                "county": city_name
            },
            "contact": {
                "phone": f"{area_code}-555-{9000 + provider_counter:04d}",
                "fax": f"{area_code}-555-{9500 + provider_counter:04d}"
            },
            "hours": {
                "monday_friday": "8:00 AM - 8:00 PM",
                "saturday_sunday": "9:00 AM - 5:00 PM"
            },
            "services": ["Minor illness treatment", "Minor injury treatment", "X-rays", "Lab tests", "Immunizations"],
            "onsite_lab": True,
            "onsite_xray": True,
            "patient_ratings": {
                "average_rating": round(4.4 + (provider_counter % 5) * 0.1, 1),
                "total_reviews": 200 + provider_counter * 10,
                "wait_time": round(4.2 + (provider_counter % 6) * 0.1, 1)
            }
        }
        providers["urgent_care_centers"].append(urgent_care)

        # Generate 2 pharmacies per city
        for pharm_num in range(1, 3):
            provider_counter += 1
            networks = get_network_affiliations(provider_counter, 400)

            pharmacy = {
                "provider_id": f"PHARM-{state}-{city_idx * 10 + pharm_num:03d}",
                "facility_name": f"{'ToggleHealth' if pharm_num == 1 else city_name} Pharmacy",
                "facility_type": "Retail Pharmacy",
                "network_affiliations": networks,
                "accepted_plans": get_accepted_plans(networks),
                "address": {
                    "street": f"{400 + pharm_num * 200} Pharmacy Street",
                    "city": city_name,
                    "state": state,
                    "zip": f"{zip_base}{140 + pharm_num:03d}",
                    "county": city_name
                },
                "contact": {
                    "phone": f"{area_code}-555-{9600 + provider_counter:04d}",
                    "fax": f"{area_code}-555-{9700 + provider_counter:04d}"
                },
                "hours": {
                    "monday_friday": "8:00 AM - 9:00 PM",
                    "saturday": "9:00 AM - 6:00 PM",
                    "sunday": "10:00 AM - 5:00 PM" if pharm_num == 1 else "Closed"
                },
                "services": ["Prescription filling", "Immunizations", "Medication therapy management"],
                "specialty_pharmacy": pharm_num == 1,
                "mail_order_available": pharm_num == 1
            }
            providers["pharmacies"].append(pharmacy)

    return providers

# Generate and save
if __name__ == "__main__":
    print("Generating comprehensive provider database...")
    provider_data = generate_providers()

    print(f"Generated:")
    print(f"  - {len(provider_data['hospitals'])} hospitals")
    print(f"  - {len(provider_data['primary_care_physicians'])} primary care physicians")
    print(f"  - {len(provider_data['specialists'])} specialists")
    print(f"  - {len(provider_data['mental_health_providers'])} mental health providers")
    print(f"  - {len(provider_data['urgent_care_centers'])} urgent care centers")
    print(f"  - {len(provider_data['pharmacies'])} pharmacies")
    total = sum([
        len(provider_data['hospitals']),
        len(provider_data['primary_care_physicians']),
        len(provider_data['specialists']),
        len(provider_data['mental_health_providers']),
        len(provider_data['urgent_care_centers']),
        len(provider_data['pharmacies'])
    ])
    print(f"  TOTAL: {total} providers")

    # Save to file
    output_file = "/home/user/policy_agent/data/togglehealth_provider_database.json"
    with open(output_file, 'w') as f:
        json.dump(provider_data, f, indent=2)

    print(f"\nSaved to: {output_file}")
