"""POST /api/analyze/artist — SSE stream of AI analysis."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import chartmetric, anthropic_client

router = APIRouter()


class AnalyzeRequest(BaseModel):
    cm_id: int


async def _event_stream(cm_id: int):
    artist_name = "Unknown Artist"
    try:
        yield f"data: {json.dumps({'type': 'status', 'text': 'Fetching artist data...'})}\n\n"

        raw = await chartmetric.gather_artist_data(cm_id)

        meta = raw.get("metadata") or {}
        if isinstance(meta, dict):
            artist_name = meta.get("name", artist_name)

        yield f"data: {json.dumps({'type': 'status', 'text': 'Analysing...'})}\n\n"

        summary = chartmetric.summarize_for_ai(raw)
        full_analysis = []

        async for token in anthropic_client.stream_analysis(artist_name, summary):
            full_analysis.append(token)
            yield f"data: {json.dumps({'type': 'token', 'text': token})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'artist_name': artist_name})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'text': str(e)})}\n\n"


@router.post("/analyze/artist")
async def analyze_artist(body: AnalyzeRequest):
    return StreamingResponse(
        _event_stream(body.cm_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
