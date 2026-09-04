"""Chartmetric MCP Server — exposes Chartmetric data as Claude tools via pycmc."""

import os
import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("chartmetric")

_pycmc = None


def cm():
    """Lazy-load pycmc so it only initialises (and authenticates) when first called."""
    global _pycmc
    if _pycmc is None:
        if not os.environ.get("CMCREDENTIALS"):
            raise RuntimeError(
                "CMCREDENTIALS env var not set. "
                'Set it to a JSON string: \'{"refreshtoken": "your_token_here"}\''
            )
        import pycmc as _lib
        _pycmc = _lib
    return _pycmc


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

@mcp.tool()
def search(
    query: str,
    type: str = "all",
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """Search Chartmetric for artists, tracks, playlists, albums, or curators.

    Args:
        query: Search query string (artist name, track title, etc.)
        type: One of 'all', 'artists', 'tracks', 'playlists', 'curators', 'albums', 'stations', 'cities'
        limit: Number of results to return (default 10)
        offset: Offset for pagination (default 0)
    """
    return cm().search_engine.search(query=query, type=type, limit=limit, offset=offset)


# ---------------------------------------------------------------------------
# Artist
# ---------------------------------------------------------------------------

@mcp.tool()
def get_artist_metadata(cmid: int) -> dict:
    """Get metadata for an artist by their Chartmetric ID.

    Args:
        cmid: Chartmetric artist ID (use search() to find it)
    """
    return cm().artist.metadata(cmid)


@mcp.tool()
def get_artist_fanmetrics(
    cmid: int,
    start_date: str,
    end_date: str,
    dsrc: str = "spotify",
    value_col: str = "followers",
) -> dict:
    """Get fan metric time series for an artist.

    Args:
        cmid: Chartmetric artist ID
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        dsrc: Data source — e.g. 'spotify', 'instagram', 'tiktok', 'youtube', 'facebook'
        value_col: Metric column — e.g. 'followers', 'listeners', 'popularity'
    """
    return cm().artist.fanmetrics(
        cmid=cmid,
        start_date=start_date,
        end_date=end_date,
        dsrc=dsrc,
        valueCol=value_col,
    )


@mcp.tool()
def get_artist_charts(
    cmid: int,
    chart_type: str,
    start_date: str,
    end_date: str,
) -> list:
    """Get chart performance history for an artist.

    Args:
        cmid: Chartmetric artist ID
        chart_type: Chart type — e.g. 'spotify_top_daily', 'applemusic', 'shazam', 'youtube'
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    return cm().artist.charts(
        chart_type=chart_type,
        cmid=cmid,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool()
def get_artist_playlists(
    cmid: int,
    dsrc: str = "spotify",
    start_date: str | None = None,
    status: str = "current",
) -> list:
    """Get playlists an artist appears on.

    Args:
        cmid: Chartmetric artist ID
        dsrc: Platform — 'spotify', 'applemusic', 'deezer', 'amazon'
        start_date: Optional start date in YYYY-MM-DD format
        status: 'current' or 'past'
    """
    return cm().artist.playlists(
        cmid=cmid,
        dsrc=dsrc,
        start_date=start_date,
        status=status,
    )


@mcp.tool()
def get_artist_tracks(cmid: int) -> list:
    """Get all tracks for an artist.

    Args:
        cmid: Chartmetric artist ID
    """
    return cm().artist.tracks(cmid)


@mcp.tool()
def get_artist_related(cmid: int, limit: int = 20) -> list:
    """Get artists related to the given artist.

    Args:
        cmid: Chartmetric artist ID
        limit: Number of related artists to return (default 20)
    """
    return cm().artist.related(cmid=cmid, limit=limit)


@mcp.tool()
def get_artist_urls(cmid: int) -> dict:
    """Get social and streaming URLs for an artist (Spotify, Instagram, TikTok, etc.).

    Args:
        cmid: Chartmetric artist ID
    """
    return cm().artist.urls(cmid)


@mcp.tool()
def get_artist_cpp(
    cmid: int,
    cpp_stat: str,
    start_date: str,
    end_date: str,
) -> list:
    """Get Cross-Platform Performance (CPP) data for an artist.

    Args:
        cmid: Chartmetric artist ID
        cpp_stat: Stat type — e.g. 'sp_monthly_listeners', 'sp_followers', 'ins_followers'
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    return cm().artist.cpp_data(
        cmid=cmid,
        cpp_stat=cpp_stat,
        start_date=start_date,
        end_date=end_date,
    )


# ---------------------------------------------------------------------------
# Track
# ---------------------------------------------------------------------------

@mcp.tool()
def get_track_metadata(cmid: int) -> dict:
    """Get metadata for a track by its Chartmetric ID.

    Args:
        cmid: Chartmetric track ID (use search() to find it)
    """
    return cm().track.metadata(cmid)


@mcp.tool()
def get_track_stats(
    cmid: int,
    platform: str = "spotify",
    start_date: str | None = None,
    end_date: str | None = None,
) -> list:
    """Get streaming stats for a track over time.

    Args:
        cmid: Chartmetric track ID
        platform: 'spotify', 'youtube', or 'shazam'
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
    """
    return cm().track.stats(
        cm_track_id=cmid,
        platform=platform,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool()
def get_track_playlists(
    cmid: int,
    platform: str = "spotify",
    status: str = "current",
    start_date: str | None = None,
    end_date: str | None = None,
) -> list:
    """Get playlists a track appears on.

    Args:
        cmid: Chartmetric track ID
        platform: 'spotify', 'applemusic', 'deezer', or 'amazon'
        status: 'current' or 'past'
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
    """
    return cm().track.playlists(
        cmid=cmid,
        platform=platform,
        status=status,
        start_date=start_date,
        end_date=end_date,
    )


@mcp.tool()
def get_track_charts(
    cmid: int,
    chart_type: str,
    start_date: str,
    end_date: str,
) -> list:
    """Get chart history for a track.

    Args:
        cmid: Chartmetric track ID
        chart_type: e.g. 'spotify_viral_daily', 'spotify_top_weekly', 'shazam', 'itunes'
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
    """
    return cm().track.charts(
        chart_type=chart_type,
        cm_track_id=cmid,
        start_date=start_date,
        end_date=end_date,
    )


# ---------------------------------------------------------------------------
# Playlist
# ---------------------------------------------------------------------------

@mcp.tool()
def get_playlist_metadata(cmid: int, platform: str = "spotify") -> dict:
    """Get metadata for a playlist.

    Args:
        cmid: Chartmetric playlist ID
        platform: 'spotify', 'applemusic', or 'deezer'
    """
    return cm().playlist.metadata(cmid=cmid, stype=platform)


@mcp.tool()
def get_playlist_tracks(
    cmid: int,
    platform: str = "spotify",
    span: str = "current",
) -> list:
    """Get tracks in a playlist.

    Args:
        cmid: Chartmetric playlist ID
        platform: 'spotify', 'applemusic', 'deezer', or 'amazon'
        span: 'current' or 'past'
    """
    return cm().playlist.tracks(cmid=cmid, stype=platform, span=span)


@mcp.tool()
def get_playlist_snapshot(cmid: int, platform: str, date: str) -> dict:
    """Get a historical snapshot of a playlist on a specific date.

    Args:
        cmid: Chartmetric playlist ID
        platform: 'spotify', 'applemusic', 'deezer', or 'amazon'
        date: Date in YYYY-MM-DD format
    """
    return cm().playlist.snapshot(cmid=cmid, stype=platform, date=date)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Requires CMCREDENTIALS env var set to JSON string: {"refreshtoken": "..."}
    if not os.environ.get("CMCREDENTIALS"):
        raise EnvironmentError(
            "CMCREDENTIALS env var not set. "
            'Set it to a JSON string: \'{"refreshtoken": "your_token_here"}\''
        )
    mcp.run()


# ---------------------------------------------------------------------------
# Soundcharts
# ---------------------------------------------------------------------------
# Uses the legacy header auth (x-app-id / x-api-key) which the sandbox
# supports without any token-generation step.  Swap the env vars for your
# commercial credentials when the discount key arrives.
# Base URL is the same for sandbox and production — the credentials determine
# which dataset is returned.
# ---------------------------------------------------------------------------

import httpx

_SC_BASE = "https://customer.api.soundcharts.com"
_sc_headers: dict | None = None


def sc() -> dict:
    """Return Soundcharts auth headers, lazy-loading from env vars on first call."""
    global _sc_headers
    if _sc_headers is None:
        app_id = os.environ.get("SOUNDCHARTS_APP_ID")
        api_key = os.environ.get("SOUNDCHARTS_API_KEY")
        if not app_id or not api_key:
            raise RuntimeError(
                "SOUNDCHARTS_APP_ID and SOUNDCHARTS_API_KEY env vars must be set. "
                "Sandbox values are both 'soundcharts'."
            )
        _sc_headers = {"x-app-id": app_id, "x-api-key": api_key}
    return _sc_headers


def _sc_get(path: str, params: dict | None = None) -> dict | list:
    """Make a GET request to the Soundcharts API and return parsed JSON."""
    url = f"{_SC_BASE}{path}"
    with httpx.Client(timeout=30) as client:
        resp = client.get(url, headers=sc(), params={k: v for k, v in (params or {}).items() if v is not None})
    resp.raise_for_status()
    return resp.json()


# ---- Search ----------------------------------------------------------------

@mcp.tool()
def soundcharts_search_artist(
    term: str,
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """Search for an artist on Soundcharts by name or identifier.

    Returns up to 20 artists with their Soundcharts UUID, which is required
    by all other Soundcharts tools.

    Args:
        term: Artist name or identifier to search for
        limit: Number of results to return (max 20, default 10)
        offset: Pagination offset (default 0)
    """
    return _sc_get(
        f"/api/v2/artist/search/{term}",
        params={"limit": limit, "offset": offset},
    )


# ---- Artist identity -------------------------------------------------------

@mcp.tool()
def soundcharts_get_artist_by_platform_id(
    platform: str,
    identifier: str,
) -> dict:
    """Resolve a Soundcharts UUID from a platform-specific artist ID.

    Use this to convert a Spotify artist ID, Apple Music ID, etc. into the
    Soundcharts UUID needed by all other Soundcharts tools.

    Args:
        platform: Platform code — e.g. 'spotify', 'applemusic', 'deezer',
                  'youtube', 'tiktok', 'instagram', 'amazon-music'
        identifier: The artist's ID on that platform (e.g. Spotify artist ID)
    """
    return _sc_get(f"/api/v2.9/artist/by-platform/{platform}/{identifier}")


# ---- Radio airplay ---------------------------------------------------------

@mcp.tool()
def soundcharts_get_artist_radio_spins(
    uuid: str,
    start_date: str | None = None,
    end_date: str | None = None,
    country_code: str | None = None,
    radio_slugs: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get radio airplay (broadcast) history for an artist.

    Returns individual spin records — station, timestamp, and track played.
    If start_date is omitted the API defaults to 30 days before end_date.

    Args:
        uuid: Soundcharts artist UUID (use soundcharts_search_artist or
              soundcharts_get_artist_by_platform_id to obtain)
        start_date: Period start in YYYY-MM-DD format (optional)
        end_date: Period end in YYYY-MM-DD format (optional)
        country_code: 2-letter ISO 3166-2 country code to filter by country
                      (e.g. 'GB', 'US')
        radio_slugs: Comma-separated radio slugs to filter by specific stations
                     (e.g. 'bbc-2,bbc-london') — sandbox supports 'bbc-2' and
                     'bbc-london'
        limit: Number of results (max 100, default 100)
        offset: Pagination offset (default 0)
    """
    return _sc_get(
        f"/api/v2/artist/{uuid}/broadcasts",
        params={
            "startDate": start_date,
            "endDate": end_date,
            "countryCode": country_code,
            "radioSlugs": radio_slugs,
            "limit": limit,
            "offset": offset,
        },
    )


@mcp.tool()
def soundcharts_get_song_radio_spins(
    uuid: str,
    start_date: str | None = None,
    end_date: str | None = None,
    country_code: str | None = None,
    radio_slugs: str | None = None,
    limit: int = 100,
    offset: int = 0,
    sort: str = "desc",
) -> dict:
    """Get radio airplay (broadcast) history for a specific song.

    All 'airedAt' timestamps are in UTC.  If start_date is omitted the API
    defaults to 30 days before end_date.

    Args:
        uuid: Soundcharts song UUID
        start_date: Period start in ATOM format or YYYY-MM-DD (optional)
        end_date: Period end in ATOM format or YYYY-MM-DD (optional)
        country_code: 2-letter ISO 3166-2 country code filter (e.g. 'GB')
        radio_slugs: Comma-separated radio slugs (e.g. 'bbc-2,bbc-london')
        limit: Number of results (max 100, default 100)
        offset: Pagination offset (default 0)
        sort: Sort order — 'asc' or 'desc' (default 'desc')
    """
    return _sc_get(
        f"/api/v2/song/{uuid}/broadcasts",
        params={
            "startDate": start_date,
            "endDate": end_date,
            "countryCode": country_code,
            "radioSlugs": radio_slugs,
            "limit": limit,
            "offset": offset,
            "sort": sort,
        },
    )


# ---- Charts ----------------------------------------------------------------

@mcp.tool()
def soundcharts_get_artist_chart_entries(
    uuid: str,
    platform: str,
    current_only: int = 0,
    sort_by: str = "rankDate",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get chart positions for an artist's songs on a given platform.

    Returns entry date, rank date, current position, and previous position for
    every song charting (or that has charted) on the specified platform.

    Args:
        uuid: Soundcharts artist UUID
        platform: Chart platform code — e.g. 'spotify', 'apple-music',
                  'shazam', 'deezer', 'itunes'.
                  Sandbox supports 'spotify' (Viral – Global) and 'deezer'
                  (Top 200 – Metal).
        current_only: 1 to return only current chart positions, 0 for all
                      (current + historical). Default 0.
        sort_by: Sort field — 'position' or 'rankDate' (default 'rankDate')
        sort_order: 'asc' or 'desc' (default 'desc')
        limit: Number of results (max 100, default 100)
        offset: Pagination offset (default 0)
    """
    return _sc_get(
        f"/api/v2/artist/{uuid}/charts/song/ranks/{platform}",
        params={
            "currentOnly": current_only,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "limit": limit,
            "offset": offset,
        },
    )


# ---- Playlists -------------------------------------------------------------

@mcp.tool()
def soundcharts_get_artist_playlists(
    uuid: str,
    platform: str = "spotify",
    playlist_type: str = "all",
    current_only: int = 1,
    country_code: str | None = None,
    sort_by: str = "subscriberCount",
    sort_order: str = "desc",
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """Get playlist placements for an artist on a streaming platform.

    Returns the playlists an artist's tracks appear on, with position,
    entry date, and playlist subscriber count.

    Args:
        uuid: Soundcharts artist UUID
        platform: Playlist platform code — e.g. 'spotify', 'apple-music',
                  'deezer', 'amazon'.  Sandbox supports 'spotify' and
                  'apple-music'.
        playlist_type: Filter by curation type — 'all', 'editorial',
                       'algorithmic', 'algotorial', 'major', 'charts',
                       'curators_listeners', 'radios', 'this_is'
                       (default 'all')
        current_only: 1 for current placements only, 0 for current + past
                      (default 1)
        country_code: 2-letter ISO 3166-2 country code filter (optional)
        sort_by: Sort field — 'position', 'positionDate', 'entryDate', or
                 'subscriberCount' (default 'subscriberCount')
        sort_order: 'asc' or 'desc' (default 'desc')
        limit: Number of results (max 100, default 100)
        offset: Pagination offset (default 0)
    """
    return _sc_get(
        f"/api/v2.20/artist/{uuid}/playlist/current/{platform}",
        params={
            "type": playlist_type,
            "currentOnly": current_only,
            "countryCode": country_code,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "limit": limit,
            "offset": offset,
        },
    )


# ---------------------------------------------------------------------------
# Spotify Web API (Layer 1 — public catalogue, no user OAuth required)
# ---------------------------------------------------------------------------
# Uses the Client Credentials flow: POST to the token endpoint with
# client_id + client_secret, receive a Bearer token valid for 3600 seconds.
# The token is cached in module state and refreshed automatically when it
# expires, so Claude never needs to think about auth.
# ---------------------------------------------------------------------------

import base64
import time

_SP_API_BASE = "https://api.spotify.com/v1"
_SP_TOKEN_URL = "https://accounts.spotify.com/api/token"

# Cached token state
_sp_token: str | None = None
_sp_token_expiry: float = 0.0


def _spotify_token() -> str:
    """Return a valid Spotify Bearer token, fetching or refreshing as needed."""
    global _sp_token, _sp_token_expiry

    # Return cached token if it has more than 60 seconds of life left
    if _sp_token and time.time() < (_sp_token_expiry - 60):
        return _sp_token

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise RuntimeError(
            "SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET env vars must be set. "
            "Generate credentials at developer.spotify.com (free)."
        )

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            _SP_TOKEN_URL,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={"grant_type": "client_credentials"},
        )
    resp.raise_for_status()
    data = resp.json()
    _sp_token = data["access_token"]
    _sp_token_expiry = time.time() + data["expires_in"]
    return _sp_token


def _sp_get(path: str, params: dict | None = None) -> dict | list:
    """Make an authenticated GET request to the Spotify Web API."""
    url = f"{_SP_API_BASE}{path}"
    with httpx.Client(timeout=30) as client:
        resp = client.get(
            url,
            headers={"Authorization": f"Bearer {_spotify_token()}"},
            params={k: v for k, v in (params or {}).items() if v is not None},
        )
    resp.raise_for_status()
    return resp.json()


# ---- Search ----------------------------------------------------------------

@mcp.tool()
def spotify_search(
    query: str,
    type: str = "artist",
    market: str = "GB",
    limit: int = 10,
    offset: int = 0,
) -> dict:
    """Search the Spotify catalogue for artists, tracks, albums, or playlists.

    Returns Spotify-native IDs that can be passed directly to other
    spotify_* tools without a separate lookup step.

    Args:
        query: Search query — artist name, track title, album title, etc.
        type: Comma-separated list of result types — any combination of
              'artist', 'track', 'album', 'playlist' (default 'artist')
        market: ISO 3166-1 alpha-2 market code to filter availability
                (default 'GB')
        limit: Number of results per type (max 50, default 10)
        offset: Pagination offset (default 0)
    """
    return _sp_get("/search", params={"q": query, "type": type, "market": market, "limit": limit, "offset": offset})


# ---- Artist ----------------------------------------------------------------

@mcp.tool()
def spotify_get_artist(artist_id: str) -> dict:
    """Get full Spotify artist profile — name, genres, popularity score,
    follower count, and image URLs.

    Popularity is a 0–100 score calculated by Spotify from recent stream
    counts; it may lag actual popularity by a few days.

    Args:
        artist_id: Spotify artist ID (e.g. '7fz95oveAOX1S6Fl70eCLE')
    """
    return _sp_get(f"/artists/{artist_id}")


@mcp.tool()
def spotify_get_artist_top_tracks(
    artist_id: str,
    market: str = "GB",
) -> dict:
    """Get an artist's top 10 tracks on Spotify in a given market.

    Each track includes its own popularity score, album, duration, explicit
    flag, and preview URL (where available).

    Args:
        artist_id: Spotify artist ID
        market: ISO 3166-1 alpha-2 market code (default 'GB')
    """
    return _sp_get(f"/artists/{artist_id}/top-tracks", params={"market": market})


@mcp.tool()
def spotify_get_artist_albums(
    artist_id: str,
    include_groups: str = "album,single",
    market: str = "GB",
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """Get an artist's discography on Spotify.

    Args:
        artist_id: Spotify artist ID
        include_groups: Comma-separated release types to include — any
                        combination of 'album', 'single', 'appears_on',
                        'compilation' (default 'album,single')
        market: ISO 3166-1 alpha-2 market code to filter availability
                (default 'GB')
        limit: Number of results (max 50, default 50)
        offset: Pagination offset (default 0)
    """
    return _sp_get(
        f"/artists/{artist_id}/albums",
        params={"include_groups": include_groups, "market": market, "limit": limit, "offset": offset},
    )


@mcp.tool()
def spotify_get_artist_related_artists(artist_id: str) -> dict:
    """Get Spotify's 'Fans Also Like' list for an artist — up to 20 related
    artists determined by overlapping listener behaviour.

    Useful for benchmarking and identifying peer artists for the Artist Index.

    Args:
        artist_id: Spotify artist ID
    """
    return _sp_get(f"/artists/{artist_id}/related-artists")


# ---- Track -----------------------------------------------------------------

@mcp.tool()
def spotify_get_track(
    track_id: str,
    market: str = "GB",
) -> dict:
    """Get metadata for a single Spotify track — name, artists, album,
    duration, popularity score, explicit flag, and preview URL.

    Args:
        track_id: Spotify track ID
        market: ISO 3166-1 alpha-2 market code (default 'GB')
    """
    return _sp_get(f"/tracks/{track_id}", params={"market": market})


@mcp.tool()
def spotify_get_track_audio_features(
    track_ids: str | list[str],
) -> dict | list:
    """Get Spotify audio features for one track or a batch of up to 100 tracks.

    Audio features are the core acoustic fingerprint of a track and are
    directly useful for release strategy — e.g. matching BPM and energy
    profile to playlist editorial criteria.

    Features returned per track:
      - acousticness, danceability, energy, instrumentalness, liveness,
        loudness, speechiness, valence (all 0.0–1.0 except loudness in dB)
      - tempo (BPM), key (0–11 pitch class), mode (0=minor, 1=major)
      - time_signature, duration_ms

    Args:
        track_ids: A single Spotify track ID string, or a list of up to 100
                   Spotify track IDs for batch retrieval.
                   Single example:  '4iV5W9uYEdYUVa79Axb7Rh'
                   Batch example:   ['4iV5W9uYEdYUVa79Axb7Rh', '1301WleyT98MSxVHPZCA6M']
    """
    # Normalise to list
    if isinstance(track_ids, str):
        ids = [track_ids]
    else:
        ids = list(track_ids)

    if len(ids) > 100:
        raise ValueError("spotify_get_track_audio_features accepts a maximum of 100 track IDs per call.")

    if len(ids) == 1:
        # Single-track endpoint returns a plain object
        return _sp_get(f"/audio-features/{ids[0]}")
    else:
        # Batch endpoint returns {"audio_features": [...]}
        return _sp_get("/audio-features", params={"ids": ",".join(ids)})
