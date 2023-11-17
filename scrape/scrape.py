import logging
import os
import re
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import ClassVar

import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from lxml import etree
from models import DynamicRange, FilmSimulation, FujiEffect, FujiSensor, GrainEffectSize, WhiteBalanceSetting


def convert_to_float(value_str):
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


def fill_xml_template(profile_dict, template):
    """
    Fills an XML template with values from a profile dictionary.

    Args:
    profile_dict (dict): Dictionary containing profile attributes and values.
    template (str): XML template string to be filled with values.

    Returns:
    str: XML template filled with profile values.
    """
    for attribute_name, attr_value in profile_dict.items():
        xml_tag = FujiSimulationProfile.attribute_to_xml_mapping.get(attribute_name, None)

        if xml_tag:
            template = replace_xml_value(template, xml_tag, attr_value)
        else:
            print(f"Error: No XML tag mapping found for attribute '{attribute_name}'")

    return template


def replace_xml_value(template, attribute_name, attribute_value):
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
        logging.warning(f"Error: No XML tag found for attribute '{attribute_name}'")
        return template


class XMLRepresentable:
    def snake_to_camel(self, name):
        components = name.split("_")
        return "".join(x.title() for x in components)

    def as_xml(self):
        """Convert the dataclass attributes to XML string with camelCase attribute names."""
        elements = []
        for field in fields(self):
            value = getattr(self, field.name)
            # Ensure the value has a .value attribute (common in Enums)
            if hasattr(value, "value"):
                value = value.value

            camel_case_name = self.snake_to_camel(field.name)
            element = etree.Element(camel_case_name)
            element.text = str(value)
            elements.append(element)
        return "".join(etree.tostring(e, pretty_print=True, encoding="unicode") for e in elements)


@dataclass
class GrainEffect(XMLRepresentable):
    grain_effect: FujiEffect
    grain_effect_size: GrainEffectSize


@dataclass
class WhiteBalance(XMLRepresentable):
    setting: WhiteBalanceSetting
    red: int
    blue: int
    color_temp: str


@dataclass
class FujiSimulationProfile:
    film_simulation: str
    grain_effect: GrainEffect
    color_chrome_effect: FujiEffect
    color_chrome_fx_blue: FujiEffect
    white_balance: WhiteBalance
    dynamic_range: DynamicRange
    highlight: int
    shadow: int
    color: int
    sharpness: int
    high_iso_nr: int
    clarity: int
    iso: str
    exposure_compensation: float

    # Mapping between FujiSimulationProfile attributes and XML tags
    attribute_to_xml_mapping: ClassVar[dict] = {
        "film_simulation": "FilmSimulation",
        "grain_effect_grain_effect": "GrainEffect",
        "grain_effect_grain_effect_size": "GrainEffectSize",
        "color_chrome_effect": "ChromeEffect",
        "color_chrome_fx_blue": "ColorChromeBlue",
        "white_balance": "WhiteBalance",
        "dynamic_range": "WideDRange",
        "highlight": "HighlightTone",
        "shadow": "ShadowTone",
        "color": "Color",
        "sharpness": "Sharpness",
        "high_iso_nr": "NoisReduction",
        "clarity": "Clarity",
        "exposure_compensation": "ExposureBias",
        "white_balance_setting": "WhiteBalance",
        "white_balance_red": "WBShiftR",
        "white_balance_blue": "WBShiftB",
        "white_balance_color_temp": "WBColorTemp",
    }

    def to_flat_dict(self):
        flat_dict = vars(self).copy()

        for field in fields(self):
            field_value = getattr(self, field.name)

            # Check if the field is a dataclass instance and flatten it
            if is_dataclass(field_value):
                for nested_field in fields(field_value):
                    nested_field_value = getattr(field_value, nested_field.name)

                    # Special handling for enum fields
                    if isinstance(nested_field_value, Enum):
                        nested_field_value = nested_field_value.value

                    flat_dict[f"{field.name}_{nested_field.name}"] = nested_field_value

                # Remove the original nested dataclass field
                del flat_dict[field.name]

        return flat_dict


@dataclass
class FujiSimulationProfileParser:
    strong_tags: list

    def parse(self):
        def flatten_and_process_tags(tags):
            for tag in tags:
                if tag.find("br"):
                    tag_text = tag.get_text(separator="\n")
                    for line in tag_text.split("\n"):
                        yield line.strip()
                else:
                    yield tag.get_text().strip()

        filtered_tags = [tag for tag in self.strong_tags if not tag.find("a")]
        processed_tags = list(flatten_and_process_tags(filtered_tags))

        profile_dict = {}
        for tag in processed_tags:
            key, value = tag.split(": ", 1)
            key = key.lower().replace(" ", "_").replace("&", "and")
            value = value.lower()
            profile_dict[key] = self.parse_and_convert(key, value)

        return FujiSimulationProfile(**profile_dict)

    @staticmethod
    def parse_and_convert(key, value):
        def clean_string(text_string):
            return text_string.replace(" ", "_").replace(",", "").upper()

        # Custom conversion logic based on the key
        standardised_value = clean_string(value)
        # For enum fields, map them appropriately
        if key in ["color_chrome_effect", "color_chrome_fx_blue"]:
            converted_value = FujiEffect[standardised_value].value
        elif key == "dynamic_range":
            converted_value = DynamicRange[standardised_value].value
        elif key == "exposure_compensation":
            exposure_regex = r"[+-]?\d+(?:/\d+)?"
            matches = re.findall(exposure_regex, standardised_value)
            converted_value = convert_to_float(matches[0])
        elif key == "film_simulation":
            converted_value = FilmSimulation[standardised_value].value
        elif key == "white_balance":
            # Defaults
            temp_match = None

            # Extract the temperature or setting
            if "K" in standardised_value:
                temp_match = re.search(r"(\d+)K", standardised_value)
                color_temp = int(temp_match.group(1)) if temp_match else None
                setting = WhiteBalanceSetting.TEMPERATURE
            else:
                setting_match = re.match(r"([^_]+)", standardised_value)
                setting_name = setting_match.group(1).upper() if setting_match else "AUTO"
                setting = WhiteBalanceSetting[setting_name]

            # Extract red and blue adjustments
            red_regex = r"([+-]?\d+)_RED"
            blue_regex = r"([+-]?\d+)_BLUE"
            red_match = re.search(red_regex, standardised_value)
            red = int(red_match.group(1)) if red_match else 0

            blue_match = re.search(blue_regex, standardised_value)
            blue = int(blue_match.group(1)) if blue_match else 0

            return WhiteBalance(
                setting=setting, red=red, blue=blue, color_temp=f"{color_temp}K" if temp_match else "0K"
            )

        elif key == "grain_effect":
            grain_effect_values = [item.strip() for item in standardised_value.split("_")]

            # Values
            grain_effect = grain_effect_values[0]
            grain_effect_size = grain_effect_values[1]

            # Convert to enum
            converted_value = GrainEffect(
                grain_effect=FujiEffect[grain_effect].value, grain_effect_size=GrainEffectSize[grain_effect_size].value
            )

        elif key in ["highlight", "shadow", "color", "sharpness", "high_iso_nr", "clarity"]:
            converted_value = int(value)
        else:
            converted_value = standardised_value
        return converted_value


