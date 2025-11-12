### Makefile for ToggleBankRAG local dev
# Usage:
#   make           -> same as make restart
#   make restart   -> stop existing backend / frontend and relaunch them
#   make stop      -> just stop running dev servers

# Ports
BACKEND_PORT := 8000
FRONTEND_PORTS := 3000 3001

# Patterns to kill
BACKEND_PROC := backend/fastapi_wrapper.py
FRONTEND_PROC := "next dev"

.PHONY: restart stop

restart: stop
	@echo "\033[32m🚀 Starting backend...\033[0m"
	@python3 backend/fastapi_wrapper.py &
	@sleep 2  # small delay before frontend
	@echo "\033[32m📦 Starting frontend...\033[0m"
	@npm run dev &
	@echo "\033[32m✅ Servers relaunched.\033[0m"

stop:
	@echo "\033[33m⏹  Stopping running dev servers...\033[0m"
	@pkill -f $(BACKEND_PROC) 2>/dev/null || true
	@pkill -f uvicorn 2>/dev/null || true
	@pkill -f $(FRONTEND_PROC) 2>/dev/null || true
	@pkill -f "node .*next" 2>/dev/null || true
	@# Ensure ports are freed
	@lsof -ti :$(BACKEND_PORT) $(foreach p,$(FRONTEND_PORTS),:$(p)) | xargs -r kill -9 2>/dev/null || true
	@echo "\033[33m🛑 Servers stopped (if any were running).\033[0m" 