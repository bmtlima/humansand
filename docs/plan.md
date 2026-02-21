# Implementation Plan: Multi-Agent Negotiation System

## Context

Hackathon project where personal AI agents communicate with each other to negotiate tasks. A user chats with their agent via a ChatGPT-like interface, and the agent autonomously searches a registry, contacts other agents, and synthesizes answers. The user wants to see what the agent is doing (reasoning traces) and have persistent conversation history.

The repo currently has no code — only `docs/plan.md` (backend spec) and `docs/followups.md`.

---

## Architecture Overview

```
Frontend (Next.js :3000)
    |
    v
API Gateway (FastAPI :8080)    <-- NEW: conversation management, CORS, routing
    |
    v
Agent Services (FastAPI :8001-8003)  <-- one per user (Alice, Bob, Charlie)
    |
    v
Registry (FastAPI :8000)  +  Other Agents (agent-to-agent)
```

**Key addition to the original plan**: an **API Gateway** between the frontend and agents. This is needed because:
- Conversation history management needs a single service (agents are per-user processes)
- The frontend should talk to one URL, not know about agent ports
- CORS is handled in one place
- The agent `/chat` endpoint is modified to also return reasoning steps

---

## File Structure

```
humansand/
├── backend/
│   ├── .env                    # OPENROUTER_API_KEY
│   ├── requirements.txt        # fastapi, uvicorn, httpx, openai, python-dotenv
│   ├── run_demo.sh             # Starts all 5 services
│   ├── registry.py             # Registry service (port 8000)
│   ├── base_agent.py           # Per-user agent (ports 8001-8003)
│   ├── mock_data.py            # Calendar/activity data per user
│   ├── tools.py                # Tool schemas + execution
│   ├── api_gateway.py          # NEW: frontend-facing API (port 8080)
│   ├── conversation_store.py   # NEW: in-memory conversation storage
│   └── models.py               # NEW: Pydantic request/response models
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx              # Root layout with sidebar
│   │   │   └── page.tsx                # Main page (renders AppShell)
│   │   ├── components/
│   │   │   ├── chat/
│   │   │   │   ├── ChatArea.tsx        # Main chat container
│   │   │   │   ├── MessageBubble.tsx   # User/assistant message
│   │   │   │   ├── ReasoningTrace.tsx  # Collapsible agent steps
│   │   │   │   ├── ChatInput.tsx       # Text input + send
│   │   │   │   └── MessageList.tsx     # Scrollable message list
│   │   │   ├── sidebar/
│   │   │   │   ├── Sidebar.tsx         # Conversation list
│   │   │   │   ├── ConversationItem.tsx
│   │   │   │   └── NewChatButton.tsx
│   │   │   └── layout/
│   │   │       └── AppShell.tsx        # Sidebar + main area
│   │   ├── lib/
│   │   │   ├── api.ts                  # API client (all backend calls)
│   │   │   └── types.ts               # TypeScript types
│   │   └── hooks/
│   │       ├── useChat.ts             # Chat state management
│   │       └── useConversations.ts    # Conversation list state
│   └── .env.local                      # NEXT_PUBLIC_API_URL=http://localhost:8080
│
└── docs/
    ├── plan.md
    ├── plan_new.md
    └── followups.md
```

---

## API Contract (Frontend <-> Gateway)

### `POST /chat`
Send a message, get a response with reasoning steps.
```json
// Request
{ "conversation_id": "abc123 | null", "message": "Find a Rust engineer who's free", "agent": "Alice" }

// Response
{
  "conversation_id": "abc123",
  "message": {
    "role": "assistant",
    "content": "Bob is available and knows Rust...",
    "reasoning_steps": [
      { "type": "tool_call", "tool_name": "search_registry", "summary": "Searching for Rust engineers...", "result": "Found: Bob" },
      { "type": "tool_call", "tool_name": "message_agent", "summary": "Checking Bob's availability...", "result": "Bob is idle" }
    ]
  }
}
```

### `GET /conversations`
List all conversations (for sidebar). Returns `[{id, title, created_at, updated_at, agent}]`.

### `GET /conversations/{id}`
Load full conversation with all messages and reasoning steps.

### `DELETE /conversations/{id}`
Delete a conversation.

---

## Backend Modifications to Original Plan

1. **`base_agent.py` `/chat` endpoint** — modified to return `{"content": str, "reasoning_steps": list}` instead of plain text. Also accepts optional `history` field for multi-turn context.
2. **Reasoning step collection** — the tool-calling loop accumulates steps as it runs (tool name, args, result, human-readable summary).
3. **`api_gateway.py`** — new service that handles conversation CRUD, forwards messages to the correct agent via httpx, and adds CORS middleware.
4. **`conversation_store.py`** — simple dict-based in-memory store. Conversations lost on restart (fine for hackathon).

---

## Frontend Modularity Strategy

Three layers of decoupling:
1. **`api.ts`** — all backend calls in one file. If the API changes, only this file changes.
2. **Custom hooks** (`useChat`, `useConversations`) — encapsulate state. Components call `sendMessage()` and read `messages`.
3. **Presentation components** — receive data as props, render it. Zero knowledge of API or state.

Using **shadcn/ui** for primitives: button, input, scroll-area, collapsible, skeleton, badge, avatar, card.

---

## Implementation Phases

### Phase 1: Backend core
Build from `docs/plan.md`: `mock_data.py` → `requirements.txt` → `tools.py` → `registry.py` → `base_agent.py` (with reasoning steps from the start) → `.env` → `run_demo.sh`

**Verify**: `bash run_demo.sh`, curl tests, confirm reasoning steps in response.

### Phase 2: API Gateway + conversation storage
Build: `models.py` → `conversation_store.py` → `api_gateway.py`. Update `run_demo.sh`.

**Verify**: curl all gateway endpoints, create conversation, send messages, retrieve history.

### Phase 3: Frontend skeleton
`create-next-app` + `shadcn init` + install components. Build: `types.ts` → `api.ts` → `AppShell.tsx` → `layout.tsx`.

**Verify**: App runs at localhost:3000, shows two-panel layout.

### Phase 4: Chat UI (core experience)
Build: `useChat.ts` → `ChatInput.tsx` → `MessageBubble.tsx` → `ReasoningTrace.tsx` → `MessageList.tsx` → `ChatArea.tsx` → `chat/page.tsx`.

**Verify**: Send "Find a Rust engineer who's free" from the UI, see response with collapsible reasoning traces.

### Phase 5: Sidebar + conversation management
Build: `useConversations.ts` → `NewChatButton.tsx` → `ConversationItem.tsx` → `Sidebar.tsx`.

**Verify**: Create multiple conversations, switch between them, see history preserved.

### Phase 6: Polish (if time permits)
Streaming (SSE), typing indicators, auto-scroll, error toasts, agent selector dropdown, dark mode.

---

## Gotchas to Watch For

- **OpenRouter rate limits**: 3-4 LLM calls per query — test under demo load
- **Agent startup order**: add `sleep 2` after registry in `run_demo.sh`
- **Port conflicts**: 5 services on ports 8000-8003 + 8080
- **Tool call arg parsing**: OpenRouter may return args as string or dict — handle both
- **Context window growth**: add simple truncation (keep last N messages) as safety valve
- **Python version**: Use `python3` / `pip3` (system `python` is 2.7)

---

## How to Run

```bash
# Backend
cd backend
pip3 install -r requirements.txt
# Set your OpenRouter key in .env
bash run_demo.sh

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000 and try: "Find a Rust engineer who's free right now"
