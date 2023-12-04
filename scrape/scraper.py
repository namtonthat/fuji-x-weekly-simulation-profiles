import logging
import os
import re
from collections.abc import Generator
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from jinja2 import Environment, FileSystemLoader, Template
from requests.exceptions import RequestException

from scrape.models import FilmSimulation, FujiSensor, FujiSimulationProfile, KeyStandardizer, clean_camera_profile_name

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger(__name__)


def fill_xml_template(profile_dict: dict, template: str) -> str:
    """
    Fills an XML template with values from a profile dictionary.

    Args:
    profile_dict (dict): Dictionary containing profile attributes and values.
    template (str): XML template string to be filled with values.

    Returns:
    str: XML template filled with profile values.
    """
    # logger.info('Filling template with profile_dict: "%s"', profile_dict)
    for attribute_name, attr_value in profile_dict.items():
        if attr_value is None:
            logger.info(f"Attribute '{attribute_name}' is None, skipping...")
            continue
        xml_tag = FujiSimulationProfile.attribute_to_xml_mapping.get(attribute_name, None)

        if xml_tag:
            template = replace_xml_value(template, xml_tag, attr_value)
        else:
            logging.warning(f"No XML tag mapping found for attribute '{attribute_name}'")

    return template


def replace_xml_value(template: str, attribute_name: str, attribute_value: str | int) -> str:
    """
    Replaces the value of a specific XML tag in a template.

    Args:
    template (str): XML template string.
    attribute_name (str): The name of the XML tag to replace.
    attribute_value (str): The new value to insert into the tag.

    Returns:
    str: Updated XML template with the new value for the specified tag.
    """
    pattern = r"<" + re.escape(attribute_name) + r">(.*?)</" + re.escape(attribute_name) + r">"

    if re.search(pattern, template):
        return re.sub(pattern, f"<{attribute_name}>{attribute_value}</{attribute_name}>", template)
    else:
        logger.warning(f"Error: No XML tag found for attribute '{attribute_name}'")
        return template


def snake_to_camel(name: str) -> str:
    components = name.split("_")
    return "".join(x.title() for x in components)


@dataclass
class FujiSimulationProfileParser:
    tags: list

    @property
    def processed_tags(self) -> list[str]:
        "Return a list of tags with newlines removed and text stripped"

        def flatten_and_process_tags(tags: list[Tag]) -> Generator[str, None, None]:
            for tag in tags:
                # Remove <a> tags but keep their text
                for a in tag.find_all("a"):
                    a.replace_with(a.get_text())

                if tag.find("br"):
                    tag_text = tag.get_text(separator="\n")
                    for line in tag_text.split("\n"):
                        yield line.strip()
                else:
                    yield tag.get_text().strip()

        processed_tags = list(flatten_and_process_tags(self.tags))

        logger.debug("Processed tags: %s", processed_tags)
        return processed_tags

    @property
    def profile_dict(self) -> dict:
        def standardise_key_names(key_string: str) -> str:
            clean_key_name = key_string.lower().replace(" ", "_").replace("&", "and")
            # Special handling for some keys
            special_keys = {
                "color_chrome_effect_blue": "color_chrome_fx_blue",
                "grain": "grain_effect",
                "noise_reduction": "high_iso_nr",
                "sharpening": "sharpness",
            }

            if clean_key_name in special_keys:
                return special_keys[clean_key_name]
            else:
                return clean_key_name

        profile_dict = {}
        for tag in self.processed_tags:
            try:
                key, value = tag.split(": ", 1)
            except ValueError:
                # Sometimes the tag is just the film simulation name
                # e.g. "Classic Chrome"
                standardised_tag = clean_camera_profile_name(tag)
                if standardised_tag in FilmSimulation.__members__:
                    key = "film_simulation"
                    value = standardised_tag
                else:
                    continue

            KeyStandardizer.initialise_parsing_methods()
            clean_key = standardise_key_names(key)
            clean_value = KeyStandardizer.parse_key_and_standardise_value(clean_key, value)
            logger.debug("Parsing key '%s' with value '%s'", clean_key, clean_value)
            profile_dict[clean_key] = clean_value

        return profile_dict

    def create_fuji_profile(self) -> FujiSimulationProfile | None:
        try:
            fuji_profile = FujiSimulationProfile.create_instance(self.profile_dict)
        except TypeError:
            logger.warning(
                "Could not create FujiSimulationProfile instance from %s",
                self.profile_dict,
            )
            return None
        else:
            return fuji_profile


