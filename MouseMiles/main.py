"""
MouseMiles v3.1
Tracks mouse movement, clicks, and scroll — shows fun real-world comparisons.

Features:
  - Accurate DPI detection
  - Thread-safe tracking with teleport filtering
  - Click and scroll tracking
  - Session vs. all-time stats
  - Daily history with bar chart
  - RIDICULOUS achievement system with confetti celebrations 🎉
  - System tray support (requires pystray + Pillow)
  - Custom user-defined capsules
  - Always-on-top toggle
  - Window position memory
  - Atomic saves with .bak backup
  - Idle detection
  - Reset button

Built by: Bill
Enhanced with Ridiculous Achievements by Claude
Local-only | No internet | No data collection
"""

import tkinter as tk
from storage import TrackerData, DailyHistory
from tracker import MouseTracker
from config import load_settings
from achievements import AchievementTracker
from ui import MouseMilesApp


def main():
    # Load persistent data
    settings = load_settings()
    storage_data = TrackerData()
    daily_history = DailyHistory()
    achievements = AchievementTracker()

    # Initialize tracker
    tracker = MouseTracker(storage_data)
    tracker.start()

    # Build GUI
    root = tk.Tk()
    app = MouseMilesApp(root, tracker, storage_data, daily_history, settings, achievements)
    root.mainloop()


if __name__ == "__main__":
    main()
