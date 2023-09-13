from typing import Optional

import json
import os


class Config:
    def __init__(self, config_file):
        self.config_file = config_file

    def read_config(self):
        try:
            with open(self.config_file, 'r') as file:
                config_data = json.load(file)
                return config_data
        except FileNotFoundError:
            print("Config file not found.")
        except json.JSONDecodeError:
            print("Error decoding config file.")
        return None

    def read_template(self, template_name: str, config_type) -> Optional[str]:
        templates_folder = self.read_config().get(config_type).get("templates_folder")

        try:
            with open(os.path.join(templates_folder, template_name), "r", encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError:
            print(f"Template '{template_name}' not found.")
        except OSError:
            print("Error reading the template file.")
        return None
