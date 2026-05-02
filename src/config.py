import sys
import os
from pathlib import Path

APP_NAME = "Sage Bluetooth"
APP_VERSION = "1.0.0"

WINDOW_WIDTH = 400
WINDOW_HEIGHT = 600

TITLE_BAR_HEIGHT = 36
CONTROL_PANEL_HEIGHT = 52

SCAN_TIMEOUT = 10.0
MAX_DEVICES = 50

BATTERY_POLL_INTERVAL = 60
MAX_CONNECT_RETRIES = 3
CONNECT_RETRY_DELAY = 1.0

BLUETOOTH_ON_ICON = "bluetooth_on.png"
BLUETOOTH_OFF_ICON = "bluetooth_off.png"
APP_ICON = "app.ico"

USER_DATA_DIR = Path.home() / ".sage-bluetooth"
LOG_DIR = USER_DATA_DIR / "logs"
CONFIG_PATH = USER_DATA_DIR / "config.json"

STATUS_INDICATOR_COLORS = {
    "on": "#4CAF50",
    "off": "#F44336",
    "busy": "#FFC107",
}

BATTERY_COLORS = {
    "good": "#4CAF50",
    "medium": "#FF9800",
    "low": "#F44336",
}

RSSI_RANGES = [
    (-30, -50, 10),
    (-51, -60, 8),
    (-61, -70, 6),
    (-71, -80, 4),
    (-81, -90, 2),
    (-91, -200, 1),
]


def get_resource_path(relative_path: str) -> str:
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "resources")
    return os.path.join(base_path, relative_path)


def check_admin_privilege() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


import ctypes
