.PHONY: help install setup run test verify clean aws-login aws-check format lint

# Configuration
PYTHON := python3
VENV := venv
VENV_BIN := $(VENV)/bin
PYTHON_VENV := $(VENV_BIN)/python
PIP := $(VENV_BIN)/pip
AWS_PROFILE := marek
AWS_REGION := us-east-1

# Colors for output
COLOR_RESET := \033[0m
COLOR_BOLD := \033[1m
COLOR_GREEN := \033[32m
COLOR_YELLOW := \033[33m
COLOR_BLUE := \033[34m
COLOR_CYAN := \033[36m

##@ General

help: ## Display this help message
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)Medical Insurance Support Multi-Agent System$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)================================================$(COLOR_RESET)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(COLOR_BLUE)%-15s$(COLOR_RESET) %s\n", $$1, $$2 } /^##@/ { printf "\n$(COLOR_BOLD)%s$(COLOR_RESET)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Setup & Installation

install: ## Install dependencies in virtual environment
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)📦 Installing dependencies...$(COLOR_RESET)"
	@if [ ! -d "$(VENV)" ]; then \
		echo "$(COLOR_YELLOW)Creating virtual environment...$(COLOR_RESET)"; \
		$(PYTHON) -m venv $(VENV); \
	fi
	@echo "$(COLOR_YELLOW)Installing packages...$(COLOR_RESET)"
	@$(PIP) install --upgrade pip > /dev/null
	@$(PIP) install -r requirements.txt > /dev/null
	@echo "$(COLOR_GREEN)✅ Dependencies installed!$(COLOR_RESET)"

setup: install aws-check ## Complete setup: install deps and check AWS
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔍 Verifying LaunchDarkly configuration...$(COLOR_RESET)"
	@$(PYTHON_VENV) verify_ld_configs.py
	@echo ""
	@echo "$(COLOR_GREEN)$(COLOR_BOLD)✅ Setup complete!$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)Run 'make run' to start the chatbot$(COLOR_RESET)"

##@ AWS Authentication

aws-check: ## Check AWS credentials and refresh if needed
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔐 Checking AWS credentials...$(COLOR_RESET)"
	@if ! aws sts get-caller-identity --profile $(AWS_PROFILE) > /dev/null 2>&1; then \
		echo "$(COLOR_YELLOW)⚠️  AWS credentials expired or invalid$(COLOR_RESET)"; \
		echo "$(COLOR_CYAN)🔄 Refreshing AWS SSO credentials...$(COLOR_RESET)"; \
		$(MAKE) aws-login; \
	else \
		echo "$(COLOR_GREEN)✅ AWS credentials valid for profile: $(AWS_PROFILE)$(COLOR_RESET)"; \
		aws sts get-caller-identity --profile $(AWS_PROFILE) --query 'Account' --output text | \
			xargs -I {} echo "$(COLOR_CYAN)   Account: {}$(COLOR_RESET)"; \
	fi

aws-login: ## Login to AWS SSO (interactive)
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔐 Logging in to AWS SSO...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)This will open your browser for authentication$(COLOR_RESET)"
	@aws sso login --profile $(AWS_PROFILE)
	@echo "$(COLOR_GREEN)✅ AWS SSO login successful!$(COLOR_RESET)"

aws-info: ## Show current AWS identity
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)AWS Identity Information$(COLOR_RESET)"
	@aws sts get-caller-identity --profile $(AWS_PROFILE)

##@ Running the Application

run: aws-check ## Run the interactive chatbot (auto-checks AWS)
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🚀 Starting Medical Insurance Support Chatbot...$(COLOR_RESET)"
	@echo ""
	@$(PYTHON_VENV) interactive_chatbot.py

run-example: aws-check ## Run example queries
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)📋 Running example queries...$(COLOR_RESET)"
	@$(PYTHON_VENV) examples/run_example.py

run-interactive-example: aws-check ## Run examples in interactive mode
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)💬 Running interactive examples...$(COLOR_RESET)"
	@$(PYTHON_VENV) examples/run_example.py interactive

run-test: aws-check ## Run a quick test query
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🧪 Running quick test...$(COLOR_RESET)"
	@$(PYTHON_VENV) interactive_chatbot.py test

##@ Verification & Testing

verify: aws-check ## Verify LaunchDarkly and RAG configuration
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔍 Verifying system configuration...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)LaunchDarkly AI Configs:$(COLOR_RESET)"
	@$(PYTHON_VENV) verify_ld_configs.py
	@echo ""
	@echo "$(COLOR_YELLOW)RAG Integration:$(COLOR_RESET)"
	@$(PYTHON_VENV) test_rag_integration.py

verify-ld: ## Verify LaunchDarkly AI configs only
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔍 Verifying LaunchDarkly AI Configs...$(COLOR_RESET)"
	@$(PYTHON_VENV) verify_ld_configs.py

verify-rag: ## Verify RAG integration
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)📚 Verifying RAG Integration...$(COLOR_RESET)"
	@$(PYTHON_VENV) test_rag_integration.py

