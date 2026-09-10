import ctypes
import json
import os
import shutil
import sys

APP_NAME = "MouseMiles"
APP_VERSION = "3.1.0-achievements"

MM_PER_INCH = 25.4
DEFAULT_DPI = 96
AUTOSAVE_INTERVAL_MS = 5000
GUI_REFRESH_MS = 200
TELEPORT_THRESHOLD_PX = 500

# --- Paths ---

def get_legacy_app_dir():
    """Return the old portable folder used by MouseMiles v1/v2."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(os.path.abspath(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def get_app_dir():
    """Return the stable per-user data folder for MouseMiles 3."""
    base = (
        os.environ.get("LOCALAPPDATA")
        or os.environ.get("APPDATA")
        or os.path.expanduser("~")
    )
    path = os.path.join(base, APP_NAME)
    os.makedirs(path, exist_ok=True)
    return path


LEGACY_APP_DIR = get_legacy_app_dir()
APP_DIR = get_app_dir()
DATA_DIR = APP_DIR  # For achievements and other modules
DATA_FILE = os.path.join(APP_DIR, "tracker_v2.json")
HISTORY_FILE = os.path.join(APP_DIR, "history_v2.json")
CUSTOM_CAPSULES_FILE = os.path.join(APP_DIR, "custom_capsules.json")
SETTINGS_FILE = os.path.join(APP_DIR, "settings_v2.json")


def migrate_legacy_data():
    """Copy old portable data once; never overwrite newer AppData data."""
    if os.path.abspath(LEGACY_APP_DIR) == os.path.abspath(APP_DIR):
        return
    for filename in (
        "tracker_v2.json",
        "history_v2.json",
        "custom_capsules.json",
        "settings_v2.json",
    ):
        source = os.path.join(LEGACY_APP_DIR, filename)
        destination = os.path.join(APP_DIR, filename)
        if os.path.exists(source) and not os.path.exists(destination):
            try:
                shutil.copy2(source, destination)
            except Exception as exc:
                print(f"[config] migration skipped for {filename}: {exc}")


migrate_legacy_data()

# --- DPI Detection ---

def detect_dpi():
    """Query Windows for actual screen DPI. Fall back to 96."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    try:
        hdc = ctypes.windll.user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        if dpi and dpi > 0:
            return dpi
    except Exception:
        pass
    return DEFAULT_DPI


DEFAULT_SETTINGS = {
    "is_imperial": False,
    "always_on_top": True,
    "window_x": None,
    "window_y": None,
    "window_width": 520,
    "window_height": 760,
    "notifications_enabled": True,
}


def _safe_int(value, default=None):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def load_settings():
    saved = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
        except Exception:
            saved = {}
    merged = {**DEFAULT_SETTINGS, **saved}
    for key in ("window_x", "window_y", "window_width", "window_height"):
        if merged.get(key) is not None:
            merged[key] = _safe_int(merged[key], DEFAULT_SETTINGS[key])
    merged["window_width"] = max(420, merged.get("window_width") or 520)
    merged["window_height"] = max(560, merged.get("window_height") or 760)
    return merged


def save_settings(settings: dict):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        tmp = SETTINGS_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        os.replace(tmp, SETTINGS_FILE)
    except Exception as exc:
        print(f"[config] save_settings error: {exc}")