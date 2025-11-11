# Quick RAG Setup Guide

## Step 1: Create Bedrock Knowledge Bases (AWS Console)

### Policy Knowledge Base

```bash
# 1. Go to AWS Bedrock Console → Knowledge Bases
# 2. Click "Create knowledge base"
# 3. Fill in:

Name: medical-insurance-policies
Description: Policy documents for customer support
IAM Role: Create new role (auto-generated)

# 4. Configure Data Source:
Type: S3
S3 URI: s3://your-bucket-name/policies/
Chunking: Fixed-size chunks (300 tokens, 10% overlap)

# 5. Select Embeddings Model:
Model: Amazon Titan Embeddings G1 - Text v2.0
Dimensions: 1024

# 6. Configure Vector Database:
Type: OpenSearch Serverless (recommended)
Collection name: medical-policies-kb

# 7. Create and note the Knowledge Base ID
# Example: ABCD123456
```

### Provider Network Knowledge Base

```bash
# Same steps as above, but:

Name: provider-network-directory
S3 URI: s3://your-bucket-name/providers/
Collection name: provider-network-kb

# Note the Knowledge Base ID
# Example: EFGH789012
```

## Step 2: Upload Sample Documents

### For Testing (Without Real Data)

Create sample policy document:

```bash
cat > sample-policy.txt << 'EOF'
GOLD PLAN BENEFITS SUMMARY

Coverage Overview:
- Preventive Care: 100% covered, no copay
- Primary Care Visit: $25 copay
- Specialist Visit: $50 copay
- Emergency Room: $250 copay
- Urgent Care: $75 copay

Physical Therapy Coverage:
- $50 copay per visit
- Maximum 30 visits per year
- Requires referral from primary care physician
- Covered for injury recovery and post-surgical rehabilitation

Mental Health Services:
- Covered same as other medical services
- In-network: $50 copay per session
- Out-of-network: 30% coinsurance

Prescription Drug Coverage:
- Tier 1 (Generic): $10 copay
- Tier 2 (Preferred Brand): $30 copay  
- Tier 3 (Non-Preferred Brand): $60 copay
- Tier 4 (Specialty): 25% coinsurance
EOF

# Upload to S3
aws s3 cp sample-policy.txt s3://your-bucket-name/policies/
```

Create sample provider document:

```bash
cat > sample-providers.txt << 'EOF'
PROVIDER NETWORK DIRECTORY - BOSTON AREA

Dr. Sarah Johnson, MD
Specialty: Primary Care Physician
Network: Premier Network
Location: 123 Medical Plaza, Boston, MA 02108
Phone: (617) 555-0123
Languages: English, Spanish
Accepting New Patients: Yes
Board Certified: American Board of Internal Medicine

Dr. Michael Chen, MD, FACC
Specialty: Cardiologist
Sub-specialty: Interventional Cardiology
Network: Premier Network
Location: 456 Heart Center Drive, Boston, MA 02109
Phone: (617) 555-0234
Languages: English, Mandarin
Accepting New Patients: Yes
Board Certified: American Board of Cardiovascular Disease

Dr. Emily Rodriguez, MD
Specialty: Dermatologist
Network: Premier Network
Location: 789 Skin Care Lane, Cambridge, MA 02139
Phone: (617) 555-0345
Languages: English, Spanish
Accepting New Patients: Yes
Board Certified: American Board of Dermatology
Special Interests: Pediatric Dermatology, Cosmetic Dermatology
EOF

# Upload to S3
aws s3 cp sample-providers.txt s3://your-bucket-name/providers/
```

## Step 3: Sync Data Sources

```bash
# In AWS Bedrock Console:
# 1. Go to your Knowledge Base
# 2. Click on the Data Source
# 3. Click "Sync"
# 4. Wait for sync to complete (usually 1-5 minutes)

# Or via CLI:
aws bedrock-agent start-ingestion-job \
    --knowledge-base-id YOUR_POLICY_KB_ID \
    --data-source-id YOUR_DATASOURCE_ID

aws bedrock-agent start-ingestion-job \
    --knowledge-base-id YOUR_PROVIDER_KB_ID \
    --data-source-id YOUR_DATASOURCE_ID
```

