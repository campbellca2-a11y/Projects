"""Command-line interface for YouTube Version Selector."""

import argparse
import sys
import webbrowser
from typing import Optional

from . import __version__
from .cache import (
    cache_stats,
    clear_cache,
    get_cached,
    list_cached,
    remove_cached,
    set_cached,
)
from .config import (
    get_api_key,
    get_config_dir,
    get_default_profile,
    set_api_key,
    set_default_profile,
)
from .profiles import (
    Profile,
    delete_profile,
    ensure_default_profiles,
    list_profiles,
    load_profile,
    save_profile,
)
from .scorer import explain_selection, select_best
from .search import (
    APIKeyMissingError,
    QuotaExceededError,
    YouTubeSearchError,
    search_with_fallback,
)


def cmd_play(args: argparse.Namespace) -> int:
    """Play a song - the main command."""
    artist = args.artist
    track = args.track
    album = args.album
    duration = args.duration
    profile_name = args.profile or get_default_profile()
    use_cache = not args.no_cache
    explain = args.explain

    # Load profile
    profile = load_profile(profile_name)
    if not profile:
        print(f"Error: Profile '{profile_name}' not found.", file=sys.stderr)
        print(f"Available profiles: {', '.join(list_profiles())}", file=sys.stderr)
        return 1

    # Check cache first
    if use_cache:
        cached_id = get_cached(artist, track, profile_name)
        if cached_id:
            url = f"https://www.youtube.com/watch?v={cached_id}"
            if not args.url_only:
                print(f"Playing (cached): {artist} - {track}")
                webbrowser.open(url)
            else:
                print(url)
            return 0

    # Search YouTube
    try:
        print(f"Searching for: {artist} - {track}...", file=sys.stderr)
        candidates = search_with_fallback(artist, track, profile, album)
    except APIKeyMissingError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except QuotaExceededError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except YouTubeSearchError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if not candidates:
        print(f"No results found for: {artist} - {track}", file=sys.stderr)
        return 1

    # Score and select best
    best = select_best(candidates, artist, track, profile, duration)
    if not best:
        print("No suitable video found.", file=sys.stderr)
        return 1

    # Cache the result
    if use_cache:
        set_cached(artist, track, profile_name, best.video_id)

    # Output
    if explain:
        print(explain_selection(best))
        print()

    if not args.url_only:
        print(f"Playing: {best.candidate.title}")
        print(f"Channel: {best.candidate.channel_title}")
        webbrowser.open(best.url)
    else:
        print(best.url)

    return 0


def cmd_config(args: argparse.Namespace) -> int:
    """Configure YVS."""
    if args.api_key:
        set_api_key(args.api_key)
        print("API key saved.")
        return 0

    if args.default_profile:
        if args.default_profile not in list_profiles():
            print(f"Error: Profile '{args.default_profile}' not found.", file=sys.stderr)
            return 1
        set_default_profile(args.default_profile)
        print(f"Default profile set to: {args.default_profile}")
        return 0

    # Show current config
    print(f"Config directory: {get_config_dir()}")
    print(f"API key: {'configured' if get_api_key() else 'not set'}")
    print(f"Default profile: {get_default_profile()}")
    return 0


def cmd_profiles(args: argparse.Namespace) -> int:
    """Manage profiles."""
    if args.list:
        profiles = list_profiles()
        default = get_default_profile()
        if not profiles:
            print("No profiles found.")
            return 0

        print("Available profiles:")
        for name in profiles:
            marker = " (default)" if name == default else ""
            print(f"  - {name}{marker}")
        return 0

    if args.show:
        profile = load_profile(args.show)
        if not profile:
            print(f"Error: Profile '{args.show}' not found.", file=sys.stderr)
            return 1

        import json
        print(json.dumps(profile.to_dict(), indent=2))
        return 0

    if args.delete:
        if delete_profile(args.delete):
            print(f"Profile '{args.delete}' deleted.")
            return 0
        else:
            print(f"Error: Profile '{args.delete}' not found.", file=sys.stderr)
            return 1

    if args.reset_defaults:
        ensure_default_profiles()
        print("Default profiles restored.")
        return 0

    # Default: list profiles
    return cmd_profiles(argparse.Namespace(list=True, show=None, delete=None, reset_defaults=False))


def cmd_cache(args: argparse.Namespace) -> int:
    """Manage cache."""
    if args.clear:
        count = clear_cache()
        print(f"Cleared {count} cached entries.")
        return 0

    if args.list:
        entries = list_cached()
        if not entries:
            print("Cache is empty.")
            return 0

        print("Cached entries:")
        for artist, track, profile, video_id in entries:
            print(f"  {artist} - {track} [{profile}]: {video_id}")
        return 0

    if args.remove:
        parts = args.remove.split("::")
        if len(parts) != 2:
            print("Error: Use format 'artist::track'", file=sys.stderr)
            return 1
        artist, track = parts
        profile = args.profile or get_default_profile()
        if remove_cached(artist, track, profile):
            print(f"Removed cached entry for: {artist} - {track} [{profile}]")
            return 0
        else:
            print("Entry not found in cache.", file=sys.stderr)
            return 1

    # Default: show stats
    stats = cache_stats()
    print(f"Cache path: {stats['path']}")
    print(f"Entries: {stats['entries']}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point."""
    # Ensure default profiles exist
    ensure_default_profiles()

    parser = argparse.ArgumentParser(
        prog="yvs",
        description="YouTube Version Selector - Find the right version of any song",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Play command (main functionality)
    play_parser = subparsers.add_parser("play", help="Play a song")
    play_parser.add_argument("artist", help="Artist name")
    play_parser.add_argument("track", help="Track title")
    play_parser.add_argument("--album", "-a", help="Album name (optional)")
    play_parser.add_argument(
        "--duration", "-d", type=int, help="Expected duration in seconds"
    )
    play_parser.add_argument(
        "--profile", "-p", help="Profile to use (default: from config)"
    )
    play_parser.add_argument(
        "--no-cache", action="store_true", help="Skip cache lookup and storage"
    )
    play_parser.add_argument(
        "--explain", "-e", action="store_true", help="Show why this video was selected"
    )
    play_parser.add_argument(
        "--url-only", "-u", action="store_true", help="Only print URL, don't open browser"
    )
    play_parser.set_defaults(func=cmd_play)

    # Config command
    config_parser = subparsers.add_parser("config", help="Configure YVS")
    config_parser.add_argument("--api-key", help="Set YouTube API key")
    config_parser.add_argument("--default-profile", help="Set default profile")
    config_parser.set_defaults(func=cmd_config)

    # Profiles command
    profiles_parser = subparsers.add_parser("profiles", help="Manage preference profiles")
    profiles_parser.add_argument("--list", "-l", action="store_true", help="List all profiles")
    profiles_parser.add_argument("--show", "-s", help="Show profile details")
    profiles_parser.add_argument("--delete", help="Delete a profile")
    profiles_parser.add_argument(
        "--reset-defaults", action="store_true", help="Restore default profiles"
    )
    profiles_parser.set_defaults(func=cmd_profiles)

    # Cache command
    cache_parser = subparsers.add_parser("cache", help="Manage local cache")
    cache_parser.add_argument("--clear", "-c", action="store_true", help="Clear all cache")
    cache_parser.add_argument("--list", "-l", action="store_true", help="List cached entries")
    cache_parser.add_argument("--remove", "-r", help="Remove entry (format: artist::track)")
    cache_parser.add_argument("--profile", "-p", help="Profile for remove operation")
    cache_parser.set_defaults(func=cmd_cache)

    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
