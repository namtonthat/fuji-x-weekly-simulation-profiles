import logging
import os
import sys
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
    FujiSensor.X_TRANS_I: [
        "X-Pro1",
        "X-E1",
        "X-M1",
    ],
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
        "X-M5",
        "X-E5",
    ],
}


# Error Handling Classes
class InvalidDestinationPathError(ValueError):
    """Raised when the destination path cannot be parsed."""


class CameraModelExtractionError(ValueError):
    """Raised when the camera model cannot be extracted from a folder."""


class UnknownSensorError(ValueError):
    """Raised when a sensor name is not found in FujiSensor enum."""


class IncompatibleSensorError(ValueError):
    """Raised when a camera model is not compatible with the selected sensor."""


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
            if file_name.lower().endswith(FUJI_EXTENSION):
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


def select_copy_mode() -> str:
    options = {
        "1": "Bulk copy compatible sensor profiles",
        "2": "Copy selected profile(s) only (allow cross-sensor override)",
    }
    console.print("Please select copy mode:", style="bold yellow")
    for key, option in options.items():
        console.print(f"{key}: {option}", style="yellow")
    return Prompt.ask("Select mode by number", choices=list(options.keys()))


def list_fp1_files(directory: str) -> list[str]:
    return sorted([f for f in os.listdir(directory) if f.lower().endswith(FUJI_EXTENSION)])


def get_camera_model_sensors(camera_model: str) -> list[FujiSensor]:
    return [sensor for sensor, camera_models in COMPATIBILITY_MAPPING.items() if camera_model in camera_models]


def resolve_destination_sensor(
    destination_path: str,
    fuji_profiles_root: str,
) -> FujiSensor:
    camera_model = extract_camera_model(destination_path)
    candidate_sensors = get_camera_model_sensors(camera_model)
    if not candidate_sensors:
        raise UnknownSensorError()
    if len(candidate_sensors) == 1:
        return candidate_sensors[0]

    destination_profile_names = set(list_fp1_files(destination_path))
    best_sensor = candidate_sensors[0]
    best_overlap = -1
    for sensor in candidate_sensors:
        sensor_profile_dir = os.path.join(fuji_profiles_root, sensor.value)
        if not os.path.isdir(sensor_profile_dir):
            continue
        sensor_profiles = set(list_fp1_files(sensor_profile_dir))
        overlap = len(destination_profile_names.intersection(sensor_profiles))
        if overlap > best_overlap:
            best_overlap = overlap
            best_sensor = sensor

    return best_sensor


def build_cross_sensor_candidates(
    destination_path: str,
    fuji_profiles_root: str,
    selected_profile_folder: str,
) -> list[tuple[str, str, str]]:
    destination_sensor = resolve_destination_sensor(destination_path, fuji_profiles_root)
    destination_sensor_dir = os.path.join(fuji_profiles_root, destination_sensor.value)
    sensor_recipes = set(list_fp1_files(destination_sensor_dir)) if os.path.isdir(destination_sensor_dir) else set()

    selected_profile_root_folder = selected_profile_folder.split(os.sep)[0]
    excluded_folders = {destination_sensor.value, selected_profile_folder, selected_profile_root_folder}

    candidates: list[tuple[str, str, str]] = []
    for folder_name in sorted(os.listdir(fuji_profiles_root)):
        folder_path = os.path.join(fuji_profiles_root, folder_name)
        if not os.path.isdir(folder_path) or folder_name in excluded_folders:
            continue

        for file_name in list_fp1_files(folder_path):
            if file_name in sensor_recipes:
                continue
            display_name = f"{folder_name}/{file_name}"
            source_file_path = os.path.join(folder_path, file_name)
            candidates.append((display_name, source_file_path, file_name))

    return candidates


def select_fp1_file_set(directory: str, allowed_options: list[str] | None = None) -> list[str]:
    options = allowed_options if allowed_options is not None else list_fp1_files(directory)
    if not options:
        raise NoValidFileError(FUJI_EXTENSION)

    console.print("Select one or more profiles to copy as a set:", style="bold yellow")
    for i, option in enumerate(options):
        console.print(f"{i + 1}: {option}", style="yellow")
    console.print("Enter comma-separated numbers (example: 1,3,8)", style="dim")

    raw_selection = Prompt.ask("Select files by number")
    selected_indexes = []
    for token in raw_selection.split(","):
        stripped = token.strip()
        if not stripped.isdigit():
            raise InvalidSelectionError()
        selected_indexes.append(int(stripped) - 1)

    if not selected_indexes:
        raise InvalidSelectionError()

    selected_file_names = []
    for index in selected_indexes:
        if index < 0 or index >= len(options):
            raise InvalidSelectionError()
        selected_file_names.append(options[index])

    # Preserve selection order while removing duplicates
    return list(dict.fromkeys(selected_file_names))


def extract_camera_model(destination_path: str) -> str:
    path_parts = destination_path.strip(os.sep).split(os.sep)

    if not path_parts:
        raise InvalidDestinationPathError()

    last_part = path_parts[-1]

    if ":" in last_part:
        model = last_part.split(":")[0]
        if not model:
            raise CameraModelExtractionError()
        return model

    if len(path_parts) >= 2:
        model = path_parts[-2]
        if not model:
            raise CameraModelExtractionError()
        return model

    raise CameraModelExtractionError()


