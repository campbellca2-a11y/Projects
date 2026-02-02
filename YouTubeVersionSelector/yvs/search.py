"""YouTube API search integration for YVS."""

import re
from dataclasses import dataclass
from typing import Optional

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .config import get_api_key
from .profiles import Profile


@dataclass
class VideoCandidate:
    """A candidate video from YouTube search results."""

    video_id: str
    title: str
    channel_title: str
    channel_id: str
    description: str
    duration_seconds: Optional[int]
    view_count: Optional[int]
    publish_date: Optional[str]
    is_verified: bool = False

    @property
    def url(self) -> str:
        """Get the YouTube URL for this video."""
        return f"https://www.youtube.com/watch?v={self.video_id}"


class YouTubeSearchError(Exception):
    """Error during YouTube search."""

    pass


class APIKeyMissingError(YouTubeSearchError):
    """API key is not configured."""

    pass


class QuotaExceededError(YouTubeSearchError):
    """YouTube API quota exceeded."""

    pass


def parse_duration(duration_str: str) -> int:
    """Parse ISO 8601 duration to seconds.

    Examples: PT4M13S -> 253, PT1H2M3S -> 3723
    """
    if not duration_str:
        return 0

    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration_str)
    if not match:
        return 0

    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)

    return hours * 3600 + minutes * 60 + seconds


def build_search_query(
    artist: str,
    track: str,
    profile: Profile,
    album: Optional[str] = None,
) -> str:
    """Build a search query string based on metadata and profile."""
    # Start with artist and track
    query_parts = [artist, track]

    # Add album if provided
    if album:
        query_parts.append(album)

    # Add priority terms from profile
    if profile.priority:
        # Add the first priority term to help focus results
        query_parts.append(profile.priority[0])

    return " ".join(query_parts)


def search_youtube(
    artist: str,
    track: str,
    profile: Profile,
    album: Optional[str] = None,
    max_results: int = 15,
) -> list[VideoCandidate]:
    """Search YouTube for video candidates.

    Args:
        artist: Artist name
        track: Track title
        profile: Active preference profile
        album: Optional album name
        max_results: Maximum results to fetch (default 15)

    Returns:
        List of VideoCandidate objects

    Raises:
        APIKeyMissingError: If no API key is configured
        QuotaExceededError: If API quota is exceeded
        YouTubeSearchError: For other API errors
    """
    api_key = get_api_key()
    if not api_key:
        raise APIKeyMissingError(
            "YouTube API key not found. Set YOUTUBE_API_KEY environment variable "
            "or run 'yvs config --api-key YOUR_KEY'"
        )

    query = build_search_query(artist, track, profile, album)

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        # Search for videos
        search_response = (
            youtube.search()
            .list(
                q=query,
                part="snippet",
                type="video",
                maxResults=max_results,
                videoCategoryId="10",  # Music category
            )
            .execute()
        )

        if not search_response.get("items"):
            return []

        # Get video IDs for detailed info
        video_ids = [item["id"]["videoId"] for item in search_response["items"]]

        # Fetch video details (duration, view count, etc.)
        videos_response = (
            youtube.videos()
            .list(
                id=",".join(video_ids),
                part="contentDetails,statistics,snippet",
            )
            .execute()
        )

        # Build candidate list
        candidates = []
        for item in videos_response.get("items", []):
            snippet = item["snippet"]
            content_details = item.get("contentDetails", {})
            statistics = item.get("statistics", {})

            candidate = VideoCandidate(
                video_id=item["id"],
                title=snippet.get("title", ""),
                channel_title=snippet.get("channelTitle", ""),
                channel_id=snippet.get("channelId", ""),
                description=snippet.get("description", ""),
                duration_seconds=parse_duration(content_details.get("duration", "")),
                view_count=int(statistics.get("viewCount", 0)) if statistics.get("viewCount") else None,
                publish_date=snippet.get("publishedAt"),
            )
            candidates.append(candidate)

        return candidates

    except HttpError as e:
        if e.resp.status == 403:
            error_reason = e.error_details[0].get("reason", "") if e.error_details else ""
            if "quotaExceeded" in error_reason:
                raise QuotaExceededError("YouTube API quota exceeded. Try again tomorrow.")
            raise YouTubeSearchError(f"API access denied: {e}")
        raise YouTubeSearchError(f"YouTube API error: {e}")


def search_with_fallback(
    artist: str,
    track: str,
    profile: Profile,
    album: Optional[str] = None,
    max_results: int = 15,
) -> list[VideoCandidate]:
    """Search YouTube with fallback to relaxed query if no results.

    If the initial search returns no results, tries again with just
    artist + track (removing profile-specific terms).
    """
    # Try with full query first
    candidates = search_youtube(artist, track, profile, album, max_results)

    if candidates:
        return candidates

    # Fallback: search with just artist + track
    if album or profile.priority:
        api_key = get_api_key()
        if not api_key:
            raise APIKeyMissingError("YouTube API key not found.")

        try:
            youtube = build("youtube", "v3", developerKey=api_key)

            simple_query = f"{artist} {track}"

            search_response = (
                youtube.search()
                .list(
                    q=simple_query,
                    part="snippet",
                    type="video",
                    maxResults=max_results,
                )
                .execute()
            )

            if not search_response.get("items"):
                return []

            video_ids = [item["id"]["videoId"] for item in search_response["items"]]

            videos_response = (
                youtube.videos()
                .list(
                    id=",".join(video_ids),
                    part="contentDetails,statistics,snippet",
                )
                .execute()
            )

            candidates = []
            for item in videos_response.get("items", []):
                snippet = item["snippet"]
                content_details = item.get("contentDetails", {})
                statistics = item.get("statistics", {})

                candidate = VideoCandidate(
                    video_id=item["id"],
                    title=snippet.get("title", ""),
                    channel_title=snippet.get("channelTitle", ""),
                    channel_id=snippet.get("channelId", ""),
                    description=snippet.get("description", ""),
                    duration_seconds=parse_duration(content_details.get("duration", "")),
                    view_count=int(statistics.get("viewCount", 0)) if statistics.get("viewCount") else None,
                    publish_date=snippet.get("publishedAt"),
                )
                candidates.append(candidate)

            return candidates

        except HttpError as e:
            raise YouTubeSearchError(f"YouTube API error: {e}")

    return []
