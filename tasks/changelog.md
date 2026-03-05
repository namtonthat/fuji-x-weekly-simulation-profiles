# Changelog - Fix Bugs and Inconsistencies

## US-001: Fix XML mapping typo
- **Status:** Committed (batch 1)
- **Change:** `scrape/models.py:136` — `magnetic_green` → `magenta_green`
- **Assumptions:** None

## US-002: Fix template path case
- **Status:** Committed (batch 1)
- **Change:** `scrape/scraper.py:237` — `FP1.jinja2` → `fp1.jinja2`
- **Assumptions:** None

## US-003: Add error handling for exposure_compensation
- **Status:** Committed (batch 1)
- **Changes:**
  - `scrape/models.py:273-275` — added `if not matches` guard returning `0.0` with warning
  - `tests/test_parsing.py` — added 2 new tests for exposure_compensation
- **Assumptions:** Agent also fixed relative imports (US-006 overlap) — correct and aligned.
- **Note:** Manually corrected test expectation (`0.33` not `pytest.approx(1/3)`) due to rounding.

## US-004: Fix unconditional warning in create_fuji_profile
- **Status:** Committed (batch 1)
- **Change:** `scrape/scraper.py:172-180` — wrapped in try/except, warning only on failure
- **Assumptions:** None

## US-005: Add early return on empty tags
- **Status:** Committed (batch 1)
- **Change:** `scrape/scraper.py:223` — added `return None` after error log
- **Assumptions:** None

## US-007: Fix pyproject.toml configuration
- **Status:** Committed (batch 1)
- **Changes:**
  - `pyproject.toml:53` — `py311` → `py313`
  - `pyproject.toml:112` — `fuji_x_weekly_simulation_profiles` → `scrape`
- **Assumptions:** None

## US-008: Fix method name typo and logging
- **Status:** Auto-committed by agent
- **Changes:**
  - `scrape/models.py:277` — `film_simluation` → `film_simulation`
  - `scrape/models.py:401` — updated reference in `initialise_parsing_methods`
  - `scrape/models.py:9` — added `logger = logging.getLogger(__name__)`
  - `scrape/models.py` — replaced 5x `logging.warning()` with `logger.warning()`
  - `scrape/scraper.py:57` — replaced `logging.warning()` with `logger.warning()`
- **Assumptions:** None

## US-009: Fix ColorChromeBlue conditional parsing
- **Status:** Auto-committed by agent
- **Changes:**
  - `scrape/models.py` — added `resolve_conditional_value()` function
  - `scrape/scraper.py` — added `sensor` field to `FujiSimulationProfileParser`, integrated conditional resolution in `profile_dict`, threaded sensor through `get_profile()` → `as_dict()`
  - `tests/test_parsing.py` — added 6 tests for conditional value resolution + integration
- **Assumptions:** Added `sensor` parameter to `FujiRecipeLink.get_profile()` — minimal but changes the method signature. This is necessary for the feature to work.

## US-006: Fix test imports and monkeypatch targets
- **Status:** Applied (uncommitted) — needs review
- **Changes:**
  - `tests/conftest.py` — created with shared `sample_html` and `strong_tags` fixtures
  - `tests/test_parsing.py` — removed fixture definitions, fixed monkeypatch to target `FujiRecipes` staticmethod, fixed fake URL to match recipe pattern
  - `tests/test_save.py` — replaced nonexistent `OUTPUT_DIR` monkeypatch with `monkeypatch.chdir(tmp_path)`, added `_recipe_html_tags` fixture to avoid network calls, simplified assertions
- **Assumptions:**
  - Changed `sample-recipe2/` to `another-sample-recipe/` in fake HTML to match the `.*recipe/$` regex pattern
  - Simplified test_save.py significantly — removed expected_fp1 comparison (files didn't exist), replaced with XML content assertions
  - Added `_recipe_html_tags` fixture that monkeypatches `FujiRecipeLink.parse_webpage_for_tags` to avoid network calls

## US-010: Standardize extensions and re-scrape
- **Status:** Pending — requires network access and all prior fixes
