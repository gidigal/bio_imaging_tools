import os
from pathlib import Path
import json


class Settings:
    def __init__(self):
        self.data = {}
        # check if settings.json exists in current working directory. If it does - load it
        current_working_dir = os.getcwd()
        self.settings_file_name = current_working_dir + os.path.sep + 'settings.json'
        file_path = Path(self.settings_file_name)
        if file_path.is_file():
            with open(file_path, 'r') as file:
                self.data = json.load(file)

    def get(self, key):
        res = None
        if key in self.data.keys():
            res = self.data[key]
        return res

    def set(self, key, value):
        self.data[key] = value

    def save(self):
        with open(self.settings_file_name, 'w') as file:
            json.dump(self.data, file, indent=4)
        print(f"settings written to {self.settings_file_name}")


settings_instance = Settings()