from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import json
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone

from emergentintegrations.llm.chat import (
    LlmChat, UserMessage, TextDelta, ToolCallStart, ToolCallReady, StreamDone,
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

EMERGENT_LLM_KEY = os.environ['EMERGENT_LLM_KEY']
MODEL_PROVIDER = "openai"
MODEL_NAME = "gpt-5.6-terra"
SEARCH_PROVIDER = "gemini"
SEARCH_MODEL = "gemini-2.5-flash"

app = FastAPI()
api_router = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("jhax")


# ---------------------------------------------------------------------------
# jhax system prompt
# ---------------------------------------------------------------------------
JHAX_SYSTEM_PROMPT = """You are **jhax**, an AI business co-pilot built exclusively for restaurant owners and operators. You think and speak like a sharp restaurant-industry COO/consultant who has run hospitality groups for 15+ years — commercially savvy, data-driven, and direct. You are not a generic chatbot; you are a specialist who has clearly "done the homework" on this exact restaurant before the owner even finishes their sentence.

The backend has already gathered and prefilled the restaurant's data (name, location, menu, cuisine, positioning, competitors, review themes, local events/trends). Treat all of this as already "known" — never ask the owner to re-tell you their cuisine, location, or menu if it's in the data. If a field is missing or thin, say so plainly instead of guessing. Never invent specific facts (exact reviews, exact prices, named people) that aren't in the retrieved data.

ONGOING CONVERSATION BEHAVIOR:
- Reason before answering. Briefly work through what's being asked, what data supports it, and the business implication — then answer.
- Always end forward-looking answers with an execution angle: 1-3 concrete next steps the owner could act on this week. Specific > generic.
- Be proactive: if something relevant surfaces (a competitor event, a review pattern, a local holiday), mention it briefly.
- Cite what you're basing things on ("Based on your review themes, service speed is your #1 complaint").
- Never flatter without substance.

IDEA GENERATION & EXECUTION ENERGY:
- When asked for ideas, give 3-5 concrete, varied options — then point to the one you'd run first and why.
- Draft on demand: if the owner needs a caption, WhatsApp broadcast, event description, menu blurb, or email — write the actual copy-paste-ready draft. Put drafts inside a fenced code block so they're easy to copy.
- Move fast on low-stakes asks (a tagline, a specials-board line). Save visible step-by-step reasoning for weighty decisions (pricing, positioning, expansion, spend).
- Default to lists, tables, or short step-by-step plans for anything the owner will act on directly.
- Stay generative under constraints ("I have $200 and 3 days" → produce the best plan that fits).

THINK LIKE CLAUDE, NOT A HYPE BOT:
- Reason first, then answer. Never be sycophantic — if an idea is mediocre or risky, say so and offer the better version.
- Calibrate confidence honestly: distinguish "the data shows X," "industry patterns suggest X," and "I'm not sure, here's my best guess."
- Ask ONE sharp clarifying question only when a missing detail would change your answer; otherwise state an assumption and answer.
- Match depth to the question. Be genuinely useful over merely impressive.

TONE: Confident, warm, plain-spoken, zero corporate fluff. Use the owner's restaurant name and details often. Avoid hedging language — take a clear point of view while being honest when data is missing.

GUARDRAILS:
- Don't fabricate specific facts, reviews, numbers, or named competitors not present in the data — if unavailable, reason from general industry knowledge, clearly labeled as inference.
- Don't give legal/tax/licensing advice beyond general pointers — recommend a professional.
- Keep responses scannable: short paragraphs, **bolded** key terms, occasional bullets — but don't over-format every message into a slide deck.

FORMATTING: Use markdown. Bold key terms. Use tables and checklists (`- [ ]`) for action plans. Put copy-paste-ready drafts inside fenced code blocks."""


def restaurant_context_block(r: dict) -> str:
    """Compact JSON of everything jhax knows, injected into system message."""
    ctx = {
        "restaurant_name": r.get("name"),
        "location": r.get("location"),
        "cuisine": r.get("cuisine"),
        "price_tier": r.get("price_tier"),
        "rating": r.get("rating"),
        "positioning": r.get("positioning"),
        "vibe": r.get("vibe"),
        "menu_data": r.get("menu_data"),
        "competitors": r.get("competitors"),
        "review_themes": r.get("review_themes"),
        "local_context": r.get("local_context"),
        "data_confidence": r.get("data_confidence"),
    }
    return json.dumps(ctx, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------
class Restaurant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    location: Optional[str] = None
    cuisine: Optional[str] = None
    price_tier: Optional[str] = None
    rating: Optional[float] = None
    positioning: Optional[str] = None
    vibe: Optional[str] = None
    menu_data: List[dict] = Field(default_factory=list)
    competitors: List[dict] = Field(default_factory=list)
    review_themes: List[dict] = Field(default_factory=list)
    local_context: List[dict] = Field(default_factory=list)
    data_confidence: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ResearchRequest(BaseModel):
    name: str
    location: Optional[str] = None
    cuisine: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    restaurant_id: str
    role: str
    content: str
    is_snapshot: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------
def build_chat(system_message: str, search_ctx: str = "medium") -> LlmChat:
    chat = (
        LlmChat(api_key=EMERGENT_LLM_KEY, session_id=str(uuid.uuid4()), system_message=system_message)
        .with_model(MODEL_PROVIDER, MODEL_NAME)
    )
    return chat


def build_search_chat(system_message: str) -> LlmChat:
    """Gemini with live Google Search grounding — used only for data gathering."""
    chat = (
        LlmChat(api_key=EMERGENT_LLM_KEY, session_id=str(uuid.uuid4()), system_message=system_message)
        .with_model(SEARCH_PROVIDER, SEARCH_MODEL)
        .with_tools([{"googleSearch": {}}])
    )
    return chat


async def run_full(chat: LlmChat, text: str) -> str:
    """Non-streaming: exhaust the stream and return the full text."""
    out = []
    user_msg = UserMessage(text=text)
    while True:
        pending = []
        async for ev in chat.stream_message(user_msg):
            if isinstance(ev, TextDelta):
                out.append(ev.content)
            elif isinstance(ev, ToolCallReady):
                pending.append(ev.tool_call)
            elif isinstance(ev, StreamDone):
                break
        if not pending:
            break
        for tc in pending:
            chat.add_tool_result(tc.id, json.dumps({}))
        user_msg = None
    return "".join(out)


async def stream_deltas(chat: LlmChat, text: str):
    """Async generator yielding text chunks (no tool handling)."""
    user_msg = UserMessage(text=text)
    while True:
        pending = []
        async for ev in chat.stream_message(user_msg):
            if isinstance(ev, TextDelta):
                yield ev.content
            elif isinstance(ev, ToolCallReady):
                pending.append(ev.tool_call)
            elif isinstance(ev, StreamDone):
                break
        if not pending:
            break
        for tc in pending:
            chat.add_tool_result(tc.id, json.dumps({}))
        user_msg = None


WEB_SEARCH_TOOL = [{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": (
            "Search the live web (Google) for current, specific, real-world facts. "
            "Use this whenever the owner asks about competitors, nearby restaurants, current "
            "reviews or ratings, menu prices, local events, foot-traffic, or anything that "
            "should be up-to-date and verifiable. Prefer real named businesses and concrete "
            "numbers over generic guesses."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "A focused web search query, e.g. 'restaurants similar to Knowlwood Irvine yelp'"},
            },
            "required": ["query"],
        },
    },
}]


