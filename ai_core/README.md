# ai_core — portable multi-agent + memory + RAG + cache + eval toolkit

Drop this folder into any Python backend. It gives you an **AI COO orchestrator**
that routes each request to **specialist agents**, backed by **3-tier memory**,
**RAG**, a **semantic cache**, and an **eval harness** — all designed to *reduce
token spend* by checking the cheapest layer first.

```
request → cache (0 tokens if hit) → memory (tiny profile+summary) → rag (top-k only) → agents/LLM
```

## Quick start (no DB, runs anywhere)

```bash
export EMERGENT_LLM_KEY=sk-emergent-...   # or OPENAI_API_KEY
cd /app && python -m ai_core.example
```

`example.py` wires everything with in-memory stores. Q2 repeats Q1 → **cache hit, 0 generation tokens**.

## Wire it into your app (production)

```python
from ai_core import COO, Memory, RAG, SemanticCache
from ai_core.stores import MongoKV, MongoVectorStore
from ai_core.embeddings import OpenAIEmbedder
from ai_core.agents import Agent, WEB_SEARCH_SCHEMA

emb   = OpenAIEmbedder()                       # real embeddings
memory = Memory(MongoKV(db.memory))
cache  = SemanticCache(MongoVectorStore(db.cache, emb))
rag    = RAG(MongoVectorStore(db.knowledge, emb))

roster = {
  "competitor_intel": Agent("competitor_intel", "…", "system prompt…",
                            tools=[WEB_SEARCH_SCHEMA], tool_impls={"web_search": my_search}),
  "marketing":        Agent("marketing", "…", "system prompt…"),
  # add a specialist = add one entry
}

coo = COO(roster, memory=memory, cache=cache, rag=rag, rag_namespace=f"restaurant:{rid}")

# stream to your UI (SSE/WebSocket)
async def on_event(e):  # {t:'plan'|'agent_start'|'agent_done'|'tool'|'delta'|'cache_hit'|'done'}
    await push_to_client(e)

answer = await coo.handle(user_msg, user_id=uid, history=history, on_event=on_event)
```

## 🔑 LLM keys & backends (read first)

`ai_core` runs in **two modes**, auto-detected (override with `AI_CORE_BACKEND=openai|emergent`):

| Mode | When | Keys | Models used |
|------|------|------|-------------|
| **`openai`** (default outside Emergent) | you host the app yourself | `OPENAI_API_KEY` (+ `GEMINI_API_KEY` for live search/vision) | real OpenAI + Gemini model names |
| **`emergent`** | app runs on Emergent | `EMERGENT_LLM_KEY` | Emergent aliases (`gpt-5.6-terra`…) |

**Which key does what** (each part of `ai_core`):

| Component | Model (env var) | Key |
|---|---|---|
| COO reasoning / synthesis | `STRONG_MODEL` (default `gpt-4o`) | `OPENAI_API_KEY` |
| Router / summaries / eval judge | `CHEAP_MODEL` (default `gpt-4o-mini`) | `OPENAI_API_KEY` |
| Live web search | `SEARCH_MODEL` (default `gemini-2.5-flash`) | `GEMINI_API_KEY` |
| Image / scanned-file ingest | `VISION_MODEL` (default `gpt-4o-mini`) | `OPENAI_API_KEY` |
| Embeddings (cache + RAG) | `EMBED_MODEL` (`text-embedding-3-small`) | `OPENAI_API_KEY` |

> ⚠️ "GPT 5.6" is an **Emergent alias** — it does not exist on the raw OpenAI API.
> Outside Emergent, set `STRONG_MODEL`/`CHEAP_MODEL` to real OpenAI names (e.g. `gpt-4o`, `gpt-4.1`, `gpt-4o-mini`) or set an agent's `model="claude-..."` if you add an Anthropic path.

**Recommendation:**
- **Outside Emergent (your case):** `OPENAI_API_KEY` (reasoning + embeddings + vision) **+** `GEMINI_API_KEY` (live search). One OpenAI key covers most of it; Gemini is only for grounded search/vision.
- **On Emergent:** just `EMERGENT_LLM_KEY` for reasoning + search + vision, **plus** one `OPENAI_API_KEY` for embeddings (the Universal Key does not serve embeddings).

**Memory / cache / RAG persist to your DB automatically** — set `MONGO_URL` (+ `DB_NAME`)
and the API stores everything in Mongo collections `coo_memory`, `coo_cache`,
`coo_knowledge`, `coo_messages`. No `MONGO_URL` → falls back to in-memory (dev only).

---

## Integration Procedure (follow in order)

**Step 1 — Copy the package**
Place the whole `ai_core/` folder inside your backend, next to your server entrypoint:
```
your-app/backend/
├── server.py
└── ai_core/        ← paste here
```

