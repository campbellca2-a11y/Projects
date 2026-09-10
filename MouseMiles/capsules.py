import json
import os
from config import CUSTOM_CAPSULES_FILE


SCALE_REFERENCES = [
    ("mouse lengths", 0.10, "Mouse"),
    ("keyboard lengths", 0.45, "Keyboard"),
    ("doorways", 2.0, "Doorway"),
    ("bowling lanes", 18.29, "Bowling lane"),
    ("football fields", 91.44, "Football field"),
    ("miles", 1609.344, "Mile"),
    ("marathons", 42195.0, "Marathon"),
]


def get_scale_story(meters):
    """Return one legible visual comparison and the next scale landmark."""
    meters = max(0.0, float(meters or 0.0))
    if meters <= 0.0:
        return {
            "headline": "Move the mouse to begin the journey",
            "detail": "Your path will grow here as you work.",
            "current_label": "Mouse",
            "current_m": 0.10,
            "next_label": "Keyboard",
            "next_m": 0.45,
            "progress": 0.0,
        }

    index = 0
    for i, (_, reference_m, _) in enumerate(SCALE_REFERENCES):
        if meters >= reference_m:
            index = i
        else:
            break

    label, reference_m, icon_label = SCALE_REFERENCES[index]
    count = meters / reference_m
    if count < 10:
        count_text = f"{count:.1f}"
    elif count < 100:
        count_text = f"{count:.0f}"
    else:
        count_text = f"{count:,.0f}"
    headline = f"About {count_text} {label}"

    if index + 1 < len(SCALE_REFERENCES):
        next_label, next_m, next_icon = SCALE_REFERENCES[index + 1]
        progress = min(100.0, (meters / next_m) * 100.0)
        remaining = max(0.0, next_m - meters)
        detail = f"{remaining:,.1f} m until the next landmark: {next_icon}."
    else:
        next_label, next_m, next_icon = "the next landmark", reference_m * 10, "Next"
        progress = 0.0
        detail = "The journey is now beyond the everyday scale."

    return {
        "headline": headline,
        "detail": detail,
        "current_label": icon_label,
        "current_m": reference_m,
        "next_label": next_icon,
        "next_m": next_m,
        "progress": progress,
    }

class CapsuleLibrary:
    """Built-in + user-defined distance comparison capsules."""

    def __init__(self):
        self._builtin = [
            Capsule("Raw Metrics",         None,        None,  self._fmt_raw),
            Capsule("Standard LEGO Studs", 0.008,       10000, self._fmt_generic_count),
            Capsule("Standard #2 Pencils", 0.19,        100,   self._fmt_generic_count),
            Capsule("Bananas",             0.178,       500,   self._fmt_generic_count),
            Capsule("Everest Ascent",      8849,        8849,  self._fmt_big_goal),
            Capsule("A Marathon",          42195,       42195, self._fmt_big_goal),
            Capsule("International Space Station Orbit", 408000 * 2 * 3.14159, None, self._fmt_big_goal),
            Capsule("To The Moon",         384400000,   384400000, self._fmt_big_goal),
            Capsule("Equatorial Walk",     40075000,    40075000,  self._fmt_big_goal),
        ]
        self._custom = []
        self.load_custom()

    # --- Public API ---

    def all_capsules(self):
        return self._builtin + self._custom

    def get_names(self):
        return [c.name for c in self.all_capsules()]

    def get_data(self, name, meters, pixels, clicks, scroll, is_imperial):
        for c in self.all_capsules():
            if c.name == name:
                return c.format(meters, pixels, clicks, scroll, is_imperial)
        return ("Unknown", 0.0)

    # --- Custom capsules ---

    def load_custom(self):
        if not os.path.exists(CUSTOM_CAPSULES_FILE):
            return
        try:
            with open(CUSTOM_CAPSULES_FILE, "r") as f:
                items = json.load(f)
            self._custom = []
            for item in items:
                name = item.get("name", "Custom")
                distance_m = float(item.get("distance_m", 100))
                self._custom.append(
                    Capsule(name, distance_m, distance_m, self._fmt_big_goal)
                )
        except Exception as e:
            print(f"[capsules] load_custom error: {e}")

    def save_custom(self):
        items = [{"name": c.name, "distance_m": c.target_m} for c in self._custom]
        try:
            with open(CUSTOM_CAPSULES_FILE, "w") as f:
                json.dump(items, f, indent=2)
        except Exception as e:
            print(f"[capsules] save_custom error: {e}")

    def add_custom(self, name, distance_m):
        self._custom.append(
            Capsule(name, distance_m, distance_m, self._fmt_big_goal)
        )
        self.save_custom()

    def remove_custom(self, name):
        self._custom = [c for c in self._custom if c.name != name]
        self.save_custom()

    # --- Format helpers ---

    @staticmethod
    def _dist_str(meters, is_imperial):
        if is_imperial:
            feet = meters * 3.28084
            if feet >= 5280:
                return f"{feet / 5280:,.4f} mi"
            return f"{feet:,.2f} ft"
        else:
            if meters >= 1000:
                return f"{meters / 1000:,.4f} km"
            return f"{meters:,.2f} m"

    def _fmt_raw(self, capsule, meters, pixels, clicks, scroll, is_imperial):
        dist = self._dist_str(meters, is_imperial)
        text = (
            f"{int(pixels):,} px  |  {dist}\n"
            f"Clicks: {int(clicks):,}  |  Scroll steps: {int(scroll):,}"
        )
        return (text, 0.0)

    def _fmt_generic_count(self, capsule, meters, pixels, clicks, scroll, is_imperial):
        if capsule.unit_m and capsule.unit_m > 0:
            count = meters / capsule.unit_m
        else:
            count = 0
        goal = capsule.goal_count or 1
        percent = min((count / goal) * 100, 100)
        text = f"{count:,.1f} laid end-to-end  (goal: {int(goal):,})"
        return (text, percent)

    def _fmt_big_goal(self, capsule, meters, pixels, clicks, scroll, is_imperial):
        target = capsule.target_m or 1
        percent = min((meters / target) * 100, 100)

        if is_imperial:
            current = meters * 3.28084
            goal_val = target * 3.28084
            if goal_val >= 5280:
                current_str = f"{current / 5280:,.3f} mi"
                goal_str = f"{goal_val / 5280:,.1f} mi"
            else:
                current_str = f"{current:,.1f} ft"
                goal_str = f"{goal_val:,.1f} ft"
        else:
            if target >= 1000:
                current_str = f"{meters / 1000:,.3f} km"
                goal_str = f"{target / 1000:,.1f} km"
            else:
                current_str = f"{meters:,.1f} m"
                goal_str = f"{target:,.1f} m"

        text = f"{current_str} / {goal_str}  ({percent:.4f}%)"
        return (text, percent)


class Capsule:
    """A single distance comparison."""

    def __init__(self, name, unit_or_target_m, goal_count, formatter):
        self.name = name
        self.unit_m = unit_or_target_m     # size of one unit in meters (for count capsules)
        self.target_m = unit_or_target_m   # target distance in meters (for goal capsules)
        self.goal_count = goal_count
        self._formatter = formatter

    def format(self, meters, pixels, clicks, scroll, is_imperial):
        return self._formatter(self, meters, pixels, clicks, scroll, is_imperial)
