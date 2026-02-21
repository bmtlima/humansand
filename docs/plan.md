# Multi-Agent Negotiation System — Implementation Plan

## Context
Building a multi-agent system for a hackathon where personal AI assistants communicate with each other to negotiate tasks. The primary demo: a user asks "Find someone who's a software engineer proficient in Rust who is not busy right now." The agent discovers candidates via a registry, queries their agents for real-time status, and synthesizes a response.

**Key decisions:**
- LLM-driven orchestration (LLM decides when to call tools via function calling)
- Direct agent-to-agent comms (no LLM on receiving side)
- Hardcoded registry
- minimax/minimax-m2.5 via OpenRouter (OpenAI-compatible Python SDK)

---

## File Structure
```
simulation/
├── docs/
│   └── plan.md          # This file
├── registry.py          # Registry service (port 8000)
├── base_agent.py        # Agent service (configurable port)
├── mock_data.py         # Per-user mock data (calendar, activity)
├── tools.py             # Tool definitions + execution logic
├── run_demo.sh          # Script to start all services
├── requirements.txt     # Dependencies
└── .env                 # OPENROUTER_API_KEY
```

---

## Step 1: `requirements.txt`
```
fastapi
uvicorn
httpx
openai
python-dotenv
```

We use the `openai` Python SDK pointed at OpenRouter's base URL (`https://openrouter.ai/api/v1`). This gives us native tool/function calling support with the same interface.

---

## Step 2: `mock_data.py` — Per-User Mock Data

Define a dictionary keyed by user name. Each entry has calendar events and current activity.

```python
USER_MOCK_DATA = {
    "Alice": {
        "calendar": [
            {"event": "Sprint Planning", "time": "in 30 minutes", "duration": "1 hour"},
            {"event": "Project deadline", "time": "tonight", "duration": "N/A"}
        ],
        "activity": {
            "status": "Focus time",
            "application": "VS Code",
            "detail": "Coding a Rust microservice"
        }
    },
    "Bob": {
        "calendar": [
            {"event": "Lunch break", "time": "in 2 hours", "duration": "1 hour"}
        ],
        "activity": {
            "status": "Idle",
            "application": "Slack",
            "detail": "Browsing messages"
        }
    },
    "Charlie": {
        "calendar": [
            {"event": "1:1 with Manager", "time": "in 10 minutes", "duration": "30 min"},
            {"event": "Code Review", "time": "in 2 hours", "duration": "1 hour"}
        ],
        "activity": {
            "status": "In a meeting",
            "application": "Zoom",
            "detail": "Team standup"
        }
    }
}
```

This way Alice is busy (focus + deadline), Bob is free, Charlie is in meetings. Makes the demo interesting.

---

## Step 3: `tools.py` — Tool Definitions & Execution

### 3a: OpenAI-format tool schemas (for LLM registration)

```python
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_registry",
            "description": "Search the global registry for users matching a role and/or skill.",
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {"type": "string", "description": "Job role to filter by, e.g. 'Software Engineer'"},
                    "skill": {"type": "string", "description": "Skill to filter by, e.g. 'Rust'"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "message_agent",
            "description": "Send a message to another user's agent to check their availability or ask a question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_url": {"type": "string", "description": "The URL of the target agent"},
                    "user_name": {"type": "string", "description": "The name of the user whose agent you're contacting"},
                    "intent": {"type": "string", "description": "The intent of the message, e.g. 'check_availability'"}
                },
                "required": ["agent_url", "user_name", "intent"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Get your owner's upcoming calendar events to determine their schedule.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_activity",
            "description": "Get your owner's current screen/application activity from OpenClaw.",
            "parameters": {"type": "object", "properties": {}}
        }
    }
]
```

### 3b: Tool execution functions

Each function is async. `search_registry` and `message_agent` make HTTP calls. `get_calendar_events` and `get_current_activity` read from `mock_data.py` using the agent's owner name.

---

## Step 4: `registry.py` — Registry Service (Port 8000)

- Hardcoded `USERS` dict with name, role, skills list, agent_url
- `GET /search?role=...&skill=...` — filters and returns matches
- Excludes the requesting agent's own user if a `exclude` param is passed (so an agent doesn't find itself)

### Registry data:
```python
USERS = {
    "Alice": {"role": "Software Engineer", "skills": ["Rust", "Python"], "agent_url": "http://localhost:8001"},
    "Bob": {"role": "Software Engineer", "skills": ["Rust", "Go"], "agent_url": "http://localhost:8002"},
    "Charlie": {"role": "Software Engineer", "skills": ["Python", "JavaScript"], "agent_url": "http://localhost:8003"},
}
```

