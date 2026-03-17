import json
from pathlib import Path

def load_config(folder_path):
    config_file = Path(folder_path) / 'tina.run.json'
    if config_file.exists():
        with open(config_file, 'r') as file:
            return json.load(file)
    else:
        return None

def get_default_command(folder_path):
    config = load_config(folder_path)
    return config.get('default_command', 'python main.py')