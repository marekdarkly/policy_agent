# ToggleHealth RAG Datasets

## Overview

This directory contains two comprehensive, internally consistent datasets designed for use with Amazon Bedrock Knowledge Base (KB) for Retrieval Augmented Generation (RAG) applications. The datasets model a realistic medical insurance company called **ToggleHealth Insurance** and include both policy information and provider network data.

## Purpose

These datasets enable AI specialists (policy specialist and provider specialist) to answer questions about:
- Medical insurance coverage and benefits
- Provider networks and availability
- Cost structures and out-of-pocket expenses
- Special programs and wellness initiatives
- Geographic coverage areas
- Preauthorization requirements
- Claims and appeals processes

## Files

### 1. togglehealth_policy_database.json
**Size:** ~150KB
**Purpose:** Source of truth for all insurance policy information

**Contains:**
- Company information and service areas
- 4 insurance plans (HMO, PPO, EPO, HDHP)
- Coverage details and cost structures
- Copays and deductibles
- Covered services and exclusions
- Special programs (diabetes, heart health, maternity, etc.)
- Pharmacy benefits and formulary
- Claims and preauthorization procedures
- Network definitions

### 2. togglehealth_provider_database.json
**Size:** ~100KB
**Purpose:** Source of truth for provider network information

**Contains:**
- 7 hospitals (general acute care and psychiatric)
- 4 primary care physicians
- 6 specialists (cardiology, oncology, orthopedics, OB/GYN, neurology, endocrinology)
- 4 mental health providers
- 3 urgent care centers
- 2 physical therapy centers
- 4 pharmacies (3 retail + 1 mail order)
- 2 imaging centers
- 3 specialty care centers
- 1 laboratory service

**Note:** Provider database includes representative samples. Actual networks would have thousands of providers (counts are referenced in policy database).

### 3. CONSISTENCY_REVIEW.md
**Size:** ~45KB
**Purpose:** Comprehensive validation report

Documents the internal consistency review across 20 different dimensions, confirming 100% consistency between datasets.

### 4. README.md (this file)
**Purpose:** Documentation and usage guide

## Dataset Structure

### Company: ToggleHealth Insurance

**Founded:** 2015
**Headquarters:** Seattle, WA
**Service Areas:**
- Washington (all counties)
- Oregon (western counties)
- California (major metro areas)
- Idaho (Boise metro)
- Montana (Missoula, Billings metros)

### Insurance Plans

#### 1. TH-HMO-GOLD-2024 (Gold HMO)
- **Network:** TH-HMO-PRIMARY
- **Monthly Premium (Individual):** $485
- **Annual Deductible:** $1,000
- **Out-of-Pocket Max:** $6,500
- **PCP Required:** Yes
- **Referrals Required:** Yes
- **Coinsurance:** 80/20
- **Best For:** Members who want coordinated care with lower out-of-pocket costs

#### 2. TH-PPO-PLATINUM-2024 (Platinum PPO)
- **Network:** TH-PPO-PREMIER (largest network)
- **Monthly Premium (Individual):** $685
- **Annual Deductible:** $500
- **Out-of-Pocket Max:** $4,500
- **PCP Required:** No
- **Referrals Required:** No
- **Coinsurance:** 90/10
- **Out-of-Network:** 60% coverage
- **Best For:** Members who want maximum flexibility and lowest out-of-pocket costs

#### 3. TH-EPO-SILVER-2024 (Silver EPO)
- **Network:** TH-EPO-SELECT (curated network)
- **Monthly Premium (Individual):** $385
- **Annual Deductible:** $3,000
- **Out-of-Pocket Max:** $8,500
- **PCP Required:** No
- **Referrals Required:** No
- **Coinsurance:** 70/30
- **Out-of-Network:** No coverage (except emergency)
- **Best For:** Members who want affordability and don't need out-of-network access

#### 4. TH-HDHP-BRONZE-2024 (Bronze HDHP)
- **Network:** TH-HDHP-CORE
- **Monthly Premium (Individual):** $245
- **Annual Deductible:** $6,500
- **Out-of-Pocket Max:** $6,500 (same as deductible)
- **HSA Eligible:** Yes
- **HSA Employer Contribution:** $750
- **Coinsurance:** 100/0 (after deductible)
- **Best For:** Healthy members who want lowest premiums and HSA benefits

