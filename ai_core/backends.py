"""
Pluggable LLM backends. Same async interface, two implementations:

  OpenAIBackend   - official OpenAI SDK (chat + tools + streaming + embeddings + vision).
                    Used OUTSIDE Emergent with your OPENAI_API_KEY.
  EmergentBackend - emergentintegrations (Universal Key). Used inside Emergent.

`get_backend()` picks based on Config.backend(). Gemini live search lives in search.py.
"""
import base64
import json

from .config import Config


def _provider_of(model: str) -> str:
    if model.startswith("gemini"):
        return "gemini"
    if model.startswith("claude"):
        return "anthropic"
    return "openai"


# ------------------------------------------------------------------ OpenAI
class OpenAIBackend:
    def __init__(self):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY)

    async def chat(self, model, messages, tools=None, impls=None, on_event=None, max_steps=None):
        max_steps = max_steps or Config.MAX_TOOL_STEPS
        msgs = list(messages)
        steps = 0
        while True:
            kwargs = {"model": model, "messages": msgs, "stream": True}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"
            stream = await self.client.chat.completions.create(**kwargs)
            content, calls = [], {}
            async for chunk in stream:
                if not chunk.choices:
                    continue
                d = chunk.choices[0].delta
                if getattr(d, "content", None):
                    content.append(d.content)
                    if on_event:
                        await on_event({"t": "delta", "c": d.content})
                for tc in (getattr(d, "tool_calls", None) or []):
                    slot = calls.setdefault(tc.index, {"id": "", "name": "", "args": ""})
                    if tc.id:
                        slot["id"] = tc.id
                    if tc.function and tc.function.name:
                        slot["name"] = tc.function.name
                    if tc.function and tc.function.arguments:
                        slot["args"] += tc.function.arguments
            text = "".join(content)
            if not calls or steps >= max_steps:
                return text
            steps += 1
            msgs.append({"role": "assistant", "content": text or None,
                         "tool_calls": [{"id": s["id"], "type": "function",
                                         "function": {"name": s["name"], "arguments": s["args"] or "{}"}}
                                        for s in calls.values()]})
            for s in calls.values():
                try:
                    args = json.loads(s["args"] or "{}")
                except Exception:
                    args = {}
                if on_event:
                    await on_event({"t": "tool", "name": s["name"], "args": args})
                fn = (impls or {}).get(s["name"])
                try:
                    result = await fn(**args) if fn else {"error": f"no tool {s['name']}"}
                except Exception as e:
                    result = {"error": str(e)}
                msgs.append({"role": "tool", "tool_call_id": s["id"],
                             "content": json.dumps(result, default=str)})

    async def embed(self, texts, model=None):
        resp = await self.client.embeddings.create(model=model or Config.EMBED_MODEL, input=texts)
        return [d.embedding for d in resp.data]

    async def vision(self, data: bytes, filename: str, prompt: str):
        b64 = base64.b64encode(data).decode()
        mime = "image/jpeg" if filename.lower().endswith((".jpg", ".jpeg")) else "image/png"
        resp = await self.client.chat.completions.create(
            model=Config.vision(),
            messages=[{"role": "user", "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
            ]}])
        return resp.choices[0].message.content or ""


# ------------------------------------------------------------------ Emergent
class EmergentBackend:
    def _chat_obj(self, model, system, tools=None):
        from emergentintegrations.llm.chat import LlmChat
        c = LlmChat(api_key=Config.EMERGENT_LLM_KEY, session_id="ai_core",
                    system_message=system).with_model(_provider_of(model), model)
        if tools:
            c = c.with_tools(tools, tool_choice="auto")
            if model.startswith("gpt-5"):
                c = c.with_params(reasoning_effort="none")
        return c

    async def chat(self, model, messages, tools=None, impls=None, on_event=None, max_steps=None):
        from emergentintegrations.llm.chat import UserMessage, TextDelta, ToolCallReady, StreamDone
        max_steps = max_steps or Config.MAX_TOOL_STEPS
        system = "\n\n".join(m["content"] for m in messages if m["role"] == "system" and m.get("content"))
        task = "\n\n".join(m["content"] for m in messages if m["role"] == "user" and m.get("content"))
        chat = self._chat_obj(model, system, tools)
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
                fn = (impls or {}).get(tc.name)
                try:
                    result = await fn(**args) if fn else {"error": f"no tool {tc.name}"}
                except Exception as e:
                    result = {"error": str(e)}
                chat.add_tool_result(tc.id, json.dumps(result, default=str))
            user_msg = None
        return "".join(acc)

    async def embed(self, texts, model=None):
        raise RuntimeError("Universal Key does not serve embeddings; use OPENAI_API_KEY + OpenAIEmbedder")

    async def vision(self, data: bytes, filename: str, prompt: str):
        from emergentintegrations.llm.chat import LlmChat, UserMessage, ImageContent, TextDelta, StreamDone
        b64 = base64.b64encode(data).decode()
        chat = LlmChat(api_key=Config.EMERGENT_LLM_KEY, session_id="ai_core_vision",
                       system_message=prompt).with_model("gemini", Config.vision())
        out = []
        async for ev in chat.stream_message(UserMessage(text=prompt, file_contents=[ImageContent(image_base64=b64)])):
            if isinstance(ev, TextDelta):
                out.append(ev.content)
            elif isinstance(ev, StreamDone):
                break
        return "".join(out)


_BACKEND = None


def get_backend():
    global _BACKEND
    if _BACKEND is None:
        _BACKEND = OpenAIBackend() if Config.backend() == "openai" else EmergentBackend()
    return _BACKEND
