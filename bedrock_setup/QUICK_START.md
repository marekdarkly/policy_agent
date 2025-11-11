# ToggleHealth Bedrock KB - Quick Start Guide

## What You Get

Two Bedrock Knowledge Bases ready to answer questions about:
1. **Policy KB** - Insurance plans, coverage, costs, pharmacy benefits
2. **Provider KB** - Doctors, hospitals, networks, locations

## Prerequisites

- AWS Account
- AWS CLI installed and configured
- Permissions for S3, Bedrock, IAM, OpenSearch Serverless

## Option 1: Automated Setup (Recommended)

### Step 1: Upload to S3

```bash
cd /home/user/policy_agent
./bedrock_setup/setup_s3_buckets.sh
```

This script will:
- Create 2 S3 buckets
- Upload markdown files
- Enable versioning
- Save configuration

**Time:** 2-3 minutes

### Step 2: Create IAM Role

Follow the prompts from the S3 setup script or manually create:

```bash
# Load saved configuration
source bedrock_setup/config.env

# Create IAM role (see README_BEDROCK_SETUP.md Step 4)
```

**Time:** 5 minutes

### Step 3: Create OpenSearch Collection

```bash
# See README_BEDROCK_SETUP.md Step 5
# Or use AWS Console → OpenSearch Service → Serverless collections
```

**Time:** 10 minutes

### Step 4: Create Knowledge Bases (AWS Console)

**Policy KB:**
1. Bedrock Console → Knowledge bases → Create
2. Name: `togglehealth-policy-kb`
3. IAM Role: `BedrockKnowledgeBaseRole`
4. Data source: S3 → Use saved URI from config.env
5. Embeddings: Titan Embeddings G1 - Text v2.0
6. Vector store: OpenSearch Serverless → `togglehealth-kb-vectors`
7. Index: `policy-index`
8. Create and Sync

**Provider KB:**
1. Repeat above with name: `togglehealth-provider-kb`
2. Use provider S3 URI
3. Index: `provider-index`
4. Create and Sync

**Time:** 15-20 minutes

### Step 5: Test

```bash
# Test queries (replace with your KB IDs)
aws bedrock-agent-runtime retrieve-and-generate \
    --knowledge-base-id <POLICY_KB_ID> \
    --input '{"text":"What is the copay for primary care on Gold HMO?"}' \
    --region us-west-2

aws bedrock-agent-runtime retrieve-and-generate \
    --knowledge-base-id <PROVIDER_KB_ID> \
    --input '{"text":"Find a cardiologist in Seattle"}' \
    --region us-west-2
```

**Total Setup Time:** 30-40 minutes

---

## Option 2: Manual Setup

Follow the detailed guide: [README_BEDROCK_SETUP.md](README_BEDROCK_SETUP.md)

---

## Sample Queries

### Policy Knowledge Base

**Coverage Questions:**
- "What does the Platinum PPO plan cover for mental health?"
- "What is the deductible for the Bronze HDHP?"
- "Does the Gold HMO cover acupuncture?"
- "What services require preauthorization?"
- "How do I file a claim for out-of-network care?"

**Cost Questions:**
- "What are the copays for the Silver EPO plan?"
- "How much does the Gold HMO cost per month?"
- "What is the out-of-pocket maximum for Platinum PPO?"
- "What are the prescription copays for generic drugs?"

**Program Questions:**
- "What is the Diabetes Management Program?"
- "Am I eligible for the Heart Health Program?"
- "What benefits does the Maternity Support Program include?"
- "How does the HSA work with the Bronze HDHP?"

**Pharmacy Questions:**
- "What tier is Humira in the formulary?"
- "Can I use mail order pharmacy?"
- "Do I need prior authorization for specialty medications?"
- "What pharmacies are in network?"

### Provider Knowledge Base

**Provider Search:**
- "Find a primary care doctor in Seattle who speaks Spanish"
- "Show me cardiologists in the Platinum PPO network"
- "Are there orthopedic surgeons in Bellevue?"
- "Which mental health providers accept Gold HMO in Tacoma?"

**Hospital Questions:**
- "What hospitals are in the EPO network in Portland?"
- "Which hospital has the best rating in Seattle?"
- "Does Seattle General Hospital have a trauma center?"
- "What are the visiting hours for Northwest Medical Center?"

**Location Questions:**
- "Where is the nearest ToggleHealth urgent care?"
- "Are there any providers in Spokane County?"
- "What pharmacies are open on Sunday?"

