import dearpygui.dearpygui as dpg
import config
from pynput import keyboard
import threading
import pyautogui as pg
import time
import ctypes

pg.FAILSAFE = True
viewport_width = 311
viewport_height = 350
is_autoclicker_enabled = False

# To store pressed keys
keys_pressed = []
is_hotkey_recording_enabled = False

user32 = ctypes.windll.user32
mouse_event = user32.mouse_event

MOUSEEVENTF_LEFTDOWN = 0x0002  # Left click down
MOUSEEVENTF_LEFTUP = 0x0004    # Left click up

def click():
    mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)  # Simulate left mouse button press
    mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)    # Simulate left mouse button release

def on_press(key):
    global is_hotkey_recording_enabled
    if is_hotkey_recording_enabled:
        try:
            if len(keys_pressed) == 0 and len(key.char) == 1:  # Only record if nothing is in keys_pressed
                keys_pressed.append(key.char)  # Record character keys
        except AttributeError:
            # Handle special keys by converting them to their string representation
            special_key = str(key).replace("Key.", "")
            if len(keys_pressed) == 0:  # Only add special key if no keys are recorded
                keys_pressed.append(special_key)

def start_hotkey_record():
    dpg.configure_item("record_button", enabled=False)  # Disable button immediately
    global is_hotkey_recording_enabled
    keys_pressed.clear()  # Clear any previous keys
    is_hotkey_recording_enabled = True

    # Start listening to keyboard events in a separate thread
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener_thread = threading.Thread(target=listener.start)
    listener_thread.start()  # Start the listener thread
    threading.Timer(0.1, lambda: dpg.configure_item("record_button", enabled=False)).start()

def start_hotkey_listener():
    # This listener will run in a separate thread and stay active.
    listener = keyboard.Listener(on_press=on_hotkey_press)
    listener_thread = threading.Thread(target=listener.start, daemon=True)
    listener_thread.start()

# Modify `on_hotkey_press` to handle all keys properly
def on_hotkey_press(key):
    global is_autoclicker_enabled

    hotkey = config.config_data["hotkey"].lower()  # Get the hotkey from config
    try:
        # For normal character keys
        if key.char == hotkey:
            toggle_autoclicker()
    except AttributeError:
        # For special keys like 'ctrl', 'alt', 'shift'
        if str(key).replace("Key.", "").lower() == hotkey:
            toggle_autoclicker()

def autoclick():
    global is_autoclicker_enabled
    interval = config.config_data["interval_ms"] / 1000  # Convert ms to seconds

    while is_autoclicker_enabled:
        click()
        if interval > 0:
            time.sleep(interval)  # Only sleep if interval is set

def toggle_autoclicker():
    global is_autoclicker_enabled

    if is_autoclicker_enabled:
        print("Autoclicker disabled.")
        dpg.set_viewport_title("myAutoclicker (idling)")
        is_autoclicker_enabled = False  # This will stop the autoclick loop
    else:
        print("Autoclicker enabled.")
        dpg.set_viewport_title("myAutoclicker (running)")
        is_autoclicker_enabled = True
        # Start the autoclicking in a separate thread
        click_thread = threading.Thread(target=autoclick)
        click_thread.start()

def on_release(key):
    global is_hotkey_recording_enabled
    if is_hotkey_recording_enabled:
        is_hotkey_recording_enabled = False
        if keys_pressed:
            final_key = keys_pressed[0]  # Only the first recorded key
            dpg.set_value("hotkey_input", final_key.upper())
        dpg.configure_item("record_button", enabled=True)
        keys_pressed.clear()

def set_interval(new_interval):
    config.config_data["interval_ms"] = new_interval
    config.save_config()

def update_interval_input(new_interval):
    dpg.set_value("custom_interval_input", new_interval)

def load_interval_preset_buttons():
    ms_arr = [0, 25, 50, 100]
    for item in ms_arr:
        dpg.add_button(label=f"{item}ms", callback=interval_button_callback, user_data=item, width=64, height=64)

def interval_button_callback(sender, app_data, user_data):
    new_interval = user_data
    set_interval(new_interval)
    update_interval_input(new_interval)

def open_hotkey_modal(sender, app_data):
    dpg.show_item("hotkey_modal")

def save_hotkey(sender, app_data):
    hotkey = dpg.get_value("hotkey_input")
    config.config_data["hotkey"] = hotkey
    config.save_config()  # Save config on saving hotkey
    dpg.hide_item("hotkey_modal")

def select_mouse_button(sender, app_data):
    config.config_data["mouse_button"] = app_data
    config.save_config()

def setup_viewport():
    dpg.create_viewport(width=viewport_width, height=viewport_height, title="myAutoclicker (idling)", resizable=True, max_height=viewport_height, max_width=viewport_width)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary_window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()

# Create the Dear PyGui context
dpg.create_context()

# Main window
with dpg.window(width=viewport_width, height=viewport_height, tag="primary_window"):
    dpg.add_text("Click interval presets")
    with dpg.group(horizontal=True):
        load_interval_preset_buttons()
    dpg.add_spacer(height=10)
    with dpg.group(horizontal=True):
        dpg.add_text("Click interval")
        dpg.add_input_text(label=" milliseconds", default_value=config.config_data["interval_ms"], tag="custom_interval_input", width=64)
    with dpg.group(horizontal=True):
        dpg.add_text("Mouse button")
        dpg.add_combo(items=["Left", "Right", "Middle"], default_value=config.config_data["mouse_button"], tag="mouse_button", width=64, callback=select_mouse_button)
    dpg.add_spacer(height=33)
    dpg.add_button(label="Hotkey setting", height=32, width=280, callback=open_hotkey_modal)
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True):
        dpg.add_button(label=f"Start / Stop ({config.config_data["hotkey"]})", height=64, width=280, callback=toggle_autoclicker)

# Define the modal window (similar to a popup)
with dpg.window(label="Hotkey Modal", modal=True, show=False, tag="hotkey_modal", no_resize=True, no_title_bar=True, pos=[50, 100]):
    dpg.add_text("Set Hotkey")
    dpg.add_input_text(width=155, default_value=config.config_data["hotkey"], uppercase=True, no_spaces=True, readonly=True, tag="hotkey_input")
    dpg.add_spacer(height=10)
    with dpg.group(horizontal=True):
        dpg.add_button(label="Record", callback=start_hotkey_record, tag="record_button")  # Use threading here
        dpg.add_spacer(width=4)
        dpg.add_button(label="Save", callback=save_hotkey)
        dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("hotkey_modal"))

# Start listening for the user-defined hotkey
start_hotkey_listener()

# Viewport
setup_viewport()