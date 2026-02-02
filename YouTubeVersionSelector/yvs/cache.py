"""Local caching for YVS decisions."""

import json
from typing import Optional

from .config import get_cache_path


def _normalize_key(artist: str, track: str, profile: str) -> str:
    """Create a normalized cache key."""
    # Normalize: lowercase, strip whitespace
    artist = artist.lower().strip()
    track = track.lower().strip()
    profile = profile.lower().strip()
    return f"{artist}::{track}::{profile}"


def load_cache() -> dict[str, str]:
    """Load the cache from disk."""
    cache_path = get_cache_path()
    if cache_path.exists():
        try:
            with open(cache_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(cache: dict[str, str]) -> None:
    """Save the cache to disk."""
    cache_path = get_cache_path()
    with open(cache_path, "w") as f:
        json.dump(cache, f, indent=2)


def get_cached(artist: str, track: str, profile: str) -> Optional[str]:
    """Get a cached video ID for a song.

    Args:
        artist: Artist name
        track: Track title
        profile: Profile name used for selection

    Returns:
        Cached video ID, or None if not cached
    """
    cache = load_cache()
    key = _normalize_key(artist, track, profile)
    return cache.get(key)


def set_cached(artist: str, track: str, profile: str, video_id: str) -> None:
    """Cache a video ID for a song.

    Args:
        artist: Artist name
        track: Track title
        profile: Profile name used for selection
        video_id: The selected video ID
    """
    cache = load_cache()
    key = _normalize_key(artist, track, profile)
    cache[key] = video_id
    save_cache(cache)


def remove_cached(artist: str, track: str, profile: str) -> bool:
    """Remove a cached entry.

    Args:
        artist: Artist name
        track: Track title
        profile: Profile name

    Returns:
        True if entry was removed, False if not found
    """
    cache = load_cache()
    key = _normalize_key(artist, track, profile)
    if key in cache:
        del cache[key]
        save_cache(cache)
        return True
    return False


def clear_cache() -> int:
    """Clear all cached entries.

    Returns:
        Number of entries cleared
    """
    cache = load_cache()
    count = len(cache)
    save_cache({})
    return count


def list_cached() -> list[tuple[str, str, str, str]]:
    """List all cached entries.

    Returns:
        List of (artist, track, profile, video_id) tuples
    """
    cache = load_cache()
    entries = []
    for key, video_id in cache.items():
        parts = key.split("::")
        if len(parts) == 3:
            artist, track, profile = parts
            entries.append((artist, track, profile, video_id))
    return entries


def cache_stats() -> dict:
    """Get cache statistics.

    Returns:
        Dictionary with cache stats
    """
    cache = load_cache()
    cache_path = get_cache_path()

    return {
        "entries": len(cache),
        "path": str(cache_path),
        "exists": cache_path.exists(),
    }
