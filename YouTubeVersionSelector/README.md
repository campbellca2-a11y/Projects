# YouTube Version Selector (YVS)

A local-first utility that selects the *right* YouTube video for a song based on your taste profile. One click, one video, deterministic results.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Set your YouTube API key
export YOUTUBE_API_KEY="your-api-key-here"
# Or save it permanently:
python -m yvs config --api-key "your-api-key-here"

# Play a song
python -m yvs play "Radiohead" "Karma Police"
```

## Getting a YouTube API Key (Free)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the "YouTube Data API v3"
4. Go to Credentials → Create Credentials → API Key
5. Copy the key and configure YVS with it

Free tier: 10,000 units/day (~100 searches/day).

## Usage

### Play a Song

```bash
# Basic usage
python -m yvs play "Artist" "Track"

# With album hint
python -m yvs play "Radiohead" "Karma Police" --album "OK Computer"

# With expected duration (helps filter remixes)
python -m yvs play "Pink Floyd" "Time" --duration 413

# Use a specific profile
python -m yvs play "Led Zeppelin" "Stairway to Heaven" --profile live_energy

# Just get the URL (don't open browser)
python -m yvs play "The Beatles" "Yesterday" --url-only

# See why a video was selected
python -m yvs play "Nirvana" "Smells Like Teen Spirit" --explain

# Skip cache (force fresh search)
python -m yvs play "Queen" "Bohemian Rhapsody" --no-cache
```

### Profiles

Profiles define your preferences for video selection.

```bash
# List available profiles
python -m yvs profiles --list

# Show profile details
python -m yvs profiles --show studio_purist

# Set default profile
python -m yvs config --default-profile live_energy

# Restore built-in profiles
python -m yvs profiles --reset-defaults
```

**Built-in Profiles:**

| Profile | Description |
|---------|-------------|
| `studio_purist` | Official studio versions, avoids remixes/covers |
| `live_energy` | Live performances, concerts, festivals |
| `session_vibes` | Acoustic sessions, Tiny Desk, From the Basement |
| `deep_cuts` | Demos, alternate versions, rare recordings |
| `chaos` | Covers, mashups, creative interpretations |

### Cache Management

YVS caches decisions locally for instant replay.

```bash
# View cache stats
python -m yvs cache

# List cached entries
python -m yvs cache --list

# Remove a specific entry
python -m yvs cache --remove "radiohead::karma police"

# Clear entire cache
python -m yvs cache --clear
```

### Configuration

```bash
# View current config
python -m yvs config

# Set API key
python -m yvs config --api-key "YOUR_KEY"

# Set default profile
python -m yvs config --default-profile session_vibes
```

## How It Works

1. **Search**: Builds a query from artist + track + profile preferences
2. **Fetch**: Calls YouTube Data API (bounded to top 15 results)
3. **Score**: Evaluates each candidate using:
   - Channel credibility (official artist, VEVO, trusted uploaders)
   - Title/description signals (matches priority terms, avoids negative terms)
   - Duration sanity (within tolerance of expected length)
   - Popularity (low-weight tie-breaker)
4. **Select**: Returns the highest-scoring video deterministically
5. **Cache**: Stores the decision locally for instant future lookups
6. **Play**: Opens the video in your default browser

## Custom Profiles

Create a JSON file in `~/.config/yvs/profiles/`:

```json
{
  "name": "my_profile",
  "priority": ["acoustic", "unplugged"],
  "fallbacks": ["live", "official"],
  "avoid": ["karaoke", "cover", "remix"],
  "channel_weights": {
    "official_artist": 50,
    "verified_label": 40,
    "trusted_uploader": 30
  },
  "duration_tolerance_pct": 20,
  "trusted_uploaders": ["MyFavoriteChannel"]
}
```

## File Locations

- Config: `~/.config/yvs/config.json`
- Profiles: `~/.config/yvs/profiles/`
- Cache: `~/.config/yvs/cache.json`

## Design Principles

- **Determinism**: Same input → same output
- **Local-first**: No cloud dependency beyond API calls
- **Taste over engagement**: Your preferences, not YouTube's algorithm
- **Zero choice**: One click, one video

## Limitations

- Requires YouTube Data API key (free tier available)
- API quota: ~100 searches/day on free tier
- No downloading or ad-bypass (compliant playback only)
