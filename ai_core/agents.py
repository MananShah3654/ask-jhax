"""
Agent = one brain with a role prompt + its own tools. Define specialists as data;
adding a capability = adding one Agent to the roster.
"""
from dataclasses import dataclass, field
from typing import Callable, Dict, List

from .config import Config
from .llm import build_agent_chat, run_with_tools


@dataclass
class Agent:
    name: str
    description: str                       # used by the COO router to decide when to pick it
    system_prompt: str
    model: tuple = Config.STRONG_MODEL
    tools: List[dict] = field(default_factory=list)        # OpenAI-style tool schemas
    tool_impls: Dict[str, Callable] = field(default_factory=dict)

    async def run(self, task: str, ctx: str = "", on_event=None) -> str:
        system = self.system_prompt + (f"\n\n{ctx}" if ctx else "")
        chat = build_agent_chat(self.model, system, tools=self.tools or None, session=self.name)
        return await run_with_tools(chat, task, self.tool_impls, on_event=on_event)


# ---- example tool schema you can reuse across agents ----
WEB_SEARCH_SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the live web for current, specific, real facts. Use for competitors, hours, prices, reviews, events.",
        "parameters": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
}
