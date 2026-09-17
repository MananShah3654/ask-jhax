"""
Semantic cache — the biggest token saver. Before any expensive LLM call, check
if a semantically-similar question was already answered (per user). TTL lets
live-data answers expire while evergreen ones persist.
"""
from .config import Config
from .utils import now_ts


class SemanticCache:
    def __init__(self, vector_store, threshold: float = None, ttl: int = None):
        self.vs = vector_store
        self.threshold = threshold if threshold is not None else Config.CACHE_THRESHOLD
        self.ttl = ttl if ttl is not None else Config.CACHE_TTL_SECONDS

    async def get(self, query: str, user_id: str = "global"):
        hits = await self.vs.search(query, k=1, where={"user_id": user_id})
        if not hits:
            return None
        h = hits[0]
        if h.get("score", 0) < self.threshold:
            return None
        if self.ttl and (now_ts() - h.get("cached_at", 0)) > self.ttl:
            return None
        return h.get("answer")

    async def put(self, query: str, answer: str, user_id: str = "global", ttl: int = None):
        meta = {
            "text": query, "answer": answer, "user_id": user_id,
            "cached_at": now_ts(), "ttl": ttl if ttl is not None else self.ttl,
        }
        await self.vs.add([query], [meta])
