#
# Test the models within scrape
#

from ..scrape.models import FujiSensor
from ..scrape.scraper import FujiRecipe, FujiRecipeLink, FujiSimulationProfileParser

PARSED_TAGS_FILE = "source/parsed_tags_with_xa0.csv"


def test_FujiSimulationProfileParser(tags):
    FujiSimulationProfileParser(tags)

    pass


if __name__ == "__main__":
    sensor_recipes = {
        FujiSensor.X_TRANS_V: [
            FujiRecipe(
                sensor=FujiSensor.X_TRANS_V,
                link=FujiRecipeLink(
                    name="Easy Reala Ace",
                    url="https://fujixweekly.com/2024/06/20/easy-reala-ace-fujifilm-x100vi-x-trans-v-film-simulation-recipe/",
                ),
            )
        ],
    }
    with open(PARSED_TAGS_FILE) as f:
        parsed_tags = f.read()

    test_FujiSimulationProfileParser(parsed_tags)
