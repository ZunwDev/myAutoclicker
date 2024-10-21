import autoclicker
import config

if __name__ == "__main__":
    autoclicker.start_hotkey_listener()
    autoclicker.setup_viewport()
    config.load_config()
