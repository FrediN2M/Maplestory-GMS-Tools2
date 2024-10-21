import winreg
from loguru import logger


def get_registry_value(rkey_path, value_name):
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rkey_path, 0, winreg.KEY_READ)
        value, value_type = winreg.QueryValueEx(key, value_name)
        winreg.CloseKey(key)
        return value
    except FileNotFoundError:
        logger.error(f"Registry key '{rkey_path}' not found.")
    except OSError as e:
        logger.error(f"Error accessing registry key '{rkey_path}': {e}")