@dataclass
class FujiXWeeklyUrlParser:
    url: str

    def parse_webpage_for_strong_tags(self) -> list:
        page = requests.get(self.url, timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(page.content, "html.parser")
        strong_tags = soup.find_all("strong")
        return strong_tags

    def get_profile(self) -> FujiSimulationProfile:
        strong_tags = self.parse_webpage_for_strong_tags()
        fuji_profile = FujiSimulationProfileParser(strong_tags).parse()
        return fuji_profile


@dataclass
class FujiTemplateData:
    fuji_x_weekly_url: str
    film_simulation_name: str


@dataclass
class FujiRecipe:
    sensor: FujiSensor
    recipe_url: str
    film_simulation_name: str

    # Defaults
    template_location = "fuji_template.jinja2"

    @property
    def output_file_path(self) -> str:
        return f"../fuji_profiles/{self.sensor.value}/{self.film_simulation_name}.fp1"

    def fuji_profile_as_dict(self) -> dict:
        fuji_profile = FujiXWeeklyUrlParser(url=self.recipe_url).get_profile()
        return fuji_profile.to_flat_dict()

    def render_template(self):
        template_dir = os.getcwd()
        file_loader = FileSystemLoader(template_dir)
        env = Environment(loader=file_loader, autoescape=True)
        template = env.get_template("fuji_template.jinja2")

        return template

    def set_xml(self):
        template = self.render_template()
        template_data = FujiTemplateData(
            fuji_x_weekly_url=self.recipe_url, film_simulation_name=self.film_simulation_name
        )

        initial_filled_template = template.render(template_data.__dict__)
        filled_xml = fill_xml_template(self.fuji_profile_as_dict(), initial_filled_template)
        return filled_xml

    def save(self):
        output = self.set_xml()
        directory_path = os.path.dirname(self.output_file_path)
        os.makedirs(directory_path, exist_ok=True)

        with open(self.output_file_path, "w") as f:
            f.write(output)


@dataclass
class FujiRecipes:
    sensor: FujiSensor
    base_sensor_url: str
    related_recipes: list[FujiRecipe]

    @classmethod
    def fetch_recipes(cls, sensor, sensor_url):
        page = requests.get(sensor_url, timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(page.content, "html.parser")
        all_links_for_sensor = soup.find_all("a")

        related_recipes = []
        for link in all_links_for_sensor:
            try:
                recipe_link = link["href"]
            except KeyError:
                continue

            recipe_regex = r"https?://fujixweekly\.com/\d{4}/\d{2}/\d{2}/.*/$"

            if re.match(recipe_regex, recipe_link):
                sensor_recipe = FujiRecipe(sensor=sensor, recipe_url=recipe_link, film_simulation_name=link.text)
                related_recipes.append(sensor_recipe)

        return related_recipes


GLOBAL_SENSOR_LIST = {
    FujiSensor.BAYER: "https://fujixweekly.com/fujifilm-bayer-recipes/",
    FujiSensor.EXR_CMOS: "https://fujixweekly.com/fujifilm-exr-cmos-film-simulation-recipes/",
    FujiSensor.GFX: "https://fujixweekly.com/fujifilm-gfx-recipes/",
    FujiSensor.X_TRANS_I: "https://fujixweekly.com/fujifilm-x-trans-i-recipes/",
    FujiSensor.X_TRANS_II: "https://fujixweekly.com/fujifilm-x-trans-ii-recipes/",
    FujiSensor.X_TRANS_III: "https://fujixweekly.com/fujifilm-x-trans-iii-recipes/",
    FujiSensor.X_TRANS_IV: "https://fujixweekly.com/fujifilm-x-trans-iv-recipes/",
    FujiSensor.X_TRANS_V: "https://fujixweekly.com/fujifilm-x-trans-v-recipes/",
}

TIMEOUT_SECONDS = 10


if __name__ == "__main__":
    sensor_recipes = {}
    for sensor, sensor_url in GLOBAL_SENSOR_LIST.items():
        related_recipes = FujiRecipes.fetch_recipes(sensor, sensor_url)
        sensor_recipes[sensor] = FujiRecipes(sensor=sensor, base_sensor_url=sensor_url, related_recipes=related_recipes)
