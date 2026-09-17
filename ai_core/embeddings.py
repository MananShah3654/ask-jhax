"""
Embeddings with a pluggable interface.

- `OpenAIEmbedder`  : real embeddings (production). Uses OPENAI_API_KEY.
- `DevHashEmbedder` : deterministic char n-gram hashing — NO network. Dev only.

`default_embedder()` returns OpenAIEmbedder when an OpenAI key is present, else the
dev embedder — so cache/RAG get real quality automatically outside Emergent.
"""
import hashlib
import math
from typing import List

from .config import Config


class Embedder:
    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class DevHashEmbedder(Embedder):
    def __init__(self, dim: int = None):
        self.dim = dim or Config.EMBED_DIM_DEV

    def _vec(self, text: str):
        v = [0.0] * self.dim
        t = (text or "").lower()
        grams = [t[i:i + 3] for i in range(max(0, len(t) - 2))] or [t]
        for g in grams:
            h = int(hashlib.md5(g.encode()).hexdigest(), 16)
            v[h % self.dim] += 1.0
        norm = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / norm for x in v]

    async def embed(self, texts):
        return [self._vec(t) for t in texts]


class OpenAIEmbedder(Embedder):
    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        from openai import AsyncOpenAI
        self.model = model or Config.EMBED_MODEL
        self.client = AsyncOpenAI(api_key=api_key or Config.OPENAI_API_KEY, base_url=base_url)

    async def embed(self, texts):
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]


def default_embedder() -> Embedder:
    if Config.OPENAI_API_KEY:
        try:
            return OpenAIEmbedder()
        except Exception:
            pass
    return DevHashEmbedder()
