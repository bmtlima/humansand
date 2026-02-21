import json

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from models import ChatMessageRequest, ChatMessageResponse, AssistantMessage, ReasoningStep, RenameRequest
from conversation_store import store

app = FastAPI(title="API Gateway")


@app.on_event("startup")
async def startup():
    await store.initialize()


@app.on_event("shutdown")
async def shutdown():
    await store.close()


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


@app.post("/chat")
async def chat(req: ChatMessageRequest):
    # Resolve or create conversation
    conv_id = req.conversation_id
    if not conv_id or not await store.get(conv_id):
        conv_id = await store.create(req.agent)

    # Store user message
    await store.add_message(conv_id, {"role": "user", "content": req.message})

    # Get conversation history for context
    history = await store.get_history(conv_id)
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
        await store.add_message(conv_id, {
            "role": "assistant",
            "content": assistant_content,
            "reasoning_steps": stored_steps,
        })

    return StreamingResponse(relay_stream(), media_type="text/event-stream")


@app.get("/conversations")
async def list_conversations():
    return await store.list_all()


@app.get("/conversations/{conv_id}")
async def get_conversation(conv_id: str):
    conv = await store.get(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.patch("/conversations/{conv_id}")
async def rename_conversation(conv_id: str, body: RenameRequest):
    if not await store.rename(conv_id, body.title):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@app.delete("/conversations/{conv_id}")
async def delete_conversation(conv_id: str):
    if not await store.delete(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@app.get("/")
def health():
    return {"service": "api_gateway", "status": "online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
