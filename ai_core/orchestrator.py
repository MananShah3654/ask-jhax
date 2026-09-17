"""
COO orchestrator.

Pipeline for each request:
    cache.get -> hit? return (0 tokens)
    plan (cheap model) -> pick 1-3 specialists + their sub-tasks
    fan-out (parallel, bounded, timed) -> run specialists
    synthesize (strong model, streamed) -> one owner-facing answer
    cache.put + memory.update

Emits structured events via `on_event` so the UI can show per-agent progress:
    {t:'cache_hit'} {t:'plan',agents:[...]} {t:'agent_start',name} {t:'agent_done',name}
    {t:'tool',name,args} {t:'delta',c} {t:'done'}
"""
import asyncio
import json

from .config import Config
from .llm import cheap_llm, stream_llm
from .utils import extract_json

_ROUTER = """You are the COO orchestrator for a specialist team.
Given the user's request and the roster, choose which specialists to run and give each a precise sub-task.
Use 1 agent for simple asks, 2-3 for complex ones. Only choose names from the roster.
Return ONLY JSON: {"agents":[{"name":"...","task":"..."}]}"""

_SYNTH = """You are the COO. Merge the specialists' findings below into ONE clear,
non-repetitive answer for the user, in THEIR preferred tone. End with concrete next steps.
Do not mention the specialists or the internal process."""


class COO:
    def __init__(self, roster, *, memory=None, cache=None, rag=None, rag_namespace=None):
        self.roster = roster            # {name: Agent}
        self.memory = memory
        self.cache = cache
        self.rag = rag
        self.rag_namespace = rag_namespace

    async def _plan(self, request, ctx):
        desc = "\n".join(f"- {a.name}: {a.description}" for a in self.roster.values())
        raw = await cheap_llm(_ROUTER, f"ROSTER:\n{desc}\n\n{ctx}\n\nREQUEST: {request}")
        plan = extract_json(raw)
        agents = [s for s in plan.get("agents", []) if s.get("name") in self.roster]
        if not agents:  # safe fallback: first agent handles it
            first = next(iter(self.roster))
            agents = [{"name": first, "task": request}]
        return agents

    async def handle(self, request, *, user_id="global", history=None, on_event=None):
        history = history or []
        emit = on_event or (lambda e: asyncio.sleep(0))

        # 0) cache
        if self.cache:
            cached = await self.cache.get(request, user_id)
            if cached:
                await emit({"t": "cache_hit"})
                await emit({"t": "delta", "c": cached})
                await emit({"t": "done"})
                return cached

        # 1) context = memory (who they are) + RAG (what's known)
        ctx_parts = []
        if self.memory:
            ctx_parts.append(await self.memory.context_block(user_id, history))
        if self.rag and self.rag_namespace:
            rc = await self.rag.context(request, namespace=self.rag_namespace)
            if rc:
                ctx_parts.append(rc)
        ctx = "\n\n".join(p for p in ctx_parts if p)

        # 2) plan
        plan = await self._plan(request, ctx)
        await emit({"t": "plan", "agents": [p["name"] for p in plan]})

        # 3) fan-out (parallel, bounded, timed)
        sem = asyncio.Semaphore(Config.MAX_PARALLEL_AGENTS)

        async def run_one(step):
            async with sem:
                await emit({"t": "agent_start", "name": step["name"]})
                agent = self.roster[step["name"]]
                try:
                    out = await asyncio.wait_for(
                        agent.run(step["task"], ctx=ctx, on_event=emit),
                        timeout=Config.AGENT_TIMEOUT_S,
                    )
                except asyncio.TimeoutError:
                    out = f"({step['name']} timed out)"
                except Exception as e:
                    out = f"({step['name']} failed: {e})"
                await emit({"t": "agent_done", "name": step["name"]})
                return {"agent": step["name"], "output": out}

        results = await asyncio.gather(*[run_one(s) for s in plan])

        # 4) synthesize (single specialist -> skip the merge to save tokens)
        if len(results) == 1:
            answer = results[0]["output"]
            await emit({"t": "delta", "c": answer})
        else:
            merged = "\n\n".join(f"### {r['agent']}\n{r['output']}" for r in results)
            profile_ctx = ctx if self.memory else ""
            answer = await stream_llm(_SYNTH, f"{profile_ctx}\n\nFINDINGS:\n{merged}\n\nREQUEST: {request}", emit)

        # 5) persist
        if self.cache:
            await self.cache.put(request, answer, user_id)
        if self.memory:
            new_history = history + [{"role": "user", "content": request},
                                     {"role": "assistant", "content": answer}]
            asyncio.create_task(self.memory.update(user_id, new_history))

        await emit({"t": "done"})
        return answer
