"""Chartmetric service — lazy pycmc wrapper with async thread offloading."""

import asyncio
import json
import os
from datetime import date, timedelta
from typing import Any

import anyio.to_thread

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


async def gather_artist_data(cm_id: int) -> dict:
    today = _today()
    d90 = _days_ago(90)
    d30 = _days_ago(30)

    async def _run(fn, *args, **kwargs):
        try:
            return await anyio.to_thread.run_sync(lambda: fn(*args, **kwargs))
        except Exception:
            return None

    results = await asyncio.gather(
        _run(cm().artist.metadata, cm_id),
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="spotify", valueCol="followers"),
        _run(cm().artist.fanmetrics, cmid=cm_id, start_date=d90, end_date=today, dsrc="spotify", valueCol="listeners"),
        _run(cm().artist.playlists, cmid=cm_id, dsrc="spotify", start_date=d30, status="current"),
        _run(cm().artist.charts, chart_type="spotify_top_daily", cmid=cm_id, start_date=d30, end_date=today),
        _run(cm().artist.related, cmid=cm_id, limit=10),
    )

    return {
        "metadata": results[0],
        "followers": results[1],
        "listeners": results[2],
        "playlists": results[3],
        "charts": results[4],
        "related": results[5],
    }


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

    # Metadata
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

    # Fan metrics
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

    # Playlists — top 10 by followers
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

    # Charts
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

    # Related artists
    related = raw.get("related") or []
    if isinstance(related, dict):
        related = related.get("data", [])
    if related:
        names = [r.get("name", "") for r in related[:10] if r and r.get("name")]
        parts.append(f"Related artists: {', '.join(names)}")

    return "\n".join(parts)
