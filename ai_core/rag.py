"""
RAG: ingest documents -> chunk -> embed -> store; retrieve top-k relevant chunks
to inject into a prompt instead of stuffing whole documents (saves tokens).
"""
from typing import List

from .config import Config
from .utils import chunk_text


class RAG:
    def __init__(self, vector_store):
        self.vs = vector_store  # InMemoryVectorStore / MongoVectorStore

    async def ingest(self, text: str, *, namespace: str, source: str = "", extra: dict = None):
        chunks = chunk_text(text, Config.CHUNK_TOKENS, Config.CHUNK_OVERLAP)
        metas = [
            {"text": c, "namespace": namespace, "source": source, "chunk": i, **(extra or {})}
            for i, c in enumerate(chunks)
        ]
        await self.vs.add(chunks, metas)
        return len(chunks)

    async def retrieve(self, query: str, *, namespace: str, k: int = None) -> List[dict]:
        return await self.vs.search(query, k or Config.RAG_TOP_K, where={"namespace": namespace})

    async def context(self, query: str, *, namespace: str, k: int = None) -> str:
        hits = await self.retrieve(query, namespace=namespace, k=k)
        if not hits:
            return ""
        blocks = [f"[{h.get('source','doc')}#{h.get('chunk',0)}] {h.get('text','')}" for h in hits]
        return "## RETRIEVED KNOWLEDGE\n" + "\n\n".join(blocks)
