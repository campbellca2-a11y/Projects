"""Candidate scoring model for YVS."""

import re
from dataclasses import dataclass
from typing import Optional

from .profiles import Profile
from .search import VideoCandidate


@dataclass
class ScoredCandidate:
    """A video candidate with its computed score and breakdown."""

    candidate: VideoCandidate
    total_score: float
    score_breakdown: dict[str, float]

    @property
    def video_id(self) -> str:
        return self.candidate.video_id

    @property
    def url(self) -> str:
        return self.candidate.url


def normalize_text(text: str) -> str:
    """Normalize text for matching."""
    return text.lower().strip()


def text_contains_any(text: str, terms: list[str]) -> bool:
    """Check if normalized text contains any of the terms."""
    normalized = normalize_text(text)
    return any(normalize_text(term) in normalized for term in terms)


def text_contains_term(text: str, term: str) -> bool:
    """Check if normalized text contains the term."""
    return normalize_text(term) in normalize_text(text)


def score_channel_credibility(
    candidate: VideoCandidate,
    artist: str,
    profile: Profile,
) -> tuple[float, str]:
    """Score based on channel credibility.

    Returns (score, reason).
    """
    channel_lower = normalize_text(candidate.channel_title)
    artist_lower = normalize_text(artist)

    # Check for official artist channel
    # Look for artist name in channel, or common patterns like "ArtistVEVO"
    if artist_lower in channel_lower:
        return (profile.channel_weights.get("official_artist", 50), "official_artist_channel")

    # Check for VEVO (verified label)
    if "vevo" in channel_lower:
        return (profile.channel_weights.get("verified_label", 40), "vevo_channel")

    # Check for trusted uploaders
    for uploader in profile.trusted_uploaders:
        if normalize_text(uploader) in channel_lower:
            return (profile.channel_weights.get("trusted_uploader", 20), "trusted_uploader")

    # Check for common official patterns
    official_patterns = ["official", "records", "music", "entertainment"]
    if any(pattern in channel_lower for pattern in official_patterns):
        return (profile.channel_weights.get("verified_label", 40) * 0.5, "likely_official")

    return (0, "unknown_channel")


def score_title_signals(
    candidate: VideoCandidate,
    artist: str,
    track: str,
    profile: Profile,
) -> tuple[float, dict[str, float]]:
    """Score based on title and description signals.

    Returns (total_score, breakdown_dict).
    """
    title = normalize_text(candidate.title)
    description = normalize_text(candidate.description)
    combined = f"{title} {description}"

    breakdown = {}
    total = 0.0

    # Check for avoided terms (negative score)
    for avoid_term in profile.avoid:
        if text_contains_term(combined, avoid_term):
            penalty = -30
            breakdown[f"avoid_{avoid_term}"] = penalty
            total += penalty

    # Check for priority terms (positive score)
    for i, priority_term in enumerate(profile.priority):
        if text_contains_term(combined, priority_term):
            # Higher score for earlier priority terms
            score = 25 - (i * 5)
            score = max(score, 10)  # Minimum 10 points
            breakdown[f"priority_{priority_term}"] = score
            total += score
            break  # Only count first match

    # Check for fallback terms (lower positive score)
    if not any(k.startswith("priority_") for k in breakdown):
        for fallback_term in profile.fallbacks:
            if text_contains_term(combined, fallback_term):
                breakdown[f"fallback_{fallback_term}"] = 10
                total += 10
                break

    # Bonus for "Official Video" or "Official Audio"
    if "official video" in combined or "official audio" in combined:
        breakdown["official_marker"] = 15
        total += 15

    # Bonus if title contains both artist and track
    artist_lower = normalize_text(artist)
    track_lower = normalize_text(track)
    if artist_lower in title and track_lower in title:
        breakdown["title_match"] = 20
        total += 20
    elif track_lower in title:
        breakdown["track_in_title"] = 10
        total += 10

    return (total, breakdown)


def score_duration(
    candidate: VideoCandidate,
    expected_duration: Optional[int],
    profile: Profile,
) -> tuple[float, str]:
    """Score based on duration match.

    Returns (score, reason).
    """
    if not expected_duration or not candidate.duration_seconds:
        return (0, "no_duration_data")

    tolerance = profile.duration_tolerance_pct / 100.0
    min_duration = expected_duration * (1 - tolerance)
    max_duration = expected_duration * (1 + tolerance)

    if min_duration <= candidate.duration_seconds <= max_duration:
        return (15, "duration_match")

    # Penalize if way off
    if candidate.duration_seconds < expected_duration * 0.5:
        return (-10, "too_short")
    if candidate.duration_seconds > expected_duration * 2:
        return (-10, "too_long")

    return (0, "duration_outside_tolerance")


