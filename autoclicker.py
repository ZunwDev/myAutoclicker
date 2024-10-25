import dearpygui.dearpygui as dpg
import config
from pynput import keyboard
import threading
import time
import ctypes
import pyautogui as pg

viewport_width = 311
viewport_height = 350
is_autoclicker_enabled = False
autoclicker_event = threading.Event()
keys_pressed = []
is_hotkey_recording_enabled = False

user32 = ctypes.windll.user32
mouse_event = user32.mouse_event
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def click():
    pos = pg.position()
    mouse_event(MOUSEEVENTF_LEFTDOWN, pos[0], pos[1], 0, 0)
    mouse_event(MOUSEEVENTF_LEFTUP, pos[0], pos[1], 0, 0)

def on_press(key):
    global is_hotkey_recording_enabled
    if is_hotkey_recording_enabled:
        try:
            if len(keys_pressed) == 0 and len(key.char) == 1:
                keys_pressed.append(key.char)
        except AttributeError:
            special_key = str(key).replace("Key.", "")
            if len(keys_pressed) == 0:
                keys_pressed.append(special_key)

def start_hotkey_record():
    dpg.configure_item("record_button", enabled=False)
    global is_hotkey_recording_enabled
    keys_pressed.clear()
    is_hotkey_recording_enabled = True
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener_thread = threading.Thread(target=listener.start)
    listener_thread.start()
    threading.Timer(0.1, lambda: dpg.configure_item("record_button", enabled=False)).start()

def start_hotkey_listener():
    listener = keyboard.Listener(on_press=on_hotkey_press)
    listener_thread = threading.Thread(target=listener.start, daemon=True)
    listener_thread.start()

def on_hotkey_press(key):
    hotkey = config.config_data["hotkey"].lower()
    try:
        if key.char == hotkey:
            toggle_autoclicker()
    except AttributeError:
        if str(key).replace("Key.", "").lower() == hotkey:
            toggle_autoclicker()

def autoclick():
    interval = config.config_data["interval_ms"] / 1000
    while autoclicker_event.is_set():
        click()
        if (interval == 0): interval = 0.001
        time.sleep(interval)

def toggle_autoclicker():
    global is_autoclicker_enabled
    if is_autoclicker_enabled:
        print("Autoclicker disabled.")
        dpg.set_viewport_title("myAutoclicker (idling)")
        is_autoclicker_enabled = False
        autoclicker_event.clear()
    else:
        print("Autoclicker enabled.")
        dpg.set_viewport_title("myAutoclicker (running)")
        is_autoclicker_enabled = True
        autoclicker_event.set()
        threading.Thread(target=autoclick, daemon=True).start()

def on_release(key):
    global is_hotkey_recording_enabled
    if is_hotkey_recording_enabled:
        is_hotkey_recording_enabled = False
        if keys_pressed:
            final_key = keys_pressed[0]
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

def interval_input_callback(sender, app_data, user_data):
    new_interval = app_data
    set_interval(new_interval)

def open_hotkey_modal(sender, app_data):
    dpg.show_item("hotkey_modal")

def save_hotkey(sender, app_data):
    hotkey = dpg.get_value("hotkey_input")
    config.config_data["hotkey"] = hotkey
    config.save_config()
    dpg.hide_item("hotkey_modal")

def setup_viewport():
    dpg.create_viewport(width=viewport_width, height=viewport_height, title="myAutoclicker (idling)", resizable=True, max_height=viewport_height, max_width=viewport_width)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("primary_window", True)
    dpg.start_dearpygui()
    dpg.destroy_context()

dpg.create_context()

with dpg.window(width=viewport_width, height=viewport_height, tag="primary_window"):
    dpg.add_text("Click interval presets")
    with dpg.group(horizontal=True):
        load_interval_preset_buttons()
    dpg.add_spacer(height=10)
    with dpg.group(horizontal=True):
        dpg.add_text("Click interval (ms)")
        dpg.add_input_int(default_value=config.config_data["interval_ms"], tag="custom_interval_input", width=139, callback=interval_input_callback)
    dpg.add_spacer(height=55)
    dpg.add_button(label="Hotkey setting", height=32, width=280, callback=open_hotkey_modal)
    dpg.add_spacer(height=2)
    with dpg.group(horizontal=True):
        dpg.add_button(label=f"Start / Stop ({config.config_data['hotkey']})", height=64, width=280, callback=toggle_autoclicker)

with dpg.window(label="Hotkey Modal", modal=True, show=False, tag="hotkey_modal", no_resize=True, no_title_bar=True, pos=[50, 100]):
    dpg.add_text("Set Hotkey")
    dpg.add_input_text(width=155, default_value=config.config_data["hotkey"], uppercase=True, no_spaces=True, readonly=True, tag="hotkey_input")
    dpg.add_spacer(height=10)
    with dpg.group(horizontal=True):
        dpg.add_button(label="Record", callback=start_hotkey_record, tag="record_button")
        dpg.add_spacer(width=4)
        dpg.add_button(label="Save", callback=save_hotkey)
        dpg.add_button(label="Cancel", callback=lambda: dpg.hide_item("hotkey_modal"))

start_hotkey_listener()
setup_viewport()