"""Anthropic client singleton with streaming helpers."""

from typing import AsyncIterator

import anthropic

from app import config
from app.prompts import ANALYSIS_SYSTEM_PROMPT

_client: anthropic.AsyncAnthropic | None = None


def get_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        _client = anthropic.AsyncAnthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


async def stream_chat(
    messages: list[dict],
    system: str | None = None,
) -> AsyncIterator[str]:
    kwargs: dict = {
        "model": config.ANTHROPIC_MODEL,
        "max_tokens": 4096,
        "messages": messages,
    }
    if system:
        kwargs["system"] = system

    async with get_client().messages.stream(**kwargs) as stream:
        async for text in stream.text_stream:
            yield text


async def stream_analysis(artist_name: str, summary: str) -> AsyncIterator[str]:
    user_message = (
        f"Please analyse this artist: {artist_name}\n\n"
        f"Data summary:\n{summary}"
    )
    async with get_client().messages.stream(
        model=config.ANTHROPIC_MODEL,
        max_tokens=4096,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def stream_snapshot(artist_name: str, summary: str) -> AsyncIterator[str]:
    """Stream a fast 3-sentence artist snapshot using SNAPSHOT_PROMPT."""
    from app.prompts import SNAPSHOT_PROMPT
    user_message = (
        f"Artist: {artist_name}\n\n"
        f"Data summary:\n{summary}"
    )
    async with get_client().messages.stream(
        model=config.ANTHROPIC_MODEL,
        max_tokens=256,
        system=SNAPSHOT_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for text in stream.text_stream:
            yield text


async def stream_section(
    section_id: str,
    artist_name: str,
    summary: str,
    artist_web_summary: str = "",
    industry_research_summary: str = "",
) -> AsyncIterator[str]:
    """Stream a single analysis section using its focused prompt.

    artist_web_summary and industry_research_summary are injected as
    additional context before the section instruction when non-empty.
    Raises KeyError if section_id is not in SECTION_PROMPTS.
    """
    from app.prompts import SECTION_PROMPTS
    system = SECTION_PROMPTS[section_id].format(artist_name=artist_name)

    # Build user message — inject Gemini enrichment when available
    enrichment_blocks: list[str] = []
    if artist_web_summary:
        enrichment_blocks.append(
            f"Recent web intelligence for {artist_name}:\n{artist_web_summary}"
        )
    if industry_research_summary:
        enrichment_blocks.append(
            f"Relevant industry research:\n{industry_research_summary}"
        )

    if enrichment_blocks:
        enrichment = "\n\n".join(enrichment_blocks)
        enrichment += (
            "\n\nUse the above to inform your recommendations. Where the research "
            "supports a specific claim, let it shape the advice — but write as an "
            "advisor, not a researcher. Do not reproduce URLs or citation markers "
            "in your output."
        )
        user_message = (
            f"Artist: {artist_name}\n\n"
            f"Data summary:\n{summary}\n\n"
            f"{enrichment}"
        )
    else:
        user_message = (
            f"Artist: {artist_name}\n\n"
            f"Data summary:\n{summary}"
        )

    async with get_client().messages.stream(
        model=config.ANTHROPIC_MODEL,
        max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
