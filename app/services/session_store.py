"""Session store for artist analysis results.

Uses Redis when REDIS_URL is set (production on Railway), falls back to an
in-memory dict for local development without a Redis instance.

The public interface is identical in both modes — callers never need to know
which backend is active.

Redis sessions have a 24-hour TTL so memory never grows unboundedly.
The in-memory fallback has no TTL — suitable for local dev only.

Migration path: when REDIS_URL is set, this module is already using Redis.
No code change is needed when moving to production.
"""

from __future__ import annotations

import json
import logging

from app import config

log = logging.getLogger(__name__)

# Session TTL in seconds (24 hours)
_TTL = 86_400

# ── Redis backend ─────────────────────────────────────────────────────────────
_redis_client = None


def _redis():
    """Return a Redis client, lazily initialised on first call."""
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


# ── In-memory fallback ────────────────────────────────────────────────────────
_store: dict[str, dict] = {}


# ── Public interface ──────────────────────────────────────────────────────────

def save_session(session_id: str, artist_name: str, summary: str) -> None:
    """Persist an analysis session keyed by session_id."""
    payload = {"artist_name": artist_name, "summary": summary}
    if config.REDIS_URL:
        try:
            _redis().setex(f"session:{session_id}", _TTL, json.dumps(payload))
            return
        except Exception:
            log.exception("Redis save_session failed — falling back to memory")
    _store[session_id] = payload


def get_session(session_id: str) -> dict | None:
    """Return {artist_name, summary} for the given ID, or None if not found."""
    if config.REDIS_URL:
        try:
            raw = _redis().get(f"session:{session_id}")
            return json.loads(raw) if raw else None
        except Exception:
            log.exception("Redis get_session failed — falling back to memory")
    return _store.get(session_id)


def delete_session(session_id: str) -> None:
    """Remove a session."""
    if config.REDIS_URL:
        try:
            _redis().delete(f"session:{session_id}")
            return
        except Exception:
            log.exception("Redis delete_session failed — falling back to memory")
    _store.pop(session_id, None)


def session_count() -> int:
    """Diagnostic helper — number of active sessions."""
    if config.REDIS_URL:
        try:
            return _redis().dbsize()
        except Exception:
            pass
    return len(_store)