def score_popularity(candidate: VideoCandidate) -> tuple[float, str]:
    """Score based on view count (low weight, tie-breaker only).

    Returns (score, reason).
    """
    if not candidate.view_count:
        return (0, "no_view_data")

    # Logarithmic scale, max 10 points
    # 1M views = ~6 points, 10M views = ~7 points, 100M = ~8 points
    import math

    if candidate.view_count > 0:
        score = min(10, math.log10(candidate.view_count + 1))
        return (score, f"views_{candidate.view_count}")

    return (0, "zero_views")


def score_candidate(
    candidate: VideoCandidate,
    artist: str,
    track: str,
    profile: Profile,
    expected_duration: Optional[int] = None,
) -> ScoredCandidate:
    """Score a single candidate video.

    Args:
        candidate: The video candidate to score
        artist: Artist name
        track: Track title
        profile: Active preference profile
        expected_duration: Expected duration in seconds (optional)

    Returns:
        ScoredCandidate with total score and breakdown
    """
    breakdown = {}
    total = 0.0

    # Channel credibility
    channel_score, channel_reason = score_channel_credibility(candidate, artist, profile)
    breakdown[f"channel_{channel_reason}"] = channel_score
    total += channel_score

    # Title/description signals
    title_score, title_breakdown = score_title_signals(candidate, artist, track, profile)
    breakdown.update(title_breakdown)
    total += title_score

    # Duration match
    duration_score, duration_reason = score_duration(candidate, expected_duration, profile)
    breakdown[f"duration_{duration_reason}"] = duration_score
    total += duration_score

    # Popularity (tie-breaker)
    popularity_score, popularity_reason = score_popularity(candidate)
    breakdown[f"popularity_{popularity_reason}"] = popularity_score
    total += popularity_score

    return ScoredCandidate(
        candidate=candidate,
        total_score=total,
        score_breakdown=breakdown,
    )


def score_candidates(
    candidates: list[VideoCandidate],
    artist: str,
    track: str,
    profile: Profile,
    expected_duration: Optional[int] = None,
) -> list[ScoredCandidate]:
    """Score all candidates and return sorted by score (descending).

    Args:
        candidates: List of video candidates
        artist: Artist name
        track: Track title
        profile: Active preference profile
        expected_duration: Expected duration in seconds (optional)

    Returns:
        List of ScoredCandidate sorted by total_score (highest first)
    """
    scored = [
        score_candidate(candidate, artist, track, profile, expected_duration)
        for candidate in candidates
    ]

    # Sort by score descending, then by view count (deterministic tie-breaker)
    scored.sort(
        key=lambda s: (s.total_score, s.candidate.view_count or 0),
        reverse=True,
    )

    return scored


def select_best(
    candidates: list[VideoCandidate],
    artist: str,
    track: str,
    profile: Profile,
    expected_duration: Optional[int] = None,
) -> Optional[ScoredCandidate]:
    """Select the best candidate from the list.

    Args:
        candidates: List of video candidates
        artist: Artist name
        track: Track title
        profile: Active preference profile
        expected_duration: Expected duration in seconds (optional)

    Returns:
        The highest-scoring ScoredCandidate, or None if no candidates
    """
    if not candidates:
        return None

    scored = score_candidates(candidates, artist, track, profile, expected_duration)
    return scored[0] if scored else None


def explain_selection(scored: ScoredCandidate) -> str:
    """Generate a human-readable explanation of why a video was selected."""
    lines = [
        f"Selected: {scored.candidate.title}",
        f"Channel: {scored.candidate.channel_title}",
        f"Score: {scored.total_score:.1f}",
        "",
        "Score breakdown:",
    ]

    # Sort breakdown by absolute value of score
    sorted_breakdown = sorted(
        scored.score_breakdown.items(),
        key=lambda x: abs(x[1]),
        reverse=True,
    )

    for reason, score in sorted_breakdown:
        if score != 0:
            sign = "+" if score > 0 else ""
            lines.append(f"  {reason}: {sign}{score:.1f}")

    return "\n".join(lines)