**Step 2 — Install dependencies**
```bash
pip install fastapi uvicorn pydantic motor emergentintegrations
# optional, for real embeddings:
pip install openai
```

**Step 3 — Set environment variables** (outside Emergent)
```bash
export OPENAI_API_KEY=sk-...            # reasoning + embeddings + vision
export GEMINI_API_KEY=...               # live web search + image ingest (Google AI Studio)
export MONGO_URL=mongodb://localhost:27017   # memory/cache/RAG persist here
export DB_NAME=ai_core
# optional model overrides (real OpenAI names!):
export STRONG_MODEL=gpt-4o
export CHEAP_MODEL=gpt-4o-mini
# optional knobs: CACHE_THRESHOLD, RAG_TOP_K, MAX_PARALLEL_AGENTS ...
```
Running ON Emergent instead? Just `export EMERGENT_LLM_KEY=sk-emergent-...`
(+ an `OPENAI_API_KEY` for embeddings).

**Step 4 — Live web search is ON by default**
The roster and API use **Gemini + Google Search** out of the box (same as jhax) — no
setup needed. To use a different provider, pass your own:
```python
async def my_search(query: str) -> dict:
    return {"query": query, "results": "...", "sources": [...]}
roster = restaurant_coo_roster(web_search=my_search)
```

**Step 5 — Wire the COO** (memory/cache/RAG persist to Mongo automatically)
```python
from ai_core import COO, restaurant_coo_roster
from ai_core.api import _wire   # or wire manually (below)

# Easiest: the API auto-wires Mongo from MONGO_URL. To build manually:
from ai_core import Memory, RAG, SemanticCache
from ai_core.stores import MongoKV, MongoVectorStore
from ai_core.embeddings import default_embedder   # -> OpenAIEmbedder when OPENAI_API_KEY set
from motor.motor_asyncio import AsyncIOMotorClient

db  = AsyncIOMotorClient("mongodb://localhost:27017")["ai_core"]
emb = default_embedder()
coo = COO(restaurant_coo_roster(),                    # live Gemini search is ON by default
          memory=Memory(MongoKV(db.coo_memory)),      # <-- memory saved in DB
          cache=SemanticCache(MongoVectorStore(db.coo_cache, emb)),
          rag=RAG(MongoVectorStore(db.coo_knowledge, emb)),
          rag_namespace=f"restaurant:{restaurant_id}")
```

**Step 6 — Expose the streaming endpoint** (mount on your FastAPI app)
```python
from ai_core.api import build_router
app.include_router(
    build_router(web_search=my_search, mongo_db=db, rag_namespace=f"restaurant:{rid}"),
    prefix="/api")
```
…or run standalone: `uvicorn ai_core.api:app --host 0.0.0.0 --port 8080`.

**Step 7 — (Optional) Seed RAG with the restaurant's real docs & files**
Plain text:
```python
rag = RAG(MongoVectorStore(db.coo_knowledge, emb))
await rag.ingest(menu_text, namespace=f"restaurant:{rid}", source="menu")
```
Files (PDF / CSV / XLSX / images) — upload via the endpoint, or in code:
```python
from ai_core.ingest import ingest_file
with open("pnl.pdf","rb") as f:
    await ingest_file(rag, f.read(), "pnl.pdf", namespace=f"restaurant:{rid}", source="pnl")
```
Upload endpoint: `POST /api/coo/ingest` (multipart) with fields `file`, `namespace`, `source`.
Supported: `.txt .md .json .html .csv .tsv .pdf .xlsx` and images (`.png .jpg .jpeg .webp`)
— images/PDF-scans are transcribed with Gemini vision. Ingested files are then
automatically retrieved by the agents when relevant.

**Step 8 — Call it from the frontend** (SSE)
`POST /api/coo/chat/stream` with `{message, user_id, session_id}` and read the stream
(vanilla-JS client below). Show `agent_start` events as "🔎 <agent> working…".

**Step 9 — (Optional) Add eval gating in CI**
```python
from ai_core.evals.runner import run_evals
report = await run_evals("ai_core/evals/cases.jsonl", my_answer_fn)
assert report["pass_rate"] >= 0.8
```

**Step 10 — Extend for true 360°**
Add specialists or tools without touching core logic:
```python
from ai_core.agents import Agent
roster = restaurant_coo_roster(web_search=my_search, extra={
    "sommelier": Agent("sommelier", "Wine/bev pairing & margin", "<system prompt>")
})
```

---



`ai_core/api.py` gives you a ready streaming endpoint.

**Mount on your existing app:**
```python
from ai_core.api import build_router
app.include_router(build_router(web_search=my_search, mongo_db=db,
                                rag_namespace=f"restaurant:{rid}"), prefix="/api")
```

**Or run standalone:**
```python
from ai_core.api import create_app
app = create_app(web_search=my_search)      # uvicorn ai_core.api:app --port 8080
```

