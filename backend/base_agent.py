import argparse
import json
import os

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import anthropic

from mock_data import USER_MOCK_DATA
from tools import TOOL_SCHEMAS, execute_tool

load_dotenv()

# --- CLI args ---
parser = argparse.ArgumentParser()
parser.add_argument("--user-name", required=True)
parser.add_argument("--port", type=int, required=True)
args, _ = parser.parse_known_args()

USER_NAME = args.user_name
PORT = args.port

SCREENSHOT_SERVICE_URL = os.environ.get("SCREENSHOT_SERVICE_URL", "http://localhost:7000")

app = FastAPI(title=f"{USER_NAME}'s Agent")

client = anthropic.AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

vision_client = anthropic.AsyncAnthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
)

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = f"""You are a personal AI assistant for {USER_NAME}. You help your user by answering
questions, checking their schedule, and communicating with other users' agents.

You have access to tools to:
- Search a global registry of users by role/skill
- Message other users' agents to check their availability
- Check your own user's calendar

When asked to find someone, search the registry first, then message each
matching agent to check availability, then synthesize the results.

Be concise and helpful. When reporting results, include specific details about
what you found (who is available, what they're doing, their skills)."""

# Anthropic tool format (different from OpenAI)
ANTHROPIC_TOOLS = [
    {
        "name": "search_registry",
        "description": "Search the global registry for users matching a role and/or skill.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "Job role to filter by, e.g. 'Software Engineer'",
                },
                "skill": {
                    "type": "string",
                    "description": "Skill to filter by, e.g. 'Rust'",
                },
            },
        },
    },
    {
        "name": "message_agent",
        "description": "Send a message to another user's agent to check their availability or ask a question.",
        "input_schema": {
            "type": "object",
            "properties": {
                "agent_url": {
                    "type": "string",
                    "description": "The URL of the target agent",
                },
                "user_name": {
                    "type": "string",
                    "description": "The name of the user whose agent you're contacting",
                },
                "intent": {
                    "type": "string",
                    "description": "The intent of the message, e.g. 'check_availability'",
                },
            },
            "required": ["agent_url", "user_name", "intent"],
        },
    },
    {
        "name": "get_calendar_events",
        "description": "Get your owner's upcoming calendar events to determine their schedule.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


# --- Request/Response models ---

class ChatRequest(BaseModel):
    message: str
    history: list = []


class AgentMessageRequest(BaseModel):
    sender_id: str
    intent: str
    urgency: str = "normal"
    context: str = ""


# --- Endpoints ---

@app.get("/")
def health():
    return {"agent": USER_NAME, "status": "online", "port": PORT}


@app.post("/chat")
async def chat(req: ChatRequest):
    async def event_stream():
        # Build message history (Anthropic uses separate system param)
        messages = []
        for msg in req.history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": req.message})

        # Agentic tool-calling loop
        max_iterations = 10
        for _ in range(max_iterations):
            response = await client.messages.create(
                model=MODEL,
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=messages,
                tools=ANTHROPIC_TOOLS,
            )

            # Check if the model wants to use tools
            if response.stop_reason == "tool_use":
                # Append the full assistant response (may contain text + tool_use blocks)
                messages.append({"role": "assistant", "content": response.content})

                # Process each tool use block
                tool_results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue

                    fn_name = block.name
                    fn_args = block.input

                    result = await execute_tool(fn_name, fn_args, USER_NAME)

                    # Extract screenshot_url from tool results if present
                    screenshot_url = None
                    if fn_name == "message_agent":
                        try:
                            result_data = json.loads(result)
                            screenshot_url = result_data.get("screenshot_url")
                        except (json.JSONDecodeError, TypeError):
                            pass

                    step = {
                        "type": "reasoning_step",
                        "tool_name": fn_name,
                        "summary": _make_summary(fn_name, fn_args),
                        "result": result[:500],
                        "screenshot_url": screenshot_url,
                    }
                    yield f"data: {json.dumps(step)}\n\n"

                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

                messages.append({"role": "user", "content": tool_results})
            else:
                # Extract text from the response
                content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        content += block.text
                yield f"data: {json.dumps({'type': 'final', 'content': content})}\n\n"
                return

        # Safety: if we hit max iterations
        fallback = {"type": "final", "content": "I wasn't able to complete the request within the allowed steps."}
        yield f"data: {json.dumps(fallback)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/agent-message")
