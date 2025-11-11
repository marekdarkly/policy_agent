# Bedrock Knowledge Base RAG Integration

This guide explains how to set up and use AWS Bedrock Knowledge Base for Retrieval-Augmented Generation (RAG) in the Policy and Provider specialists.

## Overview

The system uses **hybrid retrieval** combining:
1. **RAG with Bedrock Knowledge Base** - Semantic search over documents
2. **Traditional structured databases** - Fast lookup of policy/provider data

This approach provides:
- 📚 Access to comprehensive policy documentation
- 🔍 Semantic search capabilities
- 💾 Fallback to structured data
- 🎯 Better accuracy with relevant context

## Architecture

### Policy Specialist RAG
```
User Query: "Does my plan cover physical therapy?"
    ↓
1. RAG Retrieval (Bedrock KB)
   - Searches policy documents semantically
   - Retrieves top 5 most relevant passages
   - Returns with relevance scores
    ↓
2. Database Lookup
   - Gets structured policy data (copays, deductibles, etc.)
    ↓
3. Combined Context
   - RAG documents + Structured data → LLM
    ↓
4. Generated Response
   - Grounded in both sources
```

### Provider Specialist RAG
```
User Query: "Find me a cardiologist in Boston"
    ↓
1. RAG Retrieval (Bedrock KB)
   - Searches provider network documents
   - Retrieves provider profiles, specialties, locations
   - Filters by network, location
    ↓
2. Database Search
   - Searches structured provider database
   - Filters by specialty, location, network
    ↓
3. Combined Results
   - RAG documents + Structured providers → LLM
    ↓
4. Generated Response
   - Comprehensive provider recommendations
```

## Setup Instructions

### 1. Create Bedrock Knowledge Bases

You need to create two Knowledge Bases in AWS Bedrock:

#### A. Policy Knowledge Base

1. **Go to AWS Bedrock Console** → Knowledge Bases
2. **Create Knowledge Base**: "Medical-Insurance-Policies"
3. **Data Source**: S3 bucket with policy documents
   - Policy PDFs, Terms & Conditions
   - Coverage guidelines
   - Benefits summaries
   - Claim procedures
4. **Embeddings Model**: Choose embedding model
   - Recommended: `amazon.titan-embed-text-v2:0`
   - Alternative: `cohere.embed-english-v3`
5. **Vector Store**: Choose storage
   - Amazon OpenSearch Serverless (recommended)
   - Amazon Aurora PostgreSQL
   - Pinecone
6. **Sync Data Source** and note the **Knowledge Base ID**

#### B. Provider Network Knowledge Base

1. **Create Knowledge Base**: "Provider-Network-Directory"
2. **Data Source**: S3 bucket with provider data
   - Provider profiles and credentials
   - Specialties and sub-specialties
   - Location and contact information
   - Network participation status
   - Patient reviews and ratings
3. **Embeddings Model**: Same as policy KB
4. **Vector Store**: Same technology as policy KB
5. **Sync Data Source** and note the **Knowledge Base ID**

### 2. Configure Environment Variables

Add to your `.env` file:

```bash
# Bedrock Knowledge Base IDs
BEDROCK_POLICY_KB_ID=your-policy-kb-id-here
BEDROCK_PROVIDER_KB_ID=your-provider-kb-id-here

# Optional: Number of documents to retrieve
RAG_TOP_K=5

# Existing AWS config (required for KB access)
AWS_REGION=us-east-1
AWS_PROFILE=marek
```

### 3. Prepare Your Knowledge Base Data

#### Policy Documents Structure

Organize policy documents in S3:

```
s3://your-policy-bucket/
├── policies/
│   ├── gold-plan-benefits.pdf
│   ├── silver-plan-benefits.pdf
│   ├── coverage-guidelines.pdf
│   └── exclusions-limitations.pdf
├── procedures/
│   ├── claims-process.pdf
│   ├── appeals-process.pdf
│   └── pre-authorization.pdf
└── reference/
    ├── copay-schedules.pdf
    ├── deductible-information.pdf
    └── network-tiers.pdf
```

