#!/usr/bin/env bash
set -euo pipefail

# ---------------------------------------------------------------------------
# Synthetic Traffic Lambda — Build & Deploy (zip-based)
#
# Usage:
#   ./lambda/synthetic_traffic/deploy.sh              # build + infra + update
#   ./lambda/synthetic_traffic/deploy.sh build         # build zip package only
#   ./lambda/synthetic_traffic/deploy.sh infra         # terraform apply only
#   ./lambda/synthetic_traffic/deploy.sh update        # build + push code to Lambdas
#   ./lambda/synthetic_traffic/deploy.sh invoke [langgraph|agent-graph]
#   ./lambda/synthetic_traffic/deploy.sh logs   [langgraph|agent-graph]
# ---------------------------------------------------------------------------

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
TF_DIR="$SCRIPT_DIR/terraform"
BUILD_DIR="$SCRIPT_DIR/build"
ZIP_PATH="$BUILD_DIR/deployment.zip"

AWS_REGION="${AWS_REGION:-us-east-1}"
PROJECT_NAME="${PROJECT_NAME:-togglehealth-synthetic}"
ENVIRONMENT="${ENVIRONMENT:-prod}"

# Source .env from project root if it exists
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

LD_SDK_KEY="${LAUNCHDARKLY_SDK_KEY:-${LD_SERVICE_TOKEN:-}}"
if [ -z "$LD_SDK_KEY" ]; then
    echo "ERROR: Set LAUNCHDARKLY_SDK_KEY or LD_SERVICE_TOKEN"
    exit 1
fi

LANGGRAPH_FUNCTION="${PROJECT_NAME}-${ENVIRONMENT}-synthetic-traffic"
AGENT_GRAPH_FUNCTION="${PROJECT_NAME}-${ENVIRONMENT}-agent-graph"

# ---------------------------------------------------------------------------
build() {
    echo "==> Building zip deployment package..."

    rm -rf "$BUILD_DIR"
    mkdir -p "$BUILD_DIR/package"

    local PKG="$BUILD_DIR/package"

    # Install dependencies for Lambda (Linux x86_64)
    echo "    Installing dependencies..."
    pip install --target "$PKG" \
        --platform manylinux2014_x86_64 \
        --implementation cp \
        --python-version 3.11 \
        --only-binary :all: \
        --upgrade --quiet \
        -r "$SCRIPT_DIR/requirements-lambda.txt" 2>&1 | tail -5

    # Copy application code
    echo "    Copying application code..."
    cp "$SCRIPT_DIR/handler.py" "$PKG/"
    cp "$SCRIPT_DIR/handler_agent_graph.py" "$PKG/"
    cp "$SCRIPT_DIR/common.py" "$PKG/"
    cp -r "$PROJECT_ROOT/src" "$PKG/src"

    # Remove large transitive dependencies not needed at runtime
    echo "    Trimming package..."
    local REMOVE_DIRS=(
        botocore boto3 s3transfer
        numpy numpy.libs zstandard
        hf_xet tokenizers huggingface_hub
        pygments
    )
    for dir in "${REMOVE_DIRS[@]}"; do
        rm -rf "$PKG/$dir" 2>/dev/null || true
    done
    find "$PKG" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PKG" -type d -name "tests" -exec rm -rf {} + 2>/dev/null || true
    find "$PKG" -name "*.pyc" -delete 2>/dev/null || true

    # Create zip
    echo "    Creating zip..."
    cd "$PKG"
    zip -r -q "$ZIP_PATH" .
    cd "$PROJECT_ROOT"

    local SIZE_MB
    SIZE_MB=$(du -m "$ZIP_PATH" | cut -f1)
    echo "==> Build complete: $ZIP_PATH (${SIZE_MB}MB)"

    if [ "$SIZE_MB" -gt 50 ]; then
        echo "WARNING: Zip exceeds 50MB — Lambda direct upload limit."
        echo "         Will use S3 for deployment."
    fi
}

