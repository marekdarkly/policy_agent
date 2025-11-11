# Bedrock Knowledge Base Setup Guide

This guide will help you deploy the ToggleHealth policy and provider datasets to Amazon Bedrock Knowledge Base.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured (`aws configure`)
3. **Permissions Required:**
   - S3: CreateBucket, PutObject, GetObject
   - Bedrock: CreateKnowledgeBase, CreateDataSource
   - IAM: CreateRole, AttachRolePolicy
   - OpenSearch Serverless: CreateCollection (if using OSS for vector store)

## Architecture Overview

```
Markdown Files (local)
    ↓
S3 Buckets (2 buckets)
    ├─ togglehealth-policy-kb-source/
    │   └─ policy markdown files
    └─ togglehealth-provider-kb-source/
        └─ provider markdown files
    ↓
Bedrock Knowledge Bases (2 KBs)
    ├─ togglehealth-policy-kb
    │   ├─ Data Source: S3 (policy bucket)
    │   ├─ Embeddings: amazon.titan-embed-text-v2
    │   └─ Vector Store: OpenSearch Serverless
    └─ togglehealth-provider-kb
        ├─ Data Source: S3 (provider bucket)
        ├─ Embeddings: amazon.titan-embed-text-v2
        └─ Vector Store: OpenSearch Serverless
```

## Step-by-Step Setup

### Step 1: Set Environment Variables

```bash
# Set your AWS region
export AWS_REGION="us-west-2"  # Change to your preferred region

# Set S3 bucket names (must be globally unique)
export POLICY_BUCKET="togglehealth-policy-kb-source-$(date +%s)"
export PROVIDER_BUCKET="togglehealth-provider-kb-source-$(date +%s)"

# Set Knowledge Base names
export POLICY_KB_NAME="togglehealth-policy-kb"
export PROVIDER_KB_NAME="togglehealth-provider-kb"

# Set embedding model
export EMBEDDING_MODEL="amazon.titan-embed-text-v2:0"
```

### Step 2: Create S3 Buckets

```bash
# Create policy bucket
aws s3 mb s3://$POLICY_BUCKET --region $AWS_REGION

# Create provider bucket
aws s3 mb s3://$PROVIDER_BUCKET --region $AWS_REGION

# Enable versioning (recommended)
aws s3api put-bucket-versioning \
    --bucket $POLICY_BUCKET \
    --versioning-configuration Status=Enabled

aws s3api put-bucket-versioning \
    --bucket $PROVIDER_BUCKET \
    --versioning-configuration Status=Enabled
```

### Step 3: Upload Markdown Files to S3

```bash
# Upload policy markdown files
aws s3 sync data/markdown/ s3://$POLICY_BUCKET/policy/ \
    --exclude "*" \
    --include "policy_overview.md" \
    --include "plan_*.md" \
    --include "special_programs.md" \
    --include "pharmacy_benefits.md" \
    --include "claims_and_preauthorization.md"

# Upload provider markdown files
aws s3 sync data/markdown/ s3://$PROVIDER_BUCKET/provider/ \
    --exclude "*" \
    --include "provider_directory_overview.md" \
    --include "providers_detailed.md"

# Verify uploads
aws s3 ls s3://$POLICY_BUCKET/policy/ --recursive
aws s3 ls s3://$PROVIDER_BUCKET/provider/ --recursive
```

### Step 4: Create IAM Role for Bedrock

Bedrock needs permissions to access your S3 buckets and use the embedding model.

```bash
# Create trust policy
cat > bedrock-kb-trust-policy.json << 'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "bedrock.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create IAM role
aws iam create-role \
    --role-name BedrockKnowledgeBaseRole \
    --assume-role-policy-document file://bedrock-kb-trust-policy.json

# Create permission policy for S3 access
cat > bedrock-kb-permissions.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::$POLICY_BUCKET/*",
        "arn:aws:s3:::$POLICY_BUCKET",
        "arn:aws:s3:::$PROVIDER_BUCKET/*",
        "arn:aws:s3:::$PROVIDER_BUCKET"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/amazon.titan-embed-text-v2:0"
    },
    {
      "Effect": "Allow",
      "Action": [
        "aoss:APIAccessAll"
      ],
      "Resource": "*"
    }
  ]
}
EOF

# Attach permission policy
aws iam put-role-policy \
    --role-name BedrockKnowledgeBaseRole \
    --policy-name BedrockKBPermissions \
    --policy-document file://bedrock-kb-permissions.json

# Get the role ARN (save this)
export KB_ROLE_ARN=$(aws iam get-role --role-name BedrockKnowledgeBaseRole --query 'Role.Arn' --output text)
echo "Role ARN: $KB_ROLE_ARN"
```

### Step 5: Create OpenSearch Serverless Collection

Bedrock Knowledge Base needs a vector store. OpenSearch Serverless is recommended.