@dataclass
class FujiRecipeLink:
    name: str
    url: str

    recipe_url_pattern: str = r"https?://fujixweekly\.com/\d{4}/\d{2}/\d{2}/.*recipe/$"

    def __post_init__(self):
        self.name = self.clean_name(self.name)

    def is_valid_recipe_link(self) -> bool:
        # Check if the URL is None
        if self.url is None:
            return False

        return bool(re.match(self.recipe_url_pattern, self.url))

    @staticmethod
    def clean_name(name: str) -> str:
        """
        Cleans the name by replacing non-ASCII characters.
        """
        # Encode to ASCII, replace non-ASCII characters with '?', then decode back
        clean_name = name.encode("ascii", "replace").decode("ascii")
        # Replace '?' with a desired character or remove it
        clean_name = clean_name.replace("?", "")
        return clean_name

    def parse_webpage_for_tags(self) -> list:
        logger.info("Parsing URL: %s", self.url)
        page = requests.get(self.url, timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(page.content, "html.parser")
        strong_tags = soup.find_all("strong")
        return strong_tags

    def get_profile(self) -> FujiSimulationProfile | None:
        try:
            tags = self.parse_webpage_for_tags()
            if not tags:
                logger.error("No tags found in the webpage")
            profile_parser_instance = FujiSimulationProfileParser(tags=tags)
            return profile_parser_instance.create_fuji_profile()
        except RequestException:
            logger.exception(f"Error fetching URL {self.url}")
        except Exception:
            logger.exception(f"Error processing profile for {self.url}")


@dataclass
class FujiRecipe:
    sensor: FujiSensor
    link: FujiRecipeLink

    # Defaults
    template_location = "templates/FP1.jinja2"

    @property
    def output_file_path(self) -> str:
        return f"fuji_profiles/{self.sensor.value}/{self.link.name}.FP1"

    @property
    def jinja2_template(self) -> Template:
        "Returns a Jinja2 template object"
        template_dir = os.getcwd()
        file_loader = FileSystemLoader(template_dir)
        env = Environment(loader=file_loader, autoescape=True)
        template = env.get_template(self.template_location)
        return template

    @property
    def filled_template(self) -> str:
        "Returns a filled Jinja2 template as a string"
        initial_filled_template = self.jinja2_template.render(self.link.__dict__)
        filled_template = fill_xml_template(self.as_dict(), initial_filled_template) + "\n"
        return filled_template

    def as_dict(self) -> dict:
        fuji_profile = FujiRecipeLink(name=self.link.name, url=self.link.url).get_profile()
        if isinstance(fuji_profile, FujiSimulationProfile):
            return fuji_profile.to_flat_dict()
        else:
            logger.warning(f"Failed to get profile for {self.link.url}")
            return {}

    def save(self) -> None:
        try:
            fuji_profile = self.as_dict()

            if fuji_profile:
                output = self.filled_template
                # Create the directory if it doesn't exist
                directory_path = os.path.dirname(self.output_file_path)
                os.makedirs(directory_path, exist_ok=True)
                logger.info('Saving recipe "%s"', self.link.name)

                with open(self.output_file_path, "w") as f:
                    f.write(output)
                logger.info(f"Profile saved successfully to {self.output_file_path}")

        except Exception:
            logger.exception(f"Failed to save profile for {self.link.url}")


@dataclass
class FujiRecipes:
    sensor: FujiSensor  # Assuming FujiSensor is defined somewhere
    base_sensor_url: str
    related_recipes: list[FujiRecipe]  # Assuming FujiRecipe is defined somewhere

    @staticmethod
    def soup_representation(url: str) -> BeautifulSoup:
        page = requests.get(url, timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(page.content, "html.parser")
        return soup

    @classmethod
    def max_recipes(cls, sensor_url: str) -> int:
        soup = cls.soup_representation(sensor_url)
        recipe_links = soup.find_all("a", href=re.compile(FujiRecipeLink.recipe_url_pattern))
        return len(recipe_links)

    @classmethod
    def fetch_recipes(cls, sensor: FujiSensor, sensor_url: str) -> list[FujiRecipe]:
        soup = cls.soup_representation(sensor_url)
        all_links_for_sensor = soup.find_all("a")

        related_recipes = []
        collect_recipes = False

        for link in all_links_for_sensor:
            link_object = FujiRecipeLink(url=link.get("href"), name=link.text)
            href = link_object.url
            if href == "#content":
                collect_recipes = True  # Start collecting recipes
                continue
            elif "twitter" in href:
                break  # Stop collecting recipes

            if collect_recipes and link_object.is_valid_recipe_link():
                sensor_recipe = FujiRecipe(sensor=sensor, link=link_object)
                if sensor_recipe in related_recipes:
                    logger.warning(f"Recipe {sensor_recipe.link.name} already fetched.")
                else:
                    related_recipes.append(sensor_recipe)

        # Validation Step
        if len(related_recipes) > cls.max_recipes(sensor_url):
            logger.warning(f"More recipes fetched ({len(related_recipes)}) than the expected maximum.")
        return related_recipes


GLOBAL_SENSOR_LIST = {
    # FujiSensor.BAYER: "https://fujixweekly.com/fujifilm-bayer-recipes/",
    # FujiSensor.EXR_CMOS: "https://fujixweekly.com/fujifilm-exr-cmos-film-simulation-recipes/",
    # FujiSensor.GFX: "https://fujixweekly.com/fujifilm-gfx-recipes/",
    # FujiSensor.X_TRANS_I: "https://fujixweekly.com/fujifilm-x-trans-i-recipes/",
    # FujiSensor.X_TRANS_II: "https://fujixweekly.com/fujifilm-x-trans-ii-recipes/",
    FujiSensor.X_TRANS_III: "https://fujixweekly.com/fujifilm-x-trans-iii-recipes/",
    # FujiSensor.X_TRANS_IV: "https://fujixweekly.com/fujifilm-x-trans-iv-recipes/",
    FujiSensor.X_TRANS_V: "https://fujixweekly.com/fujifilm-x-trans-v-recipes/",
}

TIMEOUT_SECONDS = 10


if __name__ == "__main__":
    sensor_recipes: dict = {}
    for sensor, sensor_url in GLOBAL_SENSOR_LIST.items():
        logger.info("Pulling recipes for sensor %s", sensor)
        related_recipes = FujiRecipes.fetch_recipes(sensor, sensor_url)

        for recipe in related_recipes:
            # if recipe.link.name == "1976 Kodak":
            recipe.save()
