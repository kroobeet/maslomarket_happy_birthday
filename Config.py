import json


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
