"""
Achievement UI integration for MouseMiles.
Patches the main app to add achievement checking and celebration UI.
"""

import tkinter as tk
from datetime import datetime
from achievements import ALL_ACHIEVEMENTS
from celebrations import ConfettiAnimation, AchievementToast, AchievementBadgeBar


def integrate_achievements(app):
    """
    Integrate achievement system into the MouseMilesApp.
    Call this after the app is initialized but before mainloop.
    """
    # Store reference to achievements
    app.achievements = app.achievements_tracker  # alias for convenience
    app.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    app.last_achievement_check = {}

    # Add achievement badge bar to dashboard
    try:
        app._achievement_badge_bar = AchievementBadgeBar(app.dash_frame)
        badge_frame = app._achievement_badge_bar.get_frame()
        badge_frame.pack(fill="x", pady=(0, 10))
        app._achievement_badge_bar.update()
    except Exception as e:
        print(f"[achievements_ui] badge bar setup error: {e}")

    # Patch the update loop to check achievements
    app._original_update_gui = app._update_gui
    app._update_gui = lambda: _patched_update_gui(app)


def _patched_update_gui(app):
    """Enhanced update loop that checks achievements."""
    _check_achievements(app)
    app._original_update_gui()


def _check_achievements(app):
    """Check if any achievements should be unlocked."""
    try:
        snap = app.data.get_snapshot()
        session_px, session_clicks, session_scroll = app.tracker.get_session_counters()
        today_data = app.history.get_today()

        # Check each achievement
        for ach in ALL_ACHIEVEMENTS:
            # Skip if already unlocked this period
            if app.achievements.is_unlocked(ach.name, app.session_id, ach.unlock_period):
                continue

            # Check conditions
            should_unlock = False

            # TIER 1: Session-based
            if ach.metric_type == "pixels" and session_px >= ach.threshold:
                should_unlock = True
            elif ach.metric_type == "clicks" and session_clicks >= ach.threshold:
                should_unlock = True
            elif ach.metric_type == "scroll" and session_scroll >= ach.threshold:
                should_unlock = True

            # TIER 2: Daily behavioral
            elif ach.metric_type == "daily_pixels_before_10am":
                hour = datetime.now().hour
                if hour < 10 and today_data.get("pixels", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "daily_clicks_before_9am":
                hour = datetime.now().hour
                if hour < 9 and today_data.get("clicks", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "daily_pixels_lunch":
                hour = datetime.now().hour
                if 11 <= hour < 13 and today_data.get("pixels", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "daily_clicks_afternoon":
                hour = datetime.now().hour
                if 13 <= hour < 15 and today_data.get("clicks", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "daily_pixels_after_8pm":
                hour = datetime.now().hour
                if hour >= 20 and today_data.get("pixels", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "daily_pixels_total":
                if today_data.get("pixels", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "daily_pixels_no_pause":
                if not app.tracker.is_paused and today_data.get("pixels", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "no_long_idle":
                # Placeholder - would need to track idle events
                should_unlock = False

            # TIER 3: Session achievements
            elif ach.metric_type == "fast_5km":
                elapsed_ms = app.last_achievement_check.get('elapsed_ms', 0)
                # Only check if we've moved 5km in under 2 hours
                if session_px >= 5000000 and elapsed_ms < 2*3600*1000:
                    should_unlock = True
            elif ach.metric_type == "fast_scroll":
                if session_scroll >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "always_moving":
                # Would need detailed idle tracking
                should_unlock = False
            elif ach.metric_type == "session_duration":
                elapsed_ms = app.last_achievement_check.get('elapsed_ms', 0)
                if elapsed_ms >= ach.threshold * 1000:
                    should_unlock = True
            elif ach.metric_type == "consistent_pace":
                # Placeholder
                should_unlock = False

            # TIER 4: Lifetime achievements
            elif ach.metric_type == "lifetime_pixels":
                if snap.get("total_pixels", 0) >= ach.threshold:
                    should_unlock = True
            elif ach.metric_type == "day_streak":
                if app.achievements.day_streak >= ach.threshold:
                    should_unlock = True

            # Unlock if conditions met
            if should_unlock:
                if app.achievements.unlock_achievement(ach.name, app.session_id, ach.unlock_period):
                    # Show celebration!
                    _celebrate_achievement(app, ach)
                    # Update badge bar
                    if hasattr(app, '_achievement_badge_bar'):
                        app._achievement_badge_bar.update()

        # Update daily streak
        app.achievements.check_daily_streak()

    except Exception as e:
        print(f"[achievements_ui] check error: {e}")


def _celebrate_achievement(app, achievement):
    """Show confetti + toast for achievement."""
    try:
        # Confetti burst
        confetti = ConfettiAnimation(app.root, duration_ms=2000)
        confetti.start()

        # Toast notification
        toast = AchievementToast(app.root, achievement)
        toast.show()

    except Exception as e:
        print(f"[achievements_ui] celebrate error: {e}")
