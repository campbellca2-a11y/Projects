"""
Celebration animations for achievement unlocks.
Confetti, toasts, badge popins.
"""

import tkinter as tk
import random
import math
from datetime import datetime, timedelta


class ConfettiParticle:
    """Single confetti piece."""

    def __init__(self, x, y, vx, vy, color, rotation_speed):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.rotation = 0
        self.rotation_speed = rotation_speed
        self.life = 1.0  # 0-1, fades out
        self.gravity = 0.2


class ConfettiAnimation:
    """Burst confetti animation from center of window."""

    def __init__(self, root, duration_ms=2000):
        self.root = root
        self.duration_ms = duration_ms
        self.canvas = None
        self.particles = []
        self.start_time = None
        self.animation_id = None
        self.colors = ["#E91E63", "#F06292", "#FF1744", "#FF6B6B", "#FFD93D", "#6BCF7F", "#00BCD4"]

    def start(self):
        """Start the confetti burst."""
        # Create overlay canvas
        self.canvas = tk.Canvas(
            self.root,
            bg="",
            highlightthickness=0,
            relief="flat"
        )
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)

        w = self.root.winfo_width()
        h = self.root.winfo_height()

        # Create particles from center
        center_x = w / 2
        center_y = h / 2
        num_particles = 40

        for _ in range(num_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(3, 8)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 2  # slight upward bias

            particle = ConfettiParticle(
                center_x, center_y, vx, vy,
                random.choice(self.colors),
                random.uniform(-10, 10)
            )
            self.particles.append(particle)

        self.start_time = datetime.now()
        self._animate_frame()

    def _animate_frame(self):
        """Update and draw particles."""
        if not self.canvas:
            return

        elapsed = (datetime.now() - self.start_time).total_seconds() * 1000
        progress = min(1.0, elapsed / self.duration_ms)

        w = self.root.winfo_width()
        h = self.root.winfo_height()

        # Update particles
        for particle in self.particles:
            particle.vy += particle.gravity
            particle.x += particle.vx
            particle.y += particle.vy
            particle.rotation += particle.rotation_speed
            particle.life = max(0, 1.0 - progress * 1.2)

        # Draw
        self.canvas.delete("all")

        for particle in self.particles:
            if particle.life > 0:
                # Fade color
                alpha = int(255 * particle.life)
                hex_color = particle.color

                # Draw confetti square (rotated)
                size = 6
                x, y = particle.x, particle.y

                # Simple square (no rotation support in tkinter canvas by default)
                self.canvas.create_rectangle(
                    x - size, y - size, x + size, y + size,
                    fill=hex_color, outline=hex_color
                )

        # Continue animation or stop
        if progress < 1.0:
            self.animation_id = self.root.after(16, self._animate_frame)
        else:
            self.stop()

    def stop(self):
        """Stop animation and clean up."""
        if self.animation_id:
            self.root.after_cancel(self.animation_id)
            self.animation_id = None

        if self.canvas:
            self.canvas.destroy()
            self.canvas = None


class AchievementToast:
    """Toast notification for achievement unlock."""

    TOAST_HEIGHT = 80
    TOAST_WIDTH = 300
    TOAST_DURATION_MS = 3000

    def __init__(self, root, achievement, on_close_callback=None):
        self.root = root
        self.achievement = achievement
        self.on_close_callback = on_close_callback
        self.window = None
        self.animation_id = None

    def show(self):
        """Show the toast at bottom-right of screen."""
        # Create small window
        self.window = tk.Toplevel(self.root)
        self.window.attributes("-topmost", True)
        self.window.attributes("-alpha", 0.95)
        self.window.geometry(f"{self.TOAST_WIDTH}x{self.TOAST_HEIGHT}+0+0")

        # Position at bottom-right
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = self.root.winfo_x() + w - self.TOAST_WIDTH - 20
        y = self.root.winfo_y() + h - self.TOAST_HEIGHT - 20
        self.window.geometry(f"{self.TOAST_WIDTH}x{self.TOAST_HEIGHT}+{x}+{y}")

        # Remove decorations
        self.window.overrideredirect(True)

        # Content frame
        frame = tk.Frame(self.window, bg="#1a1a1a", relief="flat", bd=1)
        frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Achievement badge
        badge_frame = tk.Frame(frame, bg="#E91E63", height=40)
        badge_frame.pack(fill="x")

        icon_label = tk.Label(
            badge_frame, text=self.achievement.icon, font=("Segoe UI", 24),
            bg="#E91E63", fg="white"
        )
        icon_label.pack(side="left", padx=10, pady=5)

        tk.Label(
            badge_frame, text="ACHIEVEMENT UNLOCKED!",
            font=("Segoe UI", 10, "bold"), bg="#E91E63", fg="white"
        ).pack(side="left", padx=5, pady=5)

        # Achievement name
        tk.Label(
            frame, text=self.achievement.name,
            font=("Segoe UI", 11, "bold"), bg="#1a1a1a", fg="white"
        ).pack(anchor="w", padx=10, pady=(5, 2))

        # Description
        tk.Label(
            frame, text=self.achievement.description,
            font=("Segoe UI", 9), bg="#1a1a1a", fg="#999",
            wraplength=self.TOAST_WIDTH - 20
        ).pack(anchor="w", padx=10, pady=(0, 5))

        # Auto-hide
        self.animation_id = self.root.after(
            self.TOAST_DURATION_MS,
            self._close
        )

    def _close(self):
        """Close the toast."""
        if self.window:
            try:
                self.window.destroy()
            except Exception:
                pass
            self.window = None

        if self.on_close_callback:
            self.on_close_callback()


class AchievementBadgeBar:
    """Display row of recently unlocked achievement badges."""

    def __init__(self, parent, achievements_tracker, max_badges=8):
        self.parent = parent
        self.achievements_tracker = achievements_tracker
        self.max_badges = max_badges
        self.frame = tk.Frame(parent, bg="#1a1a1a", height=50)
        self.badge_buttons = []

    def get_frame(self):
        """Return the frame for packing."""
        return self.frame

    def update(self):
        """Refresh badge display."""
        # Clear existing
        for btn in self.badge_buttons:
            btn.destroy()
        self.badge_buttons = []

        # Get recent achievements
        recent = self.achievements_tracker.get_visible_badges(self.max_badges)

        if not recent:
            # Show placeholder
            placeholder = tk.Label(
                self.frame, text="🔥 Unlock achievements to earn badges!",
                bg="#1a1a1a", fg="#666", font=("Segoe UI", 9)
            )
            placeholder.pack(padx=10, pady=8)
            return

        # Show badges
        badges_frame = tk.Frame(self.frame, bg="#1a1a1a")
        badges_frame.pack(fill="x", padx=5, pady=5)

        for achievement in recent:
            badge = tk.Label(
                badges_frame,
                text=f"{achievement.icon} {achievement.name}",
                bg="#2a2a2a", fg="#fff",
                font=("Segoe UI", 8),
                padx=8, pady=4,
                relief="raised", bd=1
            )
            badge.pack(side="left", padx=3)
            self.badge_buttons.append(badge)
