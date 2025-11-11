# AWS Bedrock Setup Guide

This guide explains how to configure AWS Bedrock as the LLM provider for the medical insurance support multi-agent system.

## Overview

AWS Bedrock is the default LLM provider for this system, offering:
- **Unified API**: Single Converse API across multiple model providers
- **Model Choice**: Claude, Llama, Titan, and more
- **AWS Integration**: Native integration with AWS services
- **Cost Management**: Pay-per-use with no upfront commitments
- **Security**: AWS IAM-based authentication and authorization
- **Auto Token Refresh**: Automatic AWS SSO token refresh

## Prerequisites

1. **AWS Account** with Bedrock access
2. **AWS CLI** installed (v2 recommended)
3. **Model Access** enabled in Bedrock console

## Setup Instructions

### 1. Install AWS CLI

If not already installed:

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download from: https://awscli.amazonaws.com/AWSCLIV2.msi
```

Verify installation:
```bash
aws --version
```

### 2. Configure AWS SSO

Set up AWS SSO with your organization:

```bash
aws configure sso
```

Follow the prompts:
- **SSO session name**: `agent` (or your preferred name)
- **SSO start URL**: Your organization's AWS SSO URL
- **SSO region**: Your region (e.g., `us-east-1`)
- **SSO registration scopes**: `sso:account:access`

Select the account and role you want to use.

### 3. Configure AWS Profile

Create/update `~/.aws/config`:

```ini
[profile agent]
sso_session = agent
sso_account_id = 123456789012
sso_role_name = YourRoleName
region = us-east-1
output = json

[sso-session agent]
sso_start_url = https://your-org.awsapps.com/start
sso_region = us-east-1
sso_registration_scopes = sso:account:access
```

### 4. Login to AWS SSO

```bash
aws sso login --profile agent
```

This will:
1. Open your browser
2. Ask you to authorize the session
3. Cache credentials locally

### 5. Enable Bedrock Model Access

1. Go to AWS Console → Bedrock → Model access
2. Request access to models you want to use:
   - **Anthropic Claude 3.5 Sonnet** (recommended)
   - **Anthropic Claude 3 Haiku** (cost-effective)
   - **Meta Llama 3.1 70B**
   - **Amazon Titan**

Model access is typically granted immediately for most models.

### 6. Configure Environment

Update your `.env` file:

```bash
# AWS Bedrock Configuration
AWS_PROFILE=agent
AWS_REGION=us-east-1
LLM_PROVIDER=bedrock
LLM_MODEL=claude-3-5-sonnet
```

### 7. Test Connection

```bash
# Test AWS credentials
aws sts get-caller-identity --profile agent

# Test Bedrock access
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-5-sonnet-20241022-v2:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  --cli-binary-format raw-in-base64-out \
  /dev/stdout \
  --profile agent
```

## Available Models

### Anthropic Claude (Recommended)

```python
# Claude 3.5 Sonnet (Best overall)
LLM_MODEL=claude-3-5-sonnet
# Full ID: anthropic.claude-3-5-sonnet-20241022-v2:0

# Claude 3 Sonnet (Good balance)
LLM_MODEL=claude-3-sonnet
# Full ID: anthropic.claude-3-sonnet-20240229-v1:0

# Claude 3 Haiku (Fast & cost-effective)
LLM_MODEL=claude-3-haiku
# Full ID: anthropic.claude-3-haiku-20240307-v1:0

# Claude 3 Opus (Most capable)
LLM_MODEL=claude-3-opus
# Full ID: anthropic.claude-3-opus-20240229-v1:0
```

### Meta Llama

```python
# Llama 3.1 70B (Good for complex tasks)
LLM_MODEL=llama-3-1-70b
# Full ID: meta.llama3-1-70b-instruct-v1:0

