#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Bootstrap Lambda infrastructure using AWS CLI (no Terraform needed)
#
# Creates: IAM role, Lambda functions, EventBridge hourly schedules
# Usage:   ./lambda/synthetic_traffic/bootstrap.sh
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ZIP_PATH="$SCRIPT_DIR/build/deployment.zip"

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-togglehealth-synthetic}"
ENVIRONMENT="${ENVIRONMENT:-prod}"
PREFIX="${PROJECT_NAME}-${ENVIRONMENT}"

# Source .env
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a; source "$PROJECT_ROOT/.env"; set +a
fi

LD_SDK_KEY="${LAUNCHDARKLY_SDK_KEY:-${LD_SERVICE_TOKEN:-}}"
if [ -z "$LD_SDK_KEY" ]; then
    echo "ERROR: Set LAUNCHDARKLY_SDK_KEY or LD_SERVICE_TOKEN"; exit 1
fi

AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text --region "$AWS_REGION")
echo "AWS Account: $AWS_ACCOUNT_ID, Region: $AWS_REGION"

ROLE_NAME="${PREFIX}-lambda-role"
LANGGRAPH_FN="${PREFIX}-synthetic-traffic"
AGENT_GRAPH_FN="${PREFIX}-agent-graph"

# Build zip if it doesn't exist
if [ ! -f "$ZIP_PATH" ]; then
    echo "==> Building deployment package first..."
    "$SCRIPT_DIR/deploy.sh" build
fi

# ---------------------------------------------------------------------------
# 1. IAM Role
# ---------------------------------------------------------------------------
echo "==> Creating IAM role..."

ASSUME_ROLE_POLICY='{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Service": "lambda.amazonaws.com"},
    "Action": "sts:AssumeRole"
  }]
}'

ROLE_ARN=$(aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document "$ASSUME_ROLE_POLICY" \
    --query 'Role.Arn' --output text 2>/dev/null || \
    aws iam get-role --role-name "$ROLE_NAME" --query 'Role.Arn' --output text)

echo "    Role: $ROLE_ARN"

POLICY_DOC=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["logs:CreateLogGroup","logs:CreateLogStream","logs:PutLogEvents"],
      "Resource": "arn:aws:logs:${AWS_REGION}:${AWS_ACCOUNT_ID}:*"
    },
    {
      "Effect": "Allow",
      "Action": ["ssm:GetParameter","ssm:GetParameters"],
      "Resource": "arn:aws:ssm:${AWS_REGION}:${AWS_ACCOUNT_ID}:parameter/${PROJECT_NAME}/${ENVIRONMENT}/*"
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:InvokeModel","bedrock:InvokeModelWithResponseStream"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": ["bedrock:Retrieve","bedrock:RetrieveAndGenerate"],
      "Resource": "arn:aws:bedrock:${AWS_REGION}:${AWS_ACCOUNT_ID}:knowledge-base/*"
    }
  ]
}
EOF
)

aws iam put-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-name "${PREFIX}-lambda-policy" \
    --policy-document "$POLICY_DOC"

echo "    Policy attached"

# Wait for role to propagate
echo "    Waiting for IAM role propagation..."
sleep 10

# ---------------------------------------------------------------------------
# 2. SSM Parameter (LD SDK key)
# ---------------------------------------------------------------------------
echo "==> Storing LaunchDarkly SDK key in SSM..."
aws ssm put-parameter \
    --name "/${PROJECT_NAME}/${ENVIRONMENT}/launchdarkly/sdk-key" \
    --type SecureString \
    --value "$LD_SDK_KEY" \
    --overwrite \
    --region "$AWS_REGION" \
    --no-cli-pager > /dev/null

echo "    SSM parameter stored"

# ---------------------------------------------------------------------------
# 3. Lambda Functions
# ---------------------------------------------------------------------------
ENV_VARS=$(cat <<EOF
{
  "Variables": {
    "PARAMETER_PREFIX": "/${PROJECT_NAME}/${ENVIRONMENT}",
    "LAUNCHDARKLY_ENABLED": "true",
    "LLM_PROVIDER": "bedrock",
    "LLM_MODEL": "claude-3-5-sonnet",
    "BEDROCK_POLICY_KB_ID": "${BEDROCK_POLICY_KB_ID:-}",
    "BEDROCK_PROVIDER_KB_ID": "${BEDROCK_PROVIDER_KB_ID:-}"
  }
}
EOF
)

