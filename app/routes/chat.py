"""POST /api/chat — SSE stream of conversational AI responses."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import anthropic_client
from app.services import session_store

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ArtistContext(BaseModel):
    name: str
    analysis: str
    session_id: str


class ChatRequest(BaseModel):
    messages: list[Message]
    artist_context: ArtistContext | None = None


async def _chat_stream(request: ChatRequest):
    system = None

    if request.artist_context:
        ctx = request.artist_context

        # Look up the summary server-side — never trust the client to send it
        session = session_store.get_session(ctx.session_id)

        if session:
            # Full grounded context: server-stored summary + AI analysis shown to user
            system = (
                f"You are advising on the artist: {session['artist_name']}.\n\n"
                f"RAW CHARTMETRIC DATA:\n{session['summary']}\n\n"
                f"AI ANALYSIS ALREADY SHOWN TO USER:\n{ctx.analysis}\n\n"
                f"Use the raw data to give specific, grounded answers to follow-up questions. "
                f"Reference actual metrics when helpful. Be direct and actionable."
            )
        else:
            # Session not found (expired or invalid) — fall back to analysis text only
            system = (
                f"You are advising on the artist: {ctx.name}.\n\n"
                f"AI ANALYSIS ALREADY SHOWN TO USER:\n{ctx.analysis}\n\n"
                f"Answer follow-up questions based on the analysis above. "
                f"Be direct and actionable."
            )

    messages = [m.model_dump() for m in request.messages]

    try:
        async for token in anthropic_client.stream_chat(messages, system=system):
            yield f"data: {json.dumps({'text': token})}\n\n"
        yield "data: [DONE]\n\n"
    except Exception as e:
        yield f"data: {json.dumps({'error': str(e)})}\n\n"


@router.post("/chat")
async def chat(body: ChatRequest):
    return StreamingResponse(
        _chat_stream(body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
