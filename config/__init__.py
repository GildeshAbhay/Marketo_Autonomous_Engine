import yaml
import os

# Define the path to the config.yaml file
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.yaml')

# Load the YAML file
try:
    with open(CONFIG_PATH, 'r') as file:
        _loaded_settings = yaml.safe_load(file)
except FileNotFoundError:
    _loaded_settings = {}

# Make the settings accessible from the outside
# The 'settings' variable is now a Python dictionary
settings = _loaded_settings.get("settings", {})