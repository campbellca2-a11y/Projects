import math
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading

from config import (
    APP_NAME, APP_VERSION, AUTOSAVE_INTERVAL_MS, GUI_REFRESH_MS,
    save_settings,
)
from capsules import CapsuleLibrary, get_scale_story
from notifications import MilestoneTracker, make_milestone_callback


class MouseMilesApp:
    """Main application window."""

    def __init__(self, root, tracker, storage_data, daily_history, settings, achievements_tracker=None):
        self.root = root
        self.tracker = tracker
        self.data = storage_data
        self.history = daily_history
        self.settings = settings
        self.achievements_tracker = achievements_tracker
        self.capsules = CapsuleLibrary()
        self.is_imperial = settings.get("is_imperial", False)

        # Milestones
        initial_meters = self.tracker.pixels_to_meters(self.data.get_snapshot()["total_pixels"])
        milestone_cb = make_milestone_callback(settings)
        self.milestones = MilestoneTracker(notify_callback=milestone_cb)
        self.milestones.set_initial_meters(initial_meters)

        # Window setup
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.resizable(True, True)
        self._apply_window_geometry()
        self._apply_topmost()

        # Tray support
        self._tray_icon = None
        self._tray_thread = None

        # Build UI
        self._dashboard_rows = {}
        self._build_ui()

        # Integrate achievements if available
        if self.achievements_tracker:
            from achievements_ui import integrate_achievements
            integrate_achievements(self)

        # Start loops
        self._update_gui()
        self._autosave()

        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Configure>", self._on_configure)

    # --- Window geometry ---

    def _apply_window_geometry(self):
        """Restore the window, but never leave it stranded off-screen."""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        try:
            w = int(self.settings.get("window_width", 520))
            h = int(self.settings.get("window_height", 760))
        except (TypeError, ValueError):
            w, h = 520, 760
        w = max(420, min(w, max(420, screen_w - 40)))
        h = max(560, min(h, max(560, screen_h - 80)))
        x = self.settings.get("window_x")
        y = self.settings.get("window_y")
        try:
            x = int(x) if x is not None else None
            y = int(y) if y is not None else None
        except (TypeError, ValueError):
            x, y = None, None
        if x is None or y is None or x < -w + 80 or x > screen_w - 80 or y < -h + 80 or y > screen_h - 80:
            x = max(0, (screen_w - w) // 2)
            y = max(0, (screen_h - h) // 2)
        self.root.geometry(f"{w}x{h}+{x}+{y}")
    def _apply_topmost(self):
        on_top = self.settings.get("always_on_top", True)
        self.root.attributes("-topmost", on_top)

    def _on_configure(self, event):
        if event.widget == self.root:
            self.settings["window_x"] = self.root.winfo_x()
            self.settings["window_y"] = self.root.winfo_y()
            self.settings["window_width"] = self.root.winfo_width()
            self.settings["window_height"] = self.root.winfo_height()

    # --- UI Construction ---

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Data.TLabel", font=("Segoe UI", 11))
        style.configure("Bold.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Session.TLabel", font=("Segoe UI", 9), foreground="#555555")
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("History.TLabel", font=("Segoe UI", 9))

        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Dashboard
        self._build_dashboard_tab()

        # Tab 2: History
        self._build_history_tab()

        # Tab 3: Settings
        self._build_settings_tab()

        # Bottom bar
        self._build_bottom_bar()

    def _build_dashboard_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Dashboard")

        # Scrollable area
        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        self.dash_frame = ttk.Frame(canvas)

        self.dash_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=self.dash_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Bind mousewheel to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        # Hero journey: one visual answer before the comparison library.
        hero = tk.Frame(self.dash_frame, bg="#101827", padx=14, pady=12)
        hero.pack(fill="x", pady=(0, 10))
        tk.Label(hero, text="YOUR MOUSE JOURNEY", bg="#101827", fg="#8fa9c9", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self._journey_distance_label = tk.Label(hero, text="Move the mouse to begin", bg="#101827", fg="#f8fafc", font=("Segoe UI", 22, "bold"), anchor="w")
        self._journey_distance_label.pack(anchor="w", pady=(2, 0))
        self._journey_detail_label = tk.Label(hero, text="Your path will grow here as you work.", bg="#101827", fg="#cbd5e1", font=("Segoe UI", 10), anchor="w", justify="left")
        self._journey_detail_label.pack(anchor="w", pady=(2, 6))
        self._journey_canvas = tk.Canvas(hero, height=105, bg="#101827", highlightthickness=0)
        self._journey_canvas.pack(fill="x", expand=True)
        self._journey_state_label = tk.Label(hero, text="Tracking is active", bg="#101827", fg="#79d7b1", font=("Segoe UI", 9), anchor="w")
        self._journey_state_label.pack(side="left", anchor="w", pady=(5, 0))
        self._pause_button = ttk.Button(hero, text="Pause Tracking", command=self._toggle_pause)
        self._pause_button.pack(side="right", pady=(4, 0))
        # Highlights
        highlight_frame = ttk.LabelFrame(self.dash_frame, text="Highlights", padding=5)
        highlight_frame.pack(fill="x", pady=(0, 8))
        self._lifetime_label = ttk.Label(highlight_frame, text="--", style="Data.TLabel")
        self._lifetime_label.pack(anchor="w")
        self._today_label = ttk.Label(highlight_frame, text="--", style="Data.TLabel")
        self._today_label.pack(anchor="w")

        # Session stats at top
        session_frame = ttk.LabelFrame(self.dash_frame, text="This Session", padding=5)
        session_frame.pack(fill="x", pady=(0, 8))
        self._session_label = ttk.Label(session_frame, text="--", style="Session.TLabel")
        self._session_label.pack(anchor="w")

        # Idle indicator
        self._idle_label = ttk.Label(session_frame, text="", style="Session.TLabel")
        self._idle_label.pack(anchor="w")

        ttk.Label(self.dash_frame, text="Scale Library — explore more comparisons", style="Header.TLabel").pack(anchor="w", pady=(6, 2))
        ttk.Separator(self.dash_frame, orient="horizontal").pack(fill="x", pady=(0, 6))

        # Capsule rows
        for name in self.capsules.get_names():
            row_frame = ttk.LabelFrame(self.dash_frame, text=name, padding=5)
            row_frame.pack(fill="x", pady=3)

            lbl = ttk.Label(row_frame, text="--", style="Data.TLabel")
            lbl.pack(anchor="w")

            pbar = None
            if name != "Raw Metrics":
                pbar = ttk.Progressbar(row_frame, orient="horizontal", length=100, mode="determinate")
                pbar.pack(fill="x", pady=(4, 0))

            self._dashboard_rows[name] = {"label": lbl, "pbar": pbar, "frame": row_frame}

    def _build_history_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="History")

        ttk.Label(tab, text="Last 7 Days", style="Header.TLabel").pack(anchor="w", pady=(0, 10))

        self._history_frame = ttk.Frame(tab)
        self._history_frame.pack(fill="both", expand=True)

        # Chart canvas
        self._history_canvas = tk.Canvas(self._history_frame, height=200, bg="#f9f9f9", highlightthickness=1, highlightbackground="#cccccc")
        self._history_canvas.pack(fill="x", pady=(0, 10))

        # Details list
        self._history_list_frame = ttk.Frame(self._history_frame)
        self._history_list_frame.pack(fill="x")

    def _build_settings_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Settings")

        # Always on top
        self._topmost_var = tk.BooleanVar(value=self.settings.get("always_on_top", True))
        ttk.Checkbutton(
            tab, text="Always on top", variable=self._topmost_var,
            command=self._toggle_topmost
        ).pack(anchor="w", pady=3)

        # Notifications
        self._notif_var = tk.BooleanVar(value=self.settings.get("notifications_enabled", True))
        ttk.Checkbutton(
            tab, text="Milestone notifications", variable=self._notif_var,
            command=self._toggle_notifications
        ).pack(anchor="w", pady=3)

        # DPI display
        ttk.Separator(tab, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(tab, text=f"Detected DPI: {self.tracker.dpi}", style="Bold.TLabel").pack(anchor="w")
        ttk.Label(tab, text=f"Pixel pitch: {self.tracker.pixel_pitch_mm:.4f} mm", style="Data.TLabel").pack(anchor="w")

        # Custom capsules section
        ttk.Separator(tab, orient="horizontal").pack(fill="x", pady=10)
        ttk.Label(tab, text="Custom Comparisons", style="Bold.TLabel").pack(anchor="w", pady=(0, 5))

        btn_frame = ttk.Frame(tab)
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="Add Custom", command=self._add_custom_capsule).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="Remove Custom", command=self._remove_custom_capsule).pack(side="left")

        self._custom_listbox = tk.Listbox(tab, height=5)
        self._custom_listbox.pack(fill="x", pady=5)
        self._refresh_custom_listbox()

        # Reset section
        ttk.Separator(tab, orient="horizontal").pack(fill="x", pady=10)
        reset_btn = ttk.Button(tab, text="Reset All Data", command=self._confirm_reset)
        reset_btn.pack(anchor="w")

        # Minimize to tray
        ttk.Separator(tab, orient="horizontal").pack(fill="x", pady=10)
        ttk.Button(tab, text="Minimize to Tray", command=self._minimize_to_tray).pack(anchor="w")

    def _build_bottom_bar(self):
        bottom = ttk.Frame(self.root, padding=0)
        bottom.pack(fill="x", side="bottom")
        bottom.columnconfigure(0, weight=1)
        bottom.columnconfigure(1, weight=1)

        self._sys_label = ttk.Label(
            bottom, text="", anchor="center", background="#e1e1e1", padding=8
        )
        self._sys_label.grid(row=0, column=0, sticky="ew")

        self._unit_btn = ttk.Button(bottom, text="Switch Units", command=self._toggle_units)
        self._unit_btn.grid(row=0, column=1, sticky="ew", ipady=4)

        self._update_sys_label()

    # --- Settings callbacks ---

    def _toggle_topmost(self):
        val = self._topmost_var.get()
        self.settings["always_on_top"] = val
        self.root.attributes("-topmost", val)

    def _toggle_notifications(self):
        self.settings["notifications_enabled"] = self._notif_var.get()

    def _toggle_units(self):
        self.is_imperial = not self.is_imperial
        self.settings["is_imperial"] = self.is_imperial
        self._update_sys_label()

    def _update_sys_label(self):
        text = "IMPERIAL" if self.is_imperial else "METRIC"
        self._sys_label.config(text=f"System: {text}")

    def _toggle_pause(self):
        paused = not self.tracker.is_paused
        self.tracker.set_paused(paused)
        self._pause_button.config(text="Resume Tracking" if paused else "Pause Tracking")
        self._journey_state_label.config(
            text="Tracking is paused" if paused else "Tracking is active",
            fg="#f6c85f" if paused else "#79d7b1",
        )

    def _update_journey_visual(self, meters):
        story = get_scale_story(meters)
        self._journey_distance_label.config(text=story["headline"])
        self._journey_detail_label.config(text=story["detail"])
        canvas = self._journey_canvas
        canvas.delete("all")
        width = max(260, canvas.winfo_width())
        left, right, y = 20, width - 20, 58
        canvas.create_line(left, y, right, y, fill="#334155", width=4)
        for fraction in (0.0, 0.25, 0.5, 0.75, 1.0):
            x = left + (right - left) * fraction
            canvas.create_line(x, y - 8, x, y + 8, fill="#64748b", width=1)
        target = max(float(story.get("next_m", 1.0)), 0.001)
        ratio = min(1.0, max(0.0, meters / target))
        marker_x = left + (right - left) * ratio
        if marker_x > left:
            canvas.create_line(left, y, marker_x, y, fill="#56c7c5", width=6)
        canvas.create_oval(marker_x - 8, y - 8, marker_x + 8, y + 8, fill="#f6c85f", outline="#fff1ad", width=2)
        canvas.create_text(left, 88, text="START", anchor="w", fill="#94a3b8", font=("Segoe UI", 8, "bold"))
        canvas.create_text(right, 88, text=story.get("next_label", "NEXT"), anchor="e", fill="#94a3b8", font=("Segoe UI", 8, "bold"))
    # --- Custom capsules ---

    def _refresh_custom_listbox(self):
        self._custom_listbox.delete(0, tk.END)
        for c in self.capsules._custom:
            self._custom_listbox.insert(tk.END, f"{c.name}  ({c.target_m:,.1f} m)")

    def _add_custom_capsule(self):
        name = simpledialog.askstring("Custom Capsule", "Name (e.g. 'My Street'):", parent=self.root)
        if not name:
            return
        dist = simpledialog.askfloat("Custom Capsule", "Distance in meters:", parent=self.root, minvalue=0.01)
        if not dist:
            return
        self.capsules.add_custom(name, dist)
        self._refresh_custom_listbox()
        self._rebuild_dashboard_rows()

    def _remove_custom_capsule(self):
        sel = self._custom_listbox.curselection()
        if not sel:
            messagebox.showinfo("Remove", "Select a custom capsule first.", parent=self.root)
            return
        idx = sel[0]
        name = self.capsules._custom[idx].name
        self.capsules.remove_custom(name)
        self._refresh_custom_listbox()
        self._rebuild_dashboard_rows()

    def _rebuild_dashboard_rows(self):
        """Destroy and recreate capsule rows after adding/removing custom capsules."""
        # Remove old rows that are no longer in the capsule list
        current_names = set(self.capsules.get_names())
        for name in list(self._dashboard_rows.keys()):
            if name not in current_names and name != "__session__":
                self._dashboard_rows[name]["frame"].destroy()
                del self._dashboard_rows[name]

        # Add new rows that don't exist yet
        for name in self.capsules.get_names():
            if name not in self._dashboard_rows:
                row_frame = ttk.LabelFrame(self.dash_frame, text=name, padding=5)
                row_frame.pack(fill="x", pady=3)
                lbl = ttk.Label(row_frame, text="--", style="Data.TLabel")
                lbl.pack(anchor="w")
                pbar = ttk.Progressbar(row_frame, orient="horizontal", length=100, mode="determinate")
                pbar.pack(fill="x", pady=(4, 0))
                self._dashboard_rows[name] = {"label": lbl, "pbar": pbar, "frame": row_frame}

    # --- Reset ---

    def _confirm_reset(self):
        if messagebox.askyesno("Reset", "Reset ALL tracking data to zero?\nThis cannot be undone.", parent=self.root):
            self.data.reset()
            self.history.reset()
            self.tracker.reset_session()
            self._rebuild_dashboard_rows()

    # --- Tray ---

    def _minimize_to_tray(self):
        try:
            import pystray
            from PIL import Image, ImageDraw
        except ImportError:
            messagebox.showinfo(
                "Tray",
                "System tray requires 'pystray' and 'Pillow'.\n\npip install pystray Pillow",
                parent=self.root,
            )
            return

        self.root.withdraw()

        # Create a simple icon
        img = Image.new("RGB", (64, 64), color="#4a90d9")
        draw = ImageDraw.Draw(img)
        draw.text((16, 18), "MM", fill="white")

        def on_show(icon, item):
            icon.stop()
            self.root.after(0, self.root.deiconify)

        def on_quit(icon, item):
            icon.stop()
            self.root.after(0, self._on_close)

        menu = pystray.Menu(
            pystray.MenuItem("Show", on_show, default=True),
            pystray.MenuItem("Quit", on_quit),
        )
        self._tray_icon = pystray.Icon(APP_NAME, img, APP_NAME, menu)

        self._tray_thread = threading.Thread(target=self._tray_icon.run, daemon=True)
        self._tray_thread.start()

    # --- GUI update loop ---

    def _update_gui(self):
        snap = self.data.get_snapshot()
        meters = self.tracker.pixels_to_meters(snap["total_pixels"])

        # Check milestones
        self.milestones.check(meters)

        # Update capsule rows
        for name, widgets in self._dashboard_rows.items():
            text, pct = self.capsules.get_data(
                name, meters, snap["total_pixels"],
                snap["total_clicks"], snap["total_scroll"],
                self.is_imperial,
            )
            widgets["label"].config(text=text)
            if widgets["pbar"]:
                widgets["pbar"]["value"] = pct

        # Highlights
        lifetime_dist = CapsuleLibrary._dist_str(meters, self.is_imperial)
        self._lifetime_label.config(text=f"Lifetime distance: {lifetime_dist}")
        today_px = self.history.get_today().get("pixels", 0.0)
        today_m = self.tracker.pixels_to_meters(today_px)
        today_dist = CapsuleLibrary._dist_str(today_m, self.is_imperial)
        self._today_label.config(text=f"Today's distance: {today_dist}")
        self._update_journey_visual(today_m)

        # Session stats
        sess_px, sess_clicks, sess_scroll = self.tracker.get_session_counters()
        sess_m = self.tracker.pixels_to_meters(sess_px)
        sess_dist = CapsuleLibrary._dist_str(sess_m, self.is_imperial)
        self._session_label.config(
            text=f"Distance: {sess_dist}  |  Clicks: {int(sess_clicks):,}  |  Scroll: {int(sess_scroll):,}"
        )

        # Idle indicator
        if self.tracker.is_idle:
            self._idle_label.config(text="(idle - mouse inactive for 5+ min)")
        else:
            self._idle_label.config(text="")

        # Schedule next
        self.root.after(GUI_REFRESH_MS, self._update_gui)

    # --- History tab update ---

    def _update_history(self):
        days = self.history.get_recent_days(7)

        # Update the canvas bar chart
        self._history_canvas.delete("all")
        cw = self._history_canvas.winfo_width()
        ch = self._history_canvas.winfo_height()
        if cw < 10 or ch < 10 or not days:
            return

        max_px = max((d[1].get("pixels", 0) for d in days), default=1) or 1
        bar_width = max((cw - 40) // max(len(days), 1), 10)
        padding = 20

        for i, (day_str, day_data) in enumerate(days):
            px = day_data.get("pixels", 0)
            # Square-root scaling keeps quiet days visible beside busy days.
            bar_h = math.sqrt(px / max_px) * (ch - 40) if max_px > 0 else 0
            x0 = padding + i * (bar_width + 4)
            x1 = x0 + bar_width
            y1 = ch - 20
            y0 = y1 - bar_h

            self._history_canvas.create_rectangle(x0, y0, x1, y1, fill="#4a90d9", outline="#3a7bc8")
            # Date label
            short_date = day_str[5:]  # MM-DD
            self._history_canvas.create_text(
                (x0 + x1) / 2, ch - 8, text=short_date, font=("Segoe UI", 7)
            )

        # Clear and rebuild details list
        for w in self._history_list_frame.winfo_children():
            w.destroy()

        for day_str, day_data in reversed(days):
            px = day_data.get("pixels", 0)
            m = self.tracker.pixels_to_meters(px)
            dist = CapsuleLibrary._dist_str(m, self.is_imperial)
            clicks = int(day_data.get("clicks", 0))
            ttk.Label(
                self._history_list_frame,
                text=f"{day_str}:  {dist}  |  {clicks:,} clicks",
                style="History.TLabel",
            ).pack(anchor="w")

    # --- Autosave loop ---

    def _autosave(self):
        self.data.save()

        # Update daily history
        sess_px, sess_clicks, sess_scroll = self.tracker.get_session_counters()
        self.history.update_session(sess_px, sess_clicks, sess_scroll)
        self.history.save()

        save_settings(self.settings)

        # Refresh history tab
        self._update_history()

        self.root.after(AUTOSAVE_INTERVAL_MS, self._autosave)

    # --- Shutdown ---

    def _on_close(self):
        # Final save
        self.data.save()
        save_settings(self.settings)

        # Record session into daily history baseline for next session
        sess_px, sess_clicks, sess_scroll = self.tracker.get_session_counters()
        self.history.commit_session(sess_px, sess_clicks, sess_scroll)
        self.history.save()

        self.tracker.stop()
        self.root.destroy()
