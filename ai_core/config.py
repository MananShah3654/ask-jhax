import os


class Config:
    """
    Central config. Works OUTSIDE Emergent with your own provider keys (default),
    or inside Emergent with the Universal Key as a fallback.

    Backend auto-detect (override with AI_CORE_BACKEND=openai|emergent):
      - OPENAI_API_KEY present  -> "openai"  (official OpenAI/Gemini SDKs)
      - else EMERGENT_LLM_KEY    -> "emergent"
    """
    # ---- provider keys (outside Emergent) ----
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    # ---- Emergent Universal Key (inside Emergent) ----
    EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY", "")

    FORCE_BACKEND = os.environ.get("AI_CORE_BACKEND", "")

    # ---- database (memory / cache / rag persist here) ----
    MONGO_URL = os.environ.get("MONGO_URL", "")
    DB_NAME = os.environ.get("DB_NAME", "ai_core")

    # ---- embeddings ----
    EMBED_MODEL = os.environ.get("EMBED_MODEL", "text-embedding-3-small")
    EMBED_DIM_DEV = int(os.environ.get("EMBED_DIM_DEV", "384"))

    # ---- search / vision model (Gemini) ----
    SEARCH_MODEL = os.environ.get("SEARCH_MODEL", "gemini-2.5-flash")
    VISION_MODEL = os.environ.get("VISION_MODEL", "")  # blank -> backend default

    # ---- knobs ----
    CACHE_THRESHOLD = float(os.environ.get("CACHE_THRESHOLD", "0.92"))
    CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", str(60 * 60 * 24)))
    RAG_TOP_K = int(os.environ.get("RAG_TOP_K", "4"))
    CHUNK_TOKENS = int(os.environ.get("CHUNK_TOKENS", "500"))
    CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "75"))
    MAX_TOOL_STEPS = int(os.environ.get("MAX_TOOL_STEPS", "6"))
    AGENT_TIMEOUT_S = int(os.environ.get("AGENT_TIMEOUT_S", "60"))
    MAX_PARALLEL_AGENTS = int(os.environ.get("MAX_PARALLEL_AGENTS", "4"))
    HISTORY_VERBATIM_TURNS = int(os.environ.get("HISTORY_VERBATIM_TURNS", "8"))

    @classmethod
    def backend(cls) -> str:
        if cls.FORCE_BACKEND:
            return cls.FORCE_BACKEND
        if cls.OPENAI_API_KEY:
            return "openai"
        if cls.EMERGENT_LLM_KEY:
            return "emergent"
        return "openai"

    @classmethod
    def strong(cls) -> str:
        """Owner-facing answer model."""
        return os.environ.get("STRONG_MODEL") or (
            "gpt-4o" if cls.backend() == "openai" else "gpt-5.6-terra")

    @classmethod
    def cheap(cls) -> str:
        """Routing / summaries / judge model."""
        return os.environ.get("CHEAP_MODEL") or (
            "gpt-4o-mini" if cls.backend() == "openai" else "gpt-5.4-mini")

    @classmethod
    def vision(cls) -> str:
        if cls.VISION_MODEL:
            return cls.VISION_MODEL
        return "gpt-4o-mini" if cls.backend() == "openai" else "gemini-2.5-flash"
