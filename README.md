# LinkMate

A multi-agent negotiation system where personal AI agents communicate on behalf of users. Each user has a dedicated AI agent that can search a people directory, message other agents, check calendars, and detect real-time activity via screenshot-based vision — all while preserving privacy.

> "Find someone who knows Rust and is free right now" — your agent searches the registry, contacts candidates' agents, checks their screen activity, and reports back who's available.

## How It Works

LinkMate assigns each user (Alice, Bob, Charlie, Diana) a personal AI agent. When you ask your agent a question like "find a designer to help with my project", it autonomously:

1. **Searches the registry** for people matching the role/skill
2. **Messages their agents** to check availability
3. **Detects their activity** by analyzing a screenshot of their screen (classifying it as "in a meeting", "deep in code", "available", etc. — without leaking what's actually on screen)
4. **Checks calendars** for upcoming conflicts
5. **Reports back** with a recommendation

The entire reasoning process streams to the UI in real-time so you can see exactly what your agent is doing.

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/)

### Local Development

```bash
# 1. Backend
cd backend
pip3 install -r requirements.txt
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
bash run_demo.sh     # Starts registry:8000, agents:8001-8004, gateway:8080

# 2. Frontend (separate terminal)
cd frontend
npm install
npm run dev          # http://localhost:3000
```

### Docker (full stack with screenshot service)

```bash
# Set your API key
echo "ANTHROPIC_API_KEY=sk-ant-..." > backend/.env

# Start everything
docker compose up -d --build   # Frontend at http://localhost:3001
```

> **Note**: Use `python3` / `pip3` — the system `python` may be Python 2.7.

## Architecture

```
Frontend (Next.js :3000)
  |
  v
API Gateway (:8080)                 ← Conversation persistence, SSE relay
  |
  ├── Alice's Agent (:8001)  ──┐
  ├── Bob's Agent (:8002)    ──┤── Agent-to-agent messaging
  ├── Charlie's Agent (:8003)──┤
  ├── Diana's Agent (:8004)  ──┘
  |
  ├── Registry (:8000)              ← Searchable people directory
  |
  └── Screenshot Service (:7000)    ← Playwright screen capture (Docker only)
        |
        └── Screen Servers (:6001-6004)  ← Simulated user desktops (nginx)
```

### Services

| Service | Port | Role |
|---------|------|------|
| **API Gateway** | 8080 | Single entry point for the frontend. Routes to agents, manages conversations in SQLite, relays SSE streams |
| **Agents** | 8001-8004 | One per user. Runs a Claude tool-calling loop (max 10 iterations), streams reasoning steps |
| **Registry** | 8000 | Searchable directory of users with roles and skills |
| **Screenshot Service** | 7000 | Playwright + Chromium captures simulated screens for activity detection (Docker only) |
| **Screen Servers** | 6001-6004 | Nginx containers serving static HTML pages that simulate user desktops |

### Agent Tools

Each agent has 3 tools in its Claude tool-calling loop:

| Tool | Description |
|------|-------------|
| `search_registry` | Find users by role, skill, or name (excludes self) |
| `message_agent` | Send a request to another agent's `/agent-message` endpoint |
| `get_calendar_events` | Retrieve own calendar events |

### Activity Detection

When Agent A messages Agent B, the response includes B's current activity status. This works by:

1. Agent B receives the message at `/agent-message`
2. Requests a screenshot from the screenshot service (Playwright captures the simulated screen)
3. Sends the screenshot to Claude Haiku with a privacy-preserving vision prompt
4. Haiku classifies the activity into one of 8 statuses without revealing screen content:
   - `available` · `focus_work` · `in_meeting` · `presenting`
   - `communication` · `learning` · `administration` · `away`
5. Returns the status + next calendar event to Agent A

If the screenshot service is unavailable (local dev without Docker), agents fall back to mock activity data.

### SSE Streaming

Agents stream reasoning steps as Server-Sent Events so the UI shows progress in real-time:

```
data: {"type":"reasoning_step","tool_name":"search_registry","summary":"...","result":"..."}
data: {"type":"reasoning_step","tool_name":"message_agent","summary":"...","screenshot_url":"/screenshots/bob_abc.png"}
data: {"type":"final","conversation_id":"abc123","content":"Bob is available and knows Rust..."}
```

The gateway relays these events to the frontend while also persisting the full reasoning trace in SQLite.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3, FastAPI, uvicorn, httpx, aiosqlite |
| **Frontend** | Next.js 16 (App Router), React 19, TypeScript, Tailwind CSS 4, shadcn/ui |
| **LLM (reasoning)** | Claude Sonnet 4.6 via Anthropic SDK |
| **LLM (vision/titles)** | Claude Haiku 4.5 |
| **Streaming** | Server-Sent Events (SSE) |
| **Screenshots** | Playwright + Chromium (Docker) |
| **Storage** | SQLite via aiosqlite |

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
  config.py              # Centralized configuration constants
  run_demo.sh            # Starts registry, agents, gateway
  Dockerfile.agent       # Container for registry/agents/gateway
  Dockerfile.screenshot  # Container for screenshot service

frontend/src/
  app/                   # Next.js App Router (layout, page, personal-info page)
  components/chat/       # ChatArea, MessageBubble, MessageList, ReasoningTrace, ChatInput
  components/sidebar/    # Sidebar, ConversationItem, NewChatButton
  components/agent-data/ # ProfileSection, CalendarSection
  components/layout/     # AppShell (root orchestrator)
  components/ui/         # shadcn/ui primitives
  hooks/                 # useChat, useConversations, useAgentData
  lib/                   # api.ts (HTTP + SSE client), types.ts, utils.ts

screens/                 # Simulated user screens (static HTML served via nginx)
  alice/                 # 8 HTML pages per user (available, focus_work, in_meeting, etc.)
  bob/
  charlie/
  diana/
```

## API Reference

### Gateway Endpoints (`:8080`)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Send message, streams SSE reasoning + final response |
| `GET` | `/conversations` | List all conversations |
| `GET` | `/conversations/{id}` | Get conversation with messages |
| `PATCH` | `/conversations/{id}` | Rename conversation |
| `DELETE` | `/conversations/{id}` | Delete conversation |
| `GET` | `/agent-data/{user_name}` | Get calendar + profile |
| `PUT` | `/agent-data/{user_name}` | Update calendar/activity or profile |
| `POST` | `/set-screen/{user_name}` | Switch simulated screen state (Docker only) |
| `GET` | `/screen-states` | Get all users' current screen states |

### Agent Endpoints (`:8001-8004`, internal)

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/chat` | Agentic tool loop, returns SSE stream |
| `POST` | `/agent-message` | Receive message from another agent (triggers activity detection) |
| `GET` | `/agent-data` | Return calendar + activity |
| `PUT` | `/agent-data` | Update calendar/activity (for demo) |

## Environment Variables

| File | Variable | Description |
|------|----------|-------------|
| `backend/.env` | `ANTHROPIC_API_KEY` | Required. Your Anthropic API key |
| `frontend/.env.local` | `NEXT_PUBLIC_API_URL` | API gateway URL (default: `http://localhost:8080`) |

Docker Compose sets additional variables for inter-container networking (`AGENT_*_URL`, `REGISTRY_URL`, `SCREENSHOT_SERVICE_URL`, `SCREEN_*_URL`).

## Service Startup Order

```
Registry (8000) → Agents (8001-8004) → Gateway (8080) → Frontend (3000)
```

`run_demo.sh` handles ordering with sleep delays. Docker Compose uses `depends_on`.

## Design Decisions

- **Agent-per-user isolation**: Each user runs as a separate process for fault isolation and clean ownership boundaries
- **Gateway as single entry point**: Agents are stateless; the gateway owns conversation persistence and stream relay
- **Privacy-preserving vision**: Haiku classifies screen activity into coarse categories — the requesting agent never sees actual screen content
- **SSE over WebSockets**: Data flows one direction (server → client); SSE is simpler and sufficient
- **20-message context window**: Bounds LLM costs while preserving enough conversational context
- **Graceful degradation**: Screenshot service failure falls back to mock data — local dev works without Docker