# Llama 3.1 8B (Fast & efficient)
LLM_MODEL=llama-3-1-8b
# Full ID: meta.llama3-1-8b-instruct-v1:0
```

### Amazon Titan

```python
# Titan Text Express
LLM_MODEL=titan-text-express
# Full ID: amazon.titan-text-express-v1
```

## AWS SSO Token Management

### Automatic Token Refresh

The system automatically manages AWS SSO tokens:

1. **Checks credentials** before each Bedrock API call
2. **Refreshes tokens** if expired (calls `aws sso login`)
3. **Caches validity** for 5 minutes to reduce checks

### Manual Token Refresh

If you need to manually refresh:

```bash
aws sso login --profile agent
```

### Token Expiration

AWS SSO tokens typically expire after 8-12 hours. The system will:
1. Detect expiration automatically
2. Attempt to refresh via CLI
3. Prompt you to login if refresh fails

## Using with LaunchDarkly AI Configs

### Example AI Config for Bedrock

**Config Key**: `triage_router`

```json
{
  "model": {
    "name": "claude-3-5-sonnet",
    "parameters": {
      "temperature": 0.0,
      "maxTokens": 1000
    }
  },
  "provider": "bedrock",
  "enabled": true
}
```

### Cost Optimization Strategy

```json
// Triage Router - High accuracy needed
{
  "model": {"name": "claude-3-5-sonnet"},
  "provider": "bedrock"
}

// Policy Specialist - Complex reasoning
{
  "model": {"name": "claude-3-sonnet"},
  "provider": "bedrock"
}

// Provider Specialist - Simpler task
{
  "model": {"name": "claude-3-haiku"},
  "provider": "bedrock"
}

// Scheduler Specialist - Simpler task
{
  "model": {"name": "claude-3-haiku"},
  "provider": "bedrock"
}
```

## Pricing

AWS Bedrock pricing varies by model (as of 2024):

| Model | Input (per 1M tokens) | Output (per 1M tokens) |
|-------|----------------------|------------------------|
| Claude 3.5 Sonnet | $3.00 | $15.00 |
| Claude 3 Sonnet | $3.00 | $15.00 |
| Claude 3 Haiku | $0.25 | $1.25 |
| Llama 3.1 70B | $0.99 | $0.99 |
| Llama 3.1 8B | $0.30 | $0.30 |

Check [AWS Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) for current rates.

## Troubleshooting

### Authentication Issues

```bash
# Check credentials
aws sts get-caller-identity --profile agent

# Re-login if expired
aws sso login --profile agent

# Check profile configuration
aws configure list --profile agent
```

### Model Access Denied

```
Error: AccessDeniedException
```

**Solution**: Enable model access in AWS Console → Bedrock → Model access

### Region Mismatch

```
Error: Could not connect to the endpoint URL
```

**Solution**: Ensure `AWS_REGION` matches where Bedrock is available

### Profile Not Found

```
Error: The config profile (agent) could not be found
```

**Solution**: Run `aws configure sso` to create the profile

### Token Expired

```
Error: Token has expired
```

**Solution**: System will auto-refresh. If fails, run:
```bash
aws sso login --profile agent
```

## Best Practices

1. **Use IAM Roles**: Assign minimal permissions needed for Bedrock
2. **Enable CloudTrail**: Log all Bedrock API calls
3. **Set Budgets**: Monitor costs with AWS Budgets
4. **Use Haiku for Simple Tasks**: Save costs on routine queries
5. **Cache Responses**: Reduce duplicate API calls
6. **Monitor Token Usage**: Track via LaunchDarkly metrics

## Security

### IAM Policy Example

Minimal policy for Bedrock access:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:*::foundation-model/meta.llama*"
      ]
    }
  ]
}
```

### Environment Variables

Never commit AWS credentials:
- ❌ Don't set `AWS_ACCESS_KEY_ID` in code
- ❌ Don't commit `.env` files
- ✅ Use AWS SSO or IAM roles
- ✅ Use `.env.example` as template

## Migration from OpenAI/Anthropic

To switch from OpenAI or Anthropic:

1. **Update `.env`**:
   ```bash
   # Comment out old provider
   # OPENAI_API_KEY=...

   # Enable Bedrock
   AWS_PROFILE=agent
   AWS_REGION=us-east-1
   LLM_PROVIDER=bedrock
   LLM_MODEL=claude-3-5-sonnet
   ```

2. **Update LaunchDarkly configs** (if using):
   ```json
   {
     "provider": "bedrock",
     "model": {"name": "claude-3-5-sonnet"}
   }
   ```

3. **Test**:
   ```bash
   python examples/run_example.py
   ```

## Further Reading

- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
- [AWS SSO Configuration](https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html)
- [Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)
