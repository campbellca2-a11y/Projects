# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a monorepo of independent projects ("Bill's Projects") synced via Google Drive. Each subdirectory is a standalone project with its own dependencies — there is no shared build system or workspace configuration.

The parent directory (`GoogleGemini/`) contains additional sibling projects outside this git repo. Paths prefixed with `../` refer to those sibling directories.

## Key Projects and How to Run Them

### YouTubeVersionSelector (`YouTubeVersionSelector/`)
Python CLI that picks the best YouTube video for a song based on taste profiles. Requires `YOUTUBE_API_KEY` env var or `python -m yvs config --api-key "KEY"`.

```bash
pip install -r YouTubeVersionSelector/requirements.txt
python -m yvs play "Artist" "Track"
python -m yvs play "Artist" "Track" --profile live_energy --explain
```
Architecture: `cli.py` → `search.py` (YouTube API) → `scorer.py` (profile-based scoring) → `cache.py` (JSON file cache keyed by `artist::track::profile`). Profiles are JSON files at `~/.config/yvs/profiles/`, managed via `profiles.py`. Config at `~/.config/yvs/config.json`.

### DigitalStethoscope (`DigitalStethoscope/`)
Single-file Python script monitoring CPU/RAM/frequency in real-time, logging to CSV under `data/sessions/`. Uses `psutil` and `py-cpuinfo`.

```bash
python DigitalStethoscope/stethoscope.py
```

### DogScratcher (`DogScratcher/`)
Product development documentation (specs, testing logs, photos) for a physical dog scratching product. No code.

## Sibling Projects (outside this git repo)

### MightyTags (`../MightyTags/`)
Deterministic emotion extraction engine — the core tagging library used by EOS, CycleSync, ThoughtVault, and MailMood. Detects 20 emotions from text with negation handling, coverage, and confidence metrics.

```bash
python -m mightytags
```

### MondayEngine (`../MondayEngine/`)
AI chat framework using Google Gemini API with capsule-based brand DNA enforcement. Requires `GEMINI_API_KEY` in `.env`.

```bash
python main_engine.py --mode chat           # Interactive chat
python main_engine.py --mode api --port 5000  # Flask API (/chat, /history, /clear)
```
Dependencies: `google-genai`, `Flask`, `python-dotenv`

### eos-ui (`../eos-ui/`)
Frontend for the Emotional Operating System. Next.js 16 + React 19 + TypeScript + Tailwind CSS 4.

```bash
npm run dev      # Dev server
npm run build    # Production build
npm run lint     # ESLint
```

### VPN Monitor (`../VPN Monitor/`)
Real-time network traffic monitor with VPN status detection. Requires admin privileges.

```bash
sudo python vpn_monitor.py
```

### VPNBalloon (`../VPNBalloon/`)
System tray VPN status indicator (green = active, red = down, balloon grows while VPN is off). Uses tkinter.

### WiFiSimple (`../WiFiSimple/`)
WiFi network management utility. Active version: `current_working/WiFiSimplePlus_polished_v241.py`.

### AntarcticaCams (`../AntarcticaCams/`)
Antarctic webcam dashboard. Open `antarctica-dashboard.html` in browser; optional Flask proxy: `python proxy.py`.

### SimpleSuite / SimpleSuite_for_Dad
PyInstaller-compiled Windows desktop utilities (DesktopSimple, EmailSimple, WeatherSimple, WiFiSimple, RestartSimple, AiSimple). Run `.exe` files directly.

## Architecture — The EOS Ecosystem

Several sibling projects form an interconnected emotional intelligence platform:

- **MightyTags** — Core emotion lexicon and text parser (20 emotions). Used as a dependency by other projects.
- **EOS** (`../EOS/`) — Emotional Operating System seed framework. Philosophy and capsule architecture defined in `EOSSeedSystem.md`.
- **eos-ui** — Next.js frontend for EOS.
- **ThoughtVault** (`../ThoughtVault/`) — Central knowledge infrastructure with capsule-based data storage. Backend for MondayEngine, TagSimple, and EOS.
- **CycleSync** (`../CycleSync/`) — Emotion × calendar phase matrix for cycle tracking. Integrates with MightyTags and EOS.
- **MondayEngine** — Gemini-powered chat with capsule/DNA enforcement. Uses MightyTags for emotional context.
- **TagSimple** (`../TagSimple/`) — Simplified tag management UI. Early stage.
- **Lore Master** (`../Lore Master/`) — Design docs, PDFs, and archival documents for the EOS ecosystem. No code.

## General Notes

- Python projects target 3.9+ with minimal pip dependencies (no virtual env tooling configured).
- Node.js projects require v18+.
- No shared test suites or linter/formatter configs exist.
- `../Bills_Projects/` contains overlapping copies of some projects (YouTubeVersionSelector, DigitalStethoscope, DogScratcher). This repo is the git-tracked version.
- Compiled binaries (`.exe`) are built with PyInstaller and are Windows-only.
