import json
import httpx
from mock_data import USER_MOCK_DATA

REGISTRY_URL = "http://localhost:8000"

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_registry",
            "description": "Search the global registry for users matching a role and/or skill.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "message_agent",
            "description": "Send a message to another user's agent to check their availability or ask a question.",
            "parameters": {
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_calendar_events",
            "description": "Get your owner's upcoming calendar events to determine their schedule.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


async def execute_tool(tool_name: str, args: dict, owner_name: str) -> str:
    """Execute a tool call and return the result as a string."""
    if tool_name == "search_registry":
        return await search_registry(args, owner_name)
    elif tool_name == "message_agent":
        return await message_agent(args, owner_name)
    elif tool_name == "get_calendar_events":
        return get_calendar_events(owner_name)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


async def search_registry(args: dict, exclude_user: str) -> str:
    params = {}
    if args.get("role"):
        params["role"] = args["role"]
    if args.get("skill"):
        params["skill"] = args["skill"]
    params["exclude"] = exclude_user

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{REGISTRY_URL}/search", params=params, timeout=10)
        return resp.text


async def message_agent(args: dict, sender_name: str) -> str:
    agent_url = args["agent_url"]
    payload = {
        "sender_id": sender_name,
        "intent": args.get("intent", "check_availability"),
        "urgency": "normal",
        "context": f"{sender_name} is looking for information",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{agent_url}/agent-message", json=payload, timeout=15
        )
        return resp.text


def get_calendar_events(owner_name: str) -> str:
    data = USER_MOCK_DATA.get(owner_name, {})
    events = data.get("calendar", [])
    return json.dumps(events)


