import logging
import os
from collections import OrderedDict
from dataclasses import dataclass, field

from lxml import etree as ET
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt

from scrape.models import FujiSensor

# Global variable
BASE_PATH = os.path.expanduser("~/Library/Application Support/com.fujifilm.denji/X RAW STUDIO")
FUJI_EXTENSION = ".fp1"

# Setup rich console and logging
console = Console()
logging.basicConfig(level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()])

COMPATIBILITY_MAPPING = {
    FujiSensor.BAYER: [
        "X-A1",
        "X-A2",
        "X-A3",
        "X-A5",
        "X-A7",
        "X-A10",
        "XF10",
        "X-T100",
        "X-T200",
    ],
    FujiSensor.GFX: ["GFX50R", "GFX50S", "GFX100"],
    FujiSensor.EXR_CMOS: ["X100", "XF1", "X10", "X-S1"],
    FujiSensor.X_TRANS_I: ["X-Pro1", "X-E1", "X-M1"],
    FujiSensor.X_TRANS_II: [
        "X100S",
        "X100T",
        "X-E2",
        "X-E2S",
        "X-T1",
        "X-T10",
        "X70",
        "X20",
        "X30",
        "XQ1",
        "XQ2",
    ],
    FujiSensor.X_TRANS_III: [
        "X-T2",
        "X-Pro2",
        "X100F",
        "X-T20",
        "X-E3",
        "X-H1",
        "X-T30",
    ],
    FujiSensor.X_TRANS_IV: [
        "X-T3",
        "X-T30",
        "X-Pro3",
        "X100V",
        "X-T4",
        "X-S10",
    ],
    FujiSensor.X_TRANS_V: [
        "X-T5",
        "X-H2",
        "X-H2S",
        "X-S20",
        "GFX100S",
        "GFX50SII",
        "X100VI",
        "XM5",
    ],
}


# Value error subclasses
class TagValidationError(ValueError):
    def __init__(self, tag: str, attr: str = "") -> None:
        if attr:
            super().__init__(f"Missing or empty attribute '{attr}' in '{tag}'.")
        else:
            super().__init__(f"Missing '{tag}' in extracted tags.")


class InvalidSelectionError(ValueError):
    def __init__(self) -> None:
        super().__init__("Invalid selection")


class NoValidFileError(ValueError):
    def __init__(self, file_extension: str) -> None:
        super().__init__(f"No valid {file_extension} file found in the destination folder.")


