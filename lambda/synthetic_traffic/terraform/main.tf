terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "togglehealth-synthetic"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "ld_sdk_key" {
  description = "LaunchDarkly SDK key"
  type        = string
  sensitive   = true
}

variable "schedule_expression" {
  description = "EventBridge schedule expression"
  type        = string
  default     = "rate(1 hour)"
}

variable "bedrock_policy_kb_id" {
  description = "Bedrock Knowledge Base ID for policy docs (optional)"
  type        = string
  default     = ""
}

variable "bedrock_provider_kb_id" {
  description = "Bedrock Knowledge Base ID for provider docs (optional)"
  type        = string
  default     = ""
}

# ---------------------------------------------------------------------------
# Locals
# ---------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }

  common_lambda_env = {
    PARAMETER_PREFIX       = "/${var.project_name}/${var.environment}"
    LAUNCHDARKLY_ENABLED   = "true"
    LLM_PROVIDER           = "bedrock"
    LLM_MODEL              = "claude-3-5-sonnet"
    BEDROCK_POLICY_KB_ID   = var.bedrock_policy_kb_id
    BEDROCK_PROVIDER_KB_ID = var.bedrock_provider_kb_id
  }
}

# ---------------------------------------------------------------------------
# SSM Parameter Store (secrets)
# ---------------------------------------------------------------------------

resource "aws_ssm_parameter" "ld_sdk_key" {
  name  = "/${var.project_name}/${var.environment}/launchdarkly/sdk-key"
  type  = "SecureString"
  value = var.ld_sdk_key

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# IAM
# ---------------------------------------------------------------------------

resource "aws_iam_role" "lambda_execution_role" {
  name = "${local.name_prefix}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${local.name_prefix}-lambda-policy"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = [
          "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/${var.project_name}/${var.environment}/*"
        ]
      },
      {
        Effect   = "Allow"
        Action   = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve",
          "bedrock:RetrieveAndGenerate"
        ]
        Resource = "arn:aws:bedrock:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:knowledge-base/*"
      }
    ]
  })
}

# ---------------------------------------------------------------------------
# CloudWatch Log Groups
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_log_group" "synthetic_traffic_logs" {
  name              = "/aws/lambda/${local.name_prefix}-synthetic-traffic"
  retention_in_days = 14

  tags = local.common_tags
}

resource "aws_cloudwatch_log_group" "agent_graph_logs" {
  name              = "/aws/lambda/${local.name_prefix}-agent-graph"
  retention_in_days = 14

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# Lambda Functions (zip-based, code managed by deploy.sh)
# ---------------------------------------------------------------------------

resource "aws_lambda_function" "synthetic_traffic" {
  function_name = "${local.name_prefix}-synthetic-traffic"
  role          = aws_iam_role.lambda_execution_role.arn
  runtime       = "python3.11"
  handler       = "handler.lambda_handler"
  timeout       = 900
  memory_size   = 1024

  filename         = "${path.module}/../build/deployment.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/deployment.zip")

  environment {
    variables = local.common_lambda_env
  }

  depends_on = [aws_cloudwatch_log_group.synthetic_traffic_logs]

  tags = local.common_tags
}

resource "aws_lambda_function" "agent_graph" {
  function_name = "${local.name_prefix}-agent-graph"
  role          = aws_iam_role.lambda_execution_role.arn
  runtime       = "python3.11"
  handler       = "handler_agent_graph.lambda_handler"
  timeout       = 900
  memory_size   = 1024

  filename         = "${path.module}/../build/deployment.zip"
  source_code_hash = filebase64sha256("${path.module}/../build/deployment.zip")

  environment {
    variables = local.common_lambda_env
  }

  depends_on = [aws_cloudwatch_log_group.agent_graph_logs]

  tags = local.common_tags
}

# ---------------------------------------------------------------------------
# EventBridge Schedules (hourly, one per handler)
# ---------------------------------------------------------------------------

resource "aws_cloudwatch_event_rule" "hourly_synthetic_traffic" {
  name                = "${local.name_prefix}-hourly-synthetic"
  description         = "Trigger LangGraph synthetic traffic every hour"
  schedule_expression = var.schedule_expression

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "synthetic_traffic_target" {
  rule      = aws_cloudwatch_event_rule.hourly_synthetic_traffic.name
  target_id = "LangGraphTarget"
  arn       = aws_lambda_function.synthetic_traffic.arn
}

resource "aws_lambda_permission" "allow_eventbridge" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.synthetic_traffic.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_synthetic_traffic.arn
}

resource "aws_cloudwatch_event_rule" "hourly_agent_graph" {
  name                = "${local.name_prefix}-hourly-agent-graph"
  description         = "Trigger Agent Graph synthetic traffic every hour"
  schedule_expression = var.schedule_expression

  tags = local.common_tags
}

resource "aws_cloudwatch_event_target" "agent_graph_target" {
  rule      = aws_cloudwatch_event_rule.hourly_agent_graph.name
  target_id = "AgentGraphTarget"
  arn       = aws_lambda_function.agent_graph.arn
}

resource "aws_lambda_permission" "allow_eventbridge_agent_graph" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent_graph.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.hourly_agent_graph.arn
}

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

output "langgraph_function_name" {
  description = "Name of the LangGraph synthetic traffic Lambda"
  value       = aws_lambda_function.synthetic_traffic.function_name
}

output "agent_graph_function_name" {
  description = "Name of the Agent Graph synthetic traffic Lambda"
  value       = aws_lambda_function.agent_graph.function_name
}

output "langgraph_log_group" {
  description = "CloudWatch log group for LangGraph Lambda"
  value       = aws_cloudwatch_log_group.synthetic_traffic_logs.name
}

output "agent_graph_log_group" {
  description = "CloudWatch log group for Agent Graph Lambda"
  value       = aws_cloudwatch_log_group.agent_graph_logs.name
}
