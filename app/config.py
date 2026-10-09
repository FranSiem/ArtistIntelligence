"""Configuration — load and validate environment variables at startup."""

import os
from dotenv import load_dotenv

load_dotenv()


def validate():
    missing = []
    if not os.environ.get("ANTHROPIC_API_KEY"):
        missing.append("ANTHROPIC_API_KEY")
    if not os.environ.get("CHARTMETRIC_API_KEY"):
        missing.append("CHARTMETRIC_API_KEY")
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in values."
        )


# ── Required ──────────────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL: str = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6")
CHARTMETRIC_API_KEY: str = os.environ.get("CHARTMETRIC_API_KEY", "")

# ── Redis (optional — falls back to in-memory if not set) ─────────────────────
REDIS_URL: str | None = os.environ.get("REDIS_URL")

# ── Soundcharts (optional — sandbox values work out of the box) ───────────────
SOUNDCHARTS_APP_ID: str = os.environ.get("SOUNDCHARTS_APP_ID", "")
SOUNDCHARTS_API_KEY: str = os.environ.get("SOUNDCHARTS_API_KEY", "")

# ── Spotify Web API (optional) ────────────────────────────────────────────────
SPOTIFY_CLIENT_ID: str = os.environ.get("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET: str = os.environ.get("SPOTIFY_CLIENT_SECRET", "")

# ── Last.fm (optional) ────────────────────────────────────────────────────────
LASTFM_API_KEY: str = os.environ.get("LASTFM_API_KEY", "")

# ── YouTube Data API v3 (optional) ────────────────────────────────────────────
YOUTUBE_API_KEY: str = os.environ.get("YOUTUBE_API_KEY", "")

# ── Admin portal ──────────────────────────────────────────────────────────────
ADMIN_PASSWORD: str = os.environ.get("ADMIN_PASSWORD", "")

# ── Gemini (optional — enrichment only, never blocks core analysis) ────────────
GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
