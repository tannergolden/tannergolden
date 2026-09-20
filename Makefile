# --- Developer Dispatch Points ---
#
# WHAT BELONGS HERE: the commands a person or a gate runs. No logic. Every
# target is a one-line call into `src/`, so this file cannot drift away from
# what the code actually does, and checks.yml runs the same entry points a
# contributor does rather than its own private copy of them.
#
# The code is stdlib-only Python. The two tools below are development
# dependencies, pinned here and installed by `make setup`.
#
# ---

RUFF_VERSION ?= 0.15.8
PYTEST_VERSION ?= 9.1.1
EMBLEMS_KIT ?= .emblems/src/badge-kit.py

.PHONY: help setup lint lint-fix test check render badges

help: ## Show the available targets
	@grep -hE '^[a-z][a-z-]*:.*?## ' $(MAKEFILE_LIST) \
		| sort \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}'

setup: ## Install the pinned development tools
	pip install --quiet "ruff==$(RUFF_VERSION)" "pytest==$(PYTEST_VERSION)"

lint: ## Lint the Python, with the rules declared in .ruff.toml
	ruff check .

lint-fix: ## Apply the lint fixes ruff can make automatically
	ruff check --fix .

test: ## Run the test suite
	python3 -m pytest

check: ## Verify README.md still carries every machine-owned region
	python3 src/dispatches.py --mode check

render: ## Re-render the page from committed state, without the network
	python3 src/dispatches.py --mode render

badges: ## Render .github/badges.yml into committed SVGs via the emblems kit
	python3 $(EMBLEMS_KIT) --root . --data .github/badges.yml --out assets/badges
