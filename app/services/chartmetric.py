"""Chartmetric service — lazy pycmc wrapper with async thread offloading.

Phase 1: 12 parallel Chartmetric calls (unchanged from original).
Phase 2: Soundcharts, Last.fm, YouTube called in parallel after Phase 1
         completes (gated on config keys being set — safe to skip any).

All Phase 2 results are merged into the raw dict and surfaced in
summarize_for_ai() so Claude receives a genuinely multi-source picture.
"""

import asyncio
import json
import os
from datetime import date, timedelta
from typing import Any

import anyio.to_thread

from app.services import external_apis

_pycmc = None


def cm():
    """Lazy-load pycmc — only authenticates on first call."""
    global _pycmc
    if _pycmc is None:
        api_key = os.environ["CHARTMETRIC_API_KEY"]
        os.environ["CMCREDENTIALS"] = json.dumps({"refreshtoken": api_key})
        import pycmc as _lib
        _pycmc = _lib
    return _pycmc


def _today() -> str:
    return date.today().isoformat()


def _days_ago(n: int) -> str:
    return (date.today() - timedelta(days=n)).isoformat()


# ── Search ────────────────────────────────────────────────────────────────────

async def search_artists(q: str) -> list[dict]:
    def _search():
        result = cm().search_engine.search(query=q, type="artists", limit=10)
        artists = []
        items = result if isinstance(result, list) else result.get("artists", [])
        for item in items:
            artists.append({
                "cm_id": item.get("id") or item.get("cm_artist"),
                "name": item.get("name", ""),
                "image_url": item.get("image_url") or item.get("imageUrl") or "",
                "genres": item.get("genres") or item.get("tags") or [],
            })
        return artists

    return await anyio.to_thread.run_sync(_search)


# ── Data gather ───────────────────────────────────────────────────────────────

async def gather_artist_data(cm_id: int) -> dict:
    today = _today()
    d90 = _days_ago(90)
    d30 = _days_ago(30)

    async def _run(fn, *args, **kwargs):
        try:
            return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))
        except Exception:
            return None

    # ── Phase 1: Chartmetric (unchanged) ─────────────────────────────────────
    results = await asyncio.gather(
        _run(cm().artist.metadata, cm_id),
        # Spotify
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="spotify", valueCol="followers"),
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="spotify", valueCol="listeners"),
        _run(cm().artist.playlists, cmid=cm_id, dsrc="spotify", start_date=d30, status="current"),
        _run(cm().artist.charts, chart_type="spotify_top_daily", cmid=cm_id, start_date=d30, end_date=today),
        _run(cm().artist.related, cmid=cm_id, limit=10),
        # Streaming overview
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="applemusic", valueCol="listeners"),
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="deezer", valueCol="followers"),
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="youtube_channel", valueCol="subscribers"),
        # Socials
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="instagram", valueCol="followers"),
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="tiktok", valueCol="followers"),
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="youtube_channel", valueCol="views"),
    )

    raw = {
        "metadata": results[0],
        "followers": results[1],
        "listeners": results[2],
        "playlists": results[3],
        "charts": results[4],
        "related": results[5],
        "apple_listeners": results[6],
        "deezer_followers": results[7],
        "youtube_subscribers": results[8],
        "instagram_followers": results[9],
        "tiktok_followers": results[10],
        "youtube_views": results[11],
    }

    # ── Phase 2: external APIs ────────────────────────────────────────────────
    # Extract identifiers from Phase 1 metadata
    meta = raw.get("metadata") or {}
    artist_name = meta.get("name", "") if isinstance(meta, dict) else ""

    # Spotify ID lives in the metadata urls or a dedicated field
    spotify_id = _extract_spotify_id(meta)

    # Artist URL dict for YouTube channel extraction
    artist_urls = None
    if isinstance(meta, dict):
        artist_urls = meta.get("urls") or meta.get("links")

    if artist_name or spotify_id:
        sc_data, lfm_data, yt_data = await asyncio.gather(
            external_apis.gather_soundcharts_data(spotify_id) if spotify_id else asyncio.sleep(0, result={}),
            external_apis.gather_lastfm_data(artist_name) if artist_name else asyncio.sleep(0, result={}),
            external_apis.gather_youtube_data(artist_urls),
        )
        raw["soundcharts"] = sc_data or {}
        raw["lastfm"] = lfm_data or {}
        raw["youtube_api"] = yt_data or {}
    else:
        raw["soundcharts"] = {}
        raw["lastfm"] = {}
        raw["youtube_api"] = {}

    return raw


def _extract_spotify_id(meta: Any) -> str | None:
    """Extract Spotify artist ID from Chartmetric metadata."""
    if not isinstance(meta, dict):
        return None
    # Direct field
    for key in ("spotify_artist_ids", "spotify_id", "sp_artist_id"):
        val = meta.get(key)
        if val:
            return val[0] if isinstance(val, list) else str(val)
    # Nested in code_url or url objects
    urls = meta.get("code_url") or meta.get("urls") or {}
    if isinstance(urls, dict):
        sp = urls.get("spotify") or urls.get("spotify_artist_page")
        if isinstance(sp, list) and sp:
            sp = sp[0]
        if isinstance(sp, dict):
            sp = sp.get("url", "")
        if sp and isinstance(sp, str):
            import re
            m = re.search(r"spotify\.com/artist/([A-Za-z0-9]+)", sp)
            if m:
                return m.group(1)
    return None