**Endpoints**
- `GET  /api/coo/health` → `{status, agents:[...]}`
- `POST /api/coo/chat/stream` body `{message, user_id, session_id}` → SSE stream

**SSE events:** `{t:'cache_hit'}` · `{t:'plan',agents}` · `{t:'agent_start',name}` · `{t:'tool',name,args}` · `{t:'agent_done',name}` · `{t:'delta',c}` · `{t:'error',message}` · `{t:'done'}`

**Browser client (vanilla JS):**
```js
const resp = await fetch(`${API}/api/coo/chat/stream`, {
  method: "POST", headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ message, user_id: "u1", session_id: "s1" }),
});
const reader = resp.body.getReader(); const dec = new TextDecoder(); let buf = "";
while (true) {
  const { done, value } = await reader.read(); if (done) break;
  buf += dec.decode(value, { stream: true });
  const parts = buf.split("\n\n"); buf = parts.pop();
  for (const p of parts) {
    if (!p.startsWith("data:")) continue;
    const e = JSON.parse(p.slice(5).trim());
    if (e.t === "delta") appendToBubble(e.c);
    else if (e.t === "agent_start") showStatus(`🔎 ${e.name} working…`);
    else if (e.t === "plan") console.log("agents:", e.agents);
    else if (e.t === "done") finish();
  }
}
```



| File | What |
|------|------|
| `config.py` | models, thresholds, knobs, **backend auto-detect** (env-overridable) |
| `backends.py` | **OpenAIBackend** (official SDK) + **EmergentBackend** (Universal Key) |
| `llm.py` | thin backend-agnostic helpers (`cheap_llm`, `strong_llm`, `stream_llm`) |
| `embeddings.py` | `OpenAIEmbedder` (prod) / `DevHashEmbedder` (no-network dev) |
| `stores.py` | KV + Vector stores: `InMemory*` and `Mongo*` (brute-force cosine, portable) |
| `memory.py` | 3-tier memory: short-term + rolling summary + durable **profile/tone** |
| `rag.py` | ingest/chunk/embed + top-k retrieve → inject only relevant chunks |
| `cache.py` | **semantic cache** with similarity threshold + TTL |
| `agents.py` | `Agent` dataclass (role prompt + tools) + reusable tool schemas |
| `orchestrator.py` | **COO**: cache → memory/RAG context → plan → parallel fan-out → synthesize |
| `rosters.py` | **360° restaurant-COO roster** — 16 specialist agents (data-defined) |
| `tools.py` | reusable tool schemas + deterministic calculators (prime cost, food cost, break-even) |
| `api.py` | **FastAPI SSE server** — `build_router()` / `create_app()`; chat + file-upload endpoints |
| `search.py` | **default live web search** (Gemini + Google Search, like jhax) |
| `ingest.py` | **file → text → RAG** (PDF, CSV, XLSX, images; Gemini OCR fallback for scanned PDFs) |
| `code_exec.py` | **sandboxed Python tool** for exact math & spreadsheet analysis (Code-Interpreter-style) |
| `evals/runner.py` | hard-rule checks + **LLM-as-judge**; returns `pass_rate` for CI gating |
| `evals/cases.jsonl` | sample eval cases |
| `example.py` | runnable end-to-end demo |

## Token-saving design (why each layer exists)

1. **Semantic cache** — return prior answers to similar questions → 0 generation tokens.
2. **Memory** — inject a ~100-token profile + 1-paragraph summary instead of the full history; the model learns tone/needs **once** and reuses it.
3. **RAG** — retrieve 3-5 relevant chunks instead of stuffing entire menus/reports.
4. **Model routing** — cheap model (`gpt-5.4-mini`) for routing/summaries/judge; strong model (`gpt-5.6-terra`) only for the final answer; embeddings on `text-embedding-3-small`.
5. **Single-agent shortcut** — if only one specialist runs, skip the synthesis merge.

## Production notes / upgrades

- **Vector search at scale:** `MongoVectorStore.search` uses brute-force cosine (fine for thousands of rows). Swap for **Atlas `$vectorSearch`**, **pgvector**, or **Qdrant** — keep the same `add/search` interface.
- **Observability:** log per `handle()` run: chosen agents, tokens, latency, cache-hit, 👍/👎. Add a `run_id` to every event for tracing/replay.
- **Guards:** already included — per-agent `timeout`, `MAX_TOOL_STEPS` loop cap, `MAX_PARALLEL_AGENTS` semaphore.
- **Outside Emergent:** set `OPENAI_API_KEY` (+ `GEMINI_API_KEY`) and it uses the official SDKs automatically via `backends.py` — no code changes. Force with `AI_CORE_BACKEND=openai`.
- **Eval gating in CI:**
  ```python
  report = await run_evals("ai_core/evals/cases.jsonl", my_answer_fn)
  assert report["pass_rate"] >= 0.8
  ```
