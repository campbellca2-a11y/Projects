import threading

# Milestones: (name, threshold_in_meters)
MILESTONES = [
    ("First Steps",          10),
    ("100 Meters",           100),
    ("One Kilometer",        1000),
    ("A Marathon",           42195),
    ("Mount Everest",        8849),
    ("100 Kilometers",       100000),
    ("1,000 Kilometers",     1000000),
    ("Earth's Circumference", 40075000),
    ("To The Moon",          384400000),
]


class MilestoneTracker:
    """Tracks which milestones have been reached and fires notifications."""

    def __init__(self, notify_callback=None):
        self._reached = set()
        self._callback = notify_callback  # fn(title, message)
        self._lock = threading.Lock()

    def set_initial_meters(self, meters):
        """Mark all milestones already passed (from loaded data) as reached without notifying."""
        with self._lock:
            for name, threshold in MILESTONES:
                if meters >= threshold:
                    self._reached.add(name)

    def check(self, meters):
        """Check current meters against milestones, fire callback for new ones."""
        with self._lock:
            for name, threshold in MILESTONES:
                if name not in self._reached and meters >= threshold:
                    self._reached.add(name)
                    if self._callback:
                        self._callback(name, threshold)


def show_windows_toast(title, message):
    """Show a Windows 10/11 toast notification. Fails silently if unavailable."""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            f"MouseMiles - {title}",
            message,
            duration=5,
            threaded=True,
        )
    except ImportError:
        # win10toast not installed — fall back to a simpler approach
        try:
            import ctypes
            ctypes.windll.user32.MessageBeep(0x00000040)  # MB_ICONINFORMATION beep
        except Exception:
            pass
    except Exception:
        pass


def make_milestone_callback(settings):
    """Return a callback function that shows a toast when a milestone is hit."""
    def callback(name, threshold_m):
        if not settings.get("notifications_enabled", True):
            return
        if threshold_m >= 1000:
            dist_str = f"{threshold_m / 1000:,.1f} km"
        else:
            dist_str = f"{threshold_m:,.0f} m"
        message = f"You've traveled {dist_str} with your mouse!"
        show_windows_toast(name, message)
    return callback