def normalize_sensor_name(sensor_name: str) -> str:
    """
    Normalize the sensor name to match the enum member names.
    For example: 'X-Trans-IV' -> 'X_TRANS_IV'
    """
    return sensor_name.replace("-", "_").upper()


def is_compatiable_sensor(selected_sensor: str, destination_path: str) -> bool:
    normalized_sensor_name = normalize_sensor_name(selected_sensor)

    try:
        selected_sensor_enum = FujiSensor[normalized_sensor_name]
    except KeyError as e:
        raise UnknownSensorError() from e

    compatiable_camera_models = COMPATIBILITY_MAPPING.get(selected_sensor_enum, [])

    camera_model = extract_camera_model(destination_path)

    if camera_model not in compatiable_camera_models:
        raise IncompatibleSensorError()

    console.print(f"[green]✓ Sensor '{selected_sensor_enum.name}' is compatible with '{camera_model}'[/green]")
    return True


def is_sensor_compatible_for_destination(selected_sensor: str, destination_path: str) -> bool:
    try:
        return is_compatiable_sensor(selected_sensor, destination_path)
    except (InvalidDestinationPathError, CameraModelExtractionError, UnknownSensorError, IncompatibleSensorError):
        return False


def find_valid_fp1_file(directory: str) -> FP1File | None:
    """
    Loops through files in the given directory and returns the first valid FP1File.
    Returns None if no valid file is found.
    """
    for file_name in os.listdir(directory):
        if file_name.lower().endswith(FUJI_EXTENSION):
            file_path = os.path.join(directory, file_name)
            fp1_file = FP1File(file_path)
            if fp1_file.extract_tags():
                return fp1_file
            else:
                console.print(f"[yellow][DEBUG] Invalid FP1 file (no tags): {file_path}[/yellow]")
        else:
            console.print(f"[dim][DEBUG] Skipping non-fp1 file: {file_name}[/dim]")
    return None


if __name__ == "__main__":
    console.print("[bold yellow]Starting the FP1 processing script...[/bold yellow]")
    current_dir = os.getcwd()
    fuji_profiles_dir = os.path.join(current_dir, "fuji_profiles")

    # Select Fuji profiles folder
    profile_folders = list_folders_with_subfolders(fuji_profiles_dir)
    selected_profile_folder = select_folder(profile_folders)
    fuji_profiles_path = os.path.join(fuji_profiles_dir, selected_profile_folder)

    # Select destination folder from BASE_PATH
    destination_folders = list_folders_with_subfolders(BASE_PATH)
    selected_destination_folder = select_folder(destination_folders)
    destination_path = os.path.join(BASE_PATH, selected_destination_folder)
    copy_mode = select_copy_mode()

    if copy_mode == "1":
        try:
            is_compatiable_sensor(selected_profile_folder, destination_path)
        except (InvalidDestinationPathError, CameraModelExtractionError, UnknownSensorError, IncompatibleSensorError) as e:
            console.print("[bold red]ERROR:[/bold red] {}", str(e))
            sys.exit(1)

    valid_fp1_file = find_valid_fp1_file(destination_path)
    if not valid_fp1_file:
        console.print("[bold red]No valid .fp1 files found.[/bold red]")
        raise NoValidFileError(FUJI_EXTENSION)

    console.print("[green]Valid FP1 file found and processing...[/green]")
    tags_to_apply = valid_fp1_file.extract_tags()
    console.print(f"Tags to apply: {tags_to_apply}", style="bold yellow")

    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    console.print("[bold yellow]NOTE:[/bold yellow] Result may not be an exact copy. " "X RAW STUDIO metadata and unsupported camera features can override or normalize values.")

    if copy_mode == "1":
        fuji_template_files = FP1TemplateFiles(source_directory=fuji_profiles_path, destination_directory=destination_path)
        for fp1_file in fuji_template_files.template_files:
            fp1_file.apply_tags(tags_to_apply)
            fp1_file.save()
    elif copy_mode == "2":
        available_candidates = build_cross_sensor_candidates(
            destination_path=destination_path,
            fuji_profiles_root=fuji_profiles_dir,
            selected_profile_folder=selected_profile_folder,
        )
        if not available_candidates:
            console.print("[bold red]No cross-sensor missing profiles available to copy from other folders.[/bold red]")
            sys.exit(1)

        candidate_lookup = {display_name: (source_file_path, file_name) for display_name, source_file_path, file_name in available_candidates}
        selected_display_names = select_fp1_file_set(
            fuji_profiles_path,
            allowed_options=[display_name for display_name, _, _ in available_candidates],
        )
        for selected_display_name in selected_display_names:
            source_file_path, file_name = candidate_lookup[selected_display_name]
            destination_file_path = os.path.join(destination_path, file_name)
            selected_fp1_file = FP1File(source_file_path=source_file_path, destination_file_path=destination_file_path)
            selected_fp1_file.apply_tags(tags_to_apply)
            selected_fp1_file.save()

    logging.info("Files copied successfully.")
