"""POST /api/chat — SSE stream of conversational AI responses."""

import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import anthropic_client

router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ArtistContext(BaseModel):
    name: str
    analysis: str


class ChatRequest(BaseModel):
    messages: list[Message]
    artist_context: ArtistContext | None = None


async def _chat_stream(request: ChatRequest):
    system = None
    if request.artist_context:
        system = (
            f"The user just reviewed an analysis for {request.artist_context.name}: "
            f"{request.artist_context.analysis}"
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
