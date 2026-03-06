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

1. **`scraper.py`** — Entry point (`python -m scrape.scraper`). `FujiRecipes.fetch_recipes()` scrapes a sensor page for recipe links, then for each link `FujiRecipeLink.get_profile()` parses the recipe page's `<strong>` tags into a `FujiSimulationProfile`. The `sensor` is threaded through to `FujiSimulationProfileParser` for resolving sensor-conditional values.
2. **`models.py`** — Data model layer. `FujiSimulationProfile` is a dataclass that maps to FP1 XML tags via `attribute_to_xml_mapping`. `KeyStandardizer` contains parsing methods that normalize scraped text into typed values (enums, ints, dataclasses like `WhiteBalance`, `GrainEffect`). `resolve_conditional_value()` handles sensor-specific values like "Off (X-Trans V); Weak (X-Trans IV)".
3. **`templates/fp1.jinja2`** — Jinja2 XML template for `.FP1` files. `FujiRecipe.filled_template` renders it then `fill_xml_template()` replaces XML tag values with parsed profile data.
4. **`copy-fuji-profiles.py`** — CLI tool (`python -m scrape.copy-fuji-profiles`) using Rich for interactive profile copying to macOS X Raw Studio directories. Uses case-insensitive `.fp1` matching.

### Data flow

```
fujixweekly.com sensor page → recipe URLs → parse <strong> tags
  → resolve_conditional_value (per sensor) → KeyStandardizer → FujiSimulationProfile
  → fill Jinja2 template → .FP1 file
```

### Caching

- `cached/<sensor>.txt` — Successfully scraped URLs (skipped on next run). Empty these to force re-scrape.
- `failed/<sensor>.txt` — Failed URLs (overwritten each run)
- `fuji_profiles/<sensor>/` — Generated `.FP1` profile files (uppercase extension per Fujifilm convention)

### Key sensors currently scraped

X-Trans III, X-Trans IV, X-Trans V (configured in `GLOBAL_SENSOR_LIST` in `scraper.py`).

### Known scraper limitations

- Only parses `<strong>` tags — blog posts using `<b>` or other tags will fail
- `FujiSimulationProfile` requires `film_simulation`, `white_balance`, `dynamic_range`, `sharpness`, `high_iso_nr` — monochrome recipes that omit white balance will fail
- Film simulation names with `+` (e.g., "Acros + R") produce triple underscores in `clean_camera_profile_name` and may not match `FilmSimulation` enum
- One failed key in `profile_dict` aborts the entire profile rather than skipping that field

## Code Style

- **Python 3.13**, managed with **uv**
- **Ruff** for linting and formatting (line length 200, target py313)
- **mypy** with strict settings (`disallow_untyped_defs`, `check_untyped_defs`)
- Pre-commit hooks: ruff-format, ruff lint, prettier, standard pre-commit checks
- All modules use `logger = logging.getLogger(__name__)` pattern
- Tests in `tests/` use pytest with shared fixtures in `tests/conftest.py`

## Testing

- Shared fixtures (`sample_html`, `strong_tags`) live in `tests/conftest.py`
- `test_parsing.py` — tests HTML tag processing, key standardization, conditional value resolution
- `test_save.py` — tests FP1 file generation using monkeypatched network calls and tmp_path
- Network calls are monkeypatched in tests; only `make scrape` hits the network
