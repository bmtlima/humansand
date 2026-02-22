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
- Search a global registry of users by role, skill, or name
- Message other users' agents to check their availability and current activity
- Check your own user's calendar

The registry contains users with roles like "Software Engineer" and "Designer".
When searching by role, use broad terms (e.g. "Designer" not "UI Designer").
If the user mentions someone by name, search by name to find them directly.
Try multiple search strategies if the first one returns no results.

When asked to find someone, search the registry first, then message each
matching agent to check availability, then synthesize the results.

IMPORTANT: You can only search the registry, check availability via agents, and
check calendars. You CANNOT send direct messages (Slack, email, etc.) to people
or schedule meetings on their behalf. Do not offer to do things you cannot do.
When you've gathered availability info, present the results and let the user
decide on next steps themselves.

NEVER include agent URLs in your responses — they are internal system details
and not useful to the user.

Be concise and helpful. When reporting results, include specific details about
what you found (who is available, what they're doing, their skills)."""

# Anthropic tool format (different from OpenAI)
ANTHROPIC_TOOLS = [
    {
        "name": "search_registry",
        "description": "Search the global registry for users matching a role, skill, and/or name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "role": {
                    "type": "string",
                    "description": "Job role to filter by, e.g. 'Software Engineer', 'Designer'",
                },
                "skill": {
                    "type": "string",
                    "description": "Skill to filter by, e.g. 'Rust'",
                },
                "name": {
                    "type": "string",
                    "description": "User name to look up, e.g. 'Diana'",
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
        mock_status = USER_MOCK_DATA.get(USER_NAME, {}).get("activity", {}).get("status", "").lower()
        if mock_status in ["idle", "available"]:
            analysis = {"status": "available"}
        elif "meeting" in mock_status or "zoom" in mock_status:
            analysis = {"status": "in_meeting"}
        else:
            analysis = {"status": "focus_work"}

    activity_status = analysis["status"]
    is_busy = activity_status not in ["available"]

    # 3. Get calendar from mock data (still useful)
    calendar = USER_MOCK_DATA.get(USER_NAME, {}).get("calendar", [])
    upcoming = calendar[0] if calendar else None

    return {
        "user_name": USER_NAME,
        "status": activity_status,
        "status_description": ACTIVITY_STATUSES.get(activity_status, ""),
        "upcoming": f"{upcoming['event']} {upcoming['time']}" if upcoming else "Nothing scheduled",
        "message": f"{USER_NAME} is currently: {activity_status}.",
    }


ACTIVITY_STATUSES = {
    "available": "Idle or passively consuming content (e.g. listening to music, watching a lofi stream). Not doing focused work.",
    "focus_work": "Actively working — coding, writing, designing, or other productive focused tasks in a work application.",
    "in_meeting": "On a video call or in a meeting application (e.g. Zoom, Google Meet, Teams).",
    "presenting": "Actively screen sharing or giving a presentation.",
    "communication": "Engaged in text communication — messaging on Slack, Discord, email, etc.",
    "learning": "Reading documentation, tutorials, articles, or watching educational content.",
    "administration": "Managing files, scheduling calendar events, system settings, or other administrative tasks.",
    "away": "Screen is locked, screensaver is active, or display is blank/off.",
}

VISION_PROMPT = """Classify this person's computer activity into exactly ONE of these statuses. Return ONLY a JSON object with a single "status" field.

Statuses:
""" + "\n".join(f'- "{k}": {v}' for k, v in ACTIVITY_STATUSES.items()) + """

Important rules:
- Music/lofi/ambient streams (even if playing in a video player) = "available", NOT "focus_work"
- Only use "focus_work" if you can see them actively writing code, documents, or similar
- If a messaging app (Slack, Discord, Teams chat) is visible with conversations, that is "communication" — even if other notifications are present
- If a meeting/video call notification or Zoom window is visible, prefer "in_meeting" over other statuses
- "available" means truly idle — no active app usage visible

Respond with JSON only: {"status": "<one of the statuses above>"}"""


async def _analyze_screenshot(base64_image: str) -> dict:
    """Send screenshot to Claude Haiku 4.5 for privacy-preserving activity classification."""
    try:
        response = await vision_client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=50,
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
                    {"type": "text", "text": VISION_PROMPT},
                ],
            }],
        )
        raw = response.content[0].text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        result = json.loads(raw)
        status = result.get("status", "available")
        if status not in ACTIVITY_STATUSES:
            status = "available"
        return {"status": status}
    except (json.JSONDecodeError, IndexError):
        return {"status": "available"}
    except Exception:
        return {"status": "available"}


def _make_summary(tool_name: str, args: dict) -> str:
    if tool_name == "search_registry":
        parts = []
        if args.get("name"):
            parts.append(f"name={args['name']}")
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
