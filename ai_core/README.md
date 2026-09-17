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

## FastAPI SSE server (plug into any UI)

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
| `config.py` | models, thresholds, knobs (all env-overridable) |
| `llm.py` | LLM wrappers + generic **tool-calling loop** (`run_with_tools`) |
| `embeddings.py` | `OpenAIEmbedder` (prod) / `DevHashEmbedder` (no-network dev) |
| `stores.py` | KV + Vector stores: `InMemory*` and `Mongo*` (brute-force cosine, portable) |
| `memory.py` | 3-tier memory: short-term + rolling summary + durable **profile/tone** |
| `rag.py` | ingest/chunk/embed + top-k retrieve → inject only relevant chunks |
| `cache.py` | **semantic cache** with similarity threshold + TTL |
| `agents.py` | `Agent` dataclass (role prompt + tools) + reusable tool schemas |
| `orchestrator.py` | **COO**: cache → memory/RAG context → plan → parallel fan-out → synthesize |
| `rosters.py` | **360° restaurant-COO roster** — 16 specialist agents (data-defined) |
| `tools.py` | reusable tool schemas + deterministic calculators (prime cost, food cost, break-even) |
| `api.py` | **FastAPI SSE server** — `build_router()` / `create_app()` streaming endpoint |
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
- **Outside Emergent:** replace the 3 functions in `llm.py` (`_collect`, `stream_llm`, `run_with_tools`) with official OpenAI/Gemini SDK calls. Everything else is provider-agnostic.
- **Eval gating in CI:**
  ```python
  report = await run_evals("ai_core/evals/cases.jsonl", my_answer_fn)
  assert report["pass_rate"] >= 0.8
  ```
