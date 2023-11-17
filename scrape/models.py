# A set of Enums to be used to generate the representative Fujifilm .fp1 camera settings
from enum import Enum


class FujiEffect(Enum):
    STRONG = "STRONG"
    WEAK = "WEAK"
    OFF = "OFF"


class DynamicRange(Enum):
    DRAUTO = "AUTO"
    DR400 = 400
    DR200 = 200
    DR100 = 100


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
