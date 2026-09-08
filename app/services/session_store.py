"""In-memory session store for artist analysis results.

Keyed by UUID session_id generated at analysis time. The summary string
(which contains real metric values) stays server-side — only the session_id
is sent to the frontend.

Migration path: replace the dict with Redis calls when scaling requires it.
The three public functions (save_session, get_session, delete_session) form
the stable interface — callers never touch _store directly.
"""

from __future__ import annotations

_store: dict[str, dict] = {}


def save_session(session_id: str, artist_name: str, summary: str) -> None:
    """Persist an analysis session."""
    _store[session_id] = {"artist_name": artist_name, "summary": summary}


def get_session(session_id: str) -> dict | None:
    """Return {artist_name, summary} for the given ID, or None if not found."""
    return _store.get(session_id)


def delete_session(session_id: str) -> None:
    """Remove a session (e.g. on user logout or explicit clear)."""
    _store.pop(session_id, None)


def session_count() -> int:
    """Diagnostic helper — returns number of active sessions in memory."""
    return len(_store)
