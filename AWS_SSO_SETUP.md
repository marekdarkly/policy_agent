# AWS SSO Setup Guide for Bedrock Testing

This guide will walk you through setting up AWS SSO (Single Sign-On) so you can reliably access Amazon Bedrock for testing the multi-agent system.

## Overview

AWS SSO provides secure, temporary credentials that automatically refresh, making it ideal for development and testing. This setup includes:

- **Automated credential management**: No hardcoded API keys
- **Automatic token refresh**: Credentials auto-renew when needed
- **Secure authentication**: Browser-based SSO login
- **Profile-based configuration**: Easy switching between accounts

## Prerequisites

Before starting, ensure you have:

1. **AWS Account** with access to:
   - AWS SSO (or IAM Identity Center)
   - Amazon Bedrock service
2. **Permissions** to:
   - Use AWS SSO
   - Invoke Bedrock models
   - List foundation models (optional but helpful)
3. **Information** needed:
   - Your organization's SSO start URL
   - AWS account ID
   - IAM role name to assume

## Quick Start (3 Steps)

### 1. Install AWS CLI

**Check if already installed:**
```bash
aws --version
```

**If not installed:**

**macOS:**
```bash
brew install awscli
```

**Linux:**
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

**Windows:**
- Download from: https://awscli.amazonaws.com/AWSCLIV2.msi

**Verify installation:**
```bash
aws --version
# Should show: aws-cli/2.x.x or higher
```

### 2. Run the Setup Script

We've created an interactive setup script to guide you through configuration:

```bash
python setup_aws_sso.py
```

This script will:
- Check your AWS CLI installation
- Guide you through `aws configure sso`
- Login to AWS SSO
- Verify your credentials
- Check Bedrock access
- Update your `.env` file

**Alternative: Manual Setup**

If you prefer manual setup or the script doesn't work, see [Manual Setup](#manual-setup) below.

### 3. Test the Connection

After setup, test that everything works:

```bash
python test_aws_bedrock.py
```

This will verify:
- AWS credentials are valid
- Bedrock API is accessible
- You can invoke models
- The LLM wrapper works correctly

## Manual Setup

### Step 1: Configure AWS SSO Profile

Run the interactive configuration:

```bash
aws configure sso
```

You'll be prompted for:

1. **SSO session name**: Enter `agent` (or your preferred name)
2. **SSO start URL**: Your organization's URL (e.g., `https://my-org.awsapps.com/start`)
3. **SSO region**: Your SSO region (e.g., `us-east-1`)
4. **SSO registration scopes**: `sso:account:access`
5. **CLI default client region**: Your preferred region (e.g., `us-east-1`)
6. **CLI default output format**: `json`
7. **CLI profile name**: `agent`

### Step 2: Verify Configuration File

Check that `~/.aws/config` was created correctly:

```bash
cat ~/.aws/config
```

Should contain something like:

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

**If it doesn't exist or is wrong**, create/edit it manually with your values.

### Step 3: Login to AWS SSO

```bash
aws sso login --profile agent
```

This will:
1. Open your browser
2. Ask you to authorize the session
3. Cache credentials locally (~/.aws/sso/cache/)

### Step 4: Verify Credentials

```bash
aws sts get-caller-identity --profile agent
```

Should output:
```json
{
    "UserId": "AROAXXXXXXXXXX:your-email@example.com",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/YourRoleName/your-email@example.com"
}
```

### Step 5: Enable Bedrock Model Access

