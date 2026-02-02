"""Preference profile management for YVS."""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import get_profiles_dir


@dataclass
class Profile:
    """A preference profile defining how to select videos."""

    name: str
    priority: list[str] = field(default_factory=lambda: ["official"])
    fallbacks: list[str] = field(default_factory=list)
    avoid: list[str] = field(default_factory=list)
    channel_weights: dict[str, int] = field(
        default_factory=lambda: {
            "official_artist": 50,
            "verified_label": 40,
            "trusted_uploader": 20,
        }
    )
    duration_tolerance_pct: int = 10
    trusted_uploaders: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert profile to dictionary."""
        return {
            "name": self.name,
            "priority": self.priority,
            "fallbacks": self.fallbacks,
            "avoid": self.avoid,
            "channel_weights": self.channel_weights,
            "duration_tolerance_pct": self.duration_tolerance_pct,
            "trusted_uploaders": self.trusted_uploaders,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        """Create profile from dictionary."""
        return cls(
            name=data["name"],
            priority=data.get("priority", ["official"]),
            fallbacks=data.get("fallbacks", []),
            avoid=data.get("avoid", []),
            channel_weights=data.get(
                "channel_weights",
                {"official_artist": 50, "verified_label": 40, "trusted_uploader": 20},
            ),
            duration_tolerance_pct=data.get("duration_tolerance_pct", 10),
            trusted_uploaders=data.get("trusted_uploaders", []),
        )


def get_profile_path(name: str) -> Path:
    """Get path to a profile file."""
    return get_profiles_dir() / f"{name}.json"


def load_profile(name: str) -> Optional[Profile]:
    """Load a profile by name."""
    profile_path = get_profile_path(name)
    if not profile_path.exists():
        return None

    with open(profile_path, "r") as f:
        data = json.load(f)

    return Profile.from_dict(data)


def save_profile(profile: Profile) -> None:
    """Save a profile to disk."""
    profile_path = get_profile_path(profile.name)
    with open(profile_path, "w") as f:
        json.dump(profile.to_dict(), f, indent=2)


def list_profiles() -> list[str]:
    """List all available profile names."""
    profiles_dir = get_profiles_dir()
    return [p.stem for p in profiles_dir.glob("*.json")]


def delete_profile(name: str) -> bool:
    """Delete a profile by name. Returns True if deleted."""
    profile_path = get_profile_path(name)
    if profile_path.exists():
        profile_path.unlink()
        return True
    return False


def get_default_profiles() -> dict[str, Profile]:
    """Get the built-in default profiles."""
    return {
        "studio_purist": Profile(
            name="studio_purist",
            priority=["official"],
            fallbacks=["session", "live"],
            avoid=["reaction", "nightcore", "sped up", "slowed", "remaster", "remix", "cover", "karaoke", "8d audio", "bass boosted"],
            channel_weights={
                "official_artist": 50,
                "verified_label": 40,
                "trusted_uploader": 20,
            },
            duration_tolerance_pct=10,
        ),
        "live_energy": Profile(
            name="live_energy",
            priority=["live", "concert", "festival"],
            fallbacks=["session", "official"],
            avoid=["reaction", "nightcore", "sped up", "slowed", "karaoke", "cover"],
            channel_weights={
                "official_artist": 50,
                "verified_label": 40,
                "trusted_uploader": 30,
            },
            duration_tolerance_pct=50,  # Live versions vary in length
        ),
        "session_vibes": Profile(
            name="session_vibes",
            priority=["session", "acoustic", "stripped", "tiny desk", "from the basement", "npr"],
            fallbacks=["live", "official"],
            avoid=["reaction", "nightcore", "sped up", "slowed", "karaoke", "cover", "remix"],
            channel_weights={
                "official_artist": 50,
                "verified_label": 40,
                "trusted_uploader": 35,
            },
            duration_tolerance_pct=30,
        ),
        "deep_cuts": Profile(
            name="deep_cuts",
            priority=["demo", "alternate", "unreleased", "rare"],
            fallbacks=["session", "live", "official"],
            avoid=["reaction", "nightcore", "sped up", "slowed", "karaoke"],
            channel_weights={
                "official_artist": 40,
                "verified_label": 30,
                "trusted_uploader": 40,  # Trust uploaders more for rare content
            },
            duration_tolerance_pct=40,
        ),
        "chaos": Profile(
            name="chaos",
            priority=["cover", "mashup", "remix"],
            fallbacks=["live", "session", "official"],
            avoid=["reaction", "nightcore", "sped up", "slowed", "karaoke", "8d audio"],
            channel_weights={
                "official_artist": 20,
                "verified_label": 15,
                "trusted_uploader": 30,
            },
            duration_tolerance_pct=100,  # Anything goes
        ),
    }


def ensure_default_profiles() -> None:
    """Ensure default profiles exist on disk."""
    for name, profile in get_default_profiles().items():
        profile_path = get_profile_path(name)
        if not profile_path.exists():
            save_profile(profile)
