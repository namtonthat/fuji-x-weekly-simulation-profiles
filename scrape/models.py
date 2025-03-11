# A set of Enums to be used to generate the representative Fujifilm .fp1 camera settings
import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any, ClassVar


class FujiEffect(Enum):
    STRONG = "STRONG"
    WEAK = "WEAK"
    OFF = "OFF"


class DynamicRange(Enum):
    DRAUTO = "AUTO"
    DR400 = "400"
    DR200 = "200"
    DR100 = "100"


class GrainEffectSize(Enum):
    LARGE = "LARGE"
    SMALL = "SMALL"


class FilmSimulation(Enum):
    ACROS = "Acros"
    ACROS_G = "AcrosG"
    ACROS_R = "AcrosR"
    ACROS_Y = "AcrosYe"
    ASTIA = "Astia"
    CLASSIC_CHROME = "Classic"
    CLASSIC_NEG = "ClassicNEGA"
    ETERNA = "Eterna"
    ETERNA_BLEACH_BYPASS = "BleachBypass"
    MONOCHROME = "BW"
    MONOCHROME_G = "BG"
    MONOCHROME_R = "BR"
    MONOCHROME_Y = "BYe"
    NOSTALGIC_NEG = "NostalgicNEGA"
    PRO_NEG_HI = "NEGAhi"
    PRO_NEG_STD = "NEGAStd"
    PROVIA = "Provia"
    REALA_ACE = "REALA_ACE"
    SEPIA = "Sepia"
    VELVIA = "Velvia"


class FujiSensor(Enum):
    BAYER = "Bayer"
    EXR_CMOS = "EXR-CMOS"
    GFX = "GFX"
    X_TRANS_I = "X-Trans-I"
    X_TRANS_II = "X-Trans-II"
    X_TRANS_III = "X-Trans-III"
    X_TRANS_IV = "X-Trans-IV"
    X_TRANS_V = "X-Trans-V"


class WhiteBalanceSetting(Enum):
    AUTO = "Auto"
    AUTO_AMBIENCE = "Auto_Ambience"
    AUTO_WHITE = "Auto_White"
    DAYLIGHT = "Daylight"
    FLIGHT1 = "FLight1"
    FLIGHT2 = "FLight2"
    FLIGHT3 = "FLight3"
    SHADE = "Shade"
    TEMPERATURE = "Temperature"


class WhiteBalanceBlueRed(Enum):
    BLUE = "Blue"
    RED = "Red"


@dataclass
class GrainEffect:
    grain_effect: FujiEffect
    grain_effect_size: GrainEffectSize | None = field(default=None)

    def __post_init__(self) -> None:
        if self.grain_effect == FujiEffect.OFF:
            self.grain_effect_size = None


@dataclass
class MonochomaticColor:
    warm_cool: int
    magenta_green: int


@dataclass
class WhiteBalance:
    setting: WhiteBalanceSetting
    red: int
    blue: int
    color_temp: str


@dataclass
class FujiSimulationProfile:
    film_simulation: str
    white_balance: WhiteBalance
    dynamic_range: DynamicRange
    sharpness: int
    high_iso_nr: int

    # Optional attributes
    clarity: int = 0
    color: int = 0
    color_chrome_effect: FujiEffect | None = field(default=None)
    color_chrome_fx_blue: FujiEffect | None = field(default=None)
    exposure_compensation: float | None = field(default=None)
    grain_effect: GrainEffect | None = field(default=None)
    highlight: int = 0
    iso: str | None = field(default=None)
    monochromatic_color: MonochomaticColor | None = field(default=None)
    shadow: int = 0

    # Mapping between FujiSimulationProfile attributes and XML tags
    attribute_to_xml_mapping: ClassVar[dict] = {
        "clarity": "Clarity",
        "color": "Color",
        "color_chrome_effect": "ChromeEffect",
        "color_chrome_fx_blue": "ColorChromeBlue",
        "dynamic_range": "DynamicRange",
        "exposure_compensation": "ExposureBias",
        "film_simulation": "FilmSimulation",
        "grain_effect_grain_effect": "GrainEffect",
        "grain_effect_grain_effect_size": "GrainEffectSize",
        "high_iso_nr": "NoisReduction",
        "highlight": "HighlightTone",
        "monochromatic_color_magnetic_green": "MonochromaticColor_MG",
        "monochromatic_color_warm_cool": "MonochromaticColor_WC",
        "shadow": "ShadowTone",
        "sharpness": "Sharpness",
        "white_balance_setting": "WhiteBalance",
        "white_balance_red": "WBShiftR",
        "white_balance_blue": "WBShiftB",
        "white_balance_color_temp": "WBColorTemp",
    }

    @classmethod
    def create_instance(cls, data: dict) -> "FujiSimulationProfile":
        """
        Validate the data and create a FujiSimulationProfile instance
        """
        valid_fields = {field.name for field in fields(cls)}
        filtered_data = {}

        for key, value in data.items():
            if key in valid_fields:
                filtered_data[key] = value
            else:
                logging.warning(f"Invalid key '{key}' in data. This key will be ignored.")

        return cls(**filtered_data)

    def to_flat_dict(self) -> dict:
        """
        For each dataclass attribute, flatten the dataclass into a dict.
        Use the attribute name as the prefix.
        """
        flat_dict = vars(self).copy()

        for fuji_simulation_profile_field in fields(self):
            field_value = getattr(self, fuji_simulation_profile_field.name)

            # Check if the fuji_simulation_profile_field is a dataclass instance and flatten it
            if is_dataclass(field_value):
                for nested_field in fields(field_value):
                    nested_field_value = getattr(field_value, nested_field.name)

                    # Special handling for enum fields
                    if isinstance(nested_field_value, Enum):
                        nested_field_value = nested_field_value.value

                    flat_dict[f"{fuji_simulation_profile_field.name}_{nested_field.name}"] = nested_field_value

                # Remove the original nested dataclass fuji_simulation_profile_field
                del flat_dict[fuji_simulation_profile_field.name]

        return flat_dict


