import asyncio
import json

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import ChatMessageRequest, ChatMessageResponse, AssistantMessage, ReasoningStep, RenameRequest
from conversation_store import store

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

AGENT_URLS = {
    "Alice": "http://localhost:8001",
    "Bob": "http://localhost:8002",
    "Charlie": "http://localhost:8003",
}

REGISTRY_URL = "http://localhost:8000"


@app.post("/chat")
async def chat(req: ChatMessageRequest):
    # Resolve or create conversation
    conv_id = req.conversation_id
    if not conv_id or not store.get(conv_id):
        conv_id = store.create(req.agent)

    # Store user message
    store.add_message(conv_id, {"role": "user", "content": req.message})

    # Get conversation history for context
    history = store.get_history(conv_id)
    history = history[:-1] if history else []

    # Forward to agent
    agent_url = AGENT_URLS.get(req.agent)
    if not agent_url:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent}")

    async def relay_stream():
        reasoning_steps: list[dict] = []
        assistant_content = ""

        async with httpx.AsyncClient() as client:
            try:
                async with client.stream(
                    "POST",
                    f"{agent_url}/chat",
                    json={"message": req.message, "history": history},
                    timeout=60,
                ) as resp:
                    resp.raise_for_status()
                    buffer = ""
                    async for chunk in resp.aiter_text():
                        buffer += chunk
                        # Process complete SSE lines
                        while "\n\n" in buffer:
                            line, buffer = buffer.split("\n\n", 1)
                            line = line.strip()
                            if not line.startswith("data: "):
                                continue
                            payload = line[6:]  # strip "data: "
                            try:
                                event = json.loads(payload)
                            except json.JSONDecodeError:
                                continue

                            if event.get("type") == "reasoning_step":
                                reasoning_steps.append(event)
                                yield f"data: {json.dumps(event)}\n\n"
                            elif event.get("type") == "final":
                                assistant_content = event.get("content", "")
                                final_event = {
                                    "type": "final",
                                    "conversation_id": conv_id,
                                    "content": assistant_content,
                                }
                                yield f"data: {json.dumps(final_event)}\n\n"

            except httpx.HTTPError as e:
                error_event = {
                    "type": "final",
                    "conversation_id": conv_id,
                    "content": f"Agent error: {str(e)}",
                }
                yield f"data: {json.dumps(error_event)}\n\n"
                assistant_content = error_event["content"]

        # Store the complete assistant message after stream ends
        stored_steps = [
            {
                "type": "tool_call",
                "tool_name": s.get("tool_name", ""),
                "summary": s.get("summary", ""),
                "result": s.get("result", ""),
            }
            for s in reasoning_steps
        ]
        store.add_message(conv_id, {
            "role": "assistant",
            "content": assistant_content,
            "reasoning_steps": stored_steps,
        })

    return StreamingResponse(relay_stream(), media_type="text/event-stream")


@app.get("/conversations")
def list_conversations():
    return store.list_all()


@app.get("/conversations/{conv_id}")
def get_conversation(conv_id: str):
    conv = store.get(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.patch("/conversations/{conv_id}")
def rename_conversation(conv_id: str, body: RenameRequest):
    if not store.rename(conv_id, body.title):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@app.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    if not store.delete(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@app.get("/agent-data/{user_name}")
async def get_agent_data(user_name: str):
    agent_url = AGENT_URLS.get(user_name)
    if not agent_url:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {user_name}")

    async with httpx.AsyncClient() as client:
        agent_resp, registry_resp = await asyncio.gather(
            client.get(f"{agent_url}/agent-data", timeout=10),
            client.get(f"{REGISTRY_URL}/users/{user_name}", timeout=10),
        )
    agent_data = agent_resp.json()
    profile = registry_resp.json()
    return {
        "calendar": agent_data["calendar"],
        "activity": agent_data["activity"],
        "profile": {
            "name": profile["name"],
            "role": profile["role"],
            "skills": profile["skills"],
        },
    }


class AgentDataUpdateRequest(BaseModel):
    calendar: list | None = None
    activity: dict | None = None
    profile: dict | None = None


@app.put("/agent-data/{user_name}")
async def update_agent_data(user_name: str, body: AgentDataUpdateRequest):
    agent_url = AGENT_URLS.get(user_name)
    if not agent_url:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {user_name}")

    async with httpx.AsyncClient() as client:
        tasks = []
        if body.calendar is not None or body.activity is not None:
            agent_payload = {}
            if body.calendar is not None:
                agent_payload["calendar"] = body.calendar
            if body.activity is not None:
                agent_payload["activity"] = body.activity
            tasks.append(client.put(f"{agent_url}/agent-data", json=agent_payload, timeout=10))
        if body.profile is not None:
            tasks.append(client.patch(f"{REGISTRY_URL}/users/{user_name}", json=body.profile, timeout=10))
        if tasks:
            await asyncio.gather(*tasks)
    return {"ok": True}


@app.get("/")
def health():
    return {"service": "api_gateway", "status": "online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