# ── Summarise for AI ──────────────────────────────────────────────────────────

def _fanmetric_summary(series: Any, label: str) -> dict | None:
    """Reduce a fanmetric time series to start/end/peak/change."""
    if not series:
        return None
    items = series if isinstance(series, list) else series.get("data", [])
    if not items:
        return None
    values = [x.get("value") or x.get(label) or 0 for x in items if x]
    values = [v for v in values if v is not None]
    if not values:
        return None
    start, end, peak = values[0], values[-1], max(values)
    pct = round((end - start) / start * 100, 1) if start else 0
    return {"start": start, "end": end, "peak": peak, "pct_change": pct}


def summarize_for_ai(raw: dict) -> str:
    parts: list[str] = []

    # ── Chartmetric metadata ──────────────────────────────────────────────────
    meta = raw.get("metadata") or {}
    if isinstance(meta, dict):
        name = meta.get("name", "Unknown")
        raw_genres = meta.get("genres") or meta.get("tags") or []
        if isinstance(raw_genres, dict):
            genres = []
            for v in raw_genres.values():
                if isinstance(v, dict):
                    genres.append(v.get("name", ""))
                elif isinstance(v, list):
                    genres.extend(g.get("name", "") for g in v if isinstance(g, dict))
            genres = [g for g in genres if g]
        elif isinstance(raw_genres, list):
            genres = [g.get("name", g) if isinstance(g, dict) else str(g) for g in raw_genres]
        else:
            genres = []
        cm_score = meta.get("cm_artist_rank") or meta.get("artist_rank")
        parts.append(f"Artist: {name}")
        if genres:
            parts.append(f"Genres: {', '.join(str(g) for g in genres[:5])}")
        if cm_score:
            parts.append(f"Chartmetric rank: {cm_score}")

    # ── Chartmetric fan metrics ───────────────────────────────────────────────
    followers = _fanmetric_summary(raw.get("followers"), "followers")
    if followers:
        parts.append(
            f"Spotify followers (90d): start={followers['start']:,}, "
            f"end={followers['end']:,}, peak={followers['peak']:,}, "
            f"change={followers['pct_change']:+.1f}%"
        )

    listeners = _fanmetric_summary(raw.get("listeners"), "listeners")
    if listeners:
        parts.append(
            f"Spotify monthly listeners (90d): start={listeners['start']:,}, "
            f"end={listeners['end']:,}, peak={listeners['peak']:,}, "
            f"change={listeners['pct_change']:+.1f}%"
        )

    # ── Chartmetric playlists ─────────────────────────────────────────────────
    playlists = raw.get("playlists") or []
    if isinstance(playlists, dict):
        playlists = playlists.get("data", [])
    if playlists:
        sorted_pl = sorted(
            playlists,
            key=lambda p: p.get("followers") or p.get("num_followers") or 0,
            reverse=True,
        )[:10]
        pl_lines = []
        for p in sorted_pl:
            pl_name = p.get("name", "?")
            pl_followers = p.get("followers") or p.get("num_followers") or 0
            pl_lines.append(f"  - {pl_name} ({pl_followers:,} followers)")
        parts.append("Current Spotify playlists (top 10 by followers):\n" + "\n".join(pl_lines))

    # ── Chartmetric charts ────────────────────────────────────────────────────
    charts = raw.get("charts") or []
    if isinstance(charts, dict):
        charts = charts.get("data", [])
    if charts:
        positions = [c.get("rank") or c.get("position") or 999 for c in charts if c]
        peak = min(positions) if positions else None
        parts.append(
            f"Spotify top daily chart: {len(positions)} entries in last 30d"
            + (f", peak position #{peak}" if peak else "")
        )

    # ── Chartmetric related artists ───────────────────────────────────────────
    related = raw.get("related") or []
    if isinstance(related, dict):
        related = related.get("data", [])
    if related:
        names = [r.get("name", "") for r in related[:10] if r and r.get("name")]
        parts.append(f"Related artists: {', '.join(names)}")

    # ── Chartmetric cross-platform ────────────────────────────────────────────
    for key, label in [
        ("apple_listeners", "Apple Music listeners (90d)"),
        ("deezer_followers", "Deezer followers (90d)"),
        ("youtube_subscribers", "YouTube subscribers (90d)"),
        ("instagram_followers", "Instagram followers (90d)"),
        ("tiktok_followers", "TikTok followers (90d)"),
    ]:
        col = key.split("_")[-1]
        summary = _fanmetric_summary(raw.get(key), col)
        if summary:
            parts.append(
                f"{label}: start={summary['start']:,}, end={summary['end']:,}, "
                f"change={summary['pct_change']:+.1f}%"
            )

    # ── Last.fm ───────────────────────────────────────────────────────────────
    lfm = raw.get("lastfm") or {}
    lfm_info = lfm.get("info") or {}
    lfm_artist = lfm_info.get("artist") or {} if isinstance(lfm_info, dict) else {}
    if lfm_artist:
        stats = lfm_artist.get("stats") or {}
        listeners_lfm = stats.get("listeners")
        scrobbles = stats.get("playcount")
        if listeners_lfm:
            parts.append(f"Last.fm listeners (all-time): {int(listeners_lfm):,}")
        if scrobbles:
            parts.append(f"Last.fm scrobbles (all-time): {int(scrobbles):,}")
        # Top tags
        tags_raw = lfm_artist.get("tags") or {}
        tag_list = tags_raw.get("tag") or [] if isinstance(tags_raw, dict) else []
        if tag_list:
            tag_names = [t.get("name", "") for t in tag_list[:5] if isinstance(t, dict)]
            tag_names = [t for t in tag_names if t]
            if tag_names:
                parts.append(f"Last.fm community tags: {', '.join(tag_names)}")

    lfm_tracks = lfm.get("top_tracks") or {}
    if isinstance(lfm_tracks, dict):
        track_list = (lfm_tracks.get("toptracks") or {}).get("track") or []
        if track_list:
            names = [t.get("name", "") for t in track_list[:5] if isinstance(t, dict)]
            names = [n for n in names if n]
            if names:
                parts.append(f"Last.fm top tracks by scrobbles: {', '.join(names)}")

    # ── Soundcharts ───────────────────────────────────────────────────────────
    sc = raw.get("soundcharts") or {}
    if sc:
        # Radio spins
        radio = sc.get("radio_spins") or {}
        radio_items = radio.get("items") or [] if isinstance(radio, dict) else []
        if radio_items:
            spin_count = len(radio_items)
            stations = list({
                item.get("radio", {}).get("name") or item.get("radioName", "")
                for item in radio_items[:20]
                if isinstance(item, dict)
            } - {""})[:5]
            parts.append(
                f"Soundcharts radio: {spin_count} spins in last 30 days"
                + (f", stations include: {', '.join(stations)}" if stations else "")
            )

        # Chart entries
        chart_data = sc.get("chart_entries") or {}
        chart_items = chart_data.get("items") or [] if isinstance(chart_data, dict) else []
        if chart_items:
            best = min(
                (item.get("position") or 999 for item in chart_items if isinstance(item, dict)),
                default=None,
            )
            parts.append(
                f"Soundcharts chart entries: {len(chart_items)} chart positions found"
                + (f", best position #{best}" if best and best < 999 else "")
            )

        # Soundcharts playlists
        sc_pl = sc.get("playlists") or {}
        sc_pl_items = sc_pl.get("items") or [] if isinstance(sc_pl, dict) else []
        if sc_pl_items:
            parts.append(f"Soundcharts playlist placements: {len(sc_pl_items)} current placements")

    # ── YouTube API ───────────────────────────────────────────────────────────
    yt_api = raw.get("youtube_api") or {}
    yt_stats = yt_api.get("stats") or {}
    yt_statistics = yt_stats.get("statistics") or {} if isinstance(yt_stats, dict) else {}
    if yt_statistics:
        subs = yt_statistics.get("subscriberCount")
        views = yt_statistics.get("viewCount")
        if subs:
            parts.append(f"YouTube channel subscribers: {int(subs):,}")
        if views:
            parts.append(f"YouTube channel total views: {int(views):,}")

    return "\n".join(parts)


