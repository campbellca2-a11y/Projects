import json
import os
import shutil
from datetime import date
from threading import Lock

from config import DATA_FILE, HISTORY_FILE


class AtomicJsonFile:
    """Write JSON atomically and retain one recoverable backup."""

    @staticmethod
    def save(filepath, data):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        tmp = filepath + ".tmp"
        bak = filepath + ".bak"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            if os.path.exists(filepath):
                shutil.copy2(filepath, bak)
            os.replace(tmp, filepath)
        except Exception as exc:
            print(f"[storage] atomic save error ({filepath}): {exc}")
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass

    @staticmethod
    def load(filepath, default=None):
        if default is None:
            default = {}
        for candidate in (filepath, filepath + ".bak"):
            if not os.path.exists(candidate):
                continue
            try:
                with open(candidate, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                continue
        return default


class TrackerData:
    """Thread-safe lifetime counter storage."""

    def __init__(self):
        self._lock = Lock()
        self.total_pixels = 0.0
        self.total_clicks = 0
        self.total_scroll = 0.0
        self.load()

    def load(self):
        data = AtomicJsonFile.load(DATA_FILE, {})
        with self._lock:
            try:
                self.total_pixels = max(0.0, float(data.get("total_pixels", 0.0)))
            except (TypeError, ValueError):
                self.total_pixels = 0.0
            try:
                self.total_clicks = max(0, int(data.get("total_clicks", 0)))
            except (TypeError, ValueError):
                self.total_clicks = 0
            try:
                self.total_scroll = max(0.0, float(data.get("total_scroll", 0.0)))
            except (TypeError, ValueError):
                self.total_scroll = 0.0

    def save(self):
        with self._lock:
            data = {
                "total_pixels": self.total_pixels,
                "total_clicks": self.total_clicks,
                "total_scroll": self.total_scroll,
            }
        AtomicJsonFile.save(DATA_FILE, data)

    def add_pixels(self, px):
        with self._lock:
            self.total_pixels += max(0.0, float(px))

    def add_click(self):
        with self._lock:
            self.total_clicks += 1

    def add_scroll(self, delta):
        with self._lock:
            self.total_scroll += max(0.0, float(abs(delta)))

    def get_snapshot(self):
        with self._lock:
            return {
                "total_pixels": self.total_pixels,
                "total_clicks": self.total_clicks,
                "total_scroll": self.total_scroll,
            }

    def reset(self):
        with self._lock:
            self.total_pixels = 0.0
            self.total_clicks = 0
            self.total_scroll = 0.0
        self.save()


class DailyHistory:
    """Stores per-day totals for historical tracking."""

    def __init__(self):
        self._lock = Lock()
        self.days = {}
        self._today_key = str(date.today())
        self._base_today = {"pixels": 0.0, "clicks": 0, "scroll": 0.0}
        self.load()
        self.start_session()

    @staticmethod
    def _clean_entry(entry):
        try:
            pixels = max(0.0, float(entry.get("pixels", 0.0)))
        except (TypeError, ValueError):
            pixels = 0.0
        try:
            clicks = max(0, int(entry.get("clicks", 0)))
        except (TypeError, ValueError):
            clicks = 0
        try:
            scroll = max(0.0, float(entry.get("scroll", 0.0)))
        except (TypeError, ValueError):
            scroll = 0.0
        return {"pixels": pixels, "clicks": clicks, "scroll": scroll}

    def load(self):
        data = AtomicJsonFile.load(HISTORY_FILE, {"days": {}})
        raw_days = data.get("days", {}) if isinstance(data, dict) else {}
        with self._lock:
            self.days = {
                day_key: self._clean_entry(entry)
                for day_key, entry in raw_days.items()
                if isinstance(entry, dict)
            }

    def save(self):
        with self._lock:
            data = {"days": dict(self.days)}
        AtomicJsonFile.save(HISTORY_FILE, data)

    def start_session(self):
        today = str(date.today())
        with self._lock:
            self._today_key = today
            self._base_today = self._clean_entry(
                self.days.get(today, {"pixels": 0.0, "clicks": 0, "scroll": 0.0})
            )

    def _rollover_if_needed(self):
        today = str(date.today())
        if today != self._today_key:
            self._today_key = today
            self._base_today = self._clean_entry(
                self.days.get(today, {"pixels": 0.0, "clicks": 0, "scroll": 0.0})
            )

    def update_session(self, session_pixels, session_clicks, session_scroll):
        with self._lock:
            self._rollover_if_needed()
            today = self._today_key
            self.days[today] = {
                "pixels": self._base_today["pixels"] + max(0.0, float(session_pixels)),
                "clicks": self._base_today["clicks"] + max(0, int(session_clicks)),
                "scroll": self._base_today["scroll"] + max(0.0, float(session_scroll)),
            }

    def commit_session(self, session_pixels, session_clicks, session_scroll):
        with self._lock:
            self._rollover_if_needed()
            today = self._today_key
            totals = {
                "pixels": self._base_today["pixels"] + max(0.0, float(session_pixels)),
                "clicks": self._base_today["clicks"] + max(0, int(session_clicks)),
                "scroll": self._base_today["scroll"] + max(0.0, float(session_scroll)),
            }
            self.days[today] = totals
            self._base_today = dict(totals)
            return totals

    def get_recent_days(self, n=7):
        with self._lock:
            sorted_keys = sorted(self.days.keys(), reverse=True)[:n]
            return [(key, self.days[key]) for key in reversed(sorted_keys)]

    def get_today(self):
        today = str(date.today())
        with self._lock:
            return dict(self.days.get(today, {"pixels": 0.0, "clicks": 0, "scroll": 0.0}))

    def reset(self):
        with self._lock:
            self.days = {}
            self._today_key = str(date.today())
            self._base_today = {"pixels": 0.0, "clicks": 0, "scroll": 0.0}
        self.save()