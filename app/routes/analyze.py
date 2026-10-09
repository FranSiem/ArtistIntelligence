"""Analysis routes.

POST /api/analyze/artist   — original monolithic analysis (backwards compatible)
POST /api/analyze/snapshot — Phase 1: fast 3-sentence snapshot, returns session_id
POST /api/analyze/sections — Phase 2: stream selected sections one by one
"""

import asyncio
import json
import logging
import uuid
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import chartmetric, anthropic_client, audit_log
from app.services import session_store
from app.services.gemini_client import search_artist_web, search_industry_research
from app.prompts import SECTION_PROMPTS

router = APIRouter()

log = logging.getLogger(__name__)

_VALID_SECTIONS = frozenset(SECTION_PROMPTS.keys())

# Hold references to background enrichment tasks so they aren't garbage-collected
# before they complete (asyncio only keeps weak references to tasks).
_background_tasks: set = set()


async def _enrich_session_in_background(session_id: str, artist_name: str) -> None:
    """Run Gemini enrichment and merge results into the session when complete.

    Fire-and-forget: launched from the snapshot route so the snapshot can return
    immediately from Chartmetric data. By the time the user selects sections or
    asks a chat question, this has usually completed and updated the session.
    No timeout here — the task runs to completion in the background.
    """
    try:
        # No timeout — this runs in the background and must not be capped.
        artist_web, industry_research = await asyncio.gather(
            search_artist_web(artist_name, timeout=None),
            search_industry_research("independent artist growth streaming", timeout=None),
        )
        updated = session_store.update_session(
            session_id,
            artist_web=artist_web,
            industry_research=industry_research,
        )
        _aw = artist_web or {}
        _ir = industry_research or {}
        log.info(
            "GEMINI BACKGROUND done session_id=%s artist=%r updated=%s | artist_web summary_len=%d sources=%d | industry_research summary_len=%d sources=%d",
            session_id,
            artist_name,
            updated,
            len(_aw.get("summary", "")),
            len(_aw.get("sources", [])),
            len(_ir.get("summary", "")),
            len(_ir.get("sources", [])),
        )
    except Exception:
        log.exception("GEMINI BACKGROUND failed session_id=%s", session_id)

# Topic mapped to each section for per-section industry research
SECTION_RESEARCH_TOPICS: dict[str, str] = {
    "audience_geography":    "music audience geography diaspora listeners",
    "streaming_performance": "spotify streaming performance independent artists playlists",
    "radio_press":           "radio airplay press coverage independent music strategy",
    "collaborators":         "music collaboration strategy artist features growth",
    "next_steps":            "independent artist 30 day marketing strategy",
    "revenue_royalties":     "music royalties revenue streams independent artists",
}


# ── Request models ────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    cm_id: int

class SnapshotRequest(BaseModel):
    cm_id: int

class SectionsRequest(BaseModel):
    session_id: str
    sections: List[str]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _merge_sources(*source_lists: list) -> list:
    """Deduplicate and cap combined sources at 6, keyed by URL."""
    seen: set[str] = set()
    merged: list[dict] = []
    for lst in source_lists:
        for src in lst:
            url = src.get("url", "")
            if url and url not in seen:
                seen.add(url)
                merged.append(src)
                if len(merged) >= 6:
                    return merged
    return merged


# ── Original monolithic endpoint (unchanged — backwards compatible) ────────────

async def _event_stream(cm_id: int):
    artist_name = "Unknown Artist"
    session_id = str(uuid.uuid4())
    try:
        yield f"data: {json.dumps({'type': 'status', 'text': 'Fetching artist data...'})}\n\n"
        raw = await chartmetric.gather_artist_data(cm_id)
        meta = raw.get("metadata") or {}
        if isinstance(meta, dict):
            artist_name = meta.get("name", artist_name)
        yield f"data: {json.dumps({'type': 'status', 'text': 'Analysing...'})}\n\n"
        summary = chartmetric.summarize_for_ai(raw)
        session_store.save_session(session_id, artist_name, summary)
        try:
            await audit_log.record(artist_name=artist_name, cm_id=cm_id, raw=raw, summary=summary)
        except Exception:
            pass
        async for token in anthropic_client.stream_analysis(artist_name, summary):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'artist_name': artist_name, 'session_id': session_id})}\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"


