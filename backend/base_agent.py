import argparse
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import AsyncOpenAI

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

app = FastAPI(title=f"{USER_NAME}'s Agent")

client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

MODEL = "minimax/minimax-m2.5"

SYSTEM_PROMPT = f"""You are a personal AI assistant for {USER_NAME}. You help your user by answering
questions, checking their schedule, and communicating with other users' agents.

You have access to tools to:
- Search a global registry of users by role/skill
- Message other users' agents to check their availability
- Check your own user's calendar and current activity

When asked to find someone, search the registry first, then message each
matching agent to check availability, then synthesize the results.

Be concise and helpful. When reporting results, include specific details about
what you found (who is available, what they're doing, their skills)."""


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
        # Build message history
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        for msg in req.history:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": req.message})

        # Agentic tool-calling loop
        max_iterations = 10
        for _ in range(max_iterations):
            response = await client.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=TOOL_SCHEMAS,
                tool_choice="auto",
            )

            choice = response.choices[0]

            if choice.finish_reason == "tool_calls" or (
                choice.message.tool_calls and len(choice.message.tool_calls) > 0
            ):
                # Append assistant message with tool calls
                messages.append(choice.message.model_dump())

                for tool_call in choice.message.tool_calls:
                    fn_name = tool_call.function.name
                    raw_args = tool_call.function.arguments
                    if isinstance(raw_args, str):
                        try:
                            fn_args = json.loads(raw_args)
                        except json.JSONDecodeError:
                            fn_args = {}
                    else:
                        fn_args = raw_args

                    result = await execute_tool(fn_name, fn_args, USER_NAME)

                    step = {
                        "type": "reasoning_step",
                        "tool_name": fn_name,
                        "summary": _make_summary(fn_name, fn_args),
                        "result": result[:500],
                    }
                    yield f"data: {json.dumps(step)}\n\n"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result,
                    })
            else:
                content = choice.message.content or ""
                yield f"data: {json.dumps({'type': 'final', 'content': content})}\n\n"
                return

        # Safety: if we hit max iterations
        fallback = {"type": "final", "content": "I wasn't able to complete the request within the allowed steps."}
        yield f"data: {json.dumps(fallback)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/agent-message")
async def agent_message(req: AgentMessageRequest):
    """Handle incoming messages from other agents. No LLM — direct logic."""
    data = USER_MOCK_DATA.get(USER_NAME, {})
    activity = data.get("activity", {})
    calendar = data.get("calendar", [])

    status_text = activity.get("status", "Unknown")
    is_available = status_text.lower() in ["idle", "available"]

    upcoming = calendar[0] if calendar else None
    upcoming_text = (
        f"{upcoming['event']} {upcoming['time']}" if upcoming else "Nothing scheduled soon"
    )

    return {
        "user_name": USER_NAME,
        "status": "available" if is_available else "busy",
        "current_activity": f"{status_text} - {activity.get('detail', '')}",
        "upcoming": upcoming_text,
        "message": f"{USER_NAME} {'appears to be available' if is_available else 'is currently busy'}.",
    }


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
    elif tool_name == "get_current_activity":
        return "Checking current activity..."
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
