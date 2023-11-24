import logging
import os
from dataclasses import dataclass, field

from lxml import etree as ET
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt

# Global variable
BASE_PATH = os.path.expanduser(
    "~/Library/Application Support/com.fujifilm.denji/X RAW STUDIO"
)
FUJI_EXTENSION = ".FP1"

# Setup rich console and logging
console = Console()
logging.basicConfig(
    level="INFO", format="%(message)s", datefmt="[%X]", handlers=[RichHandler()]
)


# Value error subclasses
class TagValidationError(ValueError):
    def __init__(self, tag, attr=None):
        if attr:
            super().__init__(f"Missing or empty attribute '{attr}' in '{tag}'.")
        else:
            super().__init__(f"Missing '{tag}' in extracted tags.")


class InvalidSelectionError(ValueError):
    def __init__(self):
        super().__init__("Invalid selection")


class NoValidFileError(ValueError):
    def __init__(self, file_extension):
        super().__init__(
            f"No valid {file_extension} file found in the destination folder."
        )


@dataclass
class FP1File:
    source_file_path: str
    destination_file_path: str = None
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

    def __post_init__(self):
        self.destination_file_path = self.destination_file_path or self.source_file_path
        self.xml_tree = self._parse_xml()

    def _parse_xml(self):
        parser = ET.XMLParser(remove_blank_text=True)
        with open(self.source_file_path, encoding="utf-8") as file:
            return ET.parse(file, parser)

    def extract_tags(self):
        root = self.xml_tree.getroot()
        extracted_tags = {}
        for tag in self.tags_to_extract:
            if tag == "ConversionProfile" or tag == "PropertyGroup":
                element = root if tag == "ConversionProfile" else root.find(f".//{tag}")
                if element is not None:
                    extracted_tags[tag] = element.attrib
            else:
                element = root.find(f".//{tag}")
                if element is not None and element.text:
                    extracted_tags[tag] = element.text.strip()

        return extracted_tags

    def validate_extracted_tags(self, extracted_tags):
        required_attrs = {
            "ConversionProfile": ["application", "version"],
            "PropertyGroup": ["device", "version"],
        }

        for tag, attrs in required_attrs.items():
            if tag not in extracted_tags or not isinstance(extracted_tags[tag], dict):
                raise TagValidationError(tag)

            for attr in attrs:
                if attr not in extracted_tags[tag] or not extracted_tags[tag][attr]:
                    raise TagValidationError(tag, attr)

    def apply_tags(self, master_tags):
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

    def save(self):
        with open(self.destination_file_path, "wb") as file:
            self.xml_tree.write(
                file, pretty_print=True, xml_declaration=True, encoding="UTF-8"
            )
            console.print(f"Saving {self.destination_file_path}", style="green")


@dataclass
class FP1TemplateFiles:
    source_directory: str
    destination_directory: str
    template_files: list[FP1File] = None

    def __post_init__(self):
        self.template_files = self._generate_valid_files()
        console.print(f"Found {self.total_number} valid {FUJI_EXTENSION} files found")

    def _generate_valid_files(self):
        valid_files = []
        for file_name in os.listdir(self.source_directory):
            if file_name.upper().endswith(FUJI_EXTENSION):
                valid_files.append(
                    FP1File(
                        source_file_path=os.path.join(self.source_directory, file_name),
                        destination_file_path=os.path.join(
                            self.destination_directory, file_name
                        ),
                    )
                )
            else:
                logging.warning(f"Invalid file format found: {file_name}")
        return valid_files

    @property
    def total_number(self) -> int:
        return len(self.template_files)


def list_folders_with_subfolders(base_path):
    folder_dict = {}
    for item in os.listdir(base_path):
        item_path = os.path.join(base_path, item)
        if os.path.isdir(item_path):
            subfolders = [
                f
                for f in os.listdir(item_path)
                if os.path.isdir(os.path.join(item_path, f))
            ]
            folder_dict[item] = subfolders
    return folder_dict


def select_folder(folder_dict):
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

    choice = Prompt.ask(
        "Select a folder by number", choices=[str(i + 1) for i in range(len(options))]
    )
    choice = int(choice) - 1
    if choice < 0 or choice >= len(options):
        raise InvalidSelectionError()
    return options[choice]


def find_valid_fp1_file(directory):
    for file_name in os.listdir(directory):
        if file_name.endswith(FUJI_EXTENSION):
            file_path = os.path.join(directory, file_name)
            fp1_file = FP1File(file_path)
            if fp1_file.extract_tags():
                return fp1_file
    return None


def main():
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

    valid_fp1_file = find_valid_fp1_file(destination_path)
    if not valid_fp1_file:
        raise NoValidFileError(FUJI_EXTENSION)

    tags_to_apply = valid_fp1_file.extract_tags()
    console.print(f"Tags to apply: {tags_to_apply}", style="bold yellow")

    if not os.path.exists(destination_path):
        os.makedirs(destination_path)

    fuji_template_files = FP1TemplateFiles(
        source_directory=fuji_profiles_path, destination_directory=destination_path
    )
    for fp1_file in fuji_template_files.template_files:
        fp1_file.apply_tags(tags_to_apply)
        fp1_file.save()

    logging.info("Files copied successfully.")


if __name__ == "__main__":
    console.print("[bold yellow]Starting the FP1 processing script...[/bold yellow]")
    main()