# ── Chart data extraction (used by frontend for time-series charts) ───────────

def _extract_series(raw_data: Any, value_key: str) -> list[dict]:
    """Extract [{date, value}] from a fanmetrics response."""
    if not raw_data:
        return []
    items = raw_data if isinstance(raw_data, list) else raw_data.get("data", [])
    result = []
    for item in items:
        if not item:
            continue
        date_val = item.get("timestp") or item.get("date") or item.get("timestamp")
        value = item.get(value_key) or item.get("value") or 0
        if date_val and value is not None:
            result.append({"date": str(date_val)[:10], "value": value})
    return result


def extract_charts_data(raw: dict) -> dict:
    """Extract time-series data for frontend charts."""
    return {
        "spotify": {
            "followers": _extract_series(raw.get("followers"), "followers"),
            "listeners": _extract_series(raw.get("listeners"), "listeners"),
        },
        "streaming": {
            "apple_listeners": _extract_series(raw.get("apple_listeners"), "listeners"),
            "deezer_followers": _extract_series(raw.get("deezer_followers"), "followers"),
            "youtube_subscribers": _extract_series(raw.get("youtube_subscribers"), "subscribers"),
        },
        "socials": {
            "instagram_followers": _extract_series(raw.get("instagram_followers"), "followers"),
            "tiktok_followers": _extract_series(raw.get("tiktok_followers"), "followers"),
            "youtube_views": _extract_series(raw.get("youtube_views"), "views"),
        },
    }
