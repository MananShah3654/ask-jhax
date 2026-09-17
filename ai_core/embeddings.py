"""
Embeddings with a pluggable interface.

- `OpenAIEmbedder`  : real embeddings (use in production; needs OPENAI_API_KEY
                      or an OpenAI-compatible endpoint).
- `DevHashEmbedder` : deterministic char n-gram hashing — NO network. Good enough
                      to make cache/RAG demos run locally; replace for real quality.
"""
import hashlib
import math
from typing import List

from .config import Config


class Embedder:
    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class DevHashEmbedder(Embedder):
    """Dev-only. Hashes char 3-grams into a fixed-dim L2-normalized vector."""

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
    """Real embeddings via the openai SDK. `pip install openai`."""

    def __init__(self, model: str = None, api_key: str = None, base_url: str = None):
        from openai import AsyncOpenAI
        self.model = model or Config.EMBED_MODEL
        self.client = AsyncOpenAI(api_key=api_key or Config.KEY, base_url=base_url)

    async def embed(self, texts):
        resp = await self.client.embeddings.create(model=self.model, input=texts)
        return [d.embedding for d in resp.data]


def default_embedder() -> Embedder:
    """Try real embeddings; fall back to the dev embedder so nothing crashes."""
    try:
        return OpenAIEmbedder()
    except Exception:
        return DevHashEmbedder()
