# HumanSand

Multi-agent negotiation system where personal AI agents communicate on behalf of users.

## Quick Start

```bash
# Backend (all services)
cd backend
pip3 install -r requirements.txt
bash run_demo.sh     # Starts registry:8000, agents:8001-8003, gateway:8080

# Frontend
cd frontend
npm install
npm run dev          # http://localhost:3000
```

## Tech Stack

- **Backend**: Python 3 (FastAPI, uvicorn, httpx, openai SDK via OpenRouter)
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui
- **LLM**: `minimax/minimax-m2.5` via OpenRouter
- **Streaming**: SSE (Server-Sent Events) for real-time reasoning steps

**Important**: Use `python3` / `pip3` — the system `python` is Python 2.7.

## Architecture

```
Frontend (Next.js :3000)
  → API Gateway (:8080)
      → Alice's Agent (:8001)
      → Bob's Agent (:8002)
      → Charlie's Agent (:8003)
      → Registry (:8000)
```

- **Gateway** (`api_gateway.py`): Routes frontend requests to agents, manages conversations, relays SSE streams
- **Agents** (`base_agent.py`): Per-user LLM agent with tool-calling loop, streams reasoning steps as SSE
- **Registry** (`registry.py`): Searchable directory of users/skills
- **Conversation Store** (`conversation_store.py`): In-memory (no persistence across restarts)

### SSE Streaming Flow

Agent tool loop yields events → Gateway relays → Frontend parses incrementally:
```
data: {"type":"reasoning_step","tool_name":"search_registry","summary":"...","result":"..."}
data: {"type":"final","conversation_id":"abc","content":"..."}
```

## Project Structure

```
backend/
  base_agent.py          # Per-user agent (CLI args: --user-name, --port)
  api_gateway.py         # Frontend-facing proxy
  registry.py            # User/skill registry
  tools.py               # Tool schemas + execution
  models.py              # Pydantic models
  mock_data.py           # Calendar/activity fixtures
  conversation_store.py  # In-memory store
  run_demo.sh            # Starts all services

frontend/src/
  components/chat/       # ChatArea, MessageBubble, MessageList, ReasoningTrace, ChatInput
  components/sidebar/    # Sidebar, ConversationItem, NewChatButton
  components/layout/     # AppShell
  components/ui/         # shadcn/ui primitives
  hooks/                 # useChat, useConversations
  lib/                   # api.ts, types.ts, utils.ts
```

## Conventions

- Python: snake_case files, async/await, Pydantic for validation
- React: PascalCase components, all `"use client"`, state in custom hooks not components
- UI: shadcn/ui components, Tailwind for styling, lucide-react for icons
- No test suite yet (hackathon project)

## Environment Variables

- `backend/.env`: `OPENROUTER_API_KEY`
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8080`
