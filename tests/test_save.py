import shutil
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from scrape.models import FujiSensor
from scrape.scraper import FujiRecipe, FujiRecipeLink


@pytest.fixture
def _recipe_html_tags(monkeypatch, sample_html):
    """Monkeypatch FujiRecipeLink.parse_webpage_for_tags so no network call is made."""
    soup = BeautifulSoup(sample_html, "html.parser")
    tags = soup.find_all("strong")
    monkeypatch.setattr(FujiRecipeLink, "parse_webpage_for_tags", lambda self: tags)


@pytest.fixture
def _working_dir(tmp_path, monkeypatch):
    """Set cwd to tmp_path and copy the Jinja2 template so FujiRecipe can find it."""
    project_root = Path(__file__).resolve().parent.parent
    template_src = project_root / "templates"
    template_dst = tmp_path / "templates"
    shutil.copytree(template_src, template_dst)
    monkeypatch.chdir(tmp_path)


@pytest.mark.usefixtures("_recipe_html_tags", "_working_dir")
def test_recipe_save_outputs(tmp_path):
    """
    Create a FujiRecipe, run recipe.save(), and verify the FP1 file is written
    under the expected directory structure.
    """
    recipe = FujiRecipe(
        sensor=FujiSensor.X_TRANS_IV,
        link=FujiRecipeLink(
            name="Test Recipe",
            url="https://fujixweekly.com/2024/03/15/test-recipe/",
        ),
    )

    success = recipe.save()
    assert success, f"Recipe.save() failed for {recipe.link.name}"

    generated_fp1_file = tmp_path / recipe.output_file_path
    assert generated_fp1_file.exists(), f"Generated FP1 file not found: {generated_fp1_file}"

    content = generated_fp1_file.read_text(encoding="utf-8")
    assert "<?xml" in content
    assert "ConversionProfile" in content
    assert "Test Recipe" in content
