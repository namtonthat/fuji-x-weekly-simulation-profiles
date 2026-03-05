# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scrapes fujixweekly.com for Fujifilm X camera simulation profiles (film recipes) and generates `.FP1` files compatible with Fuji X Raw Studio. A scheduled GitHub Action runs the scrape fortnightly. Also includes a CLI tool to copy generated profiles to the local X Raw Studio app directory (macOS).

## Commands

| Task | Command |
|---|---|
| Install environment | `make install` |
| Run all quality checks (lock, pre-commit, mypy) | `make check` |
| Run tests | `uv run pytest` |
| Run a single test | `uv run pytest tests/test_parsing.py::test_name` |
| Scrape recipes from fujixweekly.com | `make scrape` |
| Copy profiles to local X Raw Studio | `make copy` |
| Clear cached URLs (force re-scrape) | `make clean` |
| Build docs | `uv run mkdocs build -s` |
| Serve docs locally | `make docs` |

## Architecture

### Scraping pipeline (`scrape/`)

1. **`scraper.py`** — Entry point (`python -m scrape.scraper`). `FujiRecipes.fetch_recipes()` scrapes a sensor page for recipe links, then for each link `FujiRecipeLink.get_profile()` parses the recipe page's `<strong>` tags into a `FujiSimulationProfile`.
2. **`models.py`** — Data model layer. `FujiSimulationProfile` is a dataclass that maps to FP1 XML tags via `attribute_to_xml_mapping`. `KeyStandardizer` contains parsing methods that normalize scraped text into typed values (enums, ints, dataclasses like `WhiteBalance`, `GrainEffect`).
3. **`templates/fp1.jinja2`** — Jinja2 XML template for `.FP1` files. `FujiRecipe.filled_template` renders it then `fill_xml_template()` replaces XML tag values with parsed profile data.
4. **`copy-fuji-profiles.py`** — CLI tool (`python -m scrape.copy-fuji-profiles`) using Rich for interactive profile copying to macOS X Raw Studio directories.

### Data flow

```
fujixweekly.com sensor page → recipe URLs → parse <strong> tags → FujiSimulationProfile → fill Jinja2 template → .FP1 file
```

### Caching

- `cached/<sensor>.txt` — Successfully scraped URLs (skipped on next run)
- `failed/<sensor>.txt` — Failed URLs (overwritten each run)
- `fuji_profiles/<sensor>/` — Generated `.FP1` profile files

### Key sensors currently scraped

X-Trans III, X-Trans IV, X-Trans V (configured in `GLOBAL_SENSOR_LIST` in `scraper.py`).

## Code Style

- **Python 3.13**, managed with **uv**
- **Ruff** for linting and formatting (line length 200)
- **mypy** with strict settings (`disallow_untyped_defs`, `check_untyped_defs`)
- Pre-commit hooks: ruff-format, ruff lint, prettier, standard pre-commit checks
- Tests in `tests/` use pytest; run with `uv run pytest`
