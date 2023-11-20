import logging
import os
import re
from collections.abc import Callable, Generator
from dataclasses import dataclass
from typing import Any, ClassVar

import requests
from bs4 import BeautifulSoup
from bs4.element import Tag
from jinja2 import Environment, FileSystemLoader, Template
from requests.exceptions import RequestException

from .models import (
    DynamicRange,
    FilmSimulation,
    FujiEffect,
    FujiSensor,
    FujiSimulationProfile,
    GrainEffect,
    GrainEffectSize,
    MonochomaticColor,
    WhiteBalance,
    WhiteBalanceBlueRed,
    WhiteBalanceSetting,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Example usage
logger = logging.getLogger(__name__)


def convert_to_float(value_str: str) -> float:
    """
    Converts a string to a float. Handles both regular numbers and fractions.
    Rounds the result to two decimal places.

    Args:
    value_str (str): The string to convert, can be a number or a fraction (e.g., '1/2').

    Returns:
    float: Rounded float value of the input string.
    """
    if "/" in value_str:  # Fraction handling
        numerator, denominator = map(float, value_str.split("/"))
        return round(numerator / denominator, 2)
    else:
        return round(float(value_str), 2)


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

        # logger.info("Processed tags: %s", processed_tags)
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

            profile_dict[clean_key] = clean_value

        return profile_dict

    def create_fuji_profile(self) -> FujiSimulationProfile | None:
        try:
            fuji_profile = FujiSimulationProfile.create_instance(self.profile_dict)
        except TypeError:
            logger.warning("Could not create FujiSimulationProfile instance from %s", self.profile_dict)
            return None
        else:
            return fuji_profile


def clean_camera_profile_name(camera_tag: str) -> str:
    camera_profile = camera_tag.replace(" ", "_").replace(".", "").split("/")[0].upper()

    alternative_camera_profile_names = {"CLASSIC_NEGATIVE": "CLASSIC_NEG"}

    if camera_profile in alternative_camera_profile_names:
        camera_profile = alternative_camera_profile_names[camera_profile]

    return camera_profile


@dataclass
class KeyStandardizer:
    _parsing_methods: ClassVar[dict[str, Callable[..., Any]]] = {}

    @staticmethod
    def clean_string(text_string: str) -> str:
        """
        Utility method to clean and standardize a string.
        """
        return text_string.replace(" ", "_").replace(",", "").replace("-", "").upper()

    @staticmethod
    def parse_key_and_standardise_value(key: str, value: str) -> Any:
        """
        Standardizes the given key and value based on predefined parsing methods.

        Args:
            key (str): The key to be parsed.
            value (str): The value to be standardized.

        Returns:
            Standardized value based on the key.
        """
        standardised_value = KeyStandardizer.clean_string(value)

        # Use custom parsing method if available for the key
        parsing_method = KeyStandardizer._parsing_methods.get(key)
        if parsing_method:
            return parsing_method(standardised_value)

        return standardised_value

    @staticmethod
    def color_chrome_effect(value: str) -> str:
        return FujiEffect[value].value

    @staticmethod
    def dynamic_range(value: str) -> str:
        dynamic_range_map = {
            "DRANGE_PRIORITY_(DRP)_AUTO": "DRAUTO",
        }
        if value in dynamic_range_map:
            value = dynamic_range_map[value]

        try:
            dynamic_range_value = DynamicRange[value].value
        except KeyError:
            logger.warning("Could not parse dynamic range, setting to AUTO")
            dynamic_range_value = DynamicRange.DRAUTO.value

        return dynamic_range_value

    @staticmethod
    def exposure_compensation(value: str) -> float:
        exposure_regex = r"[+-]?\d+(?:/\d+)?"
        matches = re.findall(exposure_regex, value)
        return convert_to_float(matches[0])

    @staticmethod
    def film_simluation(value: str) -> str:
        camera_profile_value = clean_camera_profile_name(value)
        return FilmSimulation[camera_profile_value].value

    @staticmethod
    def grain_effect(value: str) -> GrainEffect:
        grain_effect_values = [item.strip() for item in value.split("_")]

        try:
            grain_effect = FujiEffect[grain_effect_values[0]]  # Convert string to FujiEffect enum member
            grain_effect_size = GrainEffectSize[grain_effect_values[1]] if len(grain_effect_values) > 1 else None  # Convert string to GrainEffectSize enum member or None

            return GrainEffect(grain_effect=grain_effect, grain_effect_size=grain_effect_size)
        except (IndexError, KeyError):
            logger.warning("Could not parse grain effect, setting to FujiEffect.OFF")
            return GrainEffect(grain_effect=FujiEffect.OFF)  # Use FujiEffect.OFF directly without .value

    @staticmethod
    def white_balance(value: str) -> WhiteBalance:
        def get_color_temperature(value: str) -> str:
            """
            Extracts the color temperature from the string
            Defaults to 0K if no color temperature is found
            """
            temp_match = re.search(r"(\d+)K", value)
            color_temp = int(temp_match.group(1)) if temp_match else None
            color_temp_value = f"{color_temp}K" if color_temp else "0K"

            return color_temp_value

        def get_white_balance_setting(value: str) -> tuple[WhiteBalanceSetting, str]:
            color_temp = get_color_temperature(value)

            # Extract the temperature or setting
            if "K" in value:
                setting = WhiteBalanceSetting.TEMPERATURE
            elif "AWB" in value:
                setting = WhiteBalanceSetting.AUTO
            else:
                fluorescent_match = re.search(r"FLUORESCENT_(\d)", value)
                if fluorescent_match:
                    # Check if it's a fluorescent setting
                    special_mappings = {
                        "FLUORESCENT_1": WhiteBalanceSetting.FLIGHT1,
                        "FLUORESCENT_2": WhiteBalanceSetting.FLIGHT2,
                        "FLUORESCENT_3": WhiteBalanceSetting.FLIGHT3,
                    }
                    flight_number = fluorescent_match.group(1)
                    setting = special_mappings[f"FLUORESCENT_{flight_number}"]
                else:
                    setting_match = re.match(r"([^_]+)", value)
                    setting_name = setting_match.group(1).upper() if setting_match else "AUTO"
                    setting = WhiteBalanceSetting[setting_name]

            return setting, color_temp

        def get_blue_red_numeric_value(value: str, blue_or_red: WhiteBalanceBlueRed) -> int:
            "Extracts the blue or red (+-) integer value from the string"
            numeric_red_blue_regex = {
                WhiteBalanceBlueRed.BLUE: r"([+-]?\d+)_BLUE",
                WhiteBalanceBlueRed.RED: r"([+-]?\d+)_RED",
            }

            related_regex = numeric_red_blue_regex[blue_or_red]
            match = re.search(related_regex, value)
            return int(match.group(1)) if match else 0

        blue = get_blue_red_numeric_value(value, WhiteBalanceBlueRed.BLUE)
        red = get_blue_red_numeric_value(value, WhiteBalanceBlueRed.RED)
        # Defaults
        setting, color_temp = get_white_balance_setting(value)

        return WhiteBalance(setting=setting, red=red, blue=blue, color_temp=color_temp)

    @staticmethod
    def numerical_values(value: str) -> int:
        int_regex = r"([+-]?\d+)"
        match = re.search(int_regex, value)
        if match:
            converted_value = int(match.group(0))
        else:
            logger.warning("Could not convert %s to int, setting to 0", value)
            converted_value = 0

        return converted_value

    @staticmethod
    def monochromatic_color(value: str) -> MonochomaticColor:
        """
        Extracts the monochromatic color from the string
        Example:
            value: Monochromatic Color: 0 WC & 0 MG
        Return:
            0
        """
        monochromatic_color_regex = r"(\d+)_WC_&_(\d+)_MG"
        match = re.search(monochromatic_color_regex, value)

        if match:
            warm_cool = int(match.group(1))
            magenta_green = int(match.group(2))
        else:
            logger.warning("Could not convert %s to MonochromaticColor, setting to 0", value)
            warm_cool = 0
            magenta_green = 0

        return MonochomaticColor(
            warm_cool=warm_cool,
            magenta_green=magenta_green,
        )

    @classmethod
    def initialise_parsing_methods(cls) -> None:
        cls._parsing_methods = {
            "color_chrome_effect": KeyStandardizer.color_chrome_effect,
            "dynamic_range": KeyStandardizer.dynamic_range,
            "exposure_compensation": KeyStandardizer.exposure_compensation,
            "film_simulation": KeyStandardizer.film_simluation,
            "grain_effect": KeyStandardizer.grain_effect,
            "high_iso_nr": KeyStandardizer.numerical_values,
            "highlight": KeyStandardizer.numerical_values,
            "shadow": KeyStandardizer.numerical_values,
            "sharpness": KeyStandardizer.numerical_values,
            "white_balance": KeyStandardizer.white_balance,
            "monochromatic_color": KeyStandardizer.monochromatic_color,
        }


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

        return bool(re.match(FujiRecipeLink.recipe_url_pattern, self.url))

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

    def as_dict(self) -> dict:
        fuji_profile = FujiRecipeLink(name=self.link.name, url=self.link.url).get_profile()
        if isinstance(fuji_profile, FujiSimulationProfile):
            return fuji_profile.to_flat_dict()
        else:
            logger.warning(f"Failed to get profile for {self.link.url}")
            return {}

    def render_template(self) -> Template:
        template_dir = os.getcwd()
        file_loader = FileSystemLoader(template_dir)
        env = Environment(loader=file_loader, autoescape=True)
        template = env.get_template(self.template_location)

        return template

    def save(self) -> None:
        try:
            fuji_profile = self.as_dict()

            if fuji_profile:
                template = self.render_template()
                initial_filled_template = template.render(self.link.__dict__)
                output = fill_xml_template(fuji_profile, initial_filled_template)
                # Ensure output ends with a newline
                if not output.endswith("\n"):
                    output += "\n"

                # Create the directory if it doesn't exist
                directory_path = os.path.dirname(self.output_file_path)
                os.makedirs(directory_path, exist_ok=True)
                logger.info('Saving recipe "%s"', recipe.link.name)

                with open(self.output_file_path, "w") as f:
                    f.write(output)
                logger.info(f"Profile saved successfully to {self.output_file_path}")
            else:
                logger.warning("No profile exists for self.link.url. Skipping...")

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
    # FujiSensor.X_TRANS_III: "https://fujixweekly.com/fujifilm-x-trans-iii-recipes/",
    FujiSensor.X_TRANS_IV: "https://fujixweekly.com/fujifilm-x-trans-iv-recipes/",
    FujiSensor.X_TRANS_V: "https://fujixweekly.com/fujifilm-x-trans-v-recipes/",
}

TIMEOUT_SECONDS = 10


if __name__ == "__main__":
    sensor_recipes: dict = {}
    for sensor, sensor_url in GLOBAL_SENSOR_LIST.items():
        logger.info("Pulling recipes for sensor %s", sensor)
        related_recipes = FujiRecipes.fetch_recipes(sensor, sensor_url)

        for recipe in related_recipes:
            recipe.save()