test: verify ## Run all tests and verifications
	@echo "$(COLOR_GREEN)$(COLOR_BOLD)✅ All tests passed!$(COLOR_RESET)"

##@ Development

format: ## Format code with black
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🎨 Formatting code...$(COLOR_RESET)"
	@$(VENV_BIN)/black src/ examples/ *.py --exclude venv
	@echo "$(COLOR_GREEN)✅ Code formatted!$(COLOR_RESET)"

lint: ## Run linting with ruff
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔍 Linting code...$(COLOR_RESET)"
	@$(VENV_BIN)/ruff check src/ examples/ *.py --exclude venv
	@echo "$(COLOR_GREEN)✅ Linting complete!$(COLOR_RESET)"

typecheck: ## Run type checking with mypy
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔍 Type checking...$(COLOR_RESET)"
	@$(VENV_BIN)/mypy src/ --exclude venv
	@echo "$(COLOR_GREEN)✅ Type checking complete!$(COLOR_RESET)"

quality: format lint typecheck ## Run all code quality checks
	@echo "$(COLOR_GREEN)$(COLOR_BOLD)✅ All quality checks passed!$(COLOR_RESET)"

##@ Cleanup

clean: ## Remove Python cache and build artifacts
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🧹 Cleaning up...$(COLOR_RESET)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(COLOR_GREEN)✅ Cleaned up cache and artifacts!$(COLOR_RESET)"

clean-venv: ## Remove virtual environment
	@echo "$(COLOR_BOLD)$(COLOR_YELLOW)⚠️  Removing virtual environment...$(COLOR_RESET)"
	@rm -rf $(VENV)
	@echo "$(COLOR_GREEN)✅ Virtual environment removed!$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)Run 'make install' to recreate it$(COLOR_RESET)"

clean-all: clean clean-venv ## Remove everything (cache, venv, etc.)
	@echo "$(COLOR_GREEN)$(COLOR_BOLD)✅ Complete cleanup done!$(COLOR_RESET)"

##@ Information

info: ## Show system information
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)System Information$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)==================$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Python:$(COLOR_RESET)"
	@if [ -d "$(VENV)" ]; then \
		echo "  Version: $$($(PYTHON_VENV) --version)"; \
		echo "  Location: $(PYTHON_VENV)"; \
	else \
		echo "  $(COLOR_YELLOW)Virtual environment not created$(COLOR_RESET)"; \
		echo "  Run: make install"; \
	fi
	@echo ""
	@echo "$(COLOR_BOLD)AWS Configuration:$(COLOR_RESET)"
	@echo "  Profile: $(AWS_PROFILE)"
	@echo "  Region: $(AWS_REGION)"
	@if aws sts get-caller-identity --profile $(AWS_PROFILE) > /dev/null 2>&1; then \
		echo "  Status: $(COLOR_GREEN)✅ Authenticated$(COLOR_RESET)"; \
	else \
		echo "  Status: $(COLOR_YELLOW)⚠️  Not authenticated$(COLOR_RESET)"; \
	fi
	@echo ""
	@echo "$(COLOR_BOLD)LaunchDarkly:$(COLOR_RESET)"
	@if [ -f .env ]; then \
		if grep -q "LAUNCHDARKLY_ENABLED=true" .env 2>/dev/null; then \
			echo "  Status: $(COLOR_GREEN)✅ Enabled$(COLOR_RESET)"; \
		else \
			echo "  Status: $(COLOR_YELLOW)⚠️  Disabled$(COLOR_RESET)"; \
		fi; \
		if grep -q "LAUNCHDARKLY_SDK_KEY=" .env 2>/dev/null && ! grep -q "LAUNCHDARKLY_SDK_KEY=$$" .env; then \
			echo "  SDK Key: $(COLOR_GREEN)✅ Configured$(COLOR_RESET)"; \
		else \
			echo "  SDK Key: $(COLOR_YELLOW)⚠️  Not configured$(COLOR_RESET)"; \
		fi; \
	else \
		echo "  $(COLOR_YELLOW)⚠️  .env file not found$(COLOR_RESET)"; \
	fi
	@echo ""
	@echo "$(COLOR_BOLD)RAG (Bedrock KB):$(COLOR_RESET)"
	@if [ -f .env ]; then \
		if grep -q "BEDROCK_POLICY_KB_ID=" .env 2>/dev/null && ! grep -q "BEDROCK_POLICY_KB_ID=$$" .env; then \
			echo "  Policy KB: $(COLOR_GREEN)✅ Configured$(COLOR_RESET)"; \
		else \
			echo "  Policy KB: $(COLOR_YELLOW)⚠️  Not configured$(COLOR_RESET)"; \
		fi; \
		if grep -q "BEDROCK_PROVIDER_KB_ID=" .env 2>/dev/null && ! grep -q "BEDROCK_PROVIDER_KB_ID=$$" .env; then \
			echo "  Provider KB: $(COLOR_GREEN)✅ Configured$(COLOR_RESET)"; \
		else \
			echo "  Provider KB: $(COLOR_YELLOW)⚠️  Not configured$(COLOR_RESET)"; \
		fi; \
	fi
	@echo ""