### Special Programs

All plans include access to certain special programs:

#### DMP-2024 (Diabetes Management Program)
- **Eligibility:** Members with Type 1 or Type 2 diabetes
- **Benefits:** Care coordination, glucose monitors, education, nutritionist
- **Participating Facilities:** Pacific Northwest Diabetes Center

#### HHP-2024 (Heart Health Program)
- **Eligibility:** Members with cardiovascular disease
- **Available On:** Gold HMO, Platinum PPO
- **Benefits:** Nurse hotline, cardiac rehab, monitoring equipment
- **Participating Facilities:** Heart & Vascular Institute of Seattle

#### MSP-2024 (Maternity Support Program)
- **Eligibility:** Pregnant members
- **Benefits:** 24/7 nurse hotline, prenatal vitamins, breast pump, screening
- **Participating Facilities:** Women's Health & Maternity Center

#### PCS-2024 (Premium Concierge Service)
- **Eligibility:** Platinum PPO members only
- **Benefits:** Dedicated care navigator, appointment scheduling, second opinions

#### HSA-2024 (HSA Support Program)
- **Eligibility:** Bronze HDHP members only
- **Benefits:** Free HSA setup, contribution matching, financial planning

### Networks

#### TH-HMO-PRIMARY
- **Plans:** Gold HMO
- **Coverage:** WA (all), OR (Multnomah, Clackamas, Washington), CA (SF Bay Area, Sacramento)
- **Size:** 2,847 PCPs, 8,934 specialists, 87 hospitals

#### TH-PPO-PREMIER
- **Plans:** Platinum PPO
- **Coverage:** WA (all), OR (west of Cascades), CA (all major metros), ID (Boise), MT (Missoula, Billings)
- **Size:** 4,521 PCPs, 14,789 specialists, 142 hospitals (LARGEST)

#### TH-EPO-SELECT
- **Plans:** Silver EPO
- **Coverage:** WA (King, Pierce, Snohomish, Spokane), OR (Multnomah, Clackamas, Washington, Marion), CA (SF Bay Area)
- **Size:** 1,923 PCPs, 6,234 specialists, 64 hospitals (SMALLEST)

#### TH-HDHP-CORE
- **Plans:** Bronze HDHP
- **Coverage:** WA (all), OR (western counties), CA (SF Bay, Sacramento, San Diego)
- **Size:** 3,234 PCPs, 9,876 specialists, 98 hospitals

## Key Features for RAG Applications

### 1. Complete Internal Consistency
- All network IDs match between databases
- All plan IDs are properly referenced
- All provider locations align with network coverage areas
- All special program IDs are valid
- All hospital affiliations reference existing hospitals

### 2. Realistic Medical Data
- Real medication names (Lisinopril, Metformin, Humira, etc.)
- Authentic medical specialties
- Valid medical schools and training institutions
- Appropriate hospital accreditations (Joint Commission, ACR, CAP)
- Realistic quality ratings

### 3. Complex Query Support
The datasets support complex queries such as:
- "What cardiologists accept the Gold HMO plan in Seattle?"
- "What's my copay for physical therapy under the Platinum PPO?"
- "Which hospitals participate in the Heart Health Program?"
- "What are the differences between the Silver EPO and Gold HMO plans?"
- "Do I need a referral to see a specialist on the Bronze HDHP?"
- "Which pharmacies can fill specialty medications in Portland?"

### 4. Comprehensive Service Coverage
- Primary care and preventive services
- Specialist care (cardiology, oncology, orthopedics, etc.)
- Mental health (therapy, psychiatry, substance abuse)
- Maternity and obstetrics
- Emergency and urgent care
- Diagnostic imaging and lab services
- Physical therapy and rehabilitation
- Pharmacy (retail and mail order)
- Telemedicine

### 5. Geographic Diversity
Providers span 5 states with realistic distribution:
- **Washington:** Seattle, Bellevue, Tacoma, Spokane
- **Oregon:** Portland
- **California:** San Francisco
- **Idaho:** Referenced in coverage
- **Montana:** Referenced in coverage

## Sample Use Cases for RAG

### Policy Specialist Queries