#### Provider Directory Structure

Organize provider data in S3:

```
s3://your-provider-bucket/
├── providers/
│   ├── primary-care-physicians.json
│   ├── specialists/
│   │   ├── cardiology.json
│   │   ├── dermatology.json
│   │   └── orthopedics.json
│   └── facilities/
│       ├── hospitals.json
│       └── urgent-care.json
├── networks/
│   ├── premier-network.json
│   └── standard-network.json
└── metadata/
    ├── provider-credentials.json
    └── quality-ratings.json
```

### 4. Test the RAG Implementation

Run the verification script:

```bash
python verify_ld_configs.py
```

Run the interactive chatbot to test RAG:

```bash
python interactive_chatbot.py
```

### 5. Monitor RAG Performance

The system logs detailed RAG metrics:

```
📚 Retrieving policy documents via RAG...
  🔍 Retrieving from Bedrock KB: 'Does my plan cover physical therapy...'
  ✅ Retrieved 5 documents (top score: 0.892)
  📄 Retrieved 5 relevant policy documents via RAG
    Doc 1: Score 0.892, Length 1234 chars
    Doc 2: Score 0.801, Length 987 chars
    Doc 3: Score 0.765, Length 1456 chars
```

## How RAG Works in Each Agent

### Policy Specialist with RAG

**Before RAG:**
- Only used structured database (limited to predefined policy data)
- Couldn't answer nuanced questions about policy terms

**With RAG:**
- Searches comprehensive policy documentation
- Finds relevant clauses and terms semantically
- Combines with structured data for complete answers
- Can answer complex policy questions with citations

**Example:**

```python
Query: "What are the exclusions for my Gold Plan?"

RAG Retrieval:
├─ Doc 1 (0.91): "Gold Plan Exclusions: Cosmetic procedures..."
├─ Doc 2 (0.84): "Pre-existing conditions covered after 6 months..."
└─ Doc 3 (0.76): "Experimental treatments not covered unless..."

Database:
└─ Policy POL-12345: {copays, deductibles, network}

LLM Response:
├─ Synthesizes RAG documents + structured data
└─ Generates comprehensive answer with citations
```

### Provider Specialist with RAG

**Before RAG:**
- Only searched structured provider database
- Limited to predefined provider fields

**With RAG:**
- Searches provider profiles, specializations, reviews
- Finds providers by detailed criteria (sub-specialties, languages, etc.)
- Combines with structured database for accurate results
- Can match providers to complex patient needs

**Example:**

```python
Query: "I need a pediatric cardiologist who speaks Spanish in Boston"

RAG Retrieval:
├─ Doc 1 (0.93): "Dr. Maria Rodriguez, Pediatric Cardiology, Languages: English, Spanish..."
├─ Doc 2 (0.87): "Boston Children's Heart Center, Spanish-speaking staff available..."
└─ Doc 3 (0.79): "Network participation: Dr. Rodriguez participates in Premier..."

Database:
└─ Provider search: specialty="cardiologist", location="Boston"

LLM Response:
├─ Combines RAG findings + database results
└─ Recommends Dr. Rodriguez with full details
```

## Bedrock Knowledge Base APIs Used

### 1. Retrieve API

For granular control over retrieved documents:

```python
from src.tools.bedrock_rag import get_policy_retriever

retriever = get_policy_retriever(top_k=5)
documents = retriever.retrieve("Does my plan cover physical therapy?")

# Returns list of documents with:
# - content: The actual text
# - score: Relevance score (0-1)
# - metadata: Source file, location, etc.
```

### 2. RetrieveAndGenerate API

For end-to-end RAG (Bedrock handles both retrieval and generation):

