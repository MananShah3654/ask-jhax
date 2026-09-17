"""
3-tier memory:
  1. short-term  : last N turns, verbatim
  2. rolling     : older turns compressed into 1 paragraph
  3. profile     : durable facts + goals + constraints + TONE preferences

The point: STOP re-sending the whole history every call. Send the last few
turns + a tiny profile + a short summary. `update()` runs on a CHEAP model.
"""
import json

from .config import Config
from .llm import cheap_llm
from .utils import extract_json

_PROFILE_PROMPT = """You maintain a durable profile of a user from a conversation.
Merge NEW durable information into the existing profile. Keep it small and factual.
Capture especially the user's TONE/format preferences (e.g. blunt, wants bullets, hates fluff).
Return ONLY JSON with this shape:
{"tone_preference":"", "goals":[], "constraints":[], "facts":[], "dislikes":[]}"""

_SUMMARY_PROMPT = """Compress the older conversation below into ONE tight paragraph
that preserves decisions, context and open threads. No preamble."""


class Memory:
    def __init__(self, kv):
        self.kv = kv  # a KV store (InMemoryKV / MongoKV)

    def _pkey(self, uid): return f"profile:{uid}"
    def _skey(self, uid): return f"summary:{uid}"

    async def get_profile(self, uid) -> dict:
        return (await self.kv.get(self._pkey(uid))) or {
            "tone_preference": "", "goals": [], "constraints": [], "facts": [], "dislikes": []
        }

    async def get_summary(self, uid) -> str:
        d = await self.kv.get(self._skey(uid))
        return (d or {}).get("text", "")

    async def context_block(self, uid, history) -> str:
        """Tiny context to inject into any agent's system prompt."""
        profile = await self.get_profile(uid)
        summary = await self.get_summary(uid)
        recent = history[-Config.HISTORY_VERBATIM_TURNS:]
        convo = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
        parts = [f"## USER PROFILE\n{json.dumps(profile, ensure_ascii=False)}"]
        if summary:
            parts.append(f"## EARLIER SUMMARY\n{summary}")
        if convo:
            parts.append(f"## RECENT TURNS\n{convo}")
        return "\n\n".join(parts)

    async def update(self, uid, history):
        """Call after each turn (fire-and-forget). Cheap model only."""
        recent = history[-4:]
        turns = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in recent)
        profile = await self.get_profile(uid)
        merged = await cheap_llm(_PROFILE_PROMPT, f"EXISTING:\n{json.dumps(profile)}\n\nNEW TURNS:\n{turns}")
        new_profile = extract_json(merged)
        if new_profile:
            await self.kv.set(self._pkey(uid), new_profile)

        # roll up summary once history grows past the verbatim window
        if len(history) > Config.HISTORY_VERBATIM_TURNS + 4:
            older = history[:-Config.HISTORY_VERBATIM_TURNS]
            older_txt = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in older)
            summary = await cheap_llm(_SUMMARY_PROMPT, older_txt)
            await self.kv.set(self._skey(uid), {"text": summary.strip()})