@router.post("/analyze/artist")
async def analyze_artist(body: AnalyzeRequest):
    return StreamingResponse(
        _event_stream(body.cm_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Phase 1: Snapshot ─────────────────────────────────────────────────────────

async def _snapshot_stream(cm_id: int):
    artist_name = "Unknown Artist"
    session_id = str(uuid.uuid4())
    try:
        yield f"data: {json.dumps({'type': 'status', 'text': 'Fetching artist data...'})}\n\n"

        raw = await chartmetric.gather_artist_data(cm_id)
        meta = raw.get("metadata") or {}
        if isinstance(meta, dict):
            artist_name = meta.get("name", artist_name)

        summary = chartmetric.summarize_for_ai(raw)

        # Save the session immediately with empty Gemini fields so sections/chat
        # have something to read even before enrichment completes.
        session_store.save_session(
            session_id,
            artist_name,
            summary,
            artist_web={},
            industry_research={},
        )

        # Fire Gemini enrichment as a background task — does NOT block the snapshot.
        # It updates the session in place when it completes (usually within ~10s).
        task = asyncio.create_task(
            _enrich_session_in_background(session_id, artist_name)
        )
        _background_tasks.add(task)
        task.add_done_callback(_background_tasks.discard)

        try:
            await audit_log.record(artist_name=artist_name, cm_id=cm_id, raw=raw, summary=summary)
        except Exception:
            pass

        yield f"data: {json.dumps({'type': 'status', 'text': 'Building snapshot...'})}\n\n"

        async for token in anthropic_client.stream_snapshot(artist_name, summary):
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'artist_name': artist_name, 'session_id': session_id})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"


@router.post("/analyze/snapshot")
async def analyze_snapshot(body: SnapshotRequest):
    return StreamingResponse(
        _snapshot_stream(body.cm_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Phase 2: Sections ─────────────────────────────────────────────────────────

async def _sections_stream(session_id: str, sections: List[str]):
    invalid = [s for s in sections if s not in _VALID_SECTIONS]
    if invalid:
        yield f"data: {json.dumps({'type': 'error', 'text': f'Unknown section(s): {invalid}'})}\n\n"
        return

    session = session_store.get_session(session_id)
    if not session:
        yield f"data: {json.dumps({'type': 'error', 'text': 'Session not found or expired. Please search again.'})}\n\n"
        return

    artist_name = session["artist_name"]
    summary = session["summary"]
    # Gemini data stored at snapshot time — empty dicts if Gemini was unavailable
    artist_web: dict = session.get("artist_web") or {}
    base_industry_research: dict = session.get("industry_research") or {}

    for section_id in sections:
        try:
            yield f"data: {json.dumps({'type': 'section_start', 'section': section_id})}\n\n"

            # Fetch section-specific industry research concurrently with streaming prep
            # Uses the topic mapped to this section; gracefully returns {} on failure
            topic = SECTION_RESEARCH_TOPICS.get(section_id, "music industry independent artists")
            section_research = await search_industry_research(topic)

            async for token in anthropic_client.stream_section(
                section_id=section_id,
                artist_name=artist_name,
                summary=summary,
                artist_web_summary=artist_web.get("summary", ""),
                industry_research_summary=(
                    section_research.get("summary", "")
                    or base_industry_research.get("summary", "")
                ),
            ):
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

            yield f"data: {json.dumps({'type': 'section_done', 'section': section_id})}\n\n"

            # Emit combined sources for this section (artist web + section research)
            combined = _merge_sources(
                artist_web.get("sources", []),
                section_research.get("sources", []),
            )
            if combined:
                yield f"data: {json.dumps({'type': 'section_sources', 'section': section_id, 'sources': combined})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': f'Section {section_id} failed: {str(e)}'})}\n\n"

    yield f"data: {json.dumps({'type': 'all_done'})}\n\n"


@router.post("/analyze/sections")
async def analyze_sections(body: SectionsRequest):
    if not body.sections:
        raise HTTPException(status_code=400, detail="sections list must not be empty")
    return StreamingResponse(
        _sections_stream(body.session_id, body.sections),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