```python
retriever = get_policy_retriever()
result = retriever.retrieve_and_generate(
    query="What is my deductible?",
    model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20241022-v2:0"
)

# Returns:
# - output: Generated response
# - citations: Source documents used
# - session_id: For conversation continuity
```

## Benefits of This Implementation

### 1. Hybrid Approach
- ✅ RAG provides semantic search over comprehensive documents
- ✅ Database provides fast, structured data access
- ✅ Fallback to database if RAG fails or is not configured
- ✅ Best of both worlds!

### 2. Flexible Configuration
- 🔧 Enable/disable RAG per agent via environment variables
- 🔧 Configure number of documents to retrieve (`RAG_TOP_K`)
- 🔧 Use different KB IDs for different environments
- 🔧 Gradual rollout: test RAG with some agents first

### 3. Rich Debug Logging
- 📊 See which documents are retrieved
- 📈 View relevance scores
- 🔍 Monitor RAG vs database usage
- 📉 Track RAG performance

### 4. Cost Optimization
- 💰 Only pay for embeddings when RAG is used
- 💰 Can disable RAG for simpler queries
- 💰 Bedrock KB pricing is pay-per-use
- 💰 LaunchDarkly can control which users get RAG

## Advanced: LaunchDarkly + RAG

You can use LaunchDarkly to control RAG behavior:

### Feature Flag for RAG

Create a feature flag `enable-rag-policy` to:
- Enable RAG for premium users only
- A/B test RAG vs non-RAG responses
- Gradually roll out RAG (10% → 50% → 100%)
- Disable RAG if performance issues occur

### AI Config with RAG Parameters

Enhance AI Configs to include RAG settings:

```json
{
  "model": {
    "name": "claude-3-5-sonnet",
    "parameters": {
      "temperature": 0.7,
      "maxTokens": 3000
    }
  },
  "provider": "bedrock",
  "enabled": true,
  "custom": {
    "rag_enabled": true,
    "rag_top_k": 5,
    "rag_score_threshold": 0.7
  }
}
```

## Troubleshooting

### "BEDROCK_POLICY_KB_ID not configured"

**Cause**: Knowledge Base ID not set in environment

**Solution**: Add to `.env`:
```bash
BEDROCK_POLICY_KB_ID=ABCDEFGHIJ  # Your actual KB ID
```

### "Error retrieving from Bedrock KB"

**Causes**:
1. Knowledge Base ID is incorrect
2. AWS credentials don't have permission
3. Knowledge Base is in a different region
4. Data source not synced

**Solutions**:
1. Verify KB ID in AWS Console
2. Check IAM permissions include `bedrock:Retrieve*`
3. Match KB region with `AWS_REGION` in `.env`
4. Sync data source in Bedrock console

### "No documents retrieved"

**Causes**:
1. Query doesn't match document content
2. Knowledge Base is empty
3. Embedding model mismatch

**Solutions**:
1. Refine query with more specific terms
2. Upload and sync documents to S3
3. Verify embedding model consistency

### High Latency

**Causes**:
- First query initializes connections
- Large number of documents in KB
- Complex semantic search

**Optimizations**:
- Reduce `RAG_TOP_K` (fewer documents)
- Use smaller embedding models
- Consider caching frequent queries
- Use Bedrock KB's built-in caching

## Best Practices

### 1. Document Preparation
- ✅ Clean and format documents before upload
- ✅ Add metadata for better filtering
- ✅ Split long documents into chunks
- ✅ Use consistent naming conventions

### 2. Query Enhancement
- ✅ Include context in queries (policy ID, user info)
- ✅ Be specific about what you're looking for
- ✅ Use domain-specific terminology
- ✅ Combine multiple search strategies

### 3. Result Validation
- ✅ Check relevance scores (>0.7 is good)
- ✅ Validate against structured data
- ✅ Cite sources in responses
- ✅ Log retrieval quality metrics

### 4. Performance Monitoring
- 📊 Track retrieval latency
- 📊 Monitor relevance score distribution
- 📊 Measure query success rate
- 📊 Compare RAG vs non-RAG accuracy