def clean_camera_profile_name(camera_tag: str) -> str:
    camera_profile = camera_tag.replace(" ", "_").replace(".", "").split("/")[0].upper()

    alternative_camera_profile_names = {"CLASSIC_NEGATIVE": "CLASSIC_NEG"}

    if camera_profile in alternative_camera_profile_names:
        camera_profile = alternative_camera_profile_names[camera_profile]

    return camera_profile


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


@dataclass
class KeyStandardizer:
    _parsing_methods: ClassVar[dict[str, Callable[..., Any]]] = {}

    @staticmethod
    def clean_string(text_string: str) -> str:
        """
        Utility method to clean and standardize a string.
        """
        return text_string.replace(" ", "_").replace(",", "").upper()

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
            logging.warning("Could not parse dynamic range, setting to AUTO")
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
            logging.warning("Could not parse grain effect, setting to FujiEffect.OFF")
            return GrainEffect(grain_effect=FujiEffect.OFF)

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

        # Extract the blue and red values / color temperature
        blue = get_blue_red_numeric_value(value, WhiteBalanceBlueRed.BLUE)
        red = get_blue_red_numeric_value(value, WhiteBalanceBlueRed.RED)
        # Defaults
        setting, color_temp = get_white_balance_setting(value)

        return WhiteBalance(setting=setting, red=red, blue=blue, color_temp=color_temp)

    @staticmethod
    def numerical_value(value: str) -> float:
        # Regular expression to match both integer and floating-point numbers
        number_regex = r"([+-]?\d+(\.\d+)?)"
        match = re.search(number_regex, value)
        if match:
            number_str = match.group(0).replace("+", "")
            if "." in number_str:  # Check if the number has a decimal part
                # Should only be the case for highlights / shadows
                return float(number_str)
            else:
                return int(number_str)
        else:
            logging.warning("Could not convert %s to float, setting to 0", value)
            converted_value = 0.0
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
            logging.warning("Could not convert %s to MonochromaticColor, setting to 0", value)
            warm_cool = 0
            magenta_green = 0

        return MonochomaticColor(
            warm_cool=warm_cool,
            magenta_green=magenta_green,
        )

    @classmethod
    def initialise_parsing_methods(cls) -> None:
        cls._parsing_methods = {
            "color": KeyStandardizer.numerical_value,
            "color_chrome_effect": KeyStandardizer.color_chrome_effect,
            "dynamic_range": KeyStandardizer.dynamic_range,
            "exposure_compensation": KeyStandardizer.exposure_compensation,
            "film_simulation": KeyStandardizer.film_simluation,
            "grain_effect": KeyStandardizer.grain_effect,
            "high_iso_nr": KeyStandardizer.numerical_value,
            "highlight": KeyStandardizer.numerical_value,
            "shadow": KeyStandardizer.numerical_value,
            "sharpness": KeyStandardizer.numerical_value,
            "white_balance": KeyStandardizer.white_balance,
            "monochromatic_color": KeyStandardizer.monochromatic_color,
        }
