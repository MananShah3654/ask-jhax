"""Thin, backend-agnostic LLM helpers. See backends.py for the implementations."""
from .config import Config
from .backends import get_backend


async def cheap_llm(system: str, text: str) -> str:
    return await get_backend().chat(
        Config.cheap(),
        [{"role": "system", "content": system}, {"role": "user", "content": text}])


async def strong_llm(system: str, text: str) -> str:
    return await get_backend().chat(
        Config.strong(),
        [{"role": "system", "content": system}, {"role": "user", "content": text}])


async def stream_llm(system: str, text: str, on_event, model: str = None) -> str:
    return await get_backend().chat(
        model or Config.strong(),
        [{"role": "system", "content": system}, {"role": "user", "content": text}],
        on_event=on_event)
