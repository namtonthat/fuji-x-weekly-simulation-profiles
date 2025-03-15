import difflib
from pathlib import Path

import pytest

from scrape.models import FujiSensor
from scrape.scraper import FujiRecipe, FujiRecipeLink


# Fixture returning sensor recipes for all cases.
@pytest.fixture
def sensor_recipes() -> dict[FujiSensor, list[FujiRecipe]]:
    return {
        FujiSensor.X_TRANS_IV: [
            FujiRecipe(
                sensor=FujiSensor.X_TRANS_IV,
                link=FujiRecipeLink(
                    name="Kentmere Pan 400",
                    url="https://fujixweekly.com/2024/03/15/kentmere-pan-400-fujifilm-x100v-x-trans-iv-v-film-simulation-recipe/",
                ),
            )
        ],
        FujiSensor.X_TRANS_V: [
            FujiRecipe(
                sensor=FujiSensor.X_TRANS_V,
                link=FujiRecipeLink(
                    name="Easy Reala Ace",
                    url="https://fujixweekly.com/2024/06/20/easy-reala-ace-fujifilm-x100vi-x-trans-v-film-simulation-recipe/",
                ),
            )
        ],
        FujiSensor.X_TRANS_III: [
            FujiRecipe(
                sensor=FujiSensor.X_TRANS_III,
                link=FujiRecipeLink(
                    name="Nostalgic Emulsion",
                    url="https://fujixweekly.com/2024/10/24/nostalgic-emulsion-fujifilm-x-trans-iii-plus-x-t3-x-t30-film-simulation-recipe/",
                ),
            )
        ],
    }


def test_recipe_save_outputs(tmp_path, monkeypatch):
    """
    Iterate over each sensor recipe, run recipe.save() and compare the generated FP1 output
    to the expected FP1 file.
    """
    errors = []
    expected_dir = Path(__file__).parent / "expected_fp1"

    monkeypatch.setattr("scrape.models.OUTPUT_DIR", str(tmp_path))
    # Adjust this to match your implementation so that FP1 files are written to tmp_path.

    recipe = FujiRecipe(
        sensor=FujiSensor.X_TRANS_IV,
        link=FujiRecipeLink(
            name="Test Recipe",
            url="https://fujixweekly.com/2024/03/15/test-recipe/",
        ),
    )

    # Call .save(); we expect it returns True upon success.
    success = recipe.save()
    assert success, f"Recipe.save() failed for {recipe.link.name}"

    # Determine the generated file name.
    # Here we assume a naming convention: recipe name with spaces replaced by underscores + '.fp1'
    file_name = recipe.link.name.replace(" ", "_") + ".fp1"
    generated_fp1_file = tmp_path / file_name

    if not generated_fp1_file.exists():
        errors.append(f"Generated FP1 file not found: {generated_fp1_file}")
        pytest.fail("\n\n".join(errors))

    generated_fp1 = generated_fp1_file.read_text(encoding="utf-8").strip()

    # Locate the expected FP1 file.
    expected_fp1_file = expected_dir / file_name
    if not expected_fp1_file.exists():
        errors.append(f"Expected FP1 file not found: {expected_fp1_file}")
        pytest.fail("\n\n".join(errors))

    expected_fp1 = expected_fp1_file.read_text(encoding="utf-8").strip()

    # Compare and, if needed, generate a diff.
    if generated_fp1 != expected_fp1:
        diff = "\n".join(difflib.unified_diff(expected_fp1.splitlines(), generated_fp1.splitlines(), fromfile=str(expected_fp1_file), tofile=str(generated_fp1_file), lineterm=""))
        errors.append(f"Mismatch for {recipe.link.name}:\n{diff}")

    if errors:
        pytest.fail("\n\n".join(errors))
