"""POST /api/chat — SSE stream of conversational AI responses."""

import json
import logging
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.services import anthropic_client
from app.services import session_store

router = APIRouter()

log = logging.getLogger(__name__)


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
            # Pull Gemini web enrichment stored at snapshot time
            artist_web = session.get("artist_web") or {}
            industry_research = session.get("industry_research") or {}
            web_summary = artist_web.get("summary", "") if isinstance(artist_web, dict) else ""
            research_summary = industry_research.get("summary", "") if isinstance(industry_research, dict) else ""

            # ── DEBUG: confirm what was read back from the session (temporary) ─
            log.info(
                "SESSION DEBUG chat read session_id=%s artist=%r | web summary_len=%d | research summary_len=%d",
                ctx.session_id,
                session.get("artist_name", ""),
                len(web_summary),
                len(research_summary),
            )

            web_blocks = ""
            if web_summary:
                web_blocks += (
                    f"\n\nRECENT WEB INTELLIGENCE for {session['artist_name']} "
                    f"(gathered via live web search — press, news, releases, location):\n{web_summary}"
                )
            if research_summary:
                web_blocks += f"\n\nRELEVANT INDUSTRY RESEARCH:\n{research_summary}"

            # Full grounded context: Chartmetric summary + web research + prior analysis
            system = (
                f"You are advising on the artist: {session['artist_name']}.\n\n"
                f"RAW CHARTMETRIC DATA (live, real-time data from the Chartmetric API — accurate and current, treat it as ground truth):\n{session['summary']}"
                f"{web_blocks}\n\n"
                f"AI ANALYSIS ALREADY SHOWN TO USER:\n{ctx.analysis}\n\n"
                f"Use ALL of the above — Chartmetric data AND the web intelligence — to give "
                f"specific, grounded answers. The web intelligence block has been gathered for you: "
                f"if it contains press coverage, name it; if it contains location information, use it; "
                f"if it mentions recent releases or news, reference them directly. "
                f"Reference actual metrics when helpful. Be direct and actionable. "
                f"Never say the data is limited or unavailable, and never ask the user for information "
                f"(such as their location) that already appears in the data or web intelligence above. "
                f"If session data is unavailable, work from the analysis text and give confident, specific advice."
            )
        else:
            # Session not found (expired or invalid) — fall back to analysis text only
            system = (
                f"You are advising on the artist: {ctx.name}.\n\n"
                f"AI ANALYSIS ALREADY SHOWN TO USER:\n{ctx.analysis}\n\n"
                f"Answer follow-up questions based on the analysis above. "
                f"Be direct and actionable."
                f"IMPORTANT: Never tell the user you lack access to data or that the analysis is generalised. Work confidently from the analysis provided."
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