## Cost Estimation

### Bedrock Knowledge Base Pricing (us-east-1)

**Embeddings**:
- Titan Embed: ~$0.10 per 1M tokens
- Cohere Embed: ~$0.10 per 1M tokens

**Vector Storage** (OpenSearch Serverless):
- ~$0.24/OCU-hour for indexing
- ~$0.24/OCU-hour for search

**Retrieval**:
- Free (included in Bedrock pricing)

**Example Monthly Cost**:
- 10,000 documents (500 tokens each) = 5M tokens
- Embedding cost: $0.50 (one-time)
- Storage: ~$180/month (1 OCU search)
- Very cost-effective for improved accuracy!

## Next Steps

1. **Create Knowledge Bases** in AWS Bedrock Console
2. **Upload Documents** to S3 data sources
3. **Configure Environment** with KB IDs
4. **Test RAG** with interactive chatbot
5. **Monitor Performance** and optimize
6. **Integrate with LaunchDarkly** for advanced control

## Additional Resources

- [AWS Bedrock Knowledge Base Documentation](https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base.html)
- [Bedrock Agent Runtime API Reference](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_agent-runtime_Retrieve.html)
- [LangChain AWS Integration](https://python.langchain.com/docs/integrations/providers/aws)
- [RAG Best Practices](https://docs.aws.amazon.com/bedrock/latest/userguide/kb-best-practices.html)

## Example: Creating a Policy Knowledge Base

### Step-by-Step AWS Console

1. **Navigate to Bedrock** → Knowledge Bases → Create
2. **Name**: `medical-insurance-policies`
3. **Description**: "Policy documents for multi-agent support system"
4. **IAM Permissions**: Create new service role
5. **Data Source**:
   - Type: S3
   - Bucket: `s3://your-policy-documents-bucket/`
   - Chunking: Fixed-size (300 tokens, 10% overlap)
6. **Embeddings**:
   - Model: `amazon.titan-embed-text-v2:0`
   - Dimensions: 1024
7. **Vector Store**:
   - OpenSearch Serverless (managed)
   - Index name: `policy-docs-index`
8. **Create** and wait for status: Active
9. **Sync** data source
10. **Copy Knowledge Base ID** → Add to `.env`

### Example: Uploading Policy Documents

```bash
# Create S3 bucket
aws s3 mb s3://your-policy-documents-bucket

# Upload policy PDFs
aws s3 cp ./policy-docs/ s3://your-policy-documents-bucket/policies/ --recursive

# Sync in Bedrock console or via API
aws bedrock-agent start-ingestion-job \
    --knowledge-base-id YOUR_KB_ID \
    --data-source-id YOUR_DATASOURCE_ID
```

## Monitoring RAG in Production

### Metrics to Track

1. **Retrieval Quality**
   - Average relevance scores
   - Documents retrieved per query
   - Queries with no results

2. **Response Quality**
   - Accuracy (RAG vs non-RAG)
   - User satisfaction
   - Citation usage

3. **Performance**
   - Retrieval latency (p50, p95, p99)
   - End-to-end latency
   - Cache hit rate

4. **Cost**
   - Embeddings generated
   - Storage size
   - Query volume

### LaunchDarkly Integration for RAG Control

Use LaunchDarkly to:
- ✅ Enable/disable RAG per agent
- ✅ A/B test RAG vs non-RAG
- ✅ Control `top_k` dynamically
- ✅ Set minimum relevance score thresholds
- ✅ Target RAG to specific user segments

## Conclusion

RAG with Bedrock Knowledge Base enhances your multi-agent system by:
- 🎯 Improving accuracy with relevant context
- 📚 Accessing comprehensive documentation
- 🔍 Enabling semantic search
- 💡 Providing better, more informed responses
- 📊 Maintaining full observability

The hybrid approach (RAG + structured DB) ensures robustness while maximizing response quality!

