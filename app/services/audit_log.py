"""Redis audit log for artist searches.

Each search is stored as a Redis hash under the key:
    audit:{iso_timestamp}:{cm_id}

e.g.  audit:2026-10-07T14:32:01.123456+00:00:7654321

ISO-8601 timestamps sort lexicographically, so SCAN + sort gives chronological
order without a secondary index.

TTL: 90 days (configurable via AUDIT_TTL_DAYS env var).
Falls back gracefully to a no-op if Redis is unavailable — the pipeline
never fails because the audit log is down.

Hash fields per key:
    ts          ISO-8601 UTC timestamp
    artist_name Artist display name
    cm_id       Chartmetric artist ID (string)
    raw_json    JSON-serialised full raw data dict
    summary     summarize_for_ai() output text
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from urllib.parse import quote, unquote

log = logging.getLogger(__name__)

_TTL_DAYS = int(os.environ.get("AUDIT_TTL_DAYS", "90"))
_TTL_SECONDS = _TTL_DAYS * 86_400
_KEY_PREFIX = "audit:"


def _redis():
    """Return the shared Redis client from session_store, or None if unavailable."""
    from app import config
    if not config.REDIS_URL:
        return None
    try:
        import redis as _r
        return _r.from_url(
            config.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
    except Exception:
        log.exception("audit_log: failed to connect to Redis")
        return None


def _make_key(ts: str, cm_id: int) -> str:
    """Build a Redis key that sorts chronologically."""
    return f"{_KEY_PREFIX}{ts}:{cm_id}"


def encode_key(redis_key: str) -> str:
    """URL-encode a Redis key for use in route paths."""
    return quote(redis_key, safe="")


def decode_key(encoded: str) -> str:
    """Decode a URL-encoded Redis key back to its original form."""
    return unquote(encoded)


# ── Write ─────────────────────────────────────────────────────────────────────

async def record(
    artist_name: str,
    cm_id: int,
    raw: dict,
    summary: str,
) -> str | None:
    """Store a search record. Returns the Redis key, or None on failure."""
    import anyio.to_thread
    ts = datetime.now(timezone.utc).isoformat()
    key = _make_key(ts, cm_id)
    payload = {
        "ts": ts,
        "artist_name": artist_name,
        "cm_id": str(cm_id),
        "raw_json": json.dumps(raw, default=str),
        "summary": summary,
    }
    try:
        def _write():
            r = _redis()
            if not r:
                return None
            pipe = r.pipeline()
            pipe.hset(key, mapping=payload)
            pipe.expire(key, _TTL_SECONDS)
            pipe.execute()
            return key
        return await anyio.to_thread.run_sync(_write)
    except Exception:
        log.exception("audit_log.record failed for artist=%s cm_id=%s", artist_name, cm_id)
        return None


# ── Read ──────────────────────────────────────────────────────────────────────

async def fetch_all(limit: int = 200) -> list[dict]:
    """Return the most recent searches sorted newest-first.

    Uses SCAN to find all audit:* keys — safe on Railway's Redis instance
    sizes. Sorts by key (ISO timestamp prefix) descending.
    """
    import anyio.to_thread
    try:
        def _scan():
            r = _redis()
            if not r:
                return []
            keys = []
            cursor = 0
            while True:
                cursor, batch = r.scan(cursor=cursor, match=f"{_KEY_PREFIX}*", count=200)
                keys.extend(batch)
                if cursor == 0:
                    break
            # Sort descending by key (ISO ts prefix sorts lexicographically)
            keys.sort(reverse=True)
            keys = keys[:limit]
            if not keys:
                return []
            pipe = r.pipeline()
            for k in keys:
                pipe.hmget(k, "ts", "artist_name", "cm_id")
            results = pipe.execute()
            rows = []
            for k, fields in zip(keys, results):
                ts, artist_name, cm_id = fields
                rows.append({
                    "key": k,
                    "encoded_key": encode_key(k),
                    "ts": ts or "",
                    "artist_name": artist_name or "",
                    "cm_id": cm_id or "",
                })
            return rows
        return await anyio.to_thread.run_sync(_scan)
    except Exception:
        log.exception("audit_log.fetch_all failed")
        return []


async def fetch_one(encoded_key: str) -> dict | None:
    """Return full detail for a single search by its URL-encoded Redis key."""
    import anyio.to_thread
    key = decode_key(encoded_key)
    try:
        def _get():
            r = _redis()
            if not r:
                return None
            data = r.hgetall(key)
            if not data:
                return None
            data["key"] = key
            data["encoded_key"] = encoded_key
            return data
        return await anyio.to_thread.run_sync(_get)
    except Exception:
        log.exception("audit_log.fetch_one failed for key=%s", key)
        return None


async def delete_one(encoded_key: str) -> bool:
    """Delete a search record by its URL-encoded Redis key."""
    import anyio.to_thread
    key = decode_key(encoded_key)
    try:
        def _del():
            r = _redis()
            if not r:
                return False
            r.delete(key)
            return True
        return await anyio.to_thread.run_sync(_del)
    except Exception:
        log.exception("audit_log.delete_one failed for key=%s", key)
        return False
