"""
Built-in live web search. Uses:
  - Google GenAI SDK (google-search grounding) when GEMINI_API_KEY is set  [outside Emergent]
  - emergentintegrations googleSearch when only EMERGENT_LLM_KEY is set     [inside Emergent]

Returns {query, results, sources:[{title,url}]}. Override by passing your own
`web_search=` to the roster/API if you prefer another provider (SerpAPI, Bing...).
"""
import asyncio

from .config import Config


# ---------------- Gemini native (outside Emergent) ----------------
def _genai_search_sync(query: str) -> dict:
    from google import genai
    from google.genai import types
    client = genai.Client(api_key=Config.GEMINI_API_KEY)
    resp = client.models.generate_content(
        model=Config.SEARCH_MODEL,
        contents=query,
        config=types.GenerateContentConfig(tools=[types.Tool(google_search=types.GoogleSearch())]),
    )
    text = resp.text or ""
    sources, seen = [], set()
    try:
        chunks = resp.candidates[0].grounding_metadata.grounding_chunks or []
        for ch in chunks:
            web = getattr(ch, "web", None)
            if web and web.uri and web.uri not in seen:
                seen.add(web.uri)
                sources.append({"title": getattr(web, "title", None) or "source", "url": web.uri})
    except Exception:
        pass
    return {"query": query, "results": text, "sources": sources[:6]}


# ---------------- Emergent (inside Emergent) ----------------
async def _emergent_search(query: str) -> dict:
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    sys = ("You are a live web search tool. Use Google Search to find current, specific, real facts. "
           "List the REAL business names you find.")
    chat = (LlmChat(api_key=Config.EMERGENT_LLM_KEY, session_id="ai_core_search", system_message=sys)
            .with_model("gemini", Config.SEARCH_MODEL).with_tools([{"googleSearch": {}}]))
    resp = await chat.send_message_with_tools(UserMessage(text=query))
    sources, seen = [], set()
    try:
        for a in (resp.raw.choices[0].message.annotations or []):
            c = a.get("url_citation") if isinstance(a, dict) else getattr(a, "url_citation", None)
            url = (c.get("url") if isinstance(c, dict) else getattr(c, "url", None)) if c else None
            title = (c.get("title") if isinstance(c, dict) else getattr(c, "title", None)) if c else None
            if url and url not in seen:
                seen.add(url)
                sources.append({"title": title or "source", "url": url})
    except Exception:
        pass
    return {"query": query, "results": resp.content or "", "sources": sources[:6]}


async def gemini_web_search(query: str) -> dict:
    if Config.GEMINI_API_KEY:
        return await asyncio.to_thread(_genai_search_sync, query)
    if Config.EMERGENT_LLM_KEY:
        return await _emergent_search(query)
    return {"query": query, "results": "(no search key configured)", "sources": []}