## Step 4: Configure Environment

Add to `.env`:

```bash
# Bedrock Knowledge Base IDs (from Step 1)
BEDROCK_POLICY_KB_ID=ABCD123456
BEDROCK_PROVIDER_KB_ID=EFGH789012

# RAG Configuration
RAG_TOP_K=5  # Number of documents to retrieve
```

## Step 5: Test RAG

```bash
# Activate virtual environment
source venv/bin/activate

# Run interactive chatbot
python interactive_chatbot.py
```

Try these queries to test RAG:

**Policy RAG Test:**
```
You: Does my plan cover physical therapy?
```

Expected output:
```
📚 Retrieving policy documents via RAG...
  🔍 Retrieving from Bedrock KB: 'Does my plan cover physical therapy...'
  ✅ Retrieved 3 documents (top score: 0.892)
  📄 Retrieved 3 relevant policy documents via RAG
    Doc 1: Score 0.892, Length 245 chars
    Doc 2: Score 0.801, Length 198 chars
    Doc 3: Score 0.765, Length 312 chars
```

**Provider RAG Test:**
```
You: I need to find a cardiologist in Boston
```

Expected output:
```
📚 Retrieving provider documents via RAG...
  🔍 Retrieving from Bedrock KB: 'I need to find a cardiologist...'
  ✅ Retrieved 2 documents (top score: 0.934)
  📄 Retrieved 2 relevant provider documents via RAG
    Doc 1: Score 0.934, Length 423 chars
    Doc 2: Score 0.812, Length 387 chars
```

## Step 6: IAM Permissions

Ensure your AWS user/role has these permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:Retrieve",
        "bedrock:RetrieveAndGenerate",
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:*:*:knowledge-base/*",
        "arn:aws:bedrock:*::foundation-model/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::your-bucket-name",
        "arn:aws:s3:::your-bucket-name/*"
      ]
    }
  ]
}
```

## Verification Checklist

- [ ] Created Policy Knowledge Base
- [ ] Created Provider Knowledge Base
- [ ] Uploaded sample documents to S3
- [ ] Synced data sources
- [ ] Added KB IDs to `.env`
- [ ] Tested IAM permissions
- [ ] Ran `python interactive_chatbot.py`
- [ ] Verified RAG retrieval in logs
- [ ] Tested with sample queries

## Troubleshooting Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| "KB ID not configured" | Add `BEDROCK_POLICY_KB_ID` to `.env` |
| "AccessDenied" error | Check IAM permissions above |
| "No documents retrieved" | Verify data source is synced |
| "InvalidRegion" | Match KB region with `AWS_REGION` in `.env` |
| RAG shows as disabled | Logs show "⚠️ not configured, RAG disabled" |

## Success Indicators

✅ **RAG Working**:
```
📚 Retrieving policy documents via RAG...
  ✅ Retrieved 5 documents (top score: 0.892)
  📄 Retrieved 5 relevant policy documents via RAG
```

❌ **RAG Not Configured**:
```
📚 Retrieving policy documents via RAG...
  ⚠️  BEDROCK_POLICY_KB_ID not configured, RAG disabled for policy
  ℹ️  Falling back to simulated policy database
```

## Advanced: Production Setup

For production use:

1. **Multiple Environments**: Separate KBs for dev/staging/prod
2. **Document Management**: CI/CD pipeline for doc updates
3. **Monitoring**: CloudWatch dashboards for RAG metrics
4. **Caching**: Redis for frequent queries
5. **Rate Limiting**: Protect against excessive retrieval costs
6. **Quality Assurance**: Human review of RAG responses

---

**Ready to go?** Follow Steps 1-5 and you'll have RAG running in minutes! 🚀

