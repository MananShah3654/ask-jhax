# jhax.ai — Restaurant Co-Pilot · PRD

## Original Problem Statement
Build **jhax.ai**, an AI business co-pilot exclusively for restaurant owners/operators. jhax reasons and speaks like a sharp 15-year restaurant COO/consultant: commercially savvy, data-driven, direct, honest (not sycophantic). On selecting a restaurant, the backend gathers menu + market data and jhax AUTO-STARTS the chat with a tight "Restaurant Snapshot" (who they are, where they stand vs named competitors, what's happening around them now, one non-obvious opportunity). Ongoing chat gives execution-ready steps, copy-paste drafts, and idea sets.

## Architecture
- **Frontend:** React (CRA + craco), Tailwind, shadcn/ui, framer-motion, react-markdown. Single-page co-pilot at `/`.
- **Backend:** FastAPI (`/api` prefix), MongoDB (motor). SSE streaming for AI responses.
- **AI:** GPT 5.6 (`gpt-5.6-terra`) for jhax's reasoning (snapshot + chat) via emergentintegrations Universal Key; Gemini (`gemini-2.5-flash`) with live Google Search for the restaurant research/data-gathering step.

## User Choices
- Model: GPT 5.6 reasoning + Gemini live Google Search for research.
- No login — jump straight in.
- Scope: Restaurant selection → auto Snapshot → ongoing chat co-pilot.
- Design: Warm, hospitality-inspired (ivory/sandstone/brass amber/espresso).

## User Persona
Restaurant owner/operator wanting fast, credible, execution-focused strategic advice.

## Core Requirements (static)
- No-auth landing with sample restaurants + custom entry (name, location, cuisine).
- Live research → structured profile (cuisine, price tier, rating, positioning, competitors, review themes, local context, menu).
- Auto-started Restaurant Snapshot as first assistant message (streamed).
- Streaming chat co-pilot with markdown, tables, checklists, copy-paste draft boxes, prompt chips.
- Profile sidebar + tools panel (Prime Cost calculator, Menu Engineering matrix, Caption Studio).

## Implemented (2026-06-16)
- Backend endpoints: `POST /api/restaurants/research`, `GET /api/restaurants`, `GET /api/restaurants/{id}`, `DELETE /api/restaurants/{id}`, `POST /api/restaurants/{id}/snapshot/stream` (SSE), `POST /api/restaurants/{id}/chat/stream` (SSE). Messages persisted in Mongo with conversation continuity.
- **Live web search in chat:** GPT 5.6 calls a custom `web_search` tool mid-conversation (backed by Gemini googleSearch); requires `reasoning_effort="none"` for function tools on gpt-5.6-terra. jhax now answers competitor/hours/market questions with real, current, named data. Research pulls >=4 real competitors. UI shows a "Searched the web" pill on answers.
- Frontend: Landing, ResearchingState, CoPilot 3-panel layout, ChatPanel, MessageBubble (snapshot + search pill + streaming cursor), ProfileSidebar, ToolsPanel (Prime Cost calc), Markdown renderer with copy-able draft boxes.
- Verified: 11/11 backend tests + full frontend E2E pass (100%).

## Backlog / Remaining
- P1: Saved chat history & multi-restaurant switcher (persisted list already in DB; add UI switcher).
- P2: Right-panel "Menu Re-engineering canvas" and staff-briefing generator.
- P2: Server-side timeout/fallback on the research call; remove unused `search_ctx` param.
- P2: Export drafts as PDF/print.

## Next Tasks
- Add restaurant switcher + history sidebar.
- Enrich research with real ratings/citations surfaced in UI.
