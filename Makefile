# Makefile for Local Agents with Ollama (LLaMA)

# Tools and paths
PYTHON ?= python3
VENVDIR := .venv
VENV_PY := $(VENVDIR)/bin/python
VENV_PIP := $(VENVDIR)/bin/pip
CLI := $(VENV_PY) -m app.cli

# Runtime defaults (override with make VAR=value)
MODEL ?= llama3.1:8b
HOST ?=
MODE ?= auto
LABELS ?=
JOB ?=
FILE ?=
CMD ?=

HOST_FLAG := $(if $(HOST),--host $(HOST),)
MODEL_FLAG := $(if $(MODEL),--model $(MODEL),)
LABELS_FLAG := $(if $(LABELS),--labels $(LABELS),)

.PHONY: help init venv install dev-install doctor pull-model ensure-model \
	classify classify-file run-example cli format lint typecheck clean distclean

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z0-9_.-]+:.*## / {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

init: venv install ## Create venv and install dependencies

venv: ## Create a virtual environment (if missing) and upgrade pip
	@test -d $(VENVDIR) || $(PYTHON) -m venv $(VENVDIR)
	@$(VENV_PIP) -q install --upgrade pip

install: ## Install runtime dependencies
	@$(VENV_PIP) -q install -r requirements.txt

dev-install: venv ## Install dev tools (black, ruff)
	@$(VENV_PIP) -q install black ruff

doctor: ## Print versions of Python, venv Python and Ollama if present
	@echo "Python: $$($(PYTHON) --version 2>&1 || true)"
	@echo "Venv Python: $$($(VENV_PY) --version 2>&1 || echo 'venv not created')"
	@echo "Ollama: $$(ollama --version 2>&1 || echo 'ollama not found')"

pull-model: ## Pull the specified Ollama model (override MODEL=...)
	@echo "Pulling model $(MODEL) ..."
	@ollama pull $(MODEL)

ensure-model: ## Ensure the Ollama model is available locally; pull if missing
	@if ! ollama list 2>/dev/null | grep -q "$(MODEL)"; then \
		echo "Model $(MODEL) not found locally. Pulling..."; \
		ollama pull $(MODEL); \
	else \
		echo "Model present: $(MODEL)"; \
	fi

classify: install ## Classify a single role title/description (JOB="...")
	@test -n "$(JOB)" || (echo "Please set JOB=\"...\""; exit 1)
	@$(CLI) classify-jobs --mode $(MODE) $(MODEL_FLAG) $(HOST_FLAG) $(LABELS_FLAG) "$(JOB)"

classify-file: install ## Classify roles from a file, one per line (FILE=path)
	@test -n "$(FILE)" || (echo "Please set FILE=path"; exit 1)
	@cat $(FILE) | $(CLI) classify-jobs --mode $(MODE) $(MODEL_FLAG) $(HOST_FLAG) $(LABELS_FLAG)

run-example: install ## Run example classifications
	@$(CLI) classify-jobs --mode $(MODE) $(MODEL_FLAG) $(HOST_FLAG) "Senior React Developer" "SRE / DevOps Engineer"

cli: install ## Run the CLI with an arbitrary command (CMD="classify-jobs ...")
	@test -n "$(CMD)" || (echo "Usage: make cli CMD=\"classify-jobs --mode auto ...\""; exit 1)
	@$(CLI) $(CMD)

format: ## Format code with black (installs black if missing)
	@$(VENV_PIP) -q show black >/dev/null 2>&1 || $(VENV_PIP) -q install black
	@$(VENVDIR)/bin/black app

lint: ## Lint with ruff (installs ruff if missing)
	@$(VENV_PIP) -q show ruff >/dev/null 2>&1 || $(VENV_PIP) -q install ruff
	@$(VENVDIR)/bin/ruff check app

typecheck: ## Type-check with mypy (installs mypy if missing)
	@$(VENV_PIP) -q show mypy >/dev/null 2>&1 || $(VENV_PIP) -q install mypy
	@$(VENVDIR)/bin/mypy app || true

clean: ## Remove Python cache artifacts
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true

distclean: clean ## Remove venv and caches
	@rm -rf $(VENVDIR)