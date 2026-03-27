.PHONY: help install setup run verify clean aws-login aws-check format lint test-suite test-quick upload-tools

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

run: aws-check ## Run the interactive chatbot (terminal version, auto-checks AWS)
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🚀 Starting Medical Insurance Support Chatbot (Terminal)...$(COLOR_RESET)"
	@echo ""
	@$(PYTHON_VENV) interactive_chatbot.py

run-ui: aws-check ## Run the web UI (FastAPI backend + React frontend)
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🚀 Starting ToggleHealth Web UI...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)Starting backend on http://localhost:8000...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Starting frontend on http://localhost:3000...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)Open http://localhost:3000 in your browser$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Press Ctrl+C to stop both services$(COLOR_RESET)"
	@echo ""
	@trap 'kill 0' INT; \
	(cd ui/backend && ../../$(PYTHON_VENV) server.py) & \
	(cd ui/frontend && npm run dev) & \
	wait

togglecell: aws-check ## Run ToggleCell UI (telecom demo, same AI configs)
	@echo ""
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)📱 Starting ToggleCell Support Hub...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_YELLOW)Starting backend on http://localhost:8000...$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Starting frontend on http://localhost:8080...$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_CYAN)Same AI configs as ToggleHealth, domain=togglecell$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)Prompts adapt via {{domain}} template variable$(COLOR_RESET)"
	@echo ""
	@echo "$(COLOR_GREEN)Open http://localhost:8080 in your browser$(COLOR_RESET)"
	@echo "$(COLOR_YELLOW)Press Ctrl+C to stop both services$(COLOR_RESET)"
	@echo ""
	@trap 'kill 0' INT; \
	(cd ui/backend && ../../$(PYTHON_VENV) server.py) & \
	(cd ui/frontend-togglecell && npm run dev) & \
	wait

run-test: aws-check ## Run a quick test query
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🧪 Running quick test...$(COLOR_RESET)"
	@$(PYTHON_VENV) interactive_chatbot.py test

##@ Verification & Testing

verify: aws-check info ## Verify AWS credentials and show system status
	@echo "$(COLOR_GREEN)$(COLOR_BOLD)✅ System verification complete!$(COLOR_RESET)"

##@ Development

format: ## Format code with black
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🎨 Formatting code...$(COLOR_RESET)"
	@$(VENV_BIN)/black src/ tests/ simulations/ scripts/ *.py --exclude venv
	@echo "$(COLOR_GREEN)✅ Code formatted!$(COLOR_RESET)"

lint: ## Run linting with ruff
	@echo "$(COLOR_BOLD)$(COLOR_CYAN)🔍 Linting code...$(COLOR_RESET)"
	@$(VENV_BIN)/ruff check src/ tests/ simulations/ scripts/ *.py --exclude venv
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

##@ Quick Commands

all: clean install setup ## Complete setup from scratch
	@echo ""
	@echo "$(COLOR_GREEN)$(COLOR_BOLD)🎉 Setup complete! Ready to run.$(COLOR_RESET)"
	@echo "$(COLOR_CYAN)Run 'make run' to start the chatbot$(COLOR_RESET)"

chat: run ## Alias for 'run' - start the terminal chatbot

ui: run-ui ## Alias for 'run-ui' - start the web UI

check: aws-check verify ## Check AWS credentials and system status

status: info ## Alias for 'info' - show system status

##@ Testing & Evaluation

test-suite: aws-check ## Run automated agent test suite (50 iterations)
	@echo "$(COLOR_CYAN)$(COLOR_BOLD)🧪 Running Agent Test Suite (50 iterations)...$(COLOR_RESET)"
	@. venv/bin/activate && python tests/test_agent_suite.py

test-quick: aws-check ## Run quick test (5 iterations)
	@echo "$(COLOR_CYAN)$(COLOR_BOLD)🧪 Running Quick Test (5 iterations)...$(COLOR_RESET)"
	@. venv/bin/activate && TEST_ITERATIONS=5 python tests/test_agent_suite.py

##@ LaunchDarkly Tools

upload-tools: ## Upload all 20 tools to LaunchDarkly Tool Library
	@echo "$(COLOR_CYAN)$(COLOR_BOLD)🚀 Uploading Tools to LaunchDarkly...$(COLOR_RESET)"
	@$(PYTHON_VENV) scripts/upload_tools_to_launchdarkly.py

##@ Default

.DEFAULT_GOAL := run-ui

