"""Analysis routes.

POST /api/analyze/artist   — original monolithic analysis (backwards compatible)
POST /api/analyze/snapshot — Phase 1: fast 3-sentence snapshot, returns session_id
POST /api/analyze/sections — Phase 2: stream selected sections one by one
"""

import json
import uuid
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import chartmetric, anthropic_client, audit_log
from app.services import session_store
from app.prompts import SECTION_PROMPTS

router = APIRouter()

# Valid section IDs — guards against arbitrary prompt injection
_VALID_SECTIONS = frozenset(SECTION_PROMPTS.keys())


# ── Request models ────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    cm_id: int


class SnapshotRequest(BaseModel):
    cm_id: int


class SectionsRequest(BaseModel):
    session_id: str
    sections: List[str]


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
            await audit_log.record(
                artist_name=artist_name,
                cm_id=cm_id,
                raw=raw,
                summary=summary,
            )
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

        yield f"data: {json.dumps({'type': 'status', 'text': 'Building snapshot...'})}\n\n"

        summary = chartmetric.summarize_for_ai(raw)

        # Store server-side immediately so sections can use it without re-fetching
        session_store.save_session(session_id, artist_name, summary)

        # Audit — fire and forget
        try:
            await audit_log.record(
                artist_name=artist_name,
                cm_id=cm_id,
                raw=raw,
                summary=summary,
            )
        except Exception:
            pass

        # Stream the snapshot
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
    # Validate section IDs up front — reject anything not in the allowed set
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

    for section_id in sections:
        try:
            yield f"data: {json.dumps({'type': 'section_start', 'section': section_id})}\n\n"

            async for token in anthropic_client.stream_section(section_id, artist_name, summary):
                yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

            yield f"data: {json.dumps({'type': 'section_done', 'section': section_id})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'text': f'Section {section_id} failed: {str(e)}'})}\n\n"
            # Continue with remaining sections rather than aborting the whole stream

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
