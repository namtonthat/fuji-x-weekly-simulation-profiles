# PRD: Fix Bugs and Inconsistencies

## Introduction

The fuji-x-weekly-simulation-profiles repository has accumulated bugs, inconsistencies, and data quality issues across its scraper code, tests, configuration, and generated FP1 profile files. This PRD addresses all identified issues in four phases: critical code fixes, test fixes, config fixes, and profile data fixes. After all code fixes land, the scraper is re-run to regenerate clean profiles.

## Goals

- Fix all critical bugs that cause silent data loss or runtime failures
- Ensure tests pass and actually validate the code they claim to test
- Align project configuration with actual project structure and Python version
- Produce correct, consistent FP1 profile files for all supported sensors
- Add reusable pytest fixtures to improve test maintainability

## User Stories

### US-001: Fix XML mapping typo (magnetic_green -> magenta_green)
**Description:** As a developer, I want the monochromatic color magenta-green value to be correctly mapped to the FP1 XML template so that profiles with monochromatic color settings are generated correctly.

**Acceptance Criteria:**
- [ ] In `scrape/models.py`, `attribute_to_xml_mapping` key `"monochromatic_color_magnetic_green"` is changed to `"monochromatic_color_magenta_green"`
- [ ] `uv run pytest` passes
- [ ] `uv run mypy` passes

### US-002: Fix template path case mismatch
**Description:** As a developer, I want the Jinja2 template path to match the actual filename on disk so that the scraper works on case-sensitive filesystems (Linux CI).

**Acceptance Criteria:**
- [ ] In `scrape/scraper.py`, `template_location` is changed from `"templates/FP1.jinja2"` to `"templates/fp1.jinja2"`
- [ ] `uv run pytest` passes

### US-003: Add error handling for exposure_compensation
**Description:** As a developer, I want the `exposure_compensation` parser to handle missing regex matches gracefully instead of raising an unhandled IndexError.

**Acceptance Criteria:**
- [ ] In `scrape/models.py`, `exposure_compensation()` returns a default (e.g., `0.0`) and logs a warning when no match is found
- [ ] New pytest test covers the no-match case
- [ ] `uv run pytest` passes

### US-004: Fix unconditional warning in create_fuji_profile
**Description:** As a developer, I want `create_fuji_profile()` to only log a warning when profile creation fails, not on every call.

**Acceptance Criteria:**
- [ ] In `scrape/scraper.py`, the warning in `create_fuji_profile()` is conditional — only logged when the profile is `None` or creation raised an exception
- [ ] Successful profile creation does not produce a warning log
- [ ] `uv run pytest` passes

### US-005: Add early return on empty tags in get_profile
**Description:** As a developer, I want `get_profile()` to return `None` immediately when no tags are found instead of processing empty data.

**Acceptance Criteria:**
- [ ] In `scrape/scraper.py`, `get_profile()` returns `None` after logging the error when `tags` is empty
- [ ] `uv run pytest` passes

### US-006: Fix test imports and monkeypatch targets
**Description:** As a developer, I want the test files to use correct imports and monkeypatch targets so that tests actually run and validate the code.

**Acceptance Criteria:**
- [ ] `tests/test_parsing.py` uses absolute imports (`from scrape.models import ...`) instead of relative imports
- [ ] `tests/test_parsing.py` monkeypatches `FujiRecipes.soup_representation` (the staticmethod) instead of a nonexistent module-level function
- [ ] `tests/test_save.py` monkeypatches the correct output path mechanism (e.g., `FujiRecipe.output_file_path` property or `os.getcwd`) instead of nonexistent `scrape.models.OUTPUT_DIR`
- [ ] All tests pass with `uv run pytest`

### US-007: Fix pyproject.toml configuration
**Description:** As a developer, I want the project config to reflect the actual Python version and package structure.

**Acceptance Criteria:**
- [ ] `tool.ruff.target-version` is updated from `"py311"` to `"py313"`
- [ ] `tool.coverage.run.source` is updated from `["fuji_x_weekly_simulation_profiles"]` to `["scrape"]`
- [ ] `uv run ruff check .` passes
- [ ] `uv run mypy` passes

