"""Gemini web search grounding client.

Uses Gemini 3.8 Flash with Google Search grounding to fetch live web
intelligence about an artist and relevant industry research topics.

Both functions are non-blocking enrichment — if the API is unavailable,
times out, or returns no useful data, they return an empty result so the
core Chartmetric + Claude pipeline continues unaffected.

Timeout: foreground calls default to 15s; the background enrichment path
passes timeout=None to run to completion (Gemini grounding can exceed 15s).
"""

from __future__ import annotations

import asyncio
import logging
import re

import anyio.to_thread

from app import config

log = logging.getLogger(__name__)

_TIMEOUT = 15  # seconds

# Empty result returned on any failure
_EMPTY: dict = {"summary": "", "sources": []}


def _clean_query_term(term: str) -> str:
    """Normalise an artist name / topic for use in a search query.

    Replaces ampersands with 'and', strips apostrophes and other punctuation
    that can confuse search grounding, and collapses whitespace.
    Example: "Francesca & The Apostrophe" -> "Francesca and The Apostrophe"
    """
    if not term:
        return ""
    # Replace & with 'and' so it reads naturally in a search query
    cleaned = term.replace("&", " and ")
    # Drop apostrophes/quotes entirely (don't split words)
    cleaned = re.sub(r"[\'\"`’]", "", cleaned)
    # Replace any remaining non-alphanumeric (keep spaces and hyphens) with a space
    cleaned = re.sub(r"[^\w\s-]", " ", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _make_client():
    """Return a configured Gemini client, or None if GEMINI_API_KEY is unset."""
    if not config.GEMINI_API_KEY:
        return None
    try:
        from google import genai  # type: ignore
        return genai.Client(api_key=config.GEMINI_API_KEY)
    except Exception:
        log.exception("gemini_client: failed to initialise google-genai client")
        return None


def _run_search(query: str) -> dict:
    """Synchronous Gemini call with Google Search grounding.

    Returns {"summary": str, "sources": [{"title", "url", "snippet"}]}.
    Called via anyio.to_thread.run_sync to avoid blocking the event loop.
    """
    client = _make_client()
    if not client:
        return _EMPTY

    try:
        from google.genai import types as gtypes  # type: ignore

        response = client.models.generate_content(
            model="gemini-3.8-flash",
            contents=query,
            config=gtypes.GenerateContentConfig(
                tools=[gtypes.Tool(google_search=gtypes.GoogleSearch())],
                temperature=0.2,
            ),
        )

        # Extract plain text summary
        summary = ""
        if response.candidates:
            candidate = response.candidates[0]
            if candidate.content and candidate.content.parts:
                summary = "".join(
                    p.text for p in candidate.content.parts if hasattr(p, "text") and p.text
                ).strip()

        # Extract grounding sources
        sources: list[dict] = []
        try:
            metadata = response.candidates[0].grounding_metadata
            if metadata and metadata.grounding_chunks:
                seen_urls: set[str] = set()
                for chunk in metadata.grounding_chunks:
                    web = getattr(chunk, "web", None)
                    if not web:
                        continue
                    url = getattr(web, "uri", "") or ""
                    if not url or url in seen_urls:
                        continue
                    seen_urls.add(url)
                    sources.append({
                        "title": getattr(web, "title", "") or "",
                        "url": url,
                        "snippet": getattr(web, "snippet", "") or "",
                    })
        except Exception:
            pass  # Grounding metadata absent — still return the summary

        result = {"summary": summary, "sources": sources}

        # ── DEBUG: log what Gemini actually returned (temporary) ──────────────
        log.info(
            "GEMINI DEBUG query=%r | summary_len=%d | sources=%d",
            query, len(summary), len(sources),
        )
        if summary:
            log.info("GEMINI DEBUG summary preview: %s", summary[:500])
        else:
            log.info("GEMINI DEBUG: empty summary returned")
        for i, s in enumerate(sources[:6]):
            log.info("GEMINI DEBUG source[%d]: %s — %s", i, s.get("title", ""), s.get("url", ""))

        return result

    except Exception:
        log.exception("gemini_client._run_search failed for query=%r", query)
        return _EMPTY


async def _search_with_timeout(query: str, timeout: float | None = _TIMEOUT) -> dict:
    """Run a grounded search. Returns _EMPTY on timeout or error.

    timeout=None runs the search to completion with no ceiling — used by the
    background enrichment path, which has no reason to cap how long Gemini takes.
    A numeric timeout is used by foreground paths (e.g. per-section research)
    that must not hang a request.
    """
    coro = anyio.to_thread.run_sync(lambda: _run_search(query))
    try:
        if timeout is None:
            return await coro
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        log.warning("gemini_client: search timed out after %ss for query=%r", timeout, query)
        return _EMPTY
    except Exception:
        log.exception("gemini_client: unexpected error for query=%r", query)
        return _EMPTY


# ── Public API ────────────────────────────────────────────────────────────────

async def search_artist_web(artist_name: str, timeout: float | None = _TIMEOUT) -> dict:
    """Fetch recent web news, releases, and press for an artist.

    Pass timeout=None (used by the background enrichment task) to run with no
    ceiling. Returns {"summary": str, "sources": [...]}. Never raises.
    """
    safe_name = _clean_query_term(artist_name)
    query = f"{safe_name} music recent news releases press 2024 2025"
    return await _search_with_timeout(query, timeout=timeout)


async def search_industry_research(topic: str, timeout: float | None = _TIMEOUT) -> dict:
    """Fetch relevant music industry research for a given topic.

    Pass timeout=None (used by the background enrichment task) to run with no
    ceiling. Returns {"summary": str, "sources": [...]}. Never raises.
    """
    safe_topic = _clean_query_term(topic)
    query = f"music industry research {safe_topic} independent artists streaming 2024 2025"
    return await _search_with_timeout(query, timeout=timeout)
