import math
import threading
import time
from pynput import mouse

from config import TELEPORT_THRESHOLD_PX, MM_PER_INCH, detect_dpi


class MouseTracker:
    """Thread-safe mouse movement, click, and scroll tracker."""

    def __init__(self, storage_data):
        self.data = storage_data
        self.dpi = detect_dpi()
        self.pixel_pitch_mm = MM_PER_INCH / self.dpi

        self._last_x = None
        self._last_y = None
        self._session_pixels = 0.0
        self._session_clicks = 0
        self._session_scroll = 0.0
        self._session_lock = threading.Lock()

        self._last_move_time = time.time()
        self._idle_threshold = 300
        self._paused = False
        self._state_lock = threading.Lock()

        self._listener = None
        self._running = False

    def start(self):
        self._running = True
        self._listener = mouse.Listener(
            on_move=self._on_move,
            on_click=self._on_click,
            on_scroll=self._on_scroll,
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()
            try:
                self._listener.join(timeout=1.0)
            except Exception:
                pass

    def pixels_to_meters(self, pixels):
        return max(0.0, pixels) * self.pixel_pitch_mm / 1000.0

    @property
    def is_paused(self):
        with self._state_lock:
            return self._paused

    def set_paused(self, paused):
        with self._state_lock:
            self._paused = bool(paused)
        # Clear the previous point so resuming cannot count a jump as movement.
        if paused:
            self._last_x = None
            self._last_y = None

    @property
    def is_idle(self):
        if self.is_paused:
            return False
        return (time.time() - self._last_move_time) > self._idle_threshold

    def get_session_counters(self):
        with self._session_lock:
            return self._session_pixels, self._session_clicks, self._session_scroll

    def reset_session(self):
        with self._session_lock:
            self._session_pixels = 0.0
            self._session_clicks = 0
            self._session_scroll = 0.0
    # --- Listener callbacks ---

    def _on_move(self, x, y):
        if self.is_paused:
            self._last_x = None
            self._last_y = None
            return

        if self._last_x is not None and self._last_y is not None:
            dx = x - self._last_x
            dy = y - self._last_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < TELEPORT_THRESHOLD_PX:
                self.data.add_pixels(dist)
                with self._session_lock:
                    self._session_pixels += dist

        self._last_x = x
        self._last_y = y
        self._last_move_time = time.time()

    def _on_click(self, x, y, button, pressed):
        if pressed and not self.is_paused:
            self.data.add_click()
            with self._session_lock:
                self._session_clicks += 1

    def _on_scroll(self, x, y, dx, dy):
        if not self.is_paused:
            delta = abs(dy)
            self.data.add_scroll(delta)
            with self._session_lock:
                self._session_scroll += delta