```bash
# Create security policy
cat > oss-security-policy.json << 'EOF'
{
  "Rules": [
    {
      "ResourceType": "collection",
      "Resource": ["collection/togglehealth-kb-vectors"]
    }
  ],
  "AWSOwnedKey": true
}
EOF

aws opensearchserverless create-security-policy \
    --name togglehealth-kb-encryption \
    --type encryption \
    --policy file://oss-security-policy.json

# Create network policy
cat > oss-network-policy.json << 'EOF'
{
  "Rules": [
    {
      "ResourceType": "collection",
      "Resource": ["collection/togglehealth-kb-vectors"]
    },
    {
      "ResourceType": "dashboard",
      "Resource": ["collection/togglehealth-kb-vectors"]
    }
  ],
  "AllowFromPublic": true
}
EOF

aws opensearchserverless create-security-policy \
    --name togglehealth-kb-network \
    --type network \
    --policy file://oss-network-policy.json

# Create collection
aws opensearchserverless create-collection \
    --name togglehealth-kb-vectors \
    --type VECTORSEARCH \
    --description "Vector store for ToggleHealth Knowledge Bases"

# Wait for collection to be active
aws opensearchserverless batch-get-collection \
    --names togglehealth-kb-vectors

# Get collection endpoint (save this)
export COLLECTION_ENDPOINT=$(aws opensearchserverless batch-get-collection \
    --names togglehealth-kb-vectors \
    --query 'collectionDetails[0].collectionEndpoint' \
    --output text)
echo "Collection Endpoint: $COLLECTION_ENDPOINT"
```

### Step 6: Create Knowledge Bases via Console

**Note:** As of now, creating Knowledge Bases is easier through the AWS Console. Follow these steps:

#### For Policy Knowledge Base:

1. Go to Amazon Bedrock console → Knowledge bases → Create knowledge base
2. **KB Details:**
   - Name: `togglehealth-policy-kb`
   - Description: "ToggleHealth insurance policy and coverage information"
   - IAM Role: Select `BedrockKnowledgeBaseRole`
3. **Data Source:**
   - Data source name: `policy-s3-source`
   - S3 URI: `s3://<POLICY_BUCKET>/policy/`
4. **Embeddings Model:**
   - Select: `Titan Embeddings G1 - Text v2.0`
5. **Vector Store:**
   - Select: OpenSearch Serverless
   - Collection: `togglehealth-kb-vectors`
   - Index name: `policy-index`
   - Vector field: `vector`
   - Text field: `text`
   - Metadata field: `metadata`
6. **Review and Create**

#### For Provider Knowledge Base:

1. Repeat above steps with these changes:
   - Name: `togglehealth-provider-kb`
   - Description: "ToggleHealth provider network and directory information"
   - Data source name: `provider-s3-source`
   - S3 URI: `s3://<PROVIDER_BUCKET>/provider/`
   - Index name: `provider-index`

### Step 7: Sync Data Sources

After creating the Knowledge Bases:

1. Go to each Knowledge Base
2. Click on the data source
3. Click "Sync" to ingest the markdown files
4. Wait for sync to complete (usually 5-10 minutes)

### Step 8: Test Knowledge Bases

#### Test Policy KB:

```bash
# Save KB ID
export POLICY_KB_ID="<your-policy-kb-id>"

# Test query
aws bedrock-agent-runtime retrieve-and-generate \
    --knowledge-base-id $POLICY_KB_ID \
    --input '{
        "text": "What is the copay for a primary care visit on the Gold HMO plan?"
    }' \
    --region $AWS_REGION
```

#### Test Provider KB:

```bash
# Save KB ID
export PROVIDER_KB_ID="<your-provider-kb-id>"

# Test query
aws bedrock-agent-runtime retrieve-and-generate \
    --knowledge-base-id $PROVIDER_KB_ID \
    --input '{
        "text": "Find a cardiologist in Seattle who accepts the Platinum PPO plan"
    }' \
    --region $AWS_REGION
```

## Recommended Configuration

### Chunking Strategy

**Recommended Settings:**
- **Chunking Strategy:** Fixed-size chunking
- **Max Tokens:** 300 tokens
- **Overlap:** 10% (30 tokens)

These settings work well because:
- Markdown files have clear section boundaries
- Each section contains complete, self-contained information
- 300 tokens captures full context for most questions
- Small overlap ensures continuity between chunks

### Metadata Filtering

Enable metadata filtering for:
- **Plan Type:** Filter by specific plan (Gold HMO, Platinum PPO, etc.)
- **Service Type:** Filter by service category (preventive, specialist, etc.)
- **Network:** Filter by network ID
- **Provider Type:** Filter by provider specialty
- **Geographic Location:** Filter by state or county

### Retrieval Configuration

**Recommended Settings:**
- **Number of Results:** 5-10 chunks
- **Search Type:** Hybrid (combines semantic and keyword search)
- **Reranking:** Enable if available

## Cost Estimation

### Storage Costs (S3)

- **Policy bucket:** ~1-2 MB = $0.023/month
- **Provider bucket:** ~500 KB - 1 MB = $0.012/month
- **Total S3:** < $0.05/month

### OpenSearch Serverless

