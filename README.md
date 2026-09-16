# 🍽️ jhax.ai — AI Restaurant Co-Pilot

> Drop in a restaurant name. jhax researches it live, opens with a **Restaurant Snapshot** that proves it already gets the business, then acts as a sharp 15-year restaurant-COO advisor in an ongoing chat — with real, cited web data and copy-paste-ready output.

jhax reasons like a commercially savvy hospitality operator: direct, data-driven, honest (never a hype bot), and always ending forward-looking answers with concrete execution steps.

---

## ✨ Features

- **Auto-started Restaurant Snapshot** — the moment a restaurant loads, jhax speaks first: who they are, where they stand vs named competitors, what's happening around them now, and one sharp non-obvious opportunity.
- **Live web search in-chat** — jhax calls a `web_search` tool (backed by live Google Search) whenever a question needs current, real-world facts (competitors, hours, prices, reviews, local events). Answers show a **"Searched the web"** pill and **clickable source links**.
- **Execution-first answers** — 1–3 concrete next steps, checklists, comparison tables, and idea sets (3–5 options, with the one to run first).
- **Copy-paste drafts** — captions, WhatsApp broadcasts, review replies, menu blurbs rendered in one-click copy boxes.
- **Execution Tools panel** — interactive **Prime Cost calculator**, **Menu Engineering matrix** (Star/Plowhorse/Puzzle/Dog), and a **Caption Studio**.
- **Soft-Launch Demo Script** — a built-in panel of 10 one-tap questions ordered for maximum "aha" during demos.
- **No login** — pick a sample restaurant or type a name + location and go.

---

## 🤖 Models — which & where

| Job | Model | Where in code (`backend/server.py`) |
|-----|-------|-------------------------------------|
| jhax's reasoning (Snapshot + every chat reply) | **OpenAI `gpt-5.6-terra`** (GPT 5.6) | `MODEL_NAME` → `build_chat()` → `snapshot_stream`, `chat_stream` |
| Live web search (research + in-chat lookups) | **Google `gemini-2.5-flash`** w/ Google Search grounding | `SEARCH_MODEL` → `build_search_chat()` → `research_restaurant`, `do_web_search` |

**How they work together:** Gemini fetches the *live facts*; GPT 5.6 does the *thinking* and writes the answer. When a chat question is factual, GPT 5.6 calls the `web_search` tool → the backend runs a Gemini Google-Search query → results (and source URLs) return to GPT 5.6 to reason over.

Both run through the **Emergent Universal Key** (`EMERGENT_LLM_KEY`) via the `emergentintegrations` library, so all usage bills to one balance.

> ⚙️ Note: `gpt-5.6-terra` requires `reasoning_effort="none"` to use function tools on the Chat Completions path — this is set on the tool-enabled chat.

---

## 🏗️ Architecture

```
React (CRA + craco, Tailwind, shadcn/ui, framer-motion)
        │  fetch + SSE
        ▼
FastAPI (/api)  ──►  MongoDB (motor)      # restaurants + messages
        │
        ├─ Gemini 2.5 Flash (Google Search)   # research + web_search tool
        └─ GPT 5.6 (gpt-5.6-terra)            # snapshot + chat reasoning
```

- **Streaming:** all AI responses stream over **Server-Sent Events (SSE)** with `X-Accel-Buffering: no`.
- **SSE event types:** `delta` (text chunk), `tool` (`{name, query}`), `sources` (`{items: [url,...]}`), `error`, `done`.

### Project structure
```
/app
├── backend
│   ├── server.py            # FastAPI app, LLM pipeline, SSE endpoints
│   ├── requirements.txt
│   ├── .env(.example)
│   └── tests/backend_test.py
├── frontend
│   ├── src
│   │   ├── pages/CoPilot.jsx        # orchestrates landing/researching/chat + streaming
│   │   ├── components/
│   │   │   ├── Landing.jsx          # restaurant picker + custom entry
│   │   │   ├── ResearchingState.jsx # animated data-gathering
│   │   │   ├── ChatPanel.jsx        # messages + prompt chips + composer
│   │   │   ├── MessageBubble.jsx    # markdown, snapshot card, search pill, sources
│   │   │   ├── ProfileSidebar.jsx   # cuisine/price/rating/competitors/menu
│   │   │   ├── ToolsPanel.jsx       # Prime Cost / Menu Matrix / Studio
│   │   │   ├── DemoSheet.jsx        # 10 one-tap launch questions
│   │   │   └── Markdown.jsx         # renderer + copy-able draft boxes
│   │   └── lib/api.js               # REST + SSE stream client
│   ├── package.json
│   └── .env(.example)
└── README.md
```

---

## 🔌 API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/restaurants/research` | `{name, location?, cuisine?}` → live-research a restaurant (Gemini), store & return profile |
| `GET`  | `/api/restaurants` | List saved restaurants (latest first) |
| `GET`  | `/api/restaurants/{id}` | Get restaurant + its messages |
| `DELETE` | `/api/restaurants/{id}` | Delete restaurant + messages |
| `POST` | `/api/restaurants/{id}/snapshot/stream` | SSE — auto Restaurant Snapshot (saved as first assistant message) |
| `POST` | `/api/restaurants/{id}/chat/stream` | SSE — chat turn `{message}`; GPT 5.6 with `web_search` tool |

---

## 🚀 Local development

Prereqs: Python 3.11+, Node 18+ / Yarn, MongoDB, and a valid `EMERGENT_LLM_KEY`.

```bash
# Backend
cd backend
cp .env.example .env            # fill EMERGENT_LLM_KEY
pip install -r requirements.txt
# served by supervisor on 0.0.0.0:8001 (managed env). Locally:
# uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend
cd frontend
cp .env.example .env            # set REACT_APP_BACKEND_URL
yarn install
yarn start                      # http://localhost:3000
```

In the managed Emergent environment, services run under **supervisor**:
```bash
sudo supervisorctl restart backend    # after .env / dependency changes
sudo supervisorctl restart frontend
```

### Environment variables
| File | Var | Notes |
|------|-----|-------|
| `backend/.env` | `MONGO_URL` | Mongo connection string |
| | `DB_NAME` | database name |
| | `CORS_ORIGINS` | comma-separated origins or `*` |
| | `EMERGENT_LLM_KEY` | powers GPT 5.6 + Gemini |
| `frontend/.env` | `REACT_APP_BACKEND_URL` | backend base URL; app calls `${URL}/api/...` |

---

## 🧪 Testing

```bash
cd backend && python -m pytest tests/backend_test.py -q
```
Covers research (≥4 real competitors), snapshot/chat SSE streaming, the live `web_search` tool (no refusal before searching), and conversation continuity.

---

## 🎬 Soft-launch demo tips

Open the **Demo** button (top-right) for the 10-question script. Recommended arc:
1. Let the **Snapshot** auto-open (say nothing) → "it knows me".
2. Ask about **competitors** and **business hours** → live, real, cited data.
3. Finish with a **caption or WhatsApp draft** → they leave holding something usable.

> Live-search answers take ~20–30s (a real Google lookup) — present it as "watch it actually search" rather than dead air.

---

## ⚠️ Notes & guardrails

- jhax never fabricates specific facts not found in data/search; it searches first, and says so if a search comes up empty.
- No legal/tax/licensing advice beyond general pointers.
- `LlmChat` keeps only an in-memory thread — chat history is persisted in MongoDB and replayed into the system message for continuity.