async def do_web_search(query: str):
    sys = (
        "You are a live web search tool. Use Google Search to find current, specific, real facts. "
        "Return a concise factual summary with concrete named businesses, numbers, ratings and "
        "sources where possible. If asked for competitors or nearby places, list the real business "
        "names you actually find."
    )
    chat = build_search_chat(sys)
    resp = await chat.send_message_with_tools(UserMessage(text=query))
    text = resp.content or ""
    return text, _extract_citations(resp)


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


async def stream_chat_events(chat: LlmChat, text: str):
    """Yields dict events: {'type':'delta',...} and {'type':'tool',...}. Dispatches web_search."""
    user_msg = UserMessage(text=text)
    while True:
        pending = []
        async for ev in chat.stream_message(user_msg):
            if isinstance(ev, TextDelta):
                yield {"type": "delta", "content": ev.content}
            elif isinstance(ev, ToolCallReady):
                pending.append(ev.tool_call)
            elif isinstance(ev, StreamDone):
                break
        if not pending:
            break
        for tc in pending:
            try:
                args = tc.arguments if isinstance(tc.arguments, dict) else json.loads(tc.arguments or "{}")
            except Exception:
                args = {}
            if tc.name == "web_search":
                q = args.get("query", "")
                yield {"type": "tool", "name": "web_search", "query": q}
                try:
                    result, sources = await do_web_search(q)
                except Exception as e:
                    logger.error(f"web_search failed: {e}")
                    result, sources = "Search unavailable right now.", []
                if sources:
                    yield {"type": "sources", "items": sources}
                chat.add_tool_result(tc.id, json.dumps({"query": q, "results": result}))
            else:
                chat.add_tool_result(tc.id, json.dumps({}))
        user_msg = None


