#!/usr/bin/env python3
"""Generate policy data files"""

# TH-HMO-GOLD-2024 Preventive Care
with open('/home/user/policy_agent/data/markdown/policies/TH-HMO-GOLD-2024-preventive.md', 'w') as f:
    f.write("""# Preventive Care Coverage

## Plan Information
**Plan Name:** ToggleHealth HMO Gold Plan
**Plan ID:** TH-HMO-GOLD-2024
**Plan Type:** HMO

## Preventive Services (100% Covered - No Copay)
All preventive care services are covered at 100% when obtained from an in-network provider. No deductible or copay required.

### Annual Wellness Exams
- **Annual Physical Exam:** One per year, no copay
- **Well-Child Visits:** Unlimited through age 18, no copay
- **Well-Woman Exam:** One per year, no copay
- **Medicare Annual Wellness Visit:** For members 65+, no copay

### Immunizations & Vaccines
- **Routine Childhood Vaccines:** Per CDC schedule, no copay
- **Adult Immunizations:** Flu, Pneumonia, Shingles, etc., no copay
- **COVID-19 Vaccines:** All doses and boosters, no copay
- **Travel Vaccines:** Not covered

### Cancer Screenings
- **Mammogram:** One per year for women 40+, no copay
- **Colonoscopy:** One every 10 years starting age 45, no copay
- **Pap Smear:** One every 3 years for women 21-65, no copay
- **Prostate Screening:** PSA test annually for men 50+, no copay
- **Skin Cancer Screening:** One per year, no copay
- **Lung Cancer Screening:** Low-dose CT for high-risk individuals, no copay

### Cardiovascular Screening
- **Blood Pressure Screening:** At every wellness visit, no copay
- **Cholesterol Screening:** Every 5 years starting age 20, no copay
- **Diabetes Screening:** For adults with high blood pressure, no copay
- **Obesity Screening:** BMI calculation at wellness visits, no copay

### Women's Health
- **Contraceptive Services:** Counseling and FDA-approved methods, no copay
- **Prenatal Visits:** All prenatal care visits, no copay
- **Breast Pump:** One per pregnancy, no copay
- **Lactation Support:** Counseling and support, no copay

### Other Preventive Services
- **Depression Screening:** Annual screening, no copay
- **Tobacco Cessation:** Counseling (up to 8 sessions per year), no copay
- **Alcohol Misuse Screening:** Annual screening and counseling, no copay
- **STI Screening:** HIV, Hepatitis, Chlamydia, Gonorrhea, no copay

## Important Notes
- Preventive services must be obtained from in-network providers to receive 100% coverage
- Services beyond preventive care (diagnostic or treatment) may require copay/deductible
- PCP referral not required for preventive care visits
- Additional screenings based on family history may require prior authorization
""")

# TH-HMO-GOLD-2024 Prescription Drugs
with open('/home/user/policy_agent/data/markdown/policies/TH-HMO-GOLD-2024-prescription.md', 'w') as f:
    f.write("""# Prescription Drug Coverage

## Plan Information
**Plan Name:** ToggleHealth HMO Gold Plan
**Plan ID:** TH-HMO-GOLD-2024
**Plan Type:** HMO

## Pharmacy Copays

### Tier 1 - Generic Drugs
**30-day supply (retail):** $10
**90-day supply (mail order):** $25
**Examples:** Generic antibiotics, generic blood pressure medications, generic diabetes medications

### Tier 2 - Preferred Brand-Name Drugs
**30-day supply (retail):** $35
**90-day supply (mail order):** $90
**Examples:** Preferred brands on ToggleHealth formulary

### Tier 3 - Non-Preferred Brand-Name Drugs
**30-day supply (retail):** $60
**90-day supply (mail order):** $150
**Examples:** Brand-name drugs not on preferred list

### Tier 4 - Specialty Drugs
**30-day supply:** $150 (specialty pharmacy required)
**Examples:** Cancer medications, injectable biologics, hepatitis C treatments

## Pharmacy Options

### Retail Pharmacy Network
- Available at 60,000+ pharmacies nationwide
- CVS, Walgreens, Rite Aid, and local pharmacies
- 30-day supply maximum
- Copays apply per fill

### Mail Order Pharmacy (ToggleHealth Pharmacy)
- 90-day supply available
- Lower copays than retail
- Free standard shipping (5-7 business days)
- Automatic refill program available
- Order online at my.togglehealth.com

### Specialty Pharmacy (Required for Tier 4)
- ToggleHealth Specialty Pharmacy
- Phone: 1-800-TOGGLE-RX
- Coordination with prescribing physician
- Clinical support and monitoring included

## Coverage Rules

### Prior Authorization Required For:
- Tier 4 specialty medications
- Certain high-cost Tier 3 medications
- Quantities exceeding normal limits
- Non-formulary medications

### Step Therapy May Apply:
Some medications require trying a lower-cost alternative first before coverage approval for higher-cost options.

### Diabetic Supplies Coverage
**Blood Glucose Meters:** Covered at Tier 1 copay
**Test Strips:** Covered at Tier 1 copay (up to 100 strips per month)
**Lancets:** Covered at Tier 1 copay
**Insulin:** Covered at Tier 1 or Tier 2 depending on type
**Insulin Syringes/Needles:** Covered at Tier 1 copay

### Contraceptive Coverage
- Generic oral contraceptives: $0 copay
- Brand contraceptives: $0 copay if no generic available
- Contraceptive devices (IUD, implant): Covered under medical benefits

## Annual Limit
No annual limit on prescription drug coverage

## Important Notes
- All prescription copays apply toward your out-of-pocket maximum
- Deductible does not apply to prescription drugs
- Can split prescriptions between retail and mail order
- Non-formulary drugs may not be covered without prior authorization
- Compounded medications covered with prior authorization
""")

