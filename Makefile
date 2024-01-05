.PHONY: install
install: ## Install the poetry environment and install the pre-commit hooks
	@./scripts/install.sh

.PHONY: check
check: ## Run code quality tools.
	@./scripts/check.sh

.PHONY: scrape
scrape: ## Scrape the data from the Fuji X Weekly website
	@echo "📷 Scraping data from Fuji X Weekly"
	@poetry run python -m scrape.scraper

.PHONY: copy
copy: ## Copy profiles to the required folders
	@echo "📷 Copying fuji_profiles"
	@poetry run python -m scrape.copy-fuji-profiles

.PHONY: clean
clean: ## Remove the .cached/ files
	@echo "🛀 Cleaning previous files"
	@./scripts/clean.sh

.PHONY: docs-test
docs-test: ## Test if documentation can be built without warnings or errors
	@poetry run mkdocs build -s

.PHONY: docs
docs: ## Build and serve the documentation
	@poetry run mkdocs serve

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
