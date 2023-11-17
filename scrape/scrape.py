import logging
import re
from dataclasses import dataclass, fields
from enum import Enum
from typing import ClassVar

import requests
from bs4 import BeautifulSoup
from lxml import etree


class FujiEffect(Enum):
    STRONG = "STRONG"
    WEAK = "WEAK"
    OFF = "OFF"


class DynamicRange(Enum):
    DR400 = 400
    DR200 = 200
    DR100 = 100


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


class GrainEffectSize(Enum):
    LARGE = "LARGE"
    SMALL = "SMALL"


@dataclass
class GrainEffect(XMLRepresentable):
    grain_effect: FujiEffect
    grain_effect_size: GrainEffectSize


class WhiteBalanceSetting(Enum):
    AUTO = "Auto"
    AUTO_AMBIENCE = "Auto_Ambience"
    AUTO_WHITE = "Auto_White"
    DAYLIGHT = "Daylight"
    FLIGHT1 = "FLight1"
    FLIGHT2 = "FLight2"
    FLIGHT3 = "FLight3"
    TEMPERATURE = "Temperature"


@dataclass
class WhiteBalance(XMLRepresentable):
    setting: WhiteBalanceSetting
    red: int
    blue: int
    color_temp: int = None


class FilmSimulation(Enum):
    ACROS = "Acros"
    ACROS_G = "AcrosG"
    ACROS_R = "AcrosR"
    ACROS_Y = "AcrosYe"
    ASTIA = "Astia"
    CLASSIC_CHROME = "Classic"
    CLASSIC_NEG = "ClassicNEGA"
    ETERNA = "Eterna"
    ETERNA_BLEACH_BYPASS = "BleachBypass"  # noqa: S105
    MONOCHROME = "BW"
    MONOCHROME_G = "BG"
    MONOCHROME_R = "BR"
    MONOCHROME_Y = "BYe"
    NOSTALGIC_NEG = "NostalgicNEGA"
    PRO_NEG_HI = "NEGAhi"
    PRO_NEG_STD = "NEGAStd"
    PROVIA = "Provia"
    SEPIA = "Sepia"
    VELVIA = "Velvia"


class FujiSensor(Enum):
    X_TRANS_I = "X-Trans-I"
    X_TRANS_II = "X-Trans-II"
    X_TRANS_III = "X-Trans-III"
    X_TRANS_IV = "X-Trans-IV"
    X_TRANS_V = "X-Trans-V"


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
        "grain_effect": "GrainEffect",
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
    }


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
        elif key == "film_simulation":
            converted_value = FilmSimulation[standardised_value].value
        elif key == "white_balance":
            # defaults
            temp_match = None
            color_temp = None

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

            return WhiteBalance(setting=setting, red=red, blue=blue, color_temp=color_temp if temp_match else None)

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
            converted_value = value
        return converted_value


@dataclass
class FujiXWeeklyUrlParser:
    url: str
    simluation_name: str
    sensor_type: FujiSensor

    def parse_webpage_for_strong_tags(self) -> list:
        page = requests.get(self.url, timeout=TIMEOUT_SECONDS)
        soup = BeautifulSoup(page.content, "html.parser")
        strong_tags = soup.find_all("strong")
        return strong_tags

    def create_fuji_profile(self) -> FujiSimulationProfile:
        strong_tags = self.parse_webpage_for_strong_tags()
        fuji_profile = FujiSimulationProfileParser(strong_tags).parse()
        return fuji_profile


# Function to fill the XML template
def fill_xml_template(profile, template):
    for attribute_name in fields(profile.__class__):
        attr_value = getattr(profile, attribute_name.name)
        xml_tag = profile.attribute_to_xml_mapping.get(attribute_name.name, None)

        if xml_tag:
            template = replace_xml_value(template, xml_tag, attr_value)
        else:
            print(f"Error: No XML tag mapping found for attribute '{attribute_name.name}'")

    return print(template)


# Function to replace XML value
def replace_xml_value(template, attribute_name, attribute_value):
    # Regex pattern to find the corresponding XML tag
    pattern = r"<" + re.escape(attribute_name) + r">(.*?)</" + re.escape(attribute_name) + r">"

    # Check if the pattern is found in the template
    if re.search(pattern, template):
        # Replace the found tag with the attribute value
        return re.sub(pattern, f"<{attribute_name}>{attribute_value}</{attribute_name}>", template)
    else:
        # Log an error if the tag is not found
        logging.warning(f"Error: No XML tag found for attribute '{attribute_name}'")
        return template


# Global
URL_LINK_HEADER = "Nostalgia Negative"
FUJI_WEEKLY_URL = (
    "https://fujixweekly.com/2022/11/22/nostalgia-negative-my-first-fujifilm-x-t5-x-trans-v-film-simulation-recipe/"
)
TIMEOUT_SECONDS = 10


if __name__ == "__main__":
    fuji_profile = FujiXWeeklyUrlParser(
        url=FUJI_WEEKLY_URL, simluation_name=URL_LINK_HEADER, sensor_type=FujiSensor.X_TRANS_V
    ).create_fuji_profile()

    with open("fuji_template.jinja2") as f:
        fuji_template = f.read()

    fill_xml_template(fuji_profile, fuji_template)
