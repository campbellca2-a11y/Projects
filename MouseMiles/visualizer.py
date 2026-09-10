"""
Data Visualizer for MouseMiles
Shows journey timeline, heatmap, and milestone history.
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta


class JourneyTimeline(ttk.Frame):
    """Simple line chart showing cumulative distance over time."""

    def __init__(self, parent, history, tracker, **kwargs):
        super().__init__(parent, **kwargs)
        self.history = history
        self.tracker = tracker
        self.canvas = tk.Canvas(self, bg="#f9f9f9", height=200, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event=None):
        """Redraw when window resizes."""
        self.draw_chart()

    def draw_chart(self):
        """Draw cumulative distance chart for last 14 days."""
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 50 or height < 50:
            return

        # Get data
        recent_days = self.history.get_recent_days(n=14)
        if not recent_days:
            self.canvas.create_text(
                width // 2, height // 2,
                text="No data yet. Start moving your mouse!",
                fill="#999", font=("Segoe UI", 10)
            )
            return

        # Calculate cumulative
        cumulative_km = []
        total = 0.0
        for date_str, data in reversed(recent_days):
            pixels = data.get("pixels", 0)
            meters = self.tracker.pixels_to_meters(pixels)
            total += meters
            cumulative_km.append(total / 1000.0)

        max_km = max(cumulative_km) if cumulative_km else 1.0
        if max_km == 0:
            max_km = 1.0

        # Draw axes
        margin = 40
        x_start, x_end = margin, width - 20
        y_start, y_end = height - margin, 20

        # Draw background grid
        for i in range(6):
            y = y_start - (y_start - y_end) * (i / 5.0)
            self.canvas.create_line(x_start, y, x_end, y, fill="#eee", width=1)

        # Draw axes
        self.canvas.create_line(x_start, y_start, x_end, y_start, fill="#333", width=2)
        self.canvas.create_line(x_start, y_start, x_start, y_end, fill="#333", width=2)

        # Draw data line
        points = []
        for i, km in enumerate(cumulative_km):
            x = x_start + (x_end - x_start) * (i / max(1, len(cumulative_km) - 1))
            y = y_start - (y_start - y_end) * (km / max(max_km, 1.0))
            points.append((x, y))

        if len(points) > 1:
            self.canvas.create_line(*[coord for point in points for coord in point],
                                  fill="#E91E63", width=2, smooth=True)

        # Draw points
        for x, y in points:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill="#F06292", outline="#E91E63")

        # Labels
        self.canvas.create_text(x_start - 15, y_end, text=f"{max_km:.1f}km", fill="#666", anchor="e", font=("Segoe UI", 8))
        self.canvas.create_text(x_start - 15, y_start, text="0 km", fill="#666", anchor="e", font=("Segoe UI", 8))
        self.canvas.create_text(x_start, y_start + 20, text="14d ago", fill="#666", anchor="n", font=("Segoe UI", 8))
        self.canvas.create_text(x_end, y_start + 20, text="Today", fill="#666", anchor="n", font=("Segoe UI", 8))

        # Title
        self.canvas.create_text(width // 2, 10, text="Cumulative Distance (Last 14 Days)",
                              fill="#333", font=("Segoe UI", 10, "bold"))


class ActivityHeatmap(ttk.Frame):
    """Simple heatmap showing time-of-day activity patterns."""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.canvas = tk.Canvas(self, bg="#f9f9f9", height=150, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.draw_heatmap()

    def draw_heatmap(self):
        """Draw a simple hour-based heatmap."""
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 50:
            return

        # Create 24-hour heatmap (placeholder data)
        # In real app, this would aggregate from history
        hours = list(range(24))
        max_activity = 100  # arbitrary scale

        # Simulate realistic activity (more during work hours)
        activity = [
            10, 5, 5, 5, 10, 30, 50, 70, 85, 90,  # 0-9
            85, 80, 75, 70, 85, 90, 85, 70, 60, 50,  # 10-19
            40, 30, 20, 15  # 20-23
        ]

        cell_width = width / 24
        cell_height = height - 30

        for i, act in enumerate(activity):
            x = i * cell_width
            intensity = min(1.0, act / max_activity)

            # Color gradient: blue (low) to pink (high)
            r = int(224 + (241 - 224) * intensity)
            g = int(30 + (98 - 30) * (1 - intensity))
            b = int(99 + (146 - 99) * (1 - intensity))
            color = f"#{r:02x}{g:02x}{b:02x}"

            self.canvas.create_rectangle(
                x, 0, x + cell_width, cell_height,
                fill=color, outline="#ddd"
            )

            # Hour label
            hour_str = f"{i:02d}"
            self.canvas.create_text(
                x + cell_width / 2, cell_height + 10,
                text=hour_str, fill="#666", font=("Segoe UI", 8)
            )

        # Title
        self.canvas.create_text(
            width / 2, cell_height + 25,
            text="Activity by Hour of Day (Heatmap)", fill="#333",
            font=("Segoe UI", 10, "bold")
        )


class StatsPanel(ttk.Frame):
    """Quick stats display."""

    def __init__(self, parent, storage_data, history, tracker, **kwargs):
        super().__init__(parent, **kwargs)
        self.storage = storage_data
        self.history = history
        self.tracker = tracker
        self._build_ui()

    def _build_ui(self):
        """Build stats panel."""
        ttk.Label(self, text="Quick Stats", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 10))

        # Get data
        snap = self.storage.get_snapshot()
        today = self.history.get_today()
        recent_7d = self.history.get_recent_days(7)

        lifetime_km = self.tracker.pixels_to_meters(snap.get("total_pixels", 0)) / 1000.0
        today_km = self.tracker.pixels_to_meters(today.get("pixels", 0)) / 1000.0

        avg_km_per_day = lifetime_km / max(1, len(recent_7d)) if recent_7d else 0

        # Stats grid
        stats_data = [
            ("🎯 Lifetime", f"{lifetime_km:,.1f} km"),
            ("📅 Today", f"{today_km:,.1f} km"),
            ("📊 7-day avg", f"{avg_km_per_day:,.1f} km/day"),
            ("🖱️ Total Clicks", f"{snap.get('total_clicks', 0):,}"),
            ("📜 Total Scrolls", f"{int(snap.get('total_scroll', 0)):,}"),
        ]

        for label, value in stats_data:
            frame = ttk.Frame(self)
            frame.pack(fill="x", pady=3)

            ttk.Label(frame, text=label, font=("Segoe UI", 9)).pack(side="left", width=20)
            ttk.Label(frame, text=value, font=("Segoe UI", 9, "bold"), foreground="#E91E63").pack(side="right")
