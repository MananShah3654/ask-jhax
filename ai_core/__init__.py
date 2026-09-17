"""
ai_core — a portable multi-agent + memory + RAG + cache + eval toolkit.

Drop this folder into any Python app. It runs on the Emergent Universal Key
(via `emergentintegrations`) out of the box, and is easy to swap to the raw
OpenAI/Gemini SDKs for use outside Emergent (see README).

Layers (cheapest first):
    cache  ->  memory  ->  rag  ->  agents/orchestrator (LLM)
"""
from .config import Config
from .agents import Agent
from .orchestrator import COO
from .memory import Memory
from .rag import RAG
from .cache import SemanticCache

__all__ = ["Config", "Agent", "COO", "Memory", "RAG", "SemanticCache"]
