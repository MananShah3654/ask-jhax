import os


class Config:
    """Central config. Override via env vars in your other app."""

    # Auth: Emergent Universal Key OR a raw provider key
    KEY = os.environ.get("EMERGENT_LLM_KEY") or os.environ.get("OPENAI_API_KEY", "")

    # (provider, model) tuples — cheap model for routing/summaries/judge,
    # strong model for owner-facing answers, search model for grounded lookups.
    STRONG_MODEL = ("openai", "gpt-5.6-terra")
    CHEAP_MODEL = ("openai", "gpt-5.4-mini")
    SEARCH_MODEL = ("gemini", "gemini-2.5-flash")

    # Embeddings
    EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
    EMBED_DIM_DEV = int(os.environ.get("EMBED_DIM_DEV", "384"))  # dev hash embedder dim

    # Thresholds / knobs
    CACHE_THRESHOLD = float(os.environ.get("CACHE_THRESHOLD", "0.92"))
    CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", str(60 * 60 * 24)))
    RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "4"))
    CHUNK_TOKENS = int(os.environ.get("CHUNK_TOKENS", "500"))
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "75"))
    MAX_TOOL_STEPS = int(os.environ.get("MAX_TOOL_STEPS", "6"))
    AGENT_TIMEOUT_S = int(os.environ.get("AGENT_TIMEOUT_S", "60"))
    MAX_PARALLEL_AGENTS = int(os.environ.get("MAX_PARALLEL_AGENTS", "4"))
    HISTORY_VERBATIM_TURNS = int(os.environ.get("HISTORY_VERBATIM_TURNS", "8"))