**Example 1: Coverage Question**
```
Q: "Does the Gold HMO plan cover acupuncture?"
A: No, the Gold HMO plan (TH-HMO-GOLD-2024) specifically excludes acupuncture
   in its exclusions list. However, the Platinum PPO plan (TH-PPO-PLATINUM-2024)
   does cover acupuncture with a $30 copay per session, up to 20 sessions per year,
   and no referral is required.
```

**Example 2: Cost Comparison**
```
Q: "What would I pay for an emergency room visit on the Silver EPO plan?"
A: On the Silver EPO plan (TH-EPO-SILVER-2024), emergency room visits have a $450
   copay, plus you're responsible for 30% of additional costs after your deductible
   ($3,000 individual). If you haven't met your deductible, you'll pay the full
   cost until you reach $3,000, then 30% of costs after that, up to your
   out-of-pocket maximum of $8,500.
```

**Example 3: Special Program Eligibility**
```
Q: "I have diabetes. What benefits can I get?"
A: As a member with diabetes, you're eligible for the Diabetes Management Program
   (DMP-2024) on any ToggleHealth plan. Benefits include:
   - Quarterly care coordinator check-ins
   - Free glucose monitor and test strips (or discounted on Silver EPO)
   - 100% coverage for diabetes education classes
   - Nutritionist consultations (6-12 per year depending on your plan)
   You can receive care at the Pacific Northwest Diabetes Center in Seattle.
```

### Provider Specialist Queries

**Example 1: Provider Search**
```
Q: "I need a cardiologist in Seattle who accepts the Platinum PPO plan."
A: Dr. Robert Williams is an interventional cardiologist at Pacific Northwest
   Heart Institute in Seattle (1600 Medical Tower, Suite 800). He accepts the
   Platinum PPO plan and is affiliated with Seattle General Hospital and Northwest
   Medical Center. He has 25 years of experience and a 4.9 patient rating. His
   services include cardiac catheterization, angioplasty, echocardiography, and
   heart failure management. Call 206-555-2001 to schedule an appointment.
```

**Example 2: Facility Information**
```
Q: "Which hospitals in the network have psychiatric services?"
A: Evergreen Psychiatric Hospital in Seattle (4500 Mental Health Way) is a
   dedicated psychiatric facility accepting all ToggleHealth plans. They offer:
   - Inpatient psychiatric care
   - Substance abuse treatment
   - Dual diagnosis treatment
   - Adolescent mental health services
   - ECT therapy
   They have 124 beds, Joint Commission accreditation, and specialize in mood
   disorders, addiction medicine, and trauma/PTSD. Call 206-555-0700.
```

**Example 3: Language Access**
```
Q: "Are there Spanish-speaking primary care doctors in Tacoma?"
A: Yes, Dr. Jennifer Martinez is a family medicine physician at Tacoma Family Care
   who speaks both English and Spanish. She accepts the Platinum PPO, Silver EPO,
   and Bronze HDHP plans. She's affiliated with Tacoma Regional Hospital and has
   12 years of experience. Her practice is at 3300 South 23rd Street, Tacoma.
   Call 253-555-1005.
```

## Implementation Guide for Bedrock KB

### Step 1: Upload to S3
```bash
aws s3 cp togglehealth_policy_database.json s3://your-bucket/knowledge-base/policy/
aws s3 cp togglehealth_provider_database.json s3://your-bucket/knowledge-base/provider/
```

### Step 2: Create Two Knowledge Bases

**Knowledge Base 1: Policy Specialist**
- **Name:** togglehealth-policy-kb
- **Data Source:** s3://your-bucket/knowledge-base/policy/
- **Embedding Model:** amazon.titan-embed-text-v2
- **Purpose:** Answer questions about coverage, costs, benefits, exclusions

**Knowledge Base 2: Provider Specialist**
- **Name:** togglehealth-provider-kb
- **Data Source:** s3://your-bucket/knowledge-base/provider/
- **Embedding Model:** amazon.titan-embed-text-v2
- **Purpose:** Answer questions about providers, facilities, locations, specialties

### Step 3: Configure RAG Application

Create two specialized agents:

