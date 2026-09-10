"""
MouseMiles Achievement System
Ridiculous, frequent milestones that fire every 5-10 minutes.
Tier 1: Dopamine loop (constant wins)
Tier 2: Daily behavioral themes
Tier 3: Silly achievements (session-based)
Tier 4: Big lifetime goals
"""

from enum import Enum
from datetime import datetime, timedelta
import json
import os
from config import DATA_DIR


class AchievementTier(Enum):
    TIER1 = 1  # Micro (session)
    TIER2 = 2  # Daily behavioral
    TIER3 = 3  # Silly achievements
    TIER4 = 4  # Big goals


class Achievement:
    """Single achievement definition."""

    def __init__(self, name, icon, description, tier, metric_type, threshold,
                 unlock_period='session', unlock_once=False):
        self.name = name
        self.icon = icon
        self.description = description
        self.tier = tier
        self.metric_type = metric_type  # 'pixels', 'clicks', 'scroll', 'session_duration', 'time_of_day'
        self.threshold = threshold  # value to trigger
        self.unlock_period = unlock_period  # 'session', 'daily', 'lifetime'
        self.unlock_once = unlock_once  # if True, only unlock once per period


# ============================================================================
# TIER 1: DOPAMINE LOOP (Hit every session, constantly)
# ============================================================================

TIER1_ACHIEVEMENTS = [
    Achievement("First Pixel Moved", "🖱️", "Tiny mouse twitch detected!",
                AchievementTier.TIER1, "pixels", 10, "session", unlock_once=True),

    Achievement("Moved a Pencil", "✏️", "You've moved as far as a standard pencil length!",
                AchievementTier.TIER1, "pixels", 50, "session", unlock_once=True),

    Achievement("Scrolled for Snacks", "🍪", "Enough scrolling to earn a snack break.",
                AchievementTier.TIER1, "pixels", 100, "session", unlock_once=True),

    Achievement("One Click Away", "👆", "Made your first click of the session.",
                AchievementTier.TIER1, "clicks", 1, "session", unlock_once=True),

    Achievement("Caffeinated Shuffle", "☕", "Restless energy activated.",
                AchievementTier.TIER1, "pixels", 500, "session", unlock_once=True),

    Achievement("Keyboard Jazz Hands", "🎹", "Productive fidgeting unlocked.",
                AchievementTier.TIER1, "pixels", 1000, "session", unlock_once=True),

    Achievement("Trigger Happy", "🎯", "Made 100 clicks in this session.",
                AchievementTier.TIER1, "clicks", 100, "session", unlock_once=False),

    Achievement("The Scroll Warrior", "📜", "Scrolled 500 steps. Pages: conquered.",
                AchievementTier.TIER1, "scroll", 500, "session", unlock_once=False),
]


# ============================================================================
# TIER 2: DAILY BEHAVIORAL (Reset at midnight, themed by time of day)
# ============================================================================

TIER2_ACHIEVEMENTS = [
    # MORNING
    Achievement("Sunrise Scroller", "🌅", "1km before 10am. Early bird gets the worm.",
                AchievementTier.TIER2, "daily_pixels_before_10am", 1000, "daily", unlock_once=True),

    Achievement("Coffee Hasn't Kicked In Yet", "☕😶", "500 clicks before 9am. Jittery energy!",
                AchievementTier.TIER2, "daily_clicks_before_9am", 500, "daily", unlock_once=True),

    # MIDDAY
    Achievement("Lunch Break Warrior", "🥗", "2km between 11am-1pm. Productive lunch!",
                AchievementTier.TIER2, "daily_pixels_lunch", 2000, "daily", unlock_once=True),

    Achievement("Spreadsheet Crusader", "📊", "500 clicks between 1-3pm. Crushing it.",
                AchievementTier.TIER2, "daily_clicks_afternoon", 500, "daily", unlock_once=True),

    # AFTERNOON
    Achievement("The Afternoon Slump", "😴", "Stayed active (never idle >20min) all day.",
                AchievementTier.TIER2, "no_long_idle", 1, "daily", unlock_once=True),

    Achievement("That Meeting Could've Been An Email", "📧", "3km total with tracker never paused.",
                AchievementTier.TIER2, "daily_pixels_no_pause", 3000, "daily", unlock_once=True),

    # EVENING
    Achievement("Night Owl Shuffle", "🦉", "500px after 8pm. The work never stops.",
                AchievementTier.TIER2, "daily_pixels_after_8pm", 500, "daily", unlock_once=True),

    Achievement("End of Day Victory Lap", "🏁", "5km total today. You earned this.",
                AchievementTier.TIER2, "daily_pixels_total", 5000, "daily", unlock_once=True),
]


