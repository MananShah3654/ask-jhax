"""
Storage adapters. Two kinds:

  KV stores      -> profiles, rolling summaries  (get/set json by key)
  Vector stores  -> cache + RAG chunks           (add/search by embedding)

In-memory implementations run anywhere with zero setup. Mongo implementations
persist and use brute-force cosine (works on ANY MongoDB). For scale, swap
MongoVectorStore.search for Atlas $vectorSearch or pgvector — the interface stays.
"""
import time
from typing import List, Dict, Any, Optional

from .utils import cosine, now_ts
from .embeddings import Embedder, default_embedder


# --------------------------- KV stores ---------------------------
class InMemoryKV:
    def __init__(self):
        self._d: Dict[str, dict] = {}

    async def get(self, key: str) -> Optional[dict]:
        return self._d.get(key)

    async def set(self, key: str, value: dict):
        self._d[key] = value


class MongoKV:
    def __init__(self, collection):
        self.col = collection  # a motor AsyncIOMotorCollection

    async def get(self, key: str):
        doc = await self.col.find_one({"_id": key}, {"_id": 0})
        return doc

    async def set(self, key: str, value: dict):
        await self.col.update_one({"_id": key}, {"$set": value}, upsert=True)


# --------------------------- Vector stores ---------------------------
class InMemoryVectorStore:
    def __init__(self, embedder: Embedder = None):
        self.embedder = embedder or default_embedder()
        self.items: List[dict] = []  # {vec, meta}

    async def add(self, texts: List[str], metadatas: List[dict]):
        vecs = await self.embedder.embed(texts)
        for v, m in zip(vecs, metadatas):
            self.items.append({"vec": v, "meta": m})

    async def search(self, query: str, k: int, where: dict = None):
        qv = (await self.embedder.embed([query]))[0]
        cands = self.items
        if where:
            cands = [it for it in cands if all(it["meta"].get(kk) == vv for kk, vv in where.items())]
        scored = [(cosine(qv, it["vec"]), it["meta"]) for it in cands]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, **m} for s, m in scored[:k]]


class MongoVectorStore:
    """Persistent. Brute-force cosine in Python (portable). Upgrade to $vectorSearch for scale."""

    def __init__(self, collection, embedder: Embedder = None):
        self.col = collection
        self.embedder = embedder or default_embedder()

    async def add(self, texts: List[str], metadatas: List[dict]):
        vecs = await self.embedder.embed(texts)
        docs = [{"vec": v, "meta": m, "ts": now_ts()} for v, m in zip(vecs, metadatas)]
        if docs:
            await self.col.insert_many(docs)

    async def search(self, query: str, k: int, where: dict = None):
        qv = (await self.embedder.embed([query]))[0]
        mongo_filter = {f"meta.{kk}": vv for kk, vv in (where or {}).items()}
        scored = []
        async for doc in self.col.find(mongo_filter, {"vec": 1, "meta": 1}):
            scored.append((cosine(qv, doc["vec"]), doc["meta"]))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [{"score": s, **m} for s, m in scored[:k]]