**Policy Specialist Agent:**
- Uses policy KB
- Expert in plan benefits, coverage rules, costs
- Can compare plans and explain exclusions
- Understands special programs and eligibility

**Provider Specialist Agent:**
- Uses provider KB
- Expert in finding providers and facilities
- Can filter by specialty, location, language, plan acceptance
- Provides contact information and quality ratings

### Step 4: Query Patterns

**Policy Specialist Prompts:**
- "What does [plan name] cover for [service]?"
- "What are the costs for [service] under [plan name]?"
- "Compare [plan 1] vs [plan 2] for [criteria]"
- "Am I eligible for [special program]?"
- "What's excluded from [plan name]?"
- "Do I need preauthorization for [service]?"

**Provider Specialist Prompts:**
- "Find a [specialty] in [location] that accepts [plan]"
- "Which hospitals offer [service] in [location]?"
- "Are there [language]-speaking providers?"
- "What are the hours for [facility type] in [location]?"
- "Which providers participate in [special program]?"
- "Tell me about [provider name]'s qualifications"

## Data Quality Metrics

### Completeness
- ✅ 100% of required fields populated
- ✅ All providers have complete contact information
- ✅ All plans have complete coverage details
- ✅ All networks have geographic coverage defined

### Consistency
- ✅ 100% referential integrity between databases
- ✅ All IDs unique and properly formatted
- ✅ All cross-references validated
- ✅ No circular or conflicting references

### Realism
- ✅ Real medication names
- ✅ Valid medical specialties
- ✅ Authentic medical schools
- ✅ Appropriate accreditations
- ✅ Realistic cost structures

### Comprehensiveness
- ✅ 4 plan types covering all ACA metal tiers
- ✅ All essential health benefits covered
- ✅ Multiple provider types (hospitals, PCPs, specialists, mental health, etc.)
- ✅ Geographic diversity across 5 states
- ✅ Special programs for common chronic conditions

## Maintenance and Updates

### To Add New Plans:
1. Create plan entry in policy database with unique plan_id
2. Assign to existing or new network_id
3. Define coverage, copays, and exclusions
4. Update provider database to show which providers accept the new plan

### To Add New Providers:
1. Create provider entry with unique provider_id
2. Assign appropriate network_affiliations (must match policy DB networks)
3. List accepted_plans (must match policy DB plan IDs)
4. Include complete address and contact information
5. Ensure location is within network's geographic coverage

### To Add New Special Programs:
1. Create program entry in policy database with unique program_id
2. Define eligibility and benefits
3. Add program_participation to relevant provider facilities
4. Update plan special_programs arrays as appropriate

## Troubleshooting

### Issue: RAG returns "no information found"
**Solution:** Check that:
- Query uses correct plan IDs (format: TH-{TYPE}-{TIER}-2024)
- Provider search uses valid network IDs (format: TH-{TYPE}-{NAME})
- Geographic references match coverage areas in policy database

### Issue: Inconsistent answers between specialists
**Solution:**
- Ensure both KBs are synchronized
- Verify cross-references (IDs) match between databases
- Check consistency review document

### Issue: Provider not showing up in search
**Solution:**
- Verify provider has correct network_affiliations
- Check that accepted_plans includes the plan being searched
- Confirm provider location is within network coverage area

## Versioning

**Current Version:** 2024-01-01
**Format Version:** 1.0
**Compatible With:** Amazon Bedrock KB, OpenAI Embeddings, Anthropic Claude

## License

These datasets are fictional and created for demonstration purposes. All provider names, addresses (beyond city/state), phone numbers, and specific details are synthetic. Real medication names and medical institutions are used for realism but do not imply endorsement or affiliation.

## Support and Questions

For questions about dataset structure, consistency, or usage:
1. Review CONSISTENCY_REVIEW.md for detailed validation
2. Check this README for implementation guidance
3. Examine JSON structure for field definitions

## Change Log

### Version 2024-01-01 (Initial Release)
- Created comprehensive policy database with 4 plans
- Created provider network database with 30+ provider entities
- Validated 100% internal consistency across 20 dimensions
- Documented structure and usage patterns
- Prepared for Bedrock KB ingestion

---

**Dataset Status: ✅ Production Ready**

These datasets are ready for immediate use with Amazon Bedrock Knowledge Base for RAG applications.
