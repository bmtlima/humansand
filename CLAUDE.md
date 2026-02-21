# HumanSand

Multi-agent negotiation system where personal AI agents communicate on behalf of users. Each user (Alice, Bob, Charlie, Diana) has a dedicated AI agent that can search a registry, message other agents, check calendars, and detect real-time activity via screenshot-based vision.

## Quick Start

```bash
# Backend (local, all services)
cd backend
pip3 install -r requirements.txt
bash run_demo.sh     # Starts registry:8000, agents:8001-8004, gateway:8080

# Frontend
cd frontend
npm install
npm run dev          # http://localhost:3000

# Full stack with Docker (includes screenshot service + simulated screens)
docker compose up -d --build   # Frontend at http://localhost:3001
```

**Important**: Use `python3` / `pip3` — the system `python` is Python 2.7.

## Tech Stack

- **Backend**: Python 3 (FastAPI, uvicorn, httpx, anthropic SDK, aiosqlite)
- **Frontend**: Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui
- **LLM**: `claude-sonnet-4-6` for agent reasoning, `claude-haiku-4-5` for vision/activity classification
- **Streaming**: SSE (Server-Sent Events) for real-time reasoning steps
- **Screenshot**: Playwright + Chromium (Docker) for screen capture
- **Storage**: SQLite via aiosqlite (`backend/data/conversations.db`)

## Architecture

```
Frontend (Next.js :3000)
  → API Gateway (:8080)
      → Alice's Agent (:8001)
      → Bob's Agent (:8002)
      → Charlie's Agent (:8003)
      → Diana's Agent (:8004)
      → Registry (:8000)
      → Screenshot Service (:7000, Docker only)
          → Screen Servers (:6001-6004, simulated user screens)
```

- **Gateway** (`api_gateway.py`): Routes frontend requests to agents, manages conversations in SQLite, relays SSE streams, proxies screen control
- **Agents** (`base_agent.py`): Per-user LLM agent with tool-calling loop (max 10 iterations), streams reasoning steps as SSE. Handles agent-to-agent messages with vision-based activity detection
- **Registry** (`registry.py`): Searchable directory of users/skills with persistence via `users_override.json`
- **Conversation Store** (`conversation_store.py`): SQLite-backed persistence with 20-message context window for LLM calls
- **Screenshot Service** (`screenshot_service.py`): Playwright-based screen capture, manages screen states per user

### Agent Tools

Each agent has 3 tools available in its Claude tool-calling loop:

1. **`search_registry`** — Search users by role/skill (excludes self)
2. **`message_agent`** — Send intent to another agent's `/agent-message` endpoint (triggers activity detection on target)
3. **`get_calendar_events`** — Retrieve own calendar from mock data

### Activity Detection Flow

When an agent receives a message via `/agent-message`:
1. Requests screenshot from screenshot service (Playwright captures simulated screen)
2. Sends screenshot to Claude Haiku 4.5 with privacy-preserving vision prompt
3. Classifies into: `available`, `focus_work`, `in_meeting`, `presenting`, `communication`, `learning`, `administration`, `away`
4. Returns activity status + summary (never leaks exact screen content)
5. Falls back to mock data if screenshot service unavailable

### SSE Streaming Flow

Agent tool loop yields events → Gateway relays → Frontend parses incrementally:
```
data: {"type":"reasoning_step","tool_name":"search_registry","summary":"...","result":"...","screenshot_url":null}
data: {"type":"reasoning_step","tool_name":"message_agent","summary":"...","result":"...","screenshot_url":"/screenshots/...png"}
data: {"type":"final","conversation_id":"abc","content":"..."}
```

## Project Structure

```
backend/
  base_agent.py          # Per-user agent (CLI args: --user-name, --port)
  api_gateway.py         # Frontend-facing proxy (:8080)
  registry.py            # User/skill registry (:8000)
  tools.py               # Tool schemas + async execution
  models.py              # Pydantic request/response models
  mock_data.py           # Calendar/activity fixtures
  conversation_store.py  # SQLite conversation persistence
  screenshot_service.py  # Playwright screen capture (:7000)
  run_demo.sh            # Starts registry, agents, gateway
  Dockerfile.agent       # Container for registry/agents/gateway
  Dockerfile.screenshot  # Container for screenshot service

frontend/src/
  app/                   # Next.js App Router (layout, page, personal-info page)
  components/chat/       # ChatArea, MessageBubble, MessageList, ReasoningTrace, ChatInput
  components/sidebar/    # Sidebar, ConversationItem, NewChatButton
  components/agent-data/ # ProfileSection, CalendarSection
  components/layout/     # AppShell (root orchestrator)
  components/ui/         # shadcn/ui primitives (button, avatar, badge, card, etc.)
  hooks/                 # useChat, useConversations, useAgentData
  lib/                   # api.ts (HTTP + SSE client), types.ts, utils.ts

screens/                 # Simulated user screens (static HTML served via nginx in Docker)
  alice/                 # HTML pages for each activity state
  bob/
  charlie/
  diana/

docs/
  plan.md                # Original implementation plan
  TODO.md                # Outstanding issues
  followups.md           # Feature backlog
```

## Key Endpoints

### Gateway (`:8080`, frontend-facing)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Send message, streams SSE reasoning + final response |
| GET | `/conversations` | List all conversations |
| GET | `/conversations/{id}` | Get conversation with messages |
| PATCH | `/conversations/{id}` | Rename conversation |
| DELETE | `/conversations/{id}` | Delete conversation |
| GET | `/agent-data/{user_name}` | Get calendar + profile |
| PUT | `/agent-data/{user_name}` | Update calendar/activity or profile |
| POST | `/set-screen/{user_name}` | Switch simulated screen state |
| GET | `/screen-states` | Get all users' current screen states |

### Agent (`:8001-8004`, internal)

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Agentic tool loop, returns SSE stream |
| POST | `/agent-message` | Receive message from another agent (triggers activity detection) |
| GET | `/agent-data` | Return calendar + activity |
| PUT | `/agent-data` | Update calendar/activity (for demo) |

## Conventions

- Python: snake_case files, async/await everywhere, Pydantic for validation
- React: PascalCase components, all `"use client"`, state in custom hooks not components
- UI: shadcn/ui components, Tailwind for styling, lucide-react for icons
- No test suite (hackathon project)

## Environment Variables

- `backend/.env`: `ANTHROPIC_API_KEY`
- `frontend/.env.local`: `NEXT_PUBLIC_API_URL=http://localhost:8080`

Docker overrides (set in `docker-compose.yml`):
- `AGENT_ALICE_URL`, `AGENT_BOB_URL`, `AGENT_CHARLIE_URL`, `AGENT_DIANA_URL`
- `REGISTRY_URL`, `SCREENSHOT_SERVICE_URL`
- `SCREEN_ALICE_URL`, `SCREEN_BOB_URL`, `SCREEN_CHARLIE_URL`, `SCREEN_DIANA_URL`

## Service Startup Order

Registry (8000) → Agents (8001-8004) → Gateway (8080) → Frontend (3000)

`run_demo.sh` handles this with sleep delays between stages. Docker Compose uses `depends_on`.
