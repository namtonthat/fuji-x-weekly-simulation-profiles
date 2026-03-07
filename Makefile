.DEFAULT_GOAL := help

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.PHONY: install
install: ## Install uv and pre-commit hooks
	@./scripts/install.sh

.PHONY: check
check: ## Run code quality tools.
	@./scripts/check.sh

.PHONY: copy
copy: ## Interactive copy (bulk compatible or selected profiles cross-sensor override)
	@echo "📷 Copying fuji_profiles"
	@uv run python -m scrape.copy-fuji-profiles

.PHONY: clean
clean: ## Remove the .cached/ files
	@echo "🛀 Cleaning previous files"
	@./scripts/clean.sh

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@uv run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@uv run mkdocs serve

.PHONY: scrape
scrape: ## Scrape the data from the Fuji X Weekly website
	@echo "📷 Scraping data from Fuji X Weekly"
	@uv run python -m scrape.scraper
