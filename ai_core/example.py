"""
Runnable example wiring the whole stack together (in-memory stores, no DB needed).

    python -m ai_core.example      # from /app

Swap InMemory* for Mongo* + OpenAIEmbedder in production (see README).
"""
import asyncio

from ai_core.stores import InMemoryKV, InMemoryVectorStore
from ai_core.embeddings import DevHashEmbedder
from ai_core.memory import Memory
from ai_core.rag import RAG
from ai_core.cache import SemanticCache
from ai_core.agents import Agent, WEB_SEARCH_SCHEMA
from ai_core.orchestrator import COO


# ---- a real tool implementation (stub here; wire to your search in prod) ----
async def web_search(query: str):
    return {"query": query, "results": f"(stubbed live results for: {query})"}


def build_roster():
    return {
        "competitor_intel": Agent(
            "competitor_intel",
            "Finds real nearby competitors, positioning, ratings, promos.",
            "You are a competitor-intelligence analyst. Use web_search for real names.",
            tools=[WEB_SEARCH_SCHEMA], tool_impls={"web_search": web_search},
        ),
        "marketing": Agent(
            "marketing",
            "Writes copy-paste captions, broadcasts, emails.",
            "You are a hospitality copywriter. Output ready-to-use drafts.",
        ),
        "pricing_menu": Agent(
            "pricing_menu",
            "Menu engineering, prime cost, re-pricing decisions.",
            "You are a menu economist. Be concrete and honest, not sycophantic.",
        ),
    }


async def main():
    embedder = DevHashEmbedder()
    memory = Memory(InMemoryKV())
    cache = SemanticCache(InMemoryVectorStore(embedder))
    rag = RAG(InMemoryVectorStore(embedder))
    await rag.ingest("Our bestseller is the Knowlwood burger at $13. Families love the milkshakes.",
                     namespace="restaurant:demo", source="menu")

    coo = COO(build_roster(), memory=memory, cache=cache, rag=rag, rag_namespace="restaurant:demo")

    async def on_event(e):
        t = e.get("t")
        if t == "delta":
            print(e["c"], end="", flush=True)
        elif t in ("plan", "agent_start", "agent_done", "tool", "cache_hit"):
            print(f"\n[{t}] {({k: v for k, v in e.items() if k != 't'})}")

    print("=== Q1 ===")
    await coo.handle("Who are my competitors and how do I beat them?",
                     user_id="owner1", history=[], on_event=on_event)
    print("\n\n=== Q2 (same question -> should hit cache) ===")
    await coo.handle("Who are my competitors and how do I beat them?",
                     user_id="owner1", history=[], on_event=on_event)


if __name__ == "__main__":
    asyncio.run(main())
