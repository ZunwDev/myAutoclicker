import json
import os

# Default config values
config_path = "config.json"
config_data = {
    "interval_ms": 100,
    "hotkey": "X",
}

def load_config():
    global config_data
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            config_data = json.load(f)
            print("Configuration loaded:", config_data)  # Debug statement

def save_config():
    with open(config_path, 'w') as f:
        json.dump(config_data, f)
        print("Configuration saved:", config_data)  # Debug statement

load_config()