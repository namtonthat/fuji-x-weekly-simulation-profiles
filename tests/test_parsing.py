from bs4 import BeautifulSoup

from scrape.models import FujiSensor, KeyStandardizer, resolve_conditional_value
from scrape.scraper import (
    FujiRecipes,
    FujiSimulationProfileParser,
    flatten_and_process_tags,
)


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
    flatten_and_process_tags does NOT replace \xa0; the replacement happens
    in FujiSimulationProfileParser.processed_tags.
    """
    html = "<div><strong>Test:\xa0Value</strong></div>"
    soup = BeautifulSoup(html, "html.parser")
    tags = soup.select("div > strong")
    parser = FujiSimulationProfileParser(tags=tags)
    result = parser.processed_tags
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
        <a href="https://fujixweekly.com/2024/07/15/another-sample-recipe/" >Sample Recipe 2</a>
      </body>
    </html>
    """
    return BeautifulSoup(html, "html.parser")


def test_fuji_simulation_profile_parser_monkeypatch(monkeypatch):
    """
    Test FujiSimulationProfileParser by monkeypatching the network call.
    This avoids actual network requests.
    """
    monkeypatch.setattr(FujiRecipes, "soup_representation", staticmethod(fake_soup_representation))

    # Use a dummy sensor and URL.
    dummy_sensor = FujiSensor.X_TRANS_V  # Replace with an actual enum member if needed.
    dummy_url = "https://fakex.com/sensor"

    # Call fetch_recipes, which internally uses soup_representation.
    recipes = FujiRecipes.fetch_recipes(dummy_sensor, dummy_url)

    # Check that recipes were created as expected.
    assert len(recipes) == 2
    assert recipes[0].link.url == "https://fujixweekly.com/2024/07/15/sample-recipe/"
    assert recipes[1].link.url == "https://fujixweekly.com/2024/07/15/another-sample-recipe/"


# --- Tests for KeyStandardizer.exposure_compensation ---
def test_exposure_compensation_no_match_returns_zero():
    """
    Test that exposure_compensation returns 0.0 when given a string
    with no numeric exposure value.
    """
    result = KeyStandardizer.exposure_compensation("no exposure here")
    assert result == 0.0


def test_exposure_compensation_normal_value():
    """
    Test that exposure_compensation correctly parses a normal fractional value.
    """
    result = KeyStandardizer.exposure_compensation("+1/3")
    assert result == 0.33  # convert_to_float rounds to 2 decimal places