@dataclass
class FP1File:
    source_file_path: str
    destination_file_path: str = ""
    xml_tree: ET._ElementTree = field(init=False)
    tags_to_extract: list = field(
        default_factory=lambda: [
            "ConversionProfile",
            "PropertyGroup",
            "SerialNumber",
            "TetherRAWConditonCode",
            "Editable",
            "SourceFileName",
            "Fileerror",
            "RotationAngle",
            "StructVer",
            "IOPCode",
        ]
    )

    def __post_init__(self) -> None:
        self.destination_file_path = self.destination_file_path if self.destination_file_path != "" else self.source_file_path
        self.xml_tree = self._parse_xml()

    def _parse_xml(self) -> ET._ElementTree:
        parser = ET.XMLParser(remove_blank_text=True)
        with open(self.source_file_path, encoding="utf-8") as file:
            return ET.parse(file, parser)

    def extract_tags(self) -> dict[str, str | dict[str, str]]:
        root = self.xml_tree.getroot()
        extracted_tags: dict[str, str | dict[str, str]] = {}
        for tag in self.tags_to_extract:
            if tag in self.required_attrs:
                element = root if tag == "ConversionProfile" else root.find(f".//{tag}")
                extracted_tags[tag] = dict(element.attrib) if element is not None else {}
            else:
                element = root.find(f".//{tag}")
                extracted_tags[tag] = element.text.strip() if element is not None and element.text else ""
        return extracted_tags

    @property
    def required_attrs(self) -> dict:
        return {
            "ConversionProfile": ["application", "version"],
            "PropertyGroup": ["device", "version"],
        }

    def apply_tags(self, master_tags: dict) -> None:
        root = self.xml_tree.getroot()

        for tag, value in master_tags.items():
            if tag in ["ConversionProfile", "PropertyGroup"]:
                # Apply attributes to special tags
                element = root if tag == "ConversionProfile" else root.find(f".//{tag}")

                if element is not None:
                    for attr, attr_value in value.items():
                        # Skip label attribute
                        if attr == "label":
                            continue
                        element.set(attr, attr_value)
            else:
                # Apply text content to regular tags
                element = root.find(f".//{tag}")
                if element is not None:
                    element.text = value

        # After modifying the tree, update xml_tree
        self.xml_tree = ET.ElementTree(root)

    def save(self) -> None:
        with open(self.destination_file_path, "wb") as file:
            self.xml_tree.write(file, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            console.print(f"Saving {self.destination_file_path}", style="green")


@dataclass
class FP1TemplateFiles:
    source_directory: str
    destination_directory: str
    template_files: list[FP1File] = field(init=False)

    def __post_init__(self) -> None:
        self.template_files = self._generate_valid_files()
        console.print(f"Found {self.total_number} valid {FUJI_EXTENSION} files found")

    def _generate_valid_files(self) -> list[FP1File]:
        valid_files = []
        for file_name in os.listdir(self.source_directory):
            if file_name.upper().endswith(FUJI_EXTENSION):
                valid_files.append(
                    FP1File(
                        source_file_path=os.path.join(self.source_directory, file_name),
                        destination_file_path=os.path.join(self.destination_directory, file_name),
                    )
                )
            else:
                logging.warning(f"Invalid file format found: {file_name}")
        return valid_files

    @property
    def total_number(self) -> int:
        return len(self.template_files)


def list_folders_with_subfolders(base_path: str) -> dict:
    folder_dict = {}
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            subfolders = [f for f in os.listdir(item_path) if os.path.isdir(os.path.join(item_path, f))]
            folder_dict[item] = subfolders
    sorted_dict = OrderedDict(sorted(folder_dict.items()))
    return sorted_dict


def select_folder(folder_dict: dict) -> str:
    options = []
    for folder, subfolders in folder_dict.items():
        if subfolders:
            for subfolder in subfolders:
                options.append(f"{folder}/{subfolder}")
        else:
            options.append(folder)

    console.print("Please select a folder:", style="bold yellow")
    for i, option in enumerate(options):
        console.print(f"{i + 1}: {option}", style="yellow")

    choice = Prompt.ask("Select a folder by number", choices=[str(i + 1) for i in range(len(options))])
    int_choice = int(choice) - 1
    if int_choice < 0 or int_choice >= len(options):
        raise InvalidSelectionError()
    return options[int_choice]


def find_valid_fp1_file(directory: str) -> FP1File | None:
    for file_name in os.listdir(directory):
        if file_name.endswith(FUJI_EXTENSION):
            file_path = os.path.join(directory, file_name)
            fp1_file = FP1File(file_path)
            if fp1_file.extract_tags():
                return fp1_file
    return None


def normalize_sensor_name(sensor_name: str) -> str:
    """
    Normalize the sensor name to match the enum member names.
    Example: 'X-Trans-IV' -> 'X_TRANS_IV'
    """
    return sensor_name.replace("-", "_").upper()


def is_compatiable_sensor(selected_sensor: str, destination_path: str) -> bool:
    """
    Checks the sensor type from the fuji_profiles_path and spits out a warning
    if the destination_path is not compatiable
    """
    normalized_sensor_name = normalize_sensor_name(selected_sensor)
    selected_sensor_enum = FujiSensor[normalized_sensor_name]
    compatiable_camera_models: list[str] = COMPATIBILITY_MAPPING.get(selected_sensor_enum, [])
    camera_model: str = destination_path.split("/")[-2]

    try:
        compatiable_sensor_type = camera_model in compatiable_camera_models

        if not compatiable_sensor_type:
            console.print(
                f"Warning: {camera_model} is not a compatiable sensor type;",
                "These might not be interpretted properly once copied over.",
                style="bold red",
            )
            return False
    except KeyError:
        console.print(f"Could not find {camera_model} in the compatiable sensor types.")
        return False
    return True


if __name__ == "__main__":
    console.print("[bold yellow]Starting the FP1 processing script...[/bold yellow]")
    current_dir = os.getcwd()
    fuji_profiles_dir = os.path.join(current_dir, "fuji_profiles")

    # Select Fuji profiles folder
    profile_folders = list_folders_with_subfolders(fuji_profiles_dir)
    selected_profile_folder = select_folder(profile_folders)
    fuji_profiles_path = os.path.join(fuji_profiles_dir, selected_profile_folder)

    # Select destination folder from base_path
    destination_folders = list_folders_with_subfolders(BASE_PATH)
    selected_destination_folder = select_folder(destination_folders)
    destination_path = os.path.join(BASE_PATH, selected_destination_folder)

    is_compatiable_sensor(selected_profile_folder, destination_path)

    valid_fp1_file = find_valid_fp1_file(destination_path)
    if not valid_fp1_file:
        raise NoValidFileError(FUJI_EXTENSION)

    tags_to_apply = valid_fp1_file.extract_tags()
    console.print(f"Tags to apply: {tags_to_apply}", style="bold yellow")

    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    fuji_template_files = FP1TemplateFiles(source_directory=fuji_profiles_path, destination_directory=destination_path)
    for fp1_file in fuji_template_files.template_files:
        fp1_file.apply_tags(tags_to_apply)
        fp1_file.save()

    logging.info("Files copied successfully.")