---

## Step 5: `base_agent.py` — Agent Service

### 5a: Startup config
- CLI args: `--user-name Alice --port 8001`
- Loads `OPENROUTER_API_KEY` from `.env`
- Creates OpenAI client pointed at `https://openrouter.ai/api/v1`

### 5b: `/chat` POST endpoint (User → Agent)
Request: `{"message": "Find a Rust engineer who's free right now"}`

**The Agentic Tool-Calling Loop:**
1. Build messages list: system prompt (telling LLM who it is, who it serves) + user message
2. Call LLM with messages + tool schemas
3. If response contains `tool_calls`:
   - Execute each tool call (dispatch to the right function)
   - Append assistant message (with tool calls) to messages
   - Append tool result messages to messages
   - Go to step 2
4. If response is a text message → return it to the user

**System prompt template:**
```
You are a personal AI assistant for {user_name}. You help your user by answering
questions, checking their schedule, and communicating with other users' agents.

You have access to tools to:
- Search a global registry of users by role/skill
- Message other users' agents to check their availability
- Check your own user's calendar and current activity

When asked to find someone, search the registry first, then message each
matching agent to check availability, then synthesize the results.
```

### 5c: `/agent-message` POST endpoint (Agent → Agent)
Request schema:
```json
{"sender_id": "Alice", "intent": "check_availability", "urgency": "normal", "context": "Looking for available Rust engineer"}
```

**No LLM involved.** Direct logic:
1. Read owner's mock calendar and activity data
2. Determine availability based on activity status
3. Return structured JSON:
```json
{
    "user_name": "Bob",
    "status": "available",
    "current_activity": "Idle - browsing Slack",
    "upcoming": "Lunch break in 2 hours",
    "message": "Bob appears to be available."
}
```

### 5d: Health/info endpoint
`GET /` → returns `{"agent": user_name, "status": "online"}` (useful for debugging)

---

## Step 6: `run_demo.sh` — Startup Script

```bash
#!/bin/bash
# Start all services
echo "Starting Registry on port 8000..."
uvicorn registry:app --port 8000 &

echo "Starting Alice's agent on port 8001..."
python base_agent.py --user-name Alice --port 8001 &

echo "Starting Bob's agent on port 8002..."
python base_agent.py --user-name Bob --port 8002 &

echo "Starting Charlie's agent on port 8003..."
python base_agent.py --user-name Charlie --port 8003 &

echo "All services started. Send requests to http://localhost:800X/chat"
wait
```

---

## Demo Flow (End-to-End)

1. User sends POST to Alice's agent (`localhost:8001/chat`):
   ```json
   {"message": "Find someone who's a software engineer proficient in Rust who is not busy right now"}
   ```

2. Alice's LLM receives the message + tools, decides to call `search_registry(role="Software Engineer", skill="Rust")`

3. Code executes → HTTP GET to `localhost:8000/search?role=Software+Engineer&skill=Rust&exclude=Alice`
   → Returns Bob (Rust, Go)

4. LLM receives results, decides to call `message_agent(agent_url="http://localhost:8002", user_name="Bob", intent="check_availability")`

5. Code executes → HTTP POST to `localhost:8002/agent-message`
   → Bob's agent checks mock data: Bob is idle, returns `{"status": "available", ...}`

6. LLM receives Bob's status, synthesizes: "Bob is a Software Engineer skilled in Rust and Go. He's currently available — browsing Slack with no immediate meetings."

7. Response returned to user.

---

## Verification / Testing

1. **Start all services**: `bash run_demo.sh`
2. **Test registry**: `curl "http://localhost:8000/search?skill=Rust"` — should return Alice and Bob
3. **Test agent-to-agent**: `curl -X POST http://localhost:8002/agent-message -H "Content-Type: application/json" -d '{"sender_id":"Alice","intent":"check_availability","urgency":"normal","context":"test"}'` — should return Bob's availability
4. **Test full flow**: `curl -X POST http://localhost:8001/chat -H "Content-Type: application/json" -d '{"message":"Find a Rust engineer who is free right now"}'` — should return synthesized response mentioning Bob is available
5. **Edge case**: Ask for a skill nobody has: `"Find a Haskell engineer"` — should gracefully report no matches