infra() {
    echo "==> Running Terraform..."
    cd "$TF_DIR"

    terraform init -input=false

    terraform apply \
        -var "aws_region=$AWS_REGION" \
        -var "project_name=$PROJECT_NAME" \
        -var "environment=$ENVIRONMENT" \
        -var "ld_sdk_key=$LD_SDK_KEY" \
        -var "bedrock_policy_kb_id=${BEDROCK_POLICY_KB_ID:-}" \
        -var "bedrock_provider_kb_id=${BEDROCK_PROVIDER_KB_ID:-}" \
        -auto-approve

    cd "$PROJECT_ROOT"
    echo "==> Terraform apply complete"
}

update_lambda() {
    echo "==> Updating both Lambdas with new code..."

    local SIZE_MB
    SIZE_MB=$(du -m "$ZIP_PATH" | cut -f1)

    if [ "$SIZE_MB" -gt 50 ]; then
        # Use S3 for large packages
        local BUCKET="${PROJECT_NAME}-${ENVIRONMENT}-deployments"
        local S3_KEY="lambda/deployment-$(date +%Y%m%d-%H%M%S).zip"

        echo "    Package too large for direct upload, using S3..."
        aws s3 mb "s3://$BUCKET" --region "$AWS_REGION" 2>/dev/null || true
        aws s3 cp "$ZIP_PATH" "s3://$BUCKET/$S3_KEY" --region "$AWS_REGION"

        aws lambda update-function-code \
            --function-name "$LANGGRAPH_FUNCTION" \
            --s3-bucket "$BUCKET" \
            --s3-key "$S3_KEY" \
            --region "$AWS_REGION" \
            --no-cli-pager

        aws lambda update-function-code \
            --function-name "$AGENT_GRAPH_FUNCTION" \
            --s3-bucket "$BUCKET" \
            --s3-key "$S3_KEY" \
            --region "$AWS_REGION" \
            --no-cli-pager
    else
        # Direct upload
        aws lambda update-function-code \
            --function-name "$LANGGRAPH_FUNCTION" \
            --zip-file "fileb://$ZIP_PATH" \
            --region "$AWS_REGION" \
            --no-cli-pager

        aws lambda update-function-code \
            --function-name "$AGENT_GRAPH_FUNCTION" \
            --zip-file "fileb://$ZIP_PATH" \
            --region "$AWS_REGION" \
            --no-cli-pager
    fi

    echo "==> Both Lambdas updated"
}

invoke() {
    local target="${2:-langgraph}"
    local fn_name
    if [ "$target" = "agent-graph" ]; then
        fn_name="$AGENT_GRAPH_FUNCTION"
    else
        fn_name="$LANGGRAPH_FUNCTION"
    fi

    echo "==> Invoking $fn_name (timeout 15m)..."
    aws lambda invoke \
        --function-name "$fn_name" \
        --region "$AWS_REGION" \
        --log-type Tail \
        --cli-read-timeout 900 \
        --no-cli-pager \
        /tmp/synthetic-traffic-response.json

    echo "==> Response:"
    python3 -m json.tool /tmp/synthetic-traffic-response.json
}

logs() {
    local target="${2:-langgraph}"
    local fn_name
    if [ "$target" = "agent-graph" ]; then
        fn_name="$AGENT_GRAPH_FUNCTION"
    else
        fn_name="$LANGGRAPH_FUNCTION"
    fi

    echo "==> Tailing logs for $fn_name..."
    aws logs tail \
        "/aws/lambda/$fn_name" \
        --follow \
        --region "$AWS_REGION" \
        --format short
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
case "${1:-all}" in
    build)
        build
        ;;
    infra)
        infra
        ;;
    update)
        build
        update_lambda
        ;;
    invoke)
        invoke "$@"
        ;;
    logs)
        logs "$@"
        ;;
    all)
        build
        infra
        update_lambda
        ;;
    *)
        echo "Usage: $0 {build|infra|update|invoke|logs|all}"
        exit 1
        ;;
esac
