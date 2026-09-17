import json
import math
from datetime import datetime, timezone


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def extract_json(raw: str):
    """Best-effort parse of a JSON object out of an LLM response."""
    s = (raw or "").strip()
    if "```" in s:
        for part in s.split("```"):
            p = part.strip()
            if p.startswith("json"):
                p = p[4:].strip()
            if p.startswith("{") or p.startswith("["):
                s = p
                break
    start = s.find("{")
    end = s.rfind("}")
    if start != -1 and end != -1 and end > start:
        s = s[start:end + 1]
    try:
        return json.loads(s)
    except Exception:
        return {}


def cosine(a, b) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def chunk_text(text: str, chunk_tokens: int, overlap: int):
    """Naive whitespace chunker (~4 chars/token). Swap for tiktoken in prod."""
    words = (text or "").split()
    approx_words = max(1, int(chunk_tokens * 0.75))
    step = max(1, approx_words - int(overlap * 0.75))
    out = []
    for i in range(0, len(words), step):
        piece = " ".join(words[i:i + approx_words]).strip()
        if piece:
            out.append(piece)
        if i + approx_words >= len(words):
            break
    return out
