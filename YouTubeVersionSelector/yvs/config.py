"""Configuration handling for YVS."""

import json
import os
from pathlib import Path
from typing import Optional


def get_config_dir() -> Path:
    """Get the configuration directory for YVS."""
    # Use XDG_CONFIG_HOME if available, otherwise ~/.config
    config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
    config_dir = Path(config_home) / "yvs"
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def get_config_path() -> Path:
    """Get the path to the config file."""
    return get_config_dir() / "config.json"


def get_cache_path() -> Path:
    """Get the path to the cache file."""
    return get_config_dir() / "cache.json"


def get_profiles_dir() -> Path:
    """Get the profiles directory."""
    profiles_dir = get_config_dir() / "profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    return profiles_dir


def load_config() -> dict:
    """Load configuration from file."""
    config_path = get_config_path()
    if config_path.exists():
        with open(config_path, "r") as f:
            return json.load(f)
    return {}


def save_config(config: dict) -> None:
    """Save configuration to file."""
    config_path = get_config_path()
    with open(config_path, "w") as f:
        json.dump(config, f, indent=2)


def get_api_key() -> Optional[str]:
    """Get YouTube API key from environment or config."""
    # First check environment variable
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if api_key:
        return api_key

    # Fall back to config file
    config = load_config()
    return config.get("api_key")


def set_api_key(api_key: str) -> None:
    """Save API key to config file."""
    config = load_config()
    config["api_key"] = api_key
    save_config(config)


def get_default_profile() -> str:
    """Get the default profile name."""
    config = load_config()
    return config.get("default_profile", "studio_purist")


def set_default_profile(profile_name: str) -> None:
    """Set the default profile name."""
    config = load_config()
    config["default_profile"] = profile_name
    save_config(config)
