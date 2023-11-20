# A set of Enums to be used to generate the representative Fujifilm .fp1 camera settings
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import ClassVar


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
    iso: str
    exposure_compensation: float

    # Optional attributes
    clarity: int = 0
    color: int = 0
    color_chrome_effect: FujiEffect | None = field(default=None)
    color_chrome_fx_blue: FujiEffect | None = field(default=None)
    grain_effect: GrainEffect | None = field(default=None)
    highlight: int = 0
    monochromatic_color: MonochomaticColor | None = field(default=None)
    shadow: int = 0

    # Mapping between FujiSimulationProfile attributes and XML tags
    attribute_to_xml_mapping: ClassVar[dict] = {
        "clarity": "Clarity",
        "color": "Color",
        "color_chrome_effect": "ChromeEffect",
        "color_chrome_fx_blue": "ColorChromeBlue",
        "dynamic_range": "WideDRange",
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

    def to_flat_dict(self) -> dict:
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