docs: ## Show available documentation
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)📚 Available Documentation$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)========================$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Getting Started:$(COLOR_RESET)"
	@echo "  • QUICKSTART.md                   - 2-minute setup"
	@echo "  • README.md                       - Project overview"
	@echo "  • SDD.md                          - System Design Document"
	@echo ""
	@echo "$(COLOR_BOLD)LaunchDarkly:$(COLOR_RESET)"
	@echo "  • LAUNCHDARKLY.md                 - Complete LD setup guide"
	@echo ""
	@echo "$(COLOR_BOLD)AWS & Bedrock:$(COLOR_RESET)"
	@echo "  • AWS_BEDROCK.md                  - Bedrock LLM setup"
	@echo ""
	@echo "$(COLOR_BOLD)RAG (Retrieval-Augmented Generation):$(COLOR_RESET)"
	@echo "  • BEDROCK_RAG.md                  - Complete RAG guide"
	@echo "  • RAG_SETUP_GUIDE.md              - Quick start for RAG"
	@echo "  • bedrock_setup/QUICK_START.md    - Bedrock KB automated setup"
	@echo "  • bedrock_setup/README_BEDROCK_SETUP.md - Detailed KB setup"
	@echo "  • data/README.md                  - Dataset documentation"
	@echo ""
	@echo "$(COLOR_BOLD)Data Available:$(COLOR_RESET)"
	@echo "  • data/markdown/ - 10 markdown files for Bedrock KB"
	@echo "  • data/*.json - Structured databases"
	@echo ""

##@ RAG Setup

setup-rag: ## Setup Bedrock Knowledge Bases with included data
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)📚 Setting up Bedrock Knowledge Bases...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)This will:$(COLOR_RESET)"
	@echo "  1. Create S3 buckets for policy and provider data"
	@echo "  2. Upload markdown files from data/markdown/"
	@echo "  3. Save configuration for Bedrock KB creation"
	@echo ""
	@echo "$(COLOR_YELLOW)Prerequisites:$(COLOR_RESET)"
	@echo "  • AWS CLI configured with appropriate permissions"
	@echo "  • Access to create S3 buckets, IAM roles, and Bedrock KBs"
	@echo ""
	@read -p "Continue? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		chmod +x bedrock_setup/setup_s3_buckets.sh; \
		./bedrock_setup/setup_s3_buckets.sh; \
		echo ""; \
		echo "$(COLOR_GREEN)$(COLOR_BOLD)✅ S3 setup complete!$(COLOR_RESET)"; \
		echo "$(COLOR_CYAN)Next: Follow bedrock_setup/QUICK_START.md to create Bedrock KBs$(COLOR_RESET)"; \
	else \
		echo "$(COLOR_YELLOW)⏭️  Skipped RAG setup$(COLOR_RESET)"; \
	fi

rag-help: ## Show RAG setup instructions
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)📚 Bedrock Knowledge Base Setup$(COLOR_RESET)"
	@echo "$(COLOR_BOLD)==============================$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_BOLD)Quick Setup:$(COLOR_RESET)"
	@echo "  1. Run: $(COLOR_CYAN)make setup-rag$(COLOR_RESET)          (Creates S3 buckets, uploads data)"
	@echo "  2. Follow: bedrock_setup/QUICK_START.md  (Create Bedrock KBs in console)"
	@echo "  3. Add KB IDs to .env"
	@echo "  4. Run: $(COLOR_CYAN)make verify-rag$(COLOR_RESET)         (Test RAG)"
	@echo ""
	@echo "$(COLOR_BOLD)Data Available:$(COLOR_RESET)"
	@echo "  • data/markdown/ - Markdown files ready for Bedrock KB"
	@echo "  • data/*.json - Structured JSON for databases"
	@echo ""
	@echo "$(COLOR_BOLD)Documentation:$(COLOR_RESET)"
	@echo "  • bedrock_setup/QUICK_START.md"
	@echo "  • bedrock_setup/README_BEDROCK_SETUP.md"
	@echo "  • BEDROCK_RAG.md"
	@echo "  • RAG_SETUP_GUIDE.md"
	@echo ""

##@ Quick Commands

all: clean install setup verify ## Complete setup from scratch
	@echo ""
	@echo "$(COLOR_GREEN)$(COLOR_BOLD)🎉 Setup complete! Ready to run.$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)Run 'make run' to start the chatbot$(COLOR_RESET)"

chat: run ## Alias for 'run' - start the chatbot

check: aws-check verify ## Check all configurations (AWS + LaunchDarkly + RAG)

status: info ## Alias for 'info' - show system status

##@ Default

.DEFAULT_GOAL := help