1. Go to [AWS Console](https://console.aws.amazon.com/)
2. Navigate to **Amazon Bedrock** → **Model access**
3. Click **Manage model access**
4. Select the models you want:
   - ✅ **Anthropic Claude 3.5 Sonnet** (recommended)
   - ✅ **Anthropic Claude 3 Haiku** (cost-effective)
   - ✅ **Anthropic Claude 3 Sonnet** (good balance)
   - ✅ **Meta Llama 3.1 70B** (alternative)
5. Click **Request model access**
6. Wait for approval (usually instant for most models)

### Step 6: Test Bedrock Access

```bash
aws bedrock list-foundation-models --profile agent --region us-east-1
```

Should return a list of available models. If you get an error:
- **AccessDenied**: Your IAM role needs Bedrock permissions
- **InvalidRegion**: Bedrock isn't available in that region
- **ResourceNotFound**: Bedrock may not be enabled

### Step 7: Update Environment File

Ensure your `.env` file has the correct settings:

```bash
# AWS Bedrock Configuration
AWS_PROFILE=agent
AWS_REGION=us-east-1
LLM_PROVIDER=bedrock
LLM_MODEL=claude-3-5-sonnet
```

## Testing Your Setup

### Automated Test Suite

Run the comprehensive test script:

```bash
python test_aws_bedrock.py
```

This will test:
1. ✅ Environment variables are set
2. ✅ Boto3 can be imported
3. ✅ AWS SSO Manager works
4. ✅ Bedrock client can be created
5. ✅ Models can be invoked
6. ✅ Full workflow integration (optional)

### Manual Tests

**Test 1: AWS Identity**
```bash
aws sts get-caller-identity --profile agent
```

**Test 2: List Bedrock Models**
```bash
aws bedrock list-foundation-models --profile agent --region us-east-1
```

**Test 3: Invoke a Model**
```bash
aws bedrock-runtime invoke-model \
  --model-id anthropic.claude-3-haiku-20240307-v1:0 \
  --body '{"anthropic_version":"bedrock-2023-05-31","max_tokens":100,"messages":[{"role":"user","content":"Hello"}]}' \
  --cli-binary-format raw-in-base64-out \
  /dev/stdout \
  --profile agent \
  --region us-east-1
```

**Test 4: Python Integration**
```python
from src.utils.bedrock_llm import BedrockConverseLLM
from langchain_core.messages import HumanMessage

llm = BedrockConverseLLM(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    profile_name="agent",
    region="us-east-1"
)

response = llm.invoke([HumanMessage(content="Hello!")])
print(response.content)
```

## Troubleshooting

### Error: "Token has expired"

**Solution**: Re-login to AWS SSO
```bash
aws sso login --profile agent
```

SSO tokens expire after 8-12 hours. The system will try to auto-refresh, but you can manually refresh if needed.

### Error: "Profile 'agent' not found"

**Solution**: Run AWS SSO configuration
```bash
aws configure sso
```

Or manually edit `~/.aws/config` (see Manual Setup above).

### Error: "AccessDeniedException"

**Possible causes:**
1. Your IAM role lacks Bedrock permissions
2. Bedrock is not enabled in your account
3. You haven't requested model access

**Solution**: Update IAM policy with:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

### Error: "ValidationException: The provided model identifier is invalid"

**Solution**:
1. Check the model ID is correct
2. Ensure model access is enabled in Bedrock console
3. Verify the model is available in your region

### Error: "Could not connect to the endpoint URL"

**Solution**:
- Check that Bedrock is available in your region
- Common Bedrock regions: `us-east-1`, `us-west-2`, `eu-west-1`
- Update `AWS_REGION` in `.env` file

### AWS CLI not opening browser

**Solution**:
1. Check your default browser settings
2. Try specifying browser manually:
   ```bash
   AWS_DEFAULT_BROWSER=/usr/bin/firefox aws sso login --profile agent
   ```
3. Use the manual login URL printed in the terminal

### Credentials work but Bedrock fails

**Checklist**:
- [ ] Is Bedrock enabled in your AWS account?
- [ ] Have you requested model access in the console?
- [ ] Does your IAM role have Bedrock permissions?
- [ ] Is Bedrock available in your region?
- [ ] Are you using the correct model ID?

## Daily Usage

### Starting a New Session

Each time you start working (after 8-12 hours):

```bash
# Login to refresh credentials
aws sso login --profile agent

# Run your application
python examples/run_example.py
```

### Checking Token Status

```bash
# Check if credentials are valid
aws sts get-caller-identity --profile agent
```

If this fails with "Token has expired", run `aws sso login --profile agent` again.

### Automatic Refresh

The `AWSSSOManager` class automatically handles token refresh:
- Checks credentials every 5 minutes
- Attempts auto-refresh if expired
- Falls back to manual login if auto-refresh fails

You usually don't need to manually refresh unless the system prompts you.

## IAM Permissions Reference

### Minimal Bedrock Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockInvoke",
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ],
      "Resource": [
        "arn:aws:bedrock:*::foundation-model/anthropic.claude-*",
        "arn:aws:bedrock:*::foundation-model/meta.llama*"
      ]
    },
    {
      "Sid": "BedrockList",
      "Effect": "Allow",
      "Action": [
        "bedrock:ListFoundationModels"
      ],
      "Resource": "*"
    }
  ]
}
```

### Full Development Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "BedrockFullAccess",
      "Effect": "Allow",
      "Action": [
        "bedrock:*"
      ],
      "Resource": "*"
    },
    {
      "Sid": "CloudWatchLogs",
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

## Best Practices

### Security
- ✅ Never commit `.env` file to git
- ✅ Use AWS SSO instead of long-term access keys
- ✅ Apply least-privilege IAM policies
- ✅ Rotate credentials regularly (handled by SSO)
- ✅ Enable CloudTrail for audit logging

### Cost Management
- 💰 Use Claude 3 Haiku for development/testing (cheaper)
- 💰 Use Claude 3.5 Sonnet for production (better quality)
- 💰 Set up AWS Budgets to monitor costs
- 💰 Use LaunchDarkly AI Configs to control which model each agent uses

### Performance
- ⚡ Cache SSO credentials (handled automatically)
- ⚡ Reuse Bedrock clients (handled by SSO manager)
- ⚡ Choose appropriate regions (lower latency)
- ⚡ Use connection pooling for high volume

## Advanced Configuration

### Multiple Profiles

You can configure multiple AWS profiles for different environments:

```ini
# ~/.aws/config

