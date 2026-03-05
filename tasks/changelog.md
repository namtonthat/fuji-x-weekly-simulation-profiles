# Changelog - Fix Bugs and Inconsistencies

## US-001: Fix XML mapping typo
- **Status:** Applied - ready to commit
- **Change:** `scrape/models.py:136` — `magnetic_green` → `magenta_green`
- **Assumptions:** None

## US-002: Fix template path case
- **Status:** Applied - ready to commit
- **Change:** `scrape/scraper.py:237` — `FP1.jinja2` → `fp1.jinja2`
- **Assumptions:** None

## US-003: Add error handling for exposure_compensation
- **Status:** Applied - ready to commit
- **Changes:**
  - `scrape/models.py:273-275` — added `if not matches` guard returning `0.0` with warning
  - `tests/test_parsing.py` — added 2 new tests for exposure_compensation
- **Assumptions:** Agent also fixed relative imports in test_parsing.py (overlaps with US-006). Fixed test expectation for rounding (0.33 not 0.333).
- **Note:** The import fix is correct and aligned with US-006 scope. Test expectation was wrong (`pytest.approx(1/3)` vs actual `0.33` due to `convert_to_float` rounding to 2dp) — manually corrected.

## US-004: Fix unconditional warning in create_fuji_profile
- **Status:** Applied - ready to commit
- **Change:** `scrape/scraper.py:172-180` — wrapped in try/except, warning only on failure
- **Assumptions:** None

## US-005: Add early return on empty tags
- **Status:** Applied - ready to commit
- **Change:** `scrape/scraper.py:223` — added `return None` after error log
- **Assumptions:** None

## US-006: Fix test imports and monkeypatch targets
- **Status:** Partially applied (imports fixed by US-003 agent), monkeypatch targets still need fixing
- **Remaining:** Fix monkeypatch in test_parsing.py:142 and test_save.py:52, create conftest.py

## US-007: Fix pyproject.toml configuration
- **Status:** Applied - ready to commit
- **Changes:**
  - `pyproject.toml:53` — `py311` → `py313`
  - `pyproject.toml:112` — `fuji_x_weekly_simulation_profiles` → `scrape`
- **Assumptions:** None

## US-008: Fix method name typo and logging
- **Status:** Pending

## US-009: Fix ColorChromeBlue conditional parsing
- **Status:** Pending

## US-010: Standardize extensions and re-scrape
- **Status:** Pending

## Pre-existing test failures (not caused by our changes)
- `test_nbsp_replacement` — `flatten_and_process_tags` doesn't replace `\xa0`; the replacement happens in `FujiSimulationProfileParser.processed_tags` property instead. Test expectation is wrong.
- `test_fuji_simulation_profile_parser_monkeypatch` — patches nonexistent module-level `soup_representation` (it's a staticmethod on `FujiRecipes` class)
- `test_recipe_save_outputs` — patches nonexistent `scrape.models.OUTPUT_DIR`