# TH-HMO-GOLD-2024 Special Programs
with open('/home/user/policy_agent/data/markdown/policies/TH-HMO-GOLD-2024-special-programs.md', 'w') as f:
    f.write("""# Special Health Programs

## Plan Information
**Plan Name:** ToggleHealth HMO Gold Plan
**Plan ID:** TH-HMO-GOLD-2024
**Plan Type:** HMO

## Disease Management Programs

All disease management programs are included at no additional cost to members.

### Diabetes Management Program
**Eligibility:** Members diagnosed with Type 1 or Type 2 diabetes

**Services Included:**
- Personal health coach (nurse educator)
- Quarterly check-in calls
- Blood sugar monitoring guidance
- Nutrition counseling (4 sessions per year)
- Diabetic supplies coverage
- Educational materials and resources
- Diabetic retinopathy screening reminders
- Foot care education

**Contact:** 1-800-TOGGLE-1, select option 3

### Heart Health Program
**Eligibility:** Members with heart disease, high blood pressure, or high cholesterol

**Services Included:**
- Cardiovascular risk assessment
- Personal action plan
- Nutrition counseling (4 sessions per year)
- Exercise planning with certified trainer
- Medication adherence support
- Blood pressure monitoring kit (free)
- Educational webinars monthly
- Stress management resources

**Contact:** 1-800-TOGGLE-1, select option 4

### Maternity Support Program
**Eligibility:** Pregnant members (enroll by week 12 for full benefits)

**Services Included:**
- 24/7 nurse hotline
- Pregnancy education classes (online and in-person)
- Breast pump covered
- Lactation consultant support
- Postpartum depression screening
- Newborn care education
- High-risk pregnancy support
- Incentive: $50 gift card upon completing program

**Contact:** 1-800-TOGGLE-1, select option 5

### Asthma Management Program
**Eligibility:** Members with diagnosed asthma

**Services Included:**
- Asthma action plan development
- Peak flow meter (free)
- Trigger identification guidance
- Medication management support
- Quarterly respiratory therapist check-ins
- Educational resources

**Contact:** 1-800-TOGGLE-1, select option 6

### Mental Health & Wellness Program
**Eligibility:** All members

**Services Included:**
- Employee Assistance Program (EAP)
- 24/7 mental health crisis line
- Mindfulness and meditation app subscription (free)
- Stress management webinars
- Depression and anxiety screening tools
- Referrals to in-network therapists
- Unlimited mental health therapy visits (subject to copay)

**Contact:** Mental Health Line: 1-800-TOGGLE-MH

## Wellness Programs

### Weight Management Program
**Eligibility:** Members with BMI >25 or diabetes diagnosis

**Services Included:**
- Nutritionist consultations (12 per year)
- Weight Watchers or Noom subscription (covered)
- Online support community
- Fitness tracker discount (50% off)
- Healthy recipes and meal planning

**Incentive:** Earn up to $200 in wellness rewards

### Tobacco Cessation Program
**Eligibility:** All members who use tobacco

**Services Included:**
- Tobacco cessation counseling (8 sessions per year, no copay)
- Nicotine replacement therapy (gum, patches, lozenges) - $0 copay
- Prescription cessation medications (Chantix, Zyban) - Tier 1 copay
- Quitline support 24/7
- Mobile app coaching

**Incentive:** $100 reward for completing 90-day quit program

## Care Coordination Services

### Care Transitions Program
Support for members being discharged from hospital to home or facility

**Services:**
- Post-discharge follow-up calls
- Medication reconciliation
- Follow-up appointment scheduling
- Home health coordination

### Complex Care Management
For members with multiple chronic conditions

**Services:**
- Dedicated care manager
- Care plan development
- Provider coordination
- Social services referrals
- Transportation assistance (if eligible)

## Member Incentive Program

Earn rewards for healthy behaviors:
- Complete annual physical exam: $50
- Complete preventive screenings: $25 each
- Attend health education webinar: $10 each
- Track activity for 90 days: $75
- Complete health risk assessment: $25

**Maximum annual rewards:** $500 per member

## Contact Information
**General Programs:** 1-800-TOGGLE-1
**Wellness Programs:** wellness@togglehealth.com
**Online Portal:** my.togglehealth.com/programs
""")