[profile agent-dev]
sso_session = dev
sso_account_id = 111111111111
sso_role_name = DeveloperRole
region = us-east-1

[profile agent-prod]
sso_session = prod
sso_account_id = 222222222222
sso_role_name = ProductionRole
region = us-west-2

[sso-session dev]
sso_start_url = https://dev.awsapps.com/start
sso_region = us-east-1

[sso-session prod]
sso_start_url = https://prod.awsapps.com/start
sso_region = us-west-2
```

Then switch profiles in `.env`:
```bash
AWS_PROFILE=agent-dev  # or agent-prod
```

### Cross-Region Setup

To use different regions:

```bash
# .env
AWS_PROFILE=agent
AWS_REGION=us-west-2  # Change region here
```

Bedrock is available in:
- `us-east-1` (US East - N. Virginia)
- `us-west-2` (US West - Oregon)
- `ap-southeast-1` (Singapore)
- `ap-northeast-1` (Tokyo)
- `eu-west-1` (Ireland)
- `eu-central-1` (Frankfurt)

### Environment-Specific Models

```bash
# Development
LLM_MODEL=claude-3-haiku

# Staging
LLM_MODEL=claude-3-sonnet

# Production
LLM_MODEL=claude-3-5-sonnet
```

## Resources

### Official Documentation
- [AWS SSO Configuration](https://docs.aws.amazon.com/cli/latest/userguide/sso-configure-profile-token.html)
- [Amazon Bedrock User Guide](https://docs.aws.amazon.com/bedrock/)
- [Bedrock Converse API](https://docs.aws.amazon.com/bedrock/latest/userguide/conversation-inference.html)
- [Bedrock Model IDs](https://docs.aws.amazon.com/bedrock/latest/userguide/model-ids.html)

### Internal Documentation
- [AWS_BEDROCK.md](AWS_BEDROCK.md) - Bedrock integration guide
- [LAUNCHDARKLY.md](LAUNCHDARKLY.md) - LaunchDarkly AI Config setup
- [SDD.md](SDD.md) - System design document

### Helpful Commands

```bash
# Show current AWS profile
echo $AWS_PROFILE

# List all configured profiles
aws configure list-profiles

# Check SSO login status
aws sts get-caller-identity --profile agent

# Re-login to SSO
aws sso login --profile agent

# Logout from SSO
aws sso logout --profile agent

# Clear SSO cache (if having issues)
rm -rf ~/.aws/sso/cache/

# Test Bedrock access
python test_aws_bedrock.py

# Run the multi-agent system
python examples/run_example.py
```

## Getting Help

If you encounter issues:

1. **Run the test script**: `python test_aws_bedrock.py`
2. **Check the logs**: Look for error messages
3. **Verify IAM permissions**: Check your role has Bedrock access
4. **Consult AWS documentation**: See Resources above
5. **Ask for help**: Include error messages and test results

## Next Steps

After successful setup:

1. ✅ Run the test suite: `python test_aws_bedrock.py`
2. ✅ Try the examples: `python examples/run_example.py`
3. ✅ Read [AWS_BEDROCK.md](AWS_BEDROCK.md) for advanced features
4. ✅ Set up [LaunchDarkly AI Configs](LAUNCHDARKLY.md) for model management
5. ✅ Start building your own agents!

---

**Remember**: SSO tokens expire after 8-12 hours. Just run `aws sso login --profile agent` to refresh!