async def agent_message(req: AgentMessageRequest):
    """Handle incoming messages from other agents. Screenshots own screen + vision analysis."""

    # 1. Take screenshot of own screen via screenshot service
    screenshot_url = None
    screenshot_base64 = None
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{SCREENSHOT_SERVICE_URL}/screenshot",
                json={"user_name": USER_NAME},
                timeout=15,
            )
            if resp.status_code == 200:
                data = resp.json()
                screenshot_base64 = data["screenshot_base64"]
                screenshot_url = data["screenshot_url"]
    except Exception:
        pass  # Fall back to mock data if screenshot fails

    # 2. Analyze screenshot with Claude Haiku 4.5 (vision)
    if screenshot_base64:
        analysis = await _analyze_screenshot(screenshot_base64)
    else:
        # Fallback to mock data if screenshot unavailable
        activity = USER_MOCK_DATA.get(USER_NAME, {}).get("activity", {})
        analysis = {
            "summary": f"{activity.get('status', 'Unknown')} - {activity.get('detail', '')}",
            "is_busy": activity.get("status", "").lower() not in ["idle", "available"],
        }

    # 3. Get calendar from mock data (still useful)
    calendar = USER_MOCK_DATA.get(USER_NAME, {}).get("calendar", [])
    upcoming = calendar[0] if calendar else None

    return {
        "user_name": USER_NAME,
        "status": "busy" if analysis["is_busy"] else "available",
        "current_activity": analysis["summary"],
        "upcoming": f"{upcoming['event']} {upcoming['time']}" if upcoming else "Nothing scheduled",
        "message": f"{USER_NAME} {'is currently busy' if analysis['is_busy'] else 'appears to be available'}.",
        "screenshot_url": screenshot_url,
    }


async def _analyze_screenshot(base64_image: str) -> dict:
    """Send screenshot to Claude Haiku 4.5 for vision analysis."""
    try:
        response = await vision_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image,
                        },
                    },
                    {
                        "type": "text",
                        "text": 'What is this person doing on their computer? Are they actively working or idle/available? Respond in JSON: {"summary": "1-2 sentence description", "is_busy": true/false}',
                    },
                ],
            }],
        )
        return json.loads(response.content[0].text)
    except (json.JSONDecodeError, IndexError):
        return {"summary": response.content[0].text, "is_busy": False}
    except Exception:
        return {"summary": "Unable to analyze screenshot", "is_busy": False}


def _make_summary(tool_name: str, args: dict) -> str:
    if tool_name == "search_registry":
        parts = []
        if args.get("role"):
            parts.append(f"role={args['role']}")
        if args.get("skill"):
            parts.append(f"skill={args['skill']}")
        return f"Searching registry for {', '.join(parts) or 'all users'}..."
    elif tool_name == "message_agent":
        return f"Contacting {args.get('user_name', 'unknown')}'s agent..."
    elif tool_name == "get_calendar_events":
        return "Checking calendar events..."
    return f"Calling {tool_name}..."


@app.get("/agent-data")
def get_agent_data():
    data = USER_MOCK_DATA.get(USER_NAME, {})
    return {"calendar": data.get("calendar", []), "activity": data.get("activity", {})}


class AgentDataUpdate(BaseModel):
    calendar: list | None = None
    activity: dict | None = None


@app.put("/agent-data")
def update_agent_data(req: AgentDataUpdate):
    if USER_NAME not in USER_MOCK_DATA:
        USER_MOCK_DATA[USER_NAME] = {}
    if req.calendar is not None:
        USER_MOCK_DATA[USER_NAME]["calendar"] = req.calendar
    if req.activity is not None:
        USER_MOCK_DATA[USER_NAME]["activity"] = req.activity
    return {"ok": True}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