def _extract_json(raw: str) -> dict:
    s = raw.strip()
    if "```" in s:
        # grab content between first fence
        parts = s.split("```")
        for p in parts:
            p = p.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{"):
                s = p
                break
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1:
        s = s[start:end + 1]
    return json.loads(s)


RESEARCH_PROMPT = """You are a restaurant market-research engine. Use live Google Search to research this restaurant and its local market, then return ONE JSON object (no prose, no markdown fences) with best-effort REAL data from what you find.

Restaurant name: {name}
Location: {location}
Cuisine hint: {cuisine}

Search the web for: the restaurant's actual menu & prices, its cuisine and positioning, its Google/Yelp rating and recurring review themes, 4-6 REAL nearby direct competitors (pull them from actual Google Maps / Yelp "similar to" or "people also viewed" listings for THIS restaurant, using real business names), and any real local events / seasonal moments / trends in the next 1-4 weeks that could affect it.

Return this exact JSON shape:
{{
  "cuisine": "e.g. Modern Italian",
  "price_tier": "one of: $, $$, $$$, $$$$",
  "rating": 4.3,
  "positioning": "one tight sentence on how they're positioned",
  "vibe": "3-6 words on the vibe",
  "menu_data": [
    {{"section": "Starters", "items": [{{"name": "Burrata", "price": "14"}}]}}
  ],
  "competitors": [
    {{"name": "Real competitor name", "note": "how they compare / where this restaurant loses or wins"}}
  ],
  "review_themes": [
    {{"theme": "Service speed", "sentiment": "negative", "note": "short evidence-based note"}}
  ],
  "local_context": [
    {{"title": "Event/trend name", "when": "timeframe", "impact": "why it matters to this restaurant"}}
  ],
  "data_confidence": "high | medium | low — and one line on what's thin or missing"
}}

Rules: If you cannot find real data for a field, use your best industry-informed estimate but keep data_confidence honest. Never leave arrays empty — provide at least 4 competitors (real named businesses), 3 review_themes, 2 local_context items. Only output the JSON object."""


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@api_router.get("/")
async def root():
    return {"message": "jhax.ai co-pilot online"}


@api_router.post("/restaurants/research", response_model=Restaurant)
async def research_restaurant(req: ResearchRequest):
    prompt = RESEARCH_PROMPT.format(
        name=req.name,
        location=req.location or "unknown (infer if possible)",
        cuisine=req.cuisine or "unknown",
    )
    chat = build_search_chat(
        "You research restaurants using live Google Search and return strict JSON only. Prefer real, cited facts from search results over guesses.",
    )
    raw = await run_full(chat, prompt)
    try:
        data = _extract_json(raw)
    except Exception as e:
        logger.error(f"research json parse failed: {e}\nRAW: {raw[:500]}")
        data = {}

    rating = data.get("rating")
    try:
        rating = float(rating) if rating is not None else None
    except (ValueError, TypeError):
        rating = None

    r = Restaurant(
        name=req.name,
        location=req.location or data.get("location"),
        cuisine=data.get("cuisine"),
        price_tier=data.get("price_tier"),
        rating=rating,
        positioning=data.get("positioning"),
        vibe=data.get("vibe"),
        menu_data=data.get("menu_data") or [],
        competitors=data.get("competitors") or [],
        review_themes=data.get("review_themes") or [],
        local_context=data.get("local_context") or [],
        data_confidence=data.get("data_confidence"),
    )
    await db.restaurants.insert_one(r.model_dump())
    return r


@api_router.get("/restaurants", response_model=List[Restaurant])
async def list_restaurants():
    docs = await db.restaurants.find({}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [Restaurant(**d) for d in docs]


@api_router.get("/restaurants/{rid}")
async def get_restaurant(rid: str):
    doc = await db.restaurants.find_one({"id": rid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Restaurant not found")
    msgs = await db.messages.find({"restaurant_id": rid}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return {"restaurant": doc, "messages": msgs}


@api_router.delete("/restaurants/{rid}")
async def delete_restaurant(rid: str):
    await db.restaurants.delete_one({"id": rid})
    await db.messages.delete_many({"restaurant_id": rid})
    return {"ok": True}


def sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


@api_router.post("/restaurants/{rid}/snapshot/stream")
async def snapshot_stream(rid: str):
    doc = await db.restaurants.find_one({"id": rid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Restaurant not found")

    system = JHAX_SYSTEM_PROMPT + "\n\n## RESTAURANT DATA (already known)\n" + restaurant_context_block(doc)
    trigger = f"""A restaurant has just been loaded and the owner is looking at an empty chat. Speak FIRST. Produce the **Restaurant Snapshot** now — this is your one shot to prove you already get their business. Keep it tight (6-10 lines), no filler, no "I hope this helps" energy — read like a consultant's opening line in a meeting.

Structure it as:
1. **Who they are** — cuisine, positioning, price tier, vibe (1-2 specific lines).
2. **Where they stand** — 2-3 named competitors from the data and one clear line on how {doc.get('name')} differs or is losing ground.
3. **What's happening around them now** — a nearby event/seasonal moment/trend from the data that could affect them in the next 1-4 weeks.
4. **One sharp, non-obvious opportunity** — something an owner wouldn't think to ask about.

Start by greeting the owner briefly by restaurant name, then deliver the snapshot. Use markdown with bold labels."""

    async def gen():
        acc = []
        try:
            chat = build_chat(system, search_ctx="low")
            async for chunk in stream_deltas(chat, trigger):
                acc.append(chunk)
                yield sse({"type": "delta", "content": chunk})
        except Exception as e:
            logger.error(f"snapshot stream error: {e}")
            yield sse({"type": "error", "content": "Something went wrong generating the snapshot."})
        full = "".join(acc)
        if full.strip():
            m = Message(restaurant_id=rid, role="assistant", content=full, is_snapshot=True)
            await db.messages.insert_one(m.model_dump())
        yield sse({"type": "done"})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api_router.post("/restaurants/{rid}/chat/stream")
async def chat_stream(rid: str, req: ChatRequest):
    doc = await db.restaurants.find_one({"id": rid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Restaurant not found")

    history = await db.messages.find({"restaurant_id": rid}, {"_id": 0}).sort("created_at", 1).to_list(500)

    user_m = Message(restaurant_id=rid, role="user", content=req.message)
    await db.messages.insert_one(user_m.model_dump())

    convo = ""
    for h in history[-16:]:
        who = "OWNER" if h["role"] == "user" else "JHAX"
        convo += f"\n{who}: {h['content']}\n"

    system = (
        JHAX_SYSTEM_PROMPT
        + "\n\n## LIVE WEB SEARCH (critical)\nYou have a `web_search` tool backed by live Google Search. Call it whenever the owner asks about ANY current, real-world fact — including this restaurant's OWN details: business/operating hours, address, phone, current menu prices, rating, plus competitors, nearby restaurants, reviews, and local events.\n\nHARD RULE: You must NEVER tell the owner you 'don't have' something, that it's 'not in the loaded data', or refuse to answer a factual question BEFORE you have actually called `web_search` to look it up. If the loaded restaurant data is missing a fact the owner asks about, silently call `web_search` first, then answer with what you find. Only say you couldn't find it if the search genuinely returns nothing — and even then, say you searched and came up empty. Prefer real, specific, named results with concrete numbers over generic guesses, and briefly note when you're drawing on fresh search findings."
        + "\n\n## RESTAURANT DATA (already known)\n" + restaurant_context_block(doc)
        + ("\n\n## CONVERSATION SO FAR\n" + convo if convo.strip() else "")
    )

    async def gen():
        acc = []
        try:
            chat = build_chat(system).with_tools(WEB_SEARCH_TOOL, tool_choice="auto").with_params(reasoning_effort="none")
            async for evt in stream_chat_events(chat, req.message):
                if evt["type"] == "delta":
                    acc.append(evt["content"])
                    yield sse({"type": "delta", "content": evt["content"]})
                elif evt["type"] == "tool":
                    yield sse({"type": "tool", "name": evt.get("name"), "query": evt.get("query")})
                elif evt["type"] == "sources":
                    yield sse({"type": "sources", "items": evt.get("items", [])})
        except Exception as e:
            logger.error(f"chat stream error: {e}")
            yield sse({"type": "error", "content": "Something went wrong. Try again."})
        full = "".join(acc)
        if full.strip():
            m = Message(restaurant_id=rid, role="assistant", content=full)
            await db.messages.insert_one(m.model_dump())
        yield sse({"type": "done"})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
