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
        "max_tokens": 1024,
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
        max_tokens=1024,
        system=ANALYSIS_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    ) as stream:
        async for text in stream.text_stream:
            yield text
