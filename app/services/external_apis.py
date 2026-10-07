"""Async wrappers for Soundcharts, Last.fm, and YouTube Data API.

All functions are independently gated on their respective config keys being
set — if a key is absent the function returns None immediately without making
any network call. All network errors are caught and logged; callers receive
None on failure so a single API being down never blocks the full pipeline.

These functions are called from chartmetric.gather_artist_data() as Phase 2
of the data gather, in parallel with asyncio.gather().
"""

from __future__ import annotations

import logging
from typing import Any

import anyio.to_thread
import httpx

from app import config

log = logging.getLogger(__name__)

# ── Shared HTTP helper ────────────────────────────────────────────────────────

async def _get(url: str, params: dict | None = None, headers: dict | None = None) -> Any:
    """Async GET with a 15-second timeout. Returns parsed JSON or None on error."""
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url, params=params, headers=headers)
            resp.raise_for_status()
            return resp.json()
    except Exception as exc:
        log.warning("HTTP GET %s failed: %s", url, exc)
        return None


# ── Soundcharts ───────────────────────────────────────────────────────────────

_SC_BASE = "https://customer.api.soundcharts.com"


def _sc_headers() -> dict | None:
    if not config.SOUNDCHARTS_APP_ID or not config.SOUNDCHARTS_API_KEY:
        return None
    return {
        "x-app-id": config.SOUNDCHARTS_APP_ID,
        "x-api-key": config.SOUNDCHARTS_API_KEY,
    }


async def soundcharts_get_artist_uuid(spotify_id: str) -> str | None:
    """Resolve a Soundcharts UUID from a Spotify artist ID."""
    hdrs = _sc_headers()
    if not hdrs:
        return None
    data = await _get(
        f"{_SC_BASE}/api/v2.9/artist/by-platform/spotify/{spotify_id}",
        headers=hdrs,
    )
    if not data:
        return None
    # Response shape: {"object": {"uuid": "..."}} or {"uuid": "..."}
    obj = data.get("object") or data
    return obj.get("uuid")


async def soundcharts_get_radio_spins(uuid: str, days: int = 30) -> dict | None:
    """Get radio airplay spins for an artist over the last N days."""
    hdrs = _sc_headers()
    if not hdrs:
        return None
    from datetime import date, timedelta
    end = date.today().isoformat()
    start = (date.today() - timedelta(days=days)).isoformat()
    return await _get(
        f"{_SC_BASE}/api/v2/artist/{uuid}/broadcasts",
        params={"startDate": start, "endDate": end, "limit": 100},
        headers=hdrs,
    )


async def soundcharts_get_chart_entries(uuid: str, platform: str = "spotify") -> dict | None:
    """Get chart positions for an artist's songs on a given platform."""
    hdrs = _sc_headers()
    if not hdrs:
        return None
    return await _get(
        f"{_SC_BASE}/api/v2/artist/{uuid}/charts/song/ranks/{platform}",
        params={"currentOnly": 0, "sortBy": "rankDate", "sortOrder": "desc", "limit": 50},
        headers=hdrs,
    )


async def soundcharts_get_playlists(uuid: str, platform: str = "spotify") -> dict | None:
    """Get current playlist placements for an artist."""
    hdrs = _sc_headers()
    if not hdrs:
        return None
    return await _get(
        f"{_SC_BASE}/api/v2.20/artist/{uuid}/playlist/current/{platform}",
        params={"currentOnly": 1, "sortBy": "subscriberCount", "sortOrder": "desc", "limit": 50},
        headers=hdrs,
    )


async def gather_soundcharts_data(spotify_id: str) -> dict:
    """Fetch all Soundcharts data for an artist. Returns {} if unconfigured."""
    if not _sc_headers():
        return {}

    uuid = await soundcharts_get_artist_uuid(spotify_id)
    if not uuid:
        log.info("Soundcharts: no UUID found for Spotify ID %s", spotify_id)
        return {}

    import asyncio
    radio, charts, playlists = await asyncio.gather(
        soundcharts_get_radio_spins(uuid),
        soundcharts_get_chart_entries(uuid),
        soundcharts_get_playlists(uuid),
    )
    return {
        "uuid": uuid,
        "radio_spins": radio,
        "chart_entries": charts,
        "playlists": playlists,
    }


