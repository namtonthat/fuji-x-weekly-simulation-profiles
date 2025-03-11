import pytest
from bs4 import BeautifulSoup

from ..scrape.models import FujiSensor
from ..scrape.scraper import (
    FujiRecipes,
    flatten_and_process_tags,
)


# --- FIXED Fixture: Only select top-level <strong> tags ---
@pytest.fixture
def sample_html():
    # Note: Ensure the outer container wraps all the top-level <strong> tags.
    return """
    <div>
        <strong>Film Simulation: Eterna Bleach Bypass</strong><br/>
        <strong>Dynamic Range: DR400</strong><br/>
        <strong>Grain Effect: Strong, Large</strong><br/>
        <strong>Color Chrome Effect: Strong</strong><br/>
        <strong>Color Chrome FX Blue: Off (X-Trans V); Weak (X-Trans IV)</strong><br/>
        <strong>
            White Balance: <strong>Fluorescent 1</strong>, -2 Red &amp; -4 Blue
        </strong><br/>
        <strong>Highlight: -2</strong><br/>
        <strong>Shadow: -1</strong><br/>
        <strong>Color: +2</strong><br/>
        <strong>Sharpness: -1</strong><br/>
        <strong>Fluorescent 1</strong><br/>
        <strong>High ISO NR: -4</strong><br/>
        <strong>Clarity: -2</strong><br/>
        <strong>ISO: Auto, up to ISO 6400</strong><br/>
        <strong>Exposure Compensation: +1/3 to +1 (typically)</strong><br/>
        <strong>Fujifilm X-T5</strong><br/>
        <strong>Amazon</strong><br/>
        <strong>B&amp;H</strong><br/>
        <strong>Moment</strong><br/>
        <strong>Wex</strong><br/>
        <strong>Nuzira</strong><br/>
        <strong>Fujifilm X-T5</strong><br/>
        <strong>Amazon</strong><br/>
        <strong>,</strong><br/>
        <strong>B&amp;H</strong><br/>
        <strong>Moment</strong><br/>
        <strong>Wex</strong><br/>
        <strong>Nuzira</strong>
    </div>
    """


@pytest.fixture
def strong_tags(sample_html):
    soup = BeautifulSoup(sample_html, "html.parser")
    # Only select top-level <strong> tags that are direct children of the <div>
    return soup.select("div > strong")


# --- Tests for flatten_and_process_tags ---


def test_flatten_and_process_tags(strong_tags):
    """
    Test that flatten_and_process_tags correctly processes the HTML and
    merges multi-line key/value entries as expected.
    """
    result = list(flatten_and_process_tags(strong_tags))
    expected = [
        "Film Simulation: Eterna Bleach Bypass",
        "Dynamic Range: DR400",
        "Grain Effect: Strong, Large",
        "Color Chrome Effect: Strong",
        "Color Chrome FX Blue: Off (X-Trans V); Weak (X-Trans IV)",
        "White Balance: Fluorescent 1 , -2 Red & -4 Blue",
        "Highlight: -2",
        "Shadow: -1",
        "Color: +2",
        "Sharpness: -1",
        "Fluorescent 1",
        "High ISO NR: -4",
        "Clarity: -2",
        "ISO: Auto, up to ISO 6400",
        "Exposure Compensation: +1/3 to +1 (typically)",
        "Fujifilm X-T5",
        "Amazon",
        "B&H",
        "Moment",
        "Wex",
        "Nuzira",
        "Fujifilm X-T5",
        "Amazon",
        ",",
        "B&H",
        "Moment",
        "Wex",
        "Nuzira",
    ]
    assert result == expected


def test_nbsp_replacement():
    """
    Test that non-breaking spaces (\xa0) are replaced with normal spaces.
    """
    html = "<div><strong>Test:\xa0Value</strong></div>"
    soup = BeautifulSoup(html, "html.parser")
    # Use a selector that gets the intended tag.
    tags = soup.select("div > strong")
    result = list(flatten_and_process_tags(tags))
    expected = ["Test: Value"]
    assert result == expected


# --- Monkeypatch Test for Scraper Network Call ---
#
# Assuming that in your module, there is a module-level function named
# `soup_representation` used by FujiSimulationProfileParser.fetch_recipes,
# we patch that function. If your class should have this method, consider
# adding it to the class.
def fake_soup_representation(url: str):
    from bs4 import BeautifulSoup

    # Return a fake soup that simulates a scraped page.
    html = """
    <html>
      <body>
        <a href="#content">Start</a>
        <a href="https://fujixweekly.com/2024/07/15/sample-recipe/" >Sample Recipe</a>
        <a href="https://fujixweekly.com/2024/07/15/sample-recipe2/" >Sample Recipe 2</a>
      </body>
    </html>
    """
    return BeautifulSoup(html, "html.parser")


def test_fuji_simulation_profile_parser_monkeypatch(monkeypatch):
    """
    Test FujiSimulationProfileParser by monkeypatching the network call.
    This avoids actual network requests.
    """
    # Adjust the monkeypatch target according to your implementation.
    # If FujiSimulationProfileParser does not have a soup_representation method,
    # patch the module-level function instead.
    from ..scrape import scraper  # Adjust the import to your module structure.

    monkeypatch.setattr(scraper, "soup_representation", fake_soup_representation)

    # Use a dummy sensor and URL.
    dummy_sensor = FujiSensor.X_TRANS_V  # Replace with an actual enum member if needed.
    dummy_url = "https://fakex.com/sensor"

    # Call fetch_recipes, which internally uses soup_representation.
    recipes = FujiRecipes.fetch_recipes(dummy_sensor, dummy_url)

    # Check that recipes were created as expected.
    assert len(recipes) == 2
    assert recipes[0].link.url == "https://fujixweekly.com/2024/07/15/sample-recipe/"
    assert recipes[1].link.url == "https://fujixweekly.com/2024/07/15/sample-recipe2/"
