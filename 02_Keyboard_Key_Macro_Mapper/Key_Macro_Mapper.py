"""
WARNING: Use this script at your own risk.
Simulating key presses in games may violate the game's terms of service
and could result in bans or other penalties.
This script is intended for educational purposes only.
Proceed with caution and consider the ethical implications of automation.

Note: Some games will require you to 'Run as Administrator' this script
"""

import keyboard
import threading
import time
import random
import signal
import sys
import json
from loguru import logger

# Flag to control if the trigger key should be processed
process_key_event = threading.Event()
process_key_event.set()  # Initially, allow key processing


def press_custom(simulate_key):
    # Clear the event (set it to False) to prevent re-triggering the action while it's in progress
    process_key_event.clear()

    # Random delay used to avoid detection, you can lower the timing if your ping is low enough to make a difference
    time.sleep(random.uniform(0.210, 0.240))
    logger.info(f"Simulating {simulate_key} key press")
    keyboard.press(simulate_key)
    keyboard.release(simulate_key)

    # Set the event (set it to True) to allow trigger key processing again
    process_key_event.set()


def on_press(event, trigger_key, simulate_key):
    try:
        # Check if the event is set (True) and process the trigger key press
        if process_key_event.is_set() and event.name == trigger_key:
            logger.info(f'Key pressed: {event.name}')
            threading.Thread(target=press_custom, args=(simulate_key,)).start()

    except AttributeError:
        pass  # Ignore any attribute errors


def on_release(event):
    # Stop the listener if the ESC key is pressed
    if event.name == 'esc':
        return False


def handle_exit_signal(signal_received, frame):
    logger.info("Exit signal received. Shutting down gracefully...")
    sys.exit(0)


def load_config(file_path="config.json"):
    """Load key configuration from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            config = json.load(f)
        activate_key = config.get("tigger_key", "space")  # Default to 'space' if not set
        macro_key = config.get("simulate_key", "alt")  # Default to 'alt' if not set
        return activate_key, macro_key
    except FileNotFoundError:
        logger.error(f"Config file {file_path} not found. Using default keys.")
        return "space", "alt"
    except json.JSONDecodeError:
        logger.error(f"Error decoding {file_path}. Using default keys.")
        return "space", "alt"


if __name__ == "__main__":
    # Startup warning
    logger.warning("Use this script at your own risk. Simulating key presses may lead to bans.")
    logger.info("Note: Some games will require you to 'Run as Administrator' this script.")

    # Load key configurations from config.json
    trigger_key, simulate_key = load_config()

    # Configure logging
    logger.add("App_Log_{time}.log", rotation="30 days", backtrace=True, enqueue=False, catch=True)
    logger.info(f"Mapper is Active. Press 'Alt + `' to exit. Trigger key: {trigger_key}, Simulate key: {simulate_key}")

    # Handle exit signals (graceful exit for keyboard interrupt)
    signal.signal(signal.SIGINT, handle_exit_signal)
    signal.signal(signal.SIGTERM, handle_exit_signal)

    try:
        # Start keyboard hooks and pass the custom keys
        keyboard.hook(lambda event: on_press(event, trigger_key, simulate_key))
        keyboard.hook(on_release)

        # Wait for Alt + Esc combination to exit
        keyboard.wait('alt + `')

    except KeyboardInterrupt:
        handle_exit_signal(None, None)