print("✅ Generated TH-HMO-GOLD-2024 policy documents:")
print("  - Preventive Care")
print("  - Prescription Drugs")
print("  - Special Programs")

# Generate PPO and HDHP overviews for comparison
with open('/home/user/policy_agent/data/markdown/policies/TH-PPO-PLATINUM-2024-overview.md', 'w') as f:
    f.write("""# Health Insurance Plan Overview

## Plan Identification
**Plan Name:** ToggleHealth PPO Platinum Plan
**Plan ID:** TH-PPO-PLATINUM-2024
**Plan Type:** PPO (Preferred Provider Organization)
**Effective Date:** January 1, 2024
**End Date:** December 31, 2024

## Coverage Details
**Coverage Type:** Individual and Family
**Network:** ToggleHealth Preferred Plus Network
**Primary Care Physician (PCP) Required:** No
**Referrals Required for Specialists:** No

## Annual Financial Information
**Annual Deductible:**
- Individual In-Network: $500
- Individual Out-of-Network: $1,500
- Family In-Network: $1,000
- Family Out-of-Network: $3,000

**Out-of-Pocket Maximum:**
- Individual In-Network: $4,000
- Individual Out-of-Network: $8,000
- Family In-Network: $8,000
- Family Out-of-Network: $16,000

**Monthly Premium:**
- Individual: $650
- Family: $1,750

## Plan Features
- Freedom to see any provider (in-network or out-of-network)
- Lower costs when using in-network providers
- No PCP selection required
- No referrals needed for specialists
- Nationwide coverage
- Prescription drug coverage included
- Telehealth services available

## Office Visit Copays (In-Network)
**Primary Care:** $20 per visit
**Specialist:** $40 per visit
**Urgent Care:** $60 per visit
**Emergency Room:** $250 per visit (waived if admitted)

## Out-of-Network Coverage
Services received from out-of-network providers are covered at 60% after deductible (compared to 80% in-network).

## Member Services Contact
**Phone:** 1-800-TOGGLE-1 (1-800-864-4531)
**Hours:** Monday-Friday, 8AM-8PM ET
**Website:** my.togglehealth.com
**Mobile App:** ToggleHealth Mobile (iOS & Android)
""")

print("  - TH-PPO-PLATINUM-2024 Overview")

with open('/home/user/policy_agent/data/markdown/policies/TH-HDHP-BRONZE-2024-overview.md', 'w') as f:
    f.write("""# Health Insurance Plan Overview

## Plan Identification
**Plan Name:** ToggleHealth High-Deductible Bronze Plan
**Plan ID:** TH-HDHP-BRONZE-2024
**Plan Type:** HDHP (High-Deductible Health Plan) with HSA
**Effective Date:** January 1, 2024
**End Date:** December 31, 2024

## Coverage Details
**Coverage Type:** Individual and Family
**Network:** ToggleHealth Basic Network
**Primary Care Physician (PCP) Required:** No
**Referrals Required for Specialists:** No
**HSA Eligible:** Yes

## Annual Financial Information
**Annual Deductible:**
- Individual: $3,000
- Family: $6,000

**Out-of-Pocket Maximum:**
- Individual: $7,000
- Family: $14,000

**Monthly Premium:**
- Individual: $250
- Family: $675

## Health Savings Account (HSA)
**Employer Contribution (if applicable):**
- Individual: Up to $1,000/year
- Family: Up to $2,000/year

**Member Contribution Limits (2024):**
- Individual: $4,150/year
- Family: $8,300/year
- Age 55+ catch-up: Additional $1,000/year

**HSA Benefits:**
- Tax-deductible contributions
- Tax-free growth
- Tax-free withdrawals for qualified medical expenses
- Funds roll over year to year
- Portable (yours to keep if you leave employer)

## Plan Features
- Lower monthly premiums
- High deductible must be met before coverage begins
- Preventive care covered at 100% (no deductible)
- HSA-eligible for tax advantages
- All services subject to deductible except preventive care
- After deductible: Plan pays 80%, you pay 20% coinsurance

## Cost-Sharing After Deductible
**Coinsurance:** You pay 20% of allowed amount after deductible
**No copays** - All services subject to deductible first, then coinsurance

## Preventive Care (No Deductible)
- Annual physical exam: 100% covered
- Immunizations: 100% covered
- Cancer screenings: 100% covered
- Well-child visits: 100% covered
- All ACA preventive services: 100% covered

## Member Services Contact
**Phone:** 1-800-TOGGLE-1 (1-800-864-4531)
**HSA Support:** 1-800-TOGGLE-HSA
**Hours:** Monday-Friday, 8AM-8PM ET
**Website:** my.togglehealth.com
**Mobile App:** ToggleHealth Mobile (iOS & Android)
""")

print("  - TH-HDHP-BRONZE-2024 Overview")
print("\n✅ Total: 6 policy document files created")