create_or_update_lambda() {
    local fn_name="$1"
    local handler="$2"

    echo "==> Deploying Lambda: $fn_name (handler: $handler)..."

    # Try to create; if exists, update
    if aws lambda get-function --function-name "$fn_name" --region "$AWS_REGION" > /dev/null 2>&1; then
        echo "    Function exists, updating code..."
        aws lambda update-function-code \
            --function-name "$fn_name" \
            --zip-file "fileb://$ZIP_PATH" \
            --region "$AWS_REGION" \
            --no-cli-pager > /dev/null

        # Wait for update to complete before changing config
        aws lambda wait function-updated --function-name "$fn_name" --region "$AWS_REGION"

        aws lambda update-function-configuration \
            --function-name "$fn_name" \
            --handler "$handler" \
            --environment "$ENV_VARS" \
            --timeout 900 \
            --memory-size 1024 \
            --region "$AWS_REGION" \
            --no-cli-pager > /dev/null
    else
        echo "    Creating function..."
        aws lambda create-function \
            --function-name "$fn_name" \
            --runtime python3.11 \
            --handler "$handler" \
            --role "$ROLE_ARN" \
            --zip-file "fileb://$ZIP_PATH" \
            --timeout 900 \
            --memory-size 1024 \
            --environment "$ENV_VARS" \
            --region "$AWS_REGION" \
            --no-cli-pager > /dev/null
    fi

    echo "    Done: $fn_name"
}

create_or_update_lambda "$LANGGRAPH_FN" "handler.lambda_handler"
create_or_update_lambda "$AGENT_GRAPH_FN" "handler_agent_graph.lambda_handler"

# ---------------------------------------------------------------------------
# 4. EventBridge Hourly Schedules
# ---------------------------------------------------------------------------
setup_schedule() {
    local fn_name="$1"
    local rule_name="$2"
    local desc="$3"

    echo "==> Setting up hourly schedule: $rule_name -> $fn_name"

    aws events put-rule \
        --name "$rule_name" \
        --schedule-expression "rate(1 hour)" \
        --description "$desc" \
        --region "$AWS_REGION" \
        --no-cli-pager > /dev/null

    local FN_ARN
    FN_ARN=$(aws lambda get-function \
        --function-name "$fn_name" \
        --query 'Configuration.FunctionArn' \
        --output text \
        --region "$AWS_REGION")

    aws events put-targets \
        --rule "$rule_name" \
        --targets "Id=${fn_name}-target,Arn=${FN_ARN}" \
        --region "$AWS_REGION" \
        --no-cli-pager > /dev/null

    aws lambda add-permission \
        --function-name "$fn_name" \
        --statement-id "AllowEventBridge-${rule_name}" \
        --action lambda:InvokeFunction \
        --principal events.amazonaws.com \
        --source-arn "arn:aws:events:${AWS_REGION}:${AWS_ACCOUNT_ID}:rule/${rule_name}" \
        --region "$AWS_REGION" \
        --no-cli-pager > /dev/null 2>&1 || true

    echo "    Scheduled"
}

setup_schedule "$LANGGRAPH_FN" "${PREFIX}-hourly-synthetic" "Hourly LangGraph synthetic traffic (10 iterations)"
setup_schedule "$AGENT_GRAPH_FN" "${PREFIX}-hourly-agent-graph" "Hourly Agent Graph synthetic traffic (10 iterations)"

# ---------------------------------------------------------------------------
echo ""
echo "============================================"
echo "  Deployment complete!"
echo "============================================"
echo "  LangGraph Lambda:   $LANGGRAPH_FN"
echo "  Agent Graph Lambda: $AGENT_GRAPH_FN"
echo "  Schedule:           rate(1 hour)"
echo "  Iterations/run:     10"
echo ""
echo "  Test manually:"
echo "    ./lambda/synthetic_traffic/deploy.sh invoke langgraph"
echo "    ./lambda/synthetic_traffic/deploy.sh invoke agent-graph"
echo "============================================"