# ============================================================================
# TIER 3: RIDICULOUS ACHIEVEMENTS (Once per session, for fun)
# ============================================================================

TIER3_ACHIEVEMENTS = [
    # SPEED RECORDS
    Achievement("Mouse Overclocked", "⚡", "5km in under 2 hours. Unhinged energy.",
                AchievementTier.TIER3, "fast_5km", 5000, "session", unlock_once=True),

    Achievement("Nervous Energy", "🔄", "1,000 clicks in one session. CLICK CLICK CLICK.",
                AchievementTier.TIER3, "clicks", 1000, "session", unlock_once=True),

    Achievement("Scroll Warriors", "📜", "500 scroll steps in 30 minutes. Unstoppable.",
                AchievementTier.TIER3, "fast_scroll", 500, "session", unlock_once=True),

    # PATIENCE TESTS
    Achievement("Meditation Master", "🧘", "Idle for 15+ minutes without pausing.",
                AchievementTier.TIER3, "long_idle", 15, "session", unlock_once=True),

    Achievement("Can't Sit Still", "🪑", "Never idle for more than 5min, entire session.",
                AchievementTier.TIER3, "always_moving", 1, "session", unlock_once=True),

    # ENDURANCE
    Achievement("6-Hour Grind", "💪", "Session lasted 6+ hours. That's commitment.",
                AchievementTier.TIER3, "session_duration", 6*3600, "session", unlock_once=True),

    Achievement("The Commitment", "📍", "Session lasted 12+ hours. Seek help.",
                AchievementTier.TIER3, "session_duration", 12*3600, "session", unlock_once=True),

    Achievement("That's Dedication", "🏆", "24+ hour session. You are a mad lad.",
                AchievementTier.TIER3, "session_duration", 24*3600, "session", unlock_once=True),

    # QUIRKY
    Achievement("One More Hour Said 3 Hours Ago", "😫", "Still moving after 3+ hours.",
                AchievementTier.TIER3, "session_duration", 3*3600, "session", unlock_once=True),

    Achievement("This Is Fine", "🔥🐕", "Maintained 500px/hour for 2+ hours straight.",
                AchievementTier.TIER3, "consistent_pace", 1, "session", unlock_once=True),

    Achievement("The Absolute Unit", "💪", "10km in a single session. Absolute legend.",
                AchievementTier.TIER3, "pixels", 10000, "session", unlock_once=True),
]


# ============================================================================
# TIER 4: BIG GOALS (Lifetime/Monthly)
# ============================================================================

TIER4_ACHIEVEMENTS = [
    # DISTANCE
    Achievement("Across the Room", "🚪", "10m of mouse movement total.",
                AchievementTier.TIER4, "lifetime_pixels", 10000, "lifetime", unlock_once=True),

    Achievement("Around the Block", "🏘️", "100m of mouse movement total.",
                AchievementTier.TIER4, "lifetime_pixels", 100000, "lifetime", unlock_once=True),

    Achievement("A Mile Worth of Pixels", "🛣️", "1km total. That's legit distance.",
                AchievementTier.TIER4, "lifetime_pixels", 1000000, "lifetime", unlock_once=True),

    Achievement("That's a 5K Run!", "🏃", "10km total. You ran a 5K with your mouse.",
                AchievementTier.TIER4, "lifetime_pixels", 10000000, "lifetime", unlock_once=True),

    Achievement("Cross a State", "🗺️", "100km total. Wow.",
                AchievementTier.TIER4, "lifetime_pixels", 100000000, "lifetime", unlock_once=True),

    # CONSISTENCY
    Achievement("Weeklong Warrior", "🔥", "7-day activity streak.",
                AchievementTier.TIER4, "day_streak", 7, "lifetime", unlock_once=False),

    Achievement("Habitica Who?", "🎮", "30-day activity streak.",
                AchievementTier.TIER4, "day_streak", 30, "lifetime", unlock_once=False),

    Achievement("That's Illegal", "🚨", "100-day activity streak. You're unstoppable.",
                AchievementTier.TIER4, "day_streak", 100, "lifetime", unlock_once=False),
]