- **OCU (OpenSearch Compute Units):** 2 OCU minimum = ~$350/month
- **Storage:** First 10 GB included
- **Can reduce to 1 OCU if low query volume:** ~$175/month

### Bedrock Knowledge Base

- **Embedding Generation:** $0.0001 per 1000 tokens
- **Initial ingestion:** ~$0.50 (one-time)
- **Query Costs:**
  - Retrieval: Free
  - Generate embeddings for queries: $0.0001 per 1000 tokens
  - ~$0.01 per 1000 queries

### Total Estimated Monthly Cost

- **Minimum:** ~$175/month (1 OCU)
- **Recommended:** ~$350/month (2 OCU for better performance)
- **Plus query costs:** ~$1-5/month for moderate usage

## Best Practices

### 1. Document Organization

✅ **Do:**
- Organize files by topic (policy, provider, plans)
- Use descriptive file names
- Maintain consistent formatting

❌ **Don't:**
- Mix policy and provider data in same bucket
- Use nested folder structures (keep flat)
- Include non-text files

### 2. Chunking Optimization

✅ **Do:**
- Use clear section headers (## Heading)
- Keep related information together
- Repeat key context in each section

❌ **Don't:**
- Create sections larger than 500 tokens
- Split tables across chunks
- Remove contextual information

### 3. Metadata Usage

✅ **Do:**
- Tag documents with plan types
- Include geographic information
- Mark document update dates

❌ **Don't:**
- Overload with unnecessary metadata
- Use inconsistent tag formats

### 4. Regular Updates

- **Sync frequency:** When source data changes
- **Full re-sync:** Quarterly (to ensure consistency)
- **Monitor sync status:** Check for failures
- **Version your S3 data:** Keep previous versions for rollback

### 5. Query Optimization

✅ **Good Queries:**
- "What is the copay for specialist visits on the Gold HMO plan?"
- "Find cardiologists in Seattle accepting Platinum PPO"
- "What services require preauthorization?"

❌ **Poor Queries:**
- "Tell me everything about insurance" (too broad)
- "xyz" (too vague)
- Multi-part questions without structure

## Monitoring and Maintenance

### Monitor These Metrics:

1. **Sync Status:**
   - Check data source sync completion
   - Monitor for sync failures
   - Review ingestion errors

2. **Query Performance:**
   - Average query latency
   - Retrieval accuracy
   - User satisfaction

3. **Cost Tracking:**
   - OCU usage patterns
   - Query volume trends
   - Storage growth

### Maintenance Tasks:

- **Weekly:** Check sync status
- **Monthly:** Review query logs and accuracy
- **Quarterly:** Full data re-sync
- **Annually:** Review and optimize chunking strategy

## Troubleshooting

### Issue: Sync Fails

**Check:**
- S3 bucket permissions
- IAM role has correct policies
- Files are valid markdown

**Solution:**
```bash
# Verify IAM role
aws iam get-role-policy \
    --role-name BedrockKnowledgeBaseRole \
    --policy-name BedrockKBPermissions

# Verify S3 access
aws s3 ls s3://$POLICY_BUCKET/policy/
```

### Issue: Poor Retrieval Quality

**Solutions:**
- Adjust chunk size (try 200-400 tokens)
- Increase number of retrieved chunks (try 10-15)
- Enable reranking
- Add more context to queries

### Issue: Slow Queries

**Solutions:**
- Increase OCU capacity
- Reduce number of retrieved chunks
- Use metadata filtering to narrow search

## Next Steps

After setup:

1. **Test Thoroughly:**
   - Run 20-30 test queries
   - Cover different plan types
   - Test provider searches

2. **Integrate with Application:**
   - Use AWS SDK to query KBs
   - Implement caching for common queries
   - Add error handling

3. **Monitor and Optimize:**
   - Track query patterns
   - Identify common questions
   - Refine chunking if needed

4. **Expand Dataset:**
   - Add more providers as needed
   - Update policies annually
   - Add FAQs based on user questions

---

## Quick Reference

### Useful AWS CLI Commands

```bash
# List Knowledge Bases
aws bedrock-agent list-knowledge-bases --region $AWS_REGION

# Get KB details
aws bedrock-agent get-knowledge-base \
    --knowledge-base-id <kb-id> \
    --region $AWS_REGION

# Start sync
aws bedrock-agent start-ingestion-job \
    --knowledge-base-id <kb-id> \
    --data-source-id <ds-id> \
    --region $AWS_REGION

# Query KB
aws bedrock-agent-runtime retrieve \
    --knowledge-base-id <kb-id> \
    --retrieval-query '{"text":"your question"}' \
    --region $AWS_REGION
```

### Important ARNs and IDs

Save these after creation:
- KB Role ARN: `arn:aws:iam::ACCOUNT:role/BedrockKnowledgeBaseRole`
- Policy KB ID: `<from console>`
- Provider KB ID: `<from console>`
- Collection Endpoint: `<from OSS>`

---

**Questions?** Review AWS Bedrock Knowledge Base documentation or contact AWS Support.
