"""
Built-in live web search using Gemini + Google Search grounding — the SAME
approach jhax uses. This becomes the DEFAULT `web_search` for the roster and the
API, so search works out of the box (no need to inject your own).

Override by passing your own `web_search=...` if you prefer another provider.
"""
from emergentintegrations.llm.chat import LlmChat, UserMessage

from .config import Config


def _search_chat(system: str) -> LlmChat:
    return (
        LlmChat(api_key=Config.KEY, session_id="ai_core_search", system_message=system)
        .with_model(*Config.SEARCH_MODEL)
        .with_tools([{"googleSearch": {}}])
    )


def _extract_citations(resp):
    out, seen = [], set()
    try:
        anns = resp.raw.choices[0].message.annotations or []
    except Exception:
        anns = []
    for a in anns:
        try:
            c = a.get("url_citation") if isinstance(a, dict) else getattr(a, "url_citation", None)
            if not c:
                continue
            url = c.get("url") if isinstance(c, dict) else getattr(c, "url", None)
            title = c.get("title") if isinstance(c, dict) else getattr(c, "title", None)
            if url and url not in seen:
                seen.add(url)
                out.append({"title": title or "source", "url": url})
        except Exception:
            continue
    return out[:6]


async def gemini_web_search(query: str) -> dict:
    """Default tool impl: returns {query, results, sources}."""
    sys = (
        "You are a live web search tool. Use Google Search to find current, specific, real facts. "
        "Return a concise factual summary with concrete named businesses, numbers, ratings and "
        "sources. If asked for competitors or nearby places, list the REAL business names you find."
    )
    chat = _search_chat(sys)
    resp = await chat.send_message_with_tools(UserMessage(text=query))
    return {"query": query, "results": resp.content or "", "sources": _extract_citations(resp)}
