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

## Files

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
