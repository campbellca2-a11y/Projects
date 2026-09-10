"""
3-Mode Odometer Display
Like a car's dashboard: Master (lifetime), Recent (today), Current Trip (session)
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime


class OdometerDisplay(ttk.Frame):
    """Car-style odometer with 3 modes."""

    def __init__(self, parent, tracker, storage_data, daily_history, **kwargs):
        super().__init__(parent, **kwargs)
        self.tracker = tracker
        self.storage = storage_data
        self.history = daily_history
        self.mode = tk.StringVar(value="master")
        self.session_start_time = datetime.now()

        self._build_ui()

    def _build_ui(self):
        """Build the odometer interface."""
        # Mode selector (radio buttons)
        mode_frame = ttk.Frame(self)
        mode_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(mode_frame, text="Mode:", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))

        ttk.Radiobutton(
            mode_frame, text="🏔️ Master (Lifetime)", variable=self.mode, value="master",
            command=self._on_mode_changed
        ).pack(side="left", padx=5)

        ttk.Radiobutton(
            mode_frame, text="📅 Recent (Today)", variable=self.mode, value="recent",
            command=self._on_mode_changed
        ).pack(side="left", padx=5)

        ttk.Radiobutton(
            mode_frame, text="🚀 Trip (Session)", variable=self.mode, value="trip",
            command=self._on_mode_changed
        ).pack(side="left", padx=5)

        # Main odometer display
        self.display_frame = tk.Frame(self, bg="#1a1a2e", relief="sunken", bd=2)
        self.display_frame.pack(fill="both", expand=True, pady=10)

        # Title
        self.title_label = tk.Label(
            self.display_frame, text="MASTER ODOMETER",
            bg="#1a1a2e", fg="#E91E63", font=("Segoe UI", 11, "bold")
        )
        self.title_label.pack(pady=(10, 5))

        # Large mileage display
        self.odometer_frame = tk.Frame(self.display_frame, bg="#0f1419")
        self.odometer_frame.pack(fill="x", padx=20, pady=10)

        self.mileage_label = tk.Label(
            self.odometer_frame, text="0.00 km",
            bg="#0f1419", fg="#F06292", font=("Courier New", 48, "bold"),
            relief="sunken", bd=1, padx=20, pady=10
        )
        self.mileage_label.pack(fill="x")

        # Unit toggle
        self.unit_label = tk.Label(
            self.display_frame, text="kilometers",
            bg="#1a1a2e", fg="#999", font=("Segoe UI", 10)
        )
        self.unit_label.pack(pady=(0, 5))

        # Meta info
        self.meta_frame = tk.Frame(self.display_frame, bg="#1a1a2e")
        self.meta_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.meta_label = tk.Label(
            self.meta_frame, text="Started: 847 days ago | Last reset: Never",
            bg="#1a1a2e", fg="#666", font=("Segoe UI", 9)
        )
        self.meta_label.pack(anchor="w")

        # Secondary stats
        self.stats_frame = tk.Frame(self.display_frame, bg="#1a1a2e")
        self.stats_frame.pack(fill="x", padx=20, pady=(5, 10))

        self.clicks_label = tk.Label(
            self.stats_frame, text="Clicks: 0 | Scroll: 0",
            bg="#1a1a2e", fg="#888", font=("Segoe UI", 9)
        )
        self.clicks_label.pack(anchor="w")

    def _on_mode_changed(self):
        """Update display when mode changes."""
        self.update_display()

    def update_display(self, is_imperial=False):
        """Update the odometer display with current data."""
        mode = self.mode.get()
        pixels_to_meters = lambda px: self.tracker.pixels_to_meters(px)

        if mode == "master":
            snap = self.storage.get_snapshot()
            pixels = snap.get("total_pixels", 0)
            clicks = snap.get("total_clicks", 0)
            scroll = snap.get("total_scroll", 0)
            meters = pixels_to_meters(pixels)
            title = "MASTER ODOMETER"
            subtitle = "Lifetime Total"
            reset_info = "Last reset: Never"

        elif mode == "recent":
            today_data = self.history.get_today()
            pixels = today_data.get("pixels", 0)
            clicks = today_data.get("clicks", 0)
            scroll = today_data.get("scroll", 0)
            meters = pixels_to_meters(pixels)
            title = "TODAY'S ODOMETER"
            subtitle = "Daily Total"
            reset_info = "Resets: Daily at 12:00 AM"

        else:  # trip
            session_px, session_clicks, session_scroll = self.tracker.get_session_counters()
            pixels = session_px
            clicks = session_clicks
            scroll = session_scroll
            meters = pixels_to_meters(pixels)
            title = "CURRENT TRIP"
            subtitle = "This Session"
            elapsed_min = int((datetime.now() - self.session_start_time).total_seconds() / 60)
            reset_info = f"Session started: {elapsed_min // 60}h {elapsed_min % 60}m ago"

        # Format distance
        if is_imperial:
            miles = meters / 1609.344
            if miles < 1:
                dist_str = f"{meters * 3.28084:.2f} ft"
                unit_str = "feet"
            else:
                dist_str = f"{miles:.2f} mi"
                unit_str = "miles"
        else:
            if meters < 1:
                dist_str = f"{meters * 100:.0f} cm"
                unit_str = "centimeters"
            else:
                dist_str = f"{meters / 1000:.2f} km"
                unit_str = "kilometers"

        # Update labels
        self.title_label.config(text=title)
        self.mileage_label.config(text=dist_str)
        self.unit_label.config(text=unit_str)
        self.meta_label.config(text=reset_info)
        self.clicks_label.config(
            text=f"Clicks: {int(clicks):,} | Scroll: {int(scroll):,} steps"
        )

    def reset_session_timer(self):
        """Reset the session timer (called when session starts/resumes)."""
        self.session_start_time = datetime.now()
