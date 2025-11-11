#!/bin/bash

# ToggleHealth Bedrock KB - S3 Bucket Setup Script
# This script creates S3 buckets and uploads markdown files

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}ToggleHealth Bedrock KB Setup${NC}"
echo -e "${BLUE}Step 1: S3 Buckets and Upload${NC}"
echo -e "${BLUE}================================${NC}"
echo

# Configuration
read -p "Enter AWS Region (default: us-west-2): " AWS_REGION
AWS_REGION=${AWS_REGION:-us-west-2}

read -p "Enter Policy Bucket Name (must be globally unique): " POLICY_BUCKET
if [ -z "$POLICY_BUCKET" ]; then
    POLICY_BUCKET="togglehealth-policy-kb-$(date +%s)"
    echo "Using generated name: $POLICY_BUCKET"
fi

read -p "Enter Provider Bucket Name (must be globally unique): " PROVIDER_BUCKET
if [ -z "$PROVIDER_BUCKET" ]; then
    PROVIDER_BUCKET="togglehealth-provider-kb-$(date +%s)"
    echo "Using generated name: $PROVIDER_BUCKET"
fi

echo
echo -e "${BLUE}Configuration:${NC}"
echo "AWS Region: $AWS_REGION"
echo "Policy Bucket: $POLICY_BUCKET"
echo "Provider Bucket: $PROVIDER_BUCKET"
echo

read -p "Proceed with these settings? (y/n): " CONFIRM
if [ "$CONFIRM" != "y" ]; then
    echo "Aborted."
    exit 1
fi

# Create policy bucket
echo
echo -e "${GREEN}Creating policy bucket...${NC}"
if aws s3 mb s3://$POLICY_BUCKET --region $AWS_REGION; then
    echo -e "${GREEN}✓ Policy bucket created${NC}"
else
    echo -e "${RED}✗ Failed to create policy bucket${NC}"
    exit 1
fi

# Create provider bucket
echo -e "${GREEN}Creating provider bucket...${NC}"
if aws s3 mb s3://$PROVIDER_BUCKET --region $AWS_REGION; then
    echo -e "${GREEN}✓ Provider bucket created${NC}"
else
    echo -e "${RED}✗ Failed to create provider bucket${NC}"
    exit 1
fi

# Enable versioning
echo
echo -e "${GREEN}Enabling versioning...${NC}"
aws s3api put-bucket-versioning \
    --bucket $POLICY_BUCKET \
    --versioning-configuration Status=Enabled \
    --region $AWS_REGION
echo -e "${GREEN}✓ Versioning enabled on policy bucket${NC}"

aws s3api put-bucket-versioning \
    --bucket $PROVIDER_BUCKET \
    --versioning-configuration Status=Enabled \
    --region $AWS_REGION
echo -e "${GREEN}✓ Versioning enabled on provider bucket${NC}"

# Upload files
echo
echo -e "${GREEN}Uploading markdown files...${NC}"

# Check if markdown directory exists
if [ ! -d "data/markdown" ]; then
    echo -e "${RED}✗ data/markdown directory not found${NC}"
    echo "Please run this script from the policy_agent directory"
    exit 1
fi

# Upload policy files
echo "Uploading policy files..."
aws s3 sync data/markdown/ s3://$POLICY_BUCKET/policy/ \
    --region $AWS_REGION \
    --exclude "*" \
    --include "policy_overview.md" \
    --include "plan_*.md" \
    --include "special_programs.md" \
    --include "pharmacy_benefits.md" \
    --include "claims_and_preauthorization.md"

echo -e "${GREEN}✓ Policy files uploaded${NC}"

# Upload provider files
echo "Uploading provider files..."
aws s3 sync data/markdown/ s3://$PROVIDER_BUCKET/provider/ \
    --region $AWS_REGION \
    --exclude "*" \
    --include "provider_directory_overview.md" \
    --include "providers_detailed.md"

echo -e "${GREEN}✓ Provider files uploaded${NC}"

# Verify uploads
echo
echo -e "${BLUE}Verifying uploads...${NC}"
echo
echo "Policy bucket contents:"
aws s3 ls s3://$POLICY_BUCKET/policy/ --recursive --human-readable

echo
echo "Provider bucket contents:"
aws s3 ls s3://$PROVIDER_BUCKET/provider/ --recursive --human-readable

# Save configuration
echo
echo -e "${GREEN}Saving configuration...${NC}"
cat > bedrock_setup/config.env << EOF
# ToggleHealth Bedrock KB Configuration
# Generated: $(date)

export AWS_REGION="$AWS_REGION"
export POLICY_BUCKET="$POLICY_BUCKET"
export PROVIDER_BUCKET="$PROVIDER_BUCKET"
export POLICY_S3_URI="s3://$POLICY_BUCKET/policy/"
export PROVIDER_S3_URI="s3://$PROVIDER_BUCKET/provider/"
EOF

echo -e "${GREEN}✓ Configuration saved to bedrock_setup/config.env${NC}"

# Print summary
echo
echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}================================${NC}"
echo
echo -e "${GREEN}✓ S3 buckets created and configured${NC}"
echo -e "${GREEN}✓ Markdown files uploaded${NC}"
echo -e "${GREEN}✓ Configuration saved${NC}"
echo
echo "Next steps:"
echo "1. Run ./setup_iam_role.sh to create IAM role"
echo "2. Run ./setup_opensearch.sh to create vector store"
echo "3. Create Knowledge Bases via AWS Console"
echo "4. Sync data sources"
echo
echo "S3 URIs for Knowledge Base data sources:"
echo "  Policy KB: s3://$POLICY_BUCKET/policy/"
echo "  Provider KB: s3://$PROVIDER_BUCKET/provider/"
echo

# Export for current session
export AWS_REGION="$AWS_REGION"
export POLICY_BUCKET="$POLICY_BUCKET"
export PROVIDER_BUCKET="$PROVIDER_BUCKET"

echo -e "${GREEN}Setup complete!${NC}"