### US-008: Fix method name typo and logging inconsistencies
**Description:** As a developer, I want consistent naming and logging across the codebase.

**Acceptance Criteria:**
- [ ] `scrape/models.py`: method `film_simluation` renamed to `film_simulation`
- [ ] `scrape/models.py`: reference in `initialise_parsing_methods` updated to match
- [ ] `scrape/models.py`: add `logger = logging.getLogger(__name__)` and replace all `logging.warning()` calls with `logger.warning()`
- [ ] `scrape/scraper.py`: replace `logging.warning()` call on line 57 with `logger.warning()`
- [ ] `uv run ruff check .` passes
- [ ] `uv run mypy` passes

### US-009: Fix ColorChromeBlue conditional parsing in scraper
**Description:** As a developer, I want the scraper to parse sensor-conditional values like "Off (X-Trans V); Weak (X-Trans IV)" and select the correct value for the current sensor, instead of storing the raw text.

**Acceptance Criteria:**
- [ ] Scraper code handles semicolon-separated conditional values by matching the current sensor
- [ ] New pytest fixture provides sample conditional HTML for testing
- [ ] New test verifies correct value is selected per sensor
- [ ] `uv run pytest` passes

### US-010: Re-scrape all profiles and standardize extensions
**Description:** As a developer, I want to regenerate all FP1 profiles after code fixes, using `.FP1` (uppercase) extension to match Fujifilm convention.

**Acceptance Criteria:**
- [ ] `scrape/scraper.py` output path uses `.FP1` extension
- [ ] `cached/*.txt` files are cleared to force re-scrape
- [ ] `make scrape` runs successfully and generates profiles
- [ ] All generated files use `.FP1` extension
- [ ] `scrape/copy-fuji-profiles.py` still correctly handles the files (already does case-insensitive matching)
- [ ] Empty ExposureBias values are resolved by re-scraping with fixed parser

## Functional Requirements

- FR-1: `attribute_to_xml_mapping` must use `monochromatic_color_magenta_green` as key
- FR-2: Template path must be `templates/fp1.jinja2` (matching actual file on disk)
- FR-3: `exposure_compensation()` must return `0.0` with a warning when regex finds no match
- FR-4: `create_fuji_profile()` must only warn on failure, not on success
- FR-5: `get_profile()` must return `None` immediately when no tags are found
- FR-6: All test files must use absolute imports from the `scrape` package
- FR-7: Test monkeypatches must target actual attributes/methods that exist
- FR-8: Ruff target-version must match `requires-python` (py313)
- FR-9: Coverage source must reference the actual `scrape` package
- FR-10: No misspelled method names in public API
- FR-11: All modules must use `logger = logging.getLogger(__name__)` pattern
- FR-12: Scraper must parse sensor-conditional values (e.g., "Off (X-Trans V); Weak (X-Trans IV)") and select the value matching the current sensor
- FR-13: All generated FP1 files must use `.FP1` extension (Fujifilm convention)
- FR-14: Pytest fixtures must be defined in `conftest.py` for reuse across test files

## Non-Goals

- No changes to the CLI copy tool's core functionality
- No changes to the scraping schedule or GitHub Actions workflows
- No new features or scraper capabilities beyond fixing existing bugs
- No changes to the Jinja2 template structure itself
- Cross-sensor duplicates are intentional and will not be removed (confirmed by user)

## Technical Considerations

- The scraper makes real HTTP requests to fujixweekly.com — the re-scrape step (US-010) requires network access
- Clearing `cached/*.txt` means ALL profiles will be re-scraped, not just affected ones
- The `.FP1` extension is what Fujifilm X Raw Studio produces natively; the copy script already handles this via case-insensitive matching (`file_name.lower().endswith(".fp1")`)
- Tests that need network should use monkeypatched fixtures; only `make scrape` should hit the network

## Success Metrics

- All tests pass: `uv run pytest` exits 0
- All quality checks pass: `make check` exits 0
- Zero unconditional warnings in normal scrape runs
- All FP1 files contain resolved values (no raw conditional text)
- All FP1 files use `.FP1` extension

## Open Questions

- None — all clarifications resolved.
