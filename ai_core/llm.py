"""
LLM wrappers around emergentintegrations (Emergent Universal Key).

To run OUTSIDE Emergent, replace the bodies of `_collect` / `stream_llm` /
`run_with_tools` with the official OpenAI/Gemini SDK calls — the signatures and
the orchestration logic elsewhere do not change.
"""
import json

from emergentintegrations.llm.chat import (
    LlmChat, UserMessage, TextDelta, ToolCallReady, StreamDone,
)

from .config import Config


def _chat(model, system, session="aicore", tools=None):
    c = LlmChat(api_key=Config.KEY, session_id=session, system_message=system).with_model(*model)
    if tools:
        # gpt-5.6-* needs reasoning_effort='none' to use function tools on chat completions
        c = c.with_tools(tools, tool_choice="auto").with_params(reasoning_effort="none")
    return c


async def _collect(chat, text) -> str:
    out = []
    async for ev in chat.stream_message(UserMessage(text=text)):
        if isinstance(ev, TextDelta):
            out.append(ev.content)
        elif isinstance(ev, StreamDone):
            break
    return "".join(out)


async def cheap_llm(system: str, text: str) -> str:
    return await _collect(_chat(Config.CHEAP_MODEL, system), text)


async def strong_llm(system: str, text: str) -> str:
    return await _collect(_chat(Config.STRONG_MODEL, system), text)


async def stream_llm(system: str, text: str, on_event, model=None):
    """Stream a strong-model answer, emitting {'t':'delta','c':...} events. Returns full text."""
    chat = _chat(model or Config.STRONG_MODEL, system)
    acc = []
    async for ev in chat.stream_message(UserMessage(text=text)):
        if isinstance(ev, TextDelta):
            acc.append(ev.content)
            if on_event:
                await on_event({"t": "delta", "c": ev.content})
        elif isinstance(ev, StreamDone):
            break
    return "".join(acc)


async def run_with_tools(chat, task: str, impls: dict, on_event=None, max_steps=None) -> str:
    """Generic streaming tool-calling loop. `impls` maps tool name -> async fn(**args)."""
    max_steps = max_steps or Config.MAX_TOOL_STEPS
    acc, user_msg, steps = [], UserMessage(text=task), 0
    while True:
        pending = []
        async for ev in chat.stream_message(user_msg):
            if isinstance(ev, TextDelta):
                acc.append(ev.content)
                if on_event:
                    await on_event({"t": "delta", "c": ev.content})
            elif isinstance(ev, ToolCallReady):
                pending.append(ev.tool_call)
            elif isinstance(ev, StreamDone):
                break
        if not pending or steps >= max_steps:
            break
        steps += 1
        for tc in pending:
            try:
                args = tc.arguments if isinstance(tc.arguments, dict) else json.loads(tc.arguments or "{}")
            except Exception:
                args = {}
            if on_event:
                await on_event({"t": "tool", "name": tc.name, "args": args})
            fn = impls.get(tc.name)
            try:
                result = await fn(**args) if fn else {"error": f"no tool {tc.name}"}
            except Exception as e:
                result = {"error": str(e)}
            chat.add_tool_result(tc.id, json.dumps(result, default=str))
        user_msg = None
    return "".join(acc)


def build_agent_chat(model, system, tools=None, session="agent"):
    return _chat(model, system, session=session, tools=tools)