# ── Last.fm ───────────────────────────────────────────────────────────────────

_LFM_BASE = "https://ws.audioscrobbler.com/2.0/"


async def lastfm_get_artist_info(artist_name: str) -> dict | None:
    """Get listener count, scrobbles, top tags, and bio from Last.fm."""
    if not config.LASTFM_API_KEY:
        return None
    return await _get(
        _LFM_BASE,
        params={
            "method": "artist.getInfo",
            "artist": artist_name,
            "api_key": config.LASTFM_API_KEY,
            "format": "json",
            "lang": "en",
        },
    )


async def lastfm_get_top_tracks(artist_name: str, limit: int = 10) -> dict | None:
    """Get top tracks by scrobble count from Last.fm."""
    if not config.LASTFM_API_KEY:
        return None
    return await _get(
        _LFM_BASE,
        params={
            "method": "artist.getTopTracks",
            "artist": artist_name,
            "api_key": config.LASTFM_API_KEY,
            "format": "json",
            "limit": limit,
        },
    )


async def gather_lastfm_data(artist_name: str) -> dict:
    """Fetch all Last.fm data for an artist. Returns {} if unconfigured."""
    if not config.LASTFM_API_KEY:
        return {}

    import asyncio
    info, top_tracks = await asyncio.gather(
        lastfm_get_artist_info(artist_name),
        lastfm_get_top_tracks(artist_name),
    )
    return {
        "info": info,
        "top_tracks": top_tracks,
    }


# ── YouTube Data API v3 ───────────────────────────────────────────────────────

_YT_BASE = "https://www.googleapis.com/youtube/v3"


async def youtube_get_channel_stats(channel_id: str) -> dict | None:
    """Get subscriber count, view count, and video count for a YouTube channel."""
    if not config.YOUTUBE_API_KEY:
        return None
    data = await _get(
        f"{_YT_BASE}/channels",
        params={
            "part": "statistics,snippet",
            "id": channel_id,
            "key": config.YOUTUBE_API_KEY,
        },
    )
    if not data:
        return None
    items = data.get("items", [])
    return items[0] if items else None


def _extract_youtube_channel_id(urls: Any) -> str | None:
    """Extract a YouTube channel ID from Chartmetric artist URL data.

    Chartmetric returns URLs as a dict keyed by platform name, each value
    being a list of URL objects with a 'url' field.
    Looks for keys containing 'youtube' and extracts the channel ID.
    """
    if not urls or not isinstance(urls, dict):
        return None
    for key, entries in urls.items():
        if "youtube" not in key.lower():
            continue
        if not isinstance(entries, list):
            continue
        for entry in entries:
            url = entry.get("url", "") if isinstance(entry, dict) else str(entry)
            # Handles: /channel/UCxxx, /@handle, /user/name
            import re
            m = re.search(r"youtube\.com/(?:channel/|@|user/)([A-Za-z0-9_@-]+)", url)
            if m:
                raw = m.group(1)
                # @handles need resolving — return the raw handle for now
                # Full channel IDs start with UC
                if raw.startswith("UC") and len(raw) > 10:
                    return raw
    return None


async def gather_youtube_data(artist_urls: Any) -> dict:
    """Fetch YouTube channel stats if a channel ID can be extracted. Returns {} otherwise."""
    if not config.YOUTUBE_API_KEY:
        return {}
    channel_id = _extract_youtube_channel_id(artist_urls)
    if not channel_id:
        return {}
    stats = await youtube_get_channel_stats(channel_id)
    return {"channel_id": channel_id, "stats": stats} if stats else {}
