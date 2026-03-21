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
