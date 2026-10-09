"""Session store for artist analysis results.

Uses Redis when REDIS_URL is set (production on Railway), falls back to an
in-memory dict for local development without a Redis instance.

Sessions now store an arbitrary payload dict so new fields (Gemini web
data, industry research) can be added without changing this module's
interface. The only required keys callers must set are:
    artist_name: str
    summary: str

Optional keys stored alongside them (Gemini enrichment):
    artist_web: {"summary": str, "sources": [...]}
    industry_research: {"summary": str, "sources": [...]}

Redis sessions have a 24-hour TTL.
The in-memory fallback has no TTL — suitable for local dev only.
"""

from __future__ import annotations

import json
import logging

from app import config

log = logging.getLogger(__name__)

_TTL = 86_400  # 24 hours

_redis_client = None


def _redis():
    global _redis_client
    if _redis_client is None:
        import redis as _redis_lib
        _redis_client = _redis_lib.from_url(
            config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        log.info("Session store: connected to Redis at %s", config.REDIS_URL)
    return _redis_client


_store: dict[str, dict] = {}


def save_session(session_id: str, artist_name: str, summary: str, **extra) -> None:
    """Persist a session. Pass additional keyword args to store extra fields.

    Example:
        save_session(sid, "Billie", summary,
                     artist_web={"summary": ..., "sources": [...]},
                     industry_research={"summary": ..., "sources": [...]})
    """
    payload = {"artist_name": artist_name, "summary": summary, **extra}
    if config.REDIS_URL:
        try:
            _redis().setex(f"session:{session_id}", _TTL, json.dumps(payload))
            return
        except Exception:
            log.exception("Redis save_session failed — falling back to memory")
    _store[session_id] = payload


def get_session(session_id: str) -> dict | None:
    """Return the full session payload, or None if not found."""
    if config.REDIS_URL:
        try:
            raw = _redis().get(f"session:{session_id}")
            return json.loads(raw) if raw else None
        except Exception:
            log.exception("Redis get_session failed — falling back to memory")
    return _store.get(session_id)


def delete_session(session_id: str) -> None:
    if config.REDIS_URL:
        try:
            _redis().delete(f"session:{session_id}")
            return
        except Exception:
            log.exception("Redis delete_session failed — falling back to memory")
    _store.pop(session_id, None)


def session_count() -> int:
    if config.REDIS_URL:
        try:
            return _redis().dbsize()
        except Exception:
            pass
    return len(_store)