**Details Questions:**
- "What languages does Dr. Sarah Anderson speak?"
- "What are Dr. Michael Chen's credentials?"
- "Which hospital is Dr. Lisa Patel affiliated with?"
- "Is Dr. Robert Williams accepting new patients?"

---

## Recommended Configuration

### Knowledge Base Settings

**Chunking:**
- Strategy: Fixed-size
- Max tokens: 300
- Overlap: 10% (30 tokens)

**Retrieval:**
- Number of results: 5-10
- Search type: Hybrid (if available)
- Enable reranking: Yes

**Vector Store (OpenSearch Serverless):**
- Start with 2 OCU
- Can reduce to 1 OCU for lower costs
- Enable auto-scaling if available

### Cost Optimization

**Low Budget ($200-250/month):**
- 1 OCU OpenSearch Serverless
- Combined KB (policy + provider in one)
- Basic querying

**Recommended ($350-400/month):**
- 2 OCU OpenSearch Serverless
- Separate KBs for policy and provider
- Better performance and reliability

**Production ($500+/month):**
- 4+ OCU with auto-scaling
- Separate KBs with redundancy
- Monitoring and alerting

---

## Integration Examples

### Python SDK

```python
import boto3

bedrock = boto3.client('bedrock-agent-runtime', region_name='us-west-2')

def query_policy_kb(question):
    response = bedrock.retrieve_and_generate(
        input={'text': question},
        retrieveAndGenerateConfiguration={
            'type': 'KNOWLEDGE_BASE',
            'knowledgeBaseConfiguration': {
                'knowledgeBaseId': 'YOUR_POLICY_KB_ID',
                'modelArn': 'arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0'
            }
        }
    )
    return response['output']['text']

# Usage
answer = query_policy_kb("What is the copay for specialist visits on Gold HMO?")
print(answer)
```

### Node.js SDK

```javascript
const { BedrockAgentRuntimeClient, RetrieveAndGenerateCommand } = require("@aws-sdk/client-bedrock-agent-runtime");

const client = new BedrockAgentRuntimeClient({ region: "us-west-2" });

async function queryProviderKB(question) {
    const command = new RetrieveAndGenerateCommand({
        input: { text: question },
        retrieveAndGenerateConfiguration: {
            type: "KNOWLEDGE_BASE",
            knowledgeBaseConfiguration: {
                knowledgeBaseId: "YOUR_PROVIDER_KB_ID",
                modelArn: "arn:aws:bedrock:us-west-2::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            }
        }
    });

    const response = await client.send(command);
    return response.output.text;
}

// Usage
const answer = await queryProviderKB("Find a cardiologist in Seattle");
console.log(answer);
```

---

## Troubleshooting

### "Access Denied" Error

**Solution:**
- Check IAM role permissions
- Verify S3 bucket permissions
- Ensure Bedrock has access to embedding model

### Poor Answer Quality

**Solutions:**
- Increase number of retrieved chunks (try 10-15)
- Use more specific questions
- Enable reranking if available
- Check if markdown files synced correctly

### Slow Responses

**Solutions:**
- Increase OCU capacity
- Enable caching for common queries
- Use metadata filters to narrow search
- Check OpenSearch collection status

### Sync Failures

**Solutions:**
- Verify S3 bucket access
- Check markdown file format
- Review sync logs in console
- Ensure files are under 50MB each

---

## Next Steps After Setup

1. **Test Thoroughly** - Run 20-30 diverse queries
2. **Monitor Performance** - Track query latency and accuracy
3. **Integrate** - Build application that uses the KBs
4. **Optimize** - Adjust settings based on query patterns
5. **Expand** - Add more providers and plans as needed

---

## Support Resources

- **AWS Bedrock Docs:** https://docs.aws.amazon.com/bedrock/
- **Knowledge Base Guide:** https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html
- **SDK Reference:** https://docs.aws.amazon.com/bedrock/latest/APIReference/

---

## Files in This Setup Package

- `README_BEDROCK_SETUP.md` - Detailed step-by-step guide
- `QUICK_START.md` - This file - quickstart guide
- `setup_s3_buckets.sh` - Automated S3 setup script
- `config.env` - Generated configuration (after running setup)

---

**Questions?** Review the detailed README or AWS Bedrock documentation.

**Ready to start?** Run `./bedrock_setup/setup_s3_buckets.sh`