ALL_ACHIEVEMENTS = TIER1_ACHIEVEMENTS + TIER2_ACHIEVEMENTS + TIER3_ACHIEVEMENTS + TIER4_ACHIEVEMENTS


# ============================================================================
# ACHIEVEMENT TRACKER
# ============================================================================

class AchievementTracker:
    """Tracks which achievements have been unlocked and when."""

    def __init__(self):
        self.data_file = os.path.join(DATA_DIR, "achievements.json")
        self.unlocked = {
            'session': {},      # session_id -> set of achievement names
            'daily': {},        # YYYY-MM-DD -> set of achievement names
            'lifetime': set(),  # all unlocked lifetime achievements
        }
        self.day_streak = 0
        self.last_activity_date = None
        self.load()

    def load(self):
        """Load achievement data from disk."""
        if not os.path.exists(self.data_file):
            return
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            self.unlocked['lifetime'] = set(data.get('lifetime', []))
            self.day_streak = data.get('day_streak', 0)
            self.last_activity_date = data.get('last_activity_date')
        except Exception as e:
            print(f"[achievements] load error: {e}")

    def save(self):
        """Save achievement data to disk."""
        try:
            data = {
                'lifetime': list(self.unlocked['lifetime']),
                'day_streak': self.day_streak,
                'last_activity_date': self.last_activity_date,
            }
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[achievements] save error: {e}")

    def unlock_achievement(self, achievement_name, session_id, period='session'):
        """
        Unlock an achievement if conditions are met.
        Returns True if newly unlocked, False if already unlocked in this period.
        """
        today = datetime.now().strftime("%Y-%m-%d")

        if period == 'lifetime':
            if achievement_name not in self.unlocked['lifetime']:
                self.unlocked['lifetime'].add(achievement_name)
                self.save()
                return True
            return False

        elif period == 'daily':
            if today not in self.unlocked['daily']:
                self.unlocked['daily'][today] = set()
            if achievement_name not in self.unlocked['daily'][today]:
                self.unlocked['daily'][today].add(achievement_name)
                self.save()
                return True
            return False

        elif period == 'session':
            if session_id not in self.unlocked['session']:
                self.unlocked['session'][session_id] = set()
            if achievement_name not in self.unlocked['session'][session_id]:
                self.unlocked['session'][session_id].add(achievement_name)
                return True
            return False

        return False

    def check_daily_streak(self):
        """Update daily streak based on activity today."""
        today = datetime.now().strftime("%Y-%m-%d")

        if self.last_activity_date is None:
            self.last_activity_date = today
            self.day_streak = 1
            self.save()
            return

        last_date = datetime.strptime(self.last_activity_date, "%Y-%m-%d").date()
        today_date = datetime.now().date()
        days_diff = (today_date - last_date).days

        if days_diff == 0:
            # Same day, no change
            pass
        elif days_diff == 1:
            # Consecutive day, increment streak
            self.day_streak += 1
            self.last_activity_date = today
            self.save()
        else:
            # Streak broken
            self.day_streak = 1
            self.last_activity_date = today
            self.save()

    def get_visible_badges(self, limit=10):
        """Get recently unlocked achievements to display."""
        # Combine daily + lifetime for display
        recent = []

        # Add recent daily achievements
        today = datetime.now().strftime("%Y-%m-%d")
        if today in self.unlocked['daily']:
            for name in list(self.unlocked['daily'][today])[-limit:]:
                achievement = self._get_achievement_by_name(name)
                if achievement:
                    recent.append(achievement)

        # Add recent lifetime achievements
        for name in list(self.unlocked['lifetime'])[-limit:]:
            achievement = self._get_achievement_by_name(name)
            if achievement:
                recent.append(achievement)

        return recent[:limit]

    @staticmethod
    def _get_achievement_by_name(name):
        """Find achievement by name."""
        for ach in ALL_ACHIEVEMENTS:
            if ach.name == name:
                return ach
        return None

    def is_unlocked(self, achievement_name, session_id=None, period='lifetime'):
        """Check if achievement is already unlocked."""
        if period == 'lifetime':
            return achievement_name in self.unlocked['lifetime']
        elif period == 'daily':
            today = datetime.now().strftime("%Y-%m-%d")
            return (today in self.unlocked['daily'] and
                    achievement_name in self.unlocked['daily'][today])
        elif period == 'session' and session_id:
            return (session_id in self.unlocked['session'] and
                    achievement_name in self.unlocked['session'][session_id])
        return False
