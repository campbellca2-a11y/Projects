"""
MouseMiles Theming System
NakedLadies (pink) theme + dark mode + other fun palettes
"""

from enum import Enum


class ThemeName(Enum):
    NAKEDLADIES = "nakedladies"
    OCEANBLUE = "oceanblue"
    FORESTGREEN = "forestgreen"
    SUNSET = "sunset"
    MIDNIGHT = "midnight"


class Theme:
    """Theme definition with colors."""

    def __init__(self, name, primary, accent, bg_dark, bg_light, text_dark, text_light):
        self.name = name
        self.primary = primary  # Main brand color
        self.accent = accent  # Highlight color
        self.bg_dark = bg_dark  # Dark mode background
        self.bg_light = bg_light  # Light mode background
        self.text_dark = text_dark  # Dark mode text
        self.text_light = text_light  # Light mode text

    def get_bg(self, dark_mode=False):
        return self.bg_dark if dark_mode else self.bg_light

    def get_text(self, dark_mode=False):
        return self.text_dark if dark_mode else self.text_light


# Theme Definitions
THEMES = {
    ThemeName.NAKEDLADIES: Theme(
        "NakedLadies",
        primary="#E91E63",
        accent="#F06292",
        bg_dark="#1a1a2e",
        bg_light="#fafafa",
        text_dark="#ffffff",
        text_light="#333333",
    ),
    ThemeName.OCEANBLUE: Theme(
        "Ocean Blue",
        primary="#00BCD4",
        accent="#0097A7",
        bg_dark="#0d1b26",
        bg_light="#e0f7fa",
        text_dark="#ffffff",
        text_light="#1a1a1a",
    ),
    ThemeName.FORESTGREEN: Theme(
        "Forest Green",
        primary="#4CAF50",
        accent="#2E7D32",
        bg_dark="#1b3a1b",
        bg_light="#f1f8f6",
        text_dark="#ffffff",
        text_light="#1a1a1a",
    ),
    ThemeName.SUNSET: Theme(
        "Sunset Orange",
        primary="#FF9800",
        accent="#F57C00",
        bg_dark="#2a1b0f",
        bg_light="#ffe8d6",
        text_dark="#ffffff",
        text_light="#1a1a1a",
    ),
    ThemeName.MIDNIGHT: Theme(
        "Midnight",
        primary="#9C27B0",
        accent="#7B1FA2",
        bg_dark="#0a0a0a",
        bg_light="#f5f5f5",
        text_dark="#e0e0e0",
        text_light="#333333",
    ),
}


class ThemeManager:
    """Manage theme selection and application."""

    def __init__(self, settings_dict):
        self.settings = settings_dict
        self.current_theme_name = ThemeName(settings_dict.get("theme", "nakedladies"))
        self.dark_mode = settings_dict.get("dark_mode", False)
        self.theme = THEMES[self.current_theme_name]

    def set_theme(self, theme_name):
        """Change to a different theme."""
        if isinstance(theme_name, str):
            theme_name = ThemeName(theme_name)

        self.current_theme_name = theme_name
        self.theme = THEMES[theme_name]
        self.settings["theme"] = theme_name.value

    def set_dark_mode(self, enabled):
        """Toggle dark mode."""
        self.dark_mode = enabled
        self.settings["dark_mode"] = enabled

    def get_primary(self):
        return self.theme.primary

    def get_accent(self):
        return self.theme.accent

    def get_bg(self):
        return self.theme.get_bg(self.dark_mode)

    def get_text(self):
        return self.theme.get_text(self.dark_mode)

    def get_all_theme_names(self):
        """Return list of available theme names."""
        return [t.value for t in ThemeName]


def apply_theme_to_ui(root, theme_manager):
    """Apply theme colors to the tkinter app."""
    try:
        from tkinter import ttk

        # Create a custom style
        style = ttk.Style()

        bg = theme_manager.get_bg()
        text = theme_manager.get_text()
        primary = theme_manager.get_primary()
        accent = theme_manager.get_accent()

        # Configure default styles
        style.configure(".", background=bg, foreground=text)
        style.configure("TFrame", background=bg, foreground=text)
        style.configure("TLabel", background=bg, foreground=text)
        style.configure("TButton", background=bg, foreground=text)
        style.configure("TNotebook", background=bg, foreground=text)
        style.configure("TNotebook.Tab", background=bg, foreground=text, padding=[20, 10])

        # Active tab styling
        style.map(
            "TNotebook.Tab",
            background=[("selected", primary)],
            foreground=[("selected", "white")],
        )

        # Custom styles
        style.configure("Header.TLabel", foreground=primary, font=("Segoe UI", 14, "bold"))
        style.configure("Bold.TLabel", foreground=primary, font=("Segoe UI", 10, "bold"))
        style.configure("Accent.TLabel", foreground=accent)

        # Progressbar
        style.configure("Accent.Horizontal.TProgressbar", background=primary, troughcolor=bg)

        # LabelFrame
        style.configure("TLabelframe", background=bg, foreground=primary)
        style.configure("TLabelframe.Label", background=bg, foreground=primary)

        # Root window
        root.config(bg=bg)

        return style

    except Exception as e:
        print(f"[themes] apply_theme_to_ui error: {e}")
        return None
