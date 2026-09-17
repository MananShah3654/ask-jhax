"""
Drop-in FastAPI SSE server for the COO orchestrator.

Streams per-agent progress + tokens to the browser as Server-Sent Events:
    event data shapes: {t:'cache_hit'} {t:'plan',agents:[...]}
    {t:'agent_start',name} {t:'tool',name,args} {t:'agent_done',name}
    {t:'delta',c} {t:'done'}

Use it two ways:

  A) Standalone app:
        from ai_core.api import create_app
        app = create_app(web_search=my_search)          # uvicorn ai_core.api:app
        # or: app = create_app(web_search=my_search, mongo_db=db)

  B) Mount the router on your existing FastAPI app:
        from ai_core.api import build_router
        app.include_router(build_router(web_search=my_search), prefix="/api")
"""
import asyncio
import json

from fastapi import FastAPI, APIRouter, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .orchestrator import COO
from .memory import Memory
from .cache import SemanticCache
from .rag import RAG
from .rosters import restaurant_coo_roster
from .stores import InMemoryKV, InMemoryVectorStore, MongoKV, MongoVectorStore
from .embeddings import default_embedder


class ChatBody(BaseModel):
    message: str
    user_id: str = "global"
    session_id: str = "default"


class _HistoryStore:
    """Minimal per-(user,session) history. Swap for your DB in production."""
    def __init__(self, mongo_db=None):
        self.db = mongo_db
        self._mem = {}

    async def get(self, user_id, session_id):
        key = f"{user_id}:{session_id}"
        if self.db is not None:
            docs = await self.db.coo_messages.find(
                {"key": key}, {"_id": 0, "role": 1, "content": 1}
            ).sort("ts", 1).to_list(500)
            return docs
        return list(self._mem.get(key, []))

    async def append(self, user_id, session_id, role, content):
        key = f"{user_id}:{session_id}"
        if self.db is not None:
            from .utils import now_ts
            await self.db.coo_messages.insert_one(
                {"key": key, "role": role, "content": content, "ts": now_ts()})
        else:
            self._mem.setdefault(key, []).append({"role": role, "content": content})


def _default_db():
    """Build a Mongo DB handle from env so memory/cache/RAG persist by default."""
    from .config import Config
    if not Config.MONGO_URL:
        return None
    from motor.motor_asyncio import AsyncIOMotorClient
    return AsyncIOMotorClient(Config.MONGO_URL)[Config.DB_NAME]


def _wire(web_search=None, mongo_db=None, rag_namespace="global", roster=None):
    """Build a COO + history store. Persists to Mongo by default (from MONGO_URL)."""
    if mongo_db is None:
        mongo_db = _default_db()

    emb = default_embedder()
    if mongo_db is not None:
        memory = Memory(MongoKV(mongo_db.coo_memory))
        cache = SemanticCache(MongoVectorStore(mongo_db.coo_cache, emb))
        rag = RAG(MongoVectorStore(mongo_db.coo_knowledge, emb))
    else:
        memory = Memory(InMemoryKV())
        cache = SemanticCache(InMemoryVectorStore(emb))
        rag = RAG(InMemoryVectorStore(emb))

    roster = roster or restaurant_coo_roster(web_search=web_search)
    coo = COO(roster, memory=memory, cache=cache, rag=rag, rag_namespace=rag_namespace)
    history = _HistoryStore(mongo_db)
    return coo, history, rag


def build_router(web_search=None, mongo_db=None, rag_namespace="global", roster=None) -> APIRouter:
    router = APIRouter()
    coo, history, rag = _wire(web_search, mongo_db, rag_namespace, roster)

    @router.get("/coo/health")
    async def health():
        return {"status": "ok", "agents": list(coo.roster.keys())}

    @router.post("/coo/ingest")
    async def ingest(file: UploadFile = File(...),
                     namespace: str = Form(None),
                     source: str = Form(None)):
        from .ingest import ingest_file
        data = await file.read()
        try:
            n = await ingest_file(rag, data, file.filename,
                                  namespace=namespace or rag_namespace, source=source)
        except Exception as e:
            return {"ok": False, "error": str(e), "file": file.filename}
        return {"ok": True, "chunks": n, "file": file.filename,
                "namespace": namespace or rag_namespace}

    @router.post("/coo/chat/stream")
    async def chat_stream(body: ChatBody):
        hist = await history.get(body.user_id, body.session_id)
        queue: asyncio.Queue = asyncio.Queue()
        DONE = object()

        async def on_event(e):
            await queue.put(e)

        async def run():
            try:
                answer = await coo.handle(
                    body.message, user_id=body.user_id, history=hist, on_event=on_event)
                await history.append(body.user_id, body.session_id, "user", body.message)
                await history.append(body.user_id, body.session_id, "assistant", answer)
            except Exception as ex:
                await queue.put({"t": "error", "message": str(ex)})
            finally:
                await queue.put(DONE)

        async def gen():
            task = asyncio.create_task(run())
            try:
                while True:
                    ev = await queue.get()
                    if ev is DONE:
                        break
                    yield f"data: {json.dumps(ev, default=str)}\n\n"
            finally:
                if not task.done():
                    task.cancel()

        return StreamingResponse(
            gen(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

    return router


def create_app(web_search=None, mongo_db=None, rag_namespace="global",
               roster=None, cors_origins="*") -> FastAPI:
    app = FastAPI(title="ai_core COO")
    app.include_router(build_router(web_search, mongo_db, rag_namespace, roster), prefix="/api")
    app.add_middleware(
        CORSMiddleware, allow_credentials=True,
        allow_origins=cors_origins.split(",") if isinstance(cors_origins, str) else cors_origins,
        allow_methods=["*"], allow_headers=["*"])
    return app


# default app (in-memory, no live search) so `uvicorn ai_core.api:app` just works
app = create_app()
