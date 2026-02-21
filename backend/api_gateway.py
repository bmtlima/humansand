import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from models import ChatMessageRequest, ChatMessageResponse, AssistantMessage, ReasoningStep
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


@app.post("/chat", response_model=ChatMessageResponse)
async def chat(req: ChatMessageRequest):
    # Resolve or create conversation
    conv_id = req.conversation_id
    if not conv_id or not store.get(conv_id):
        conv_id = store.create(req.agent)

    # Store user message
    store.add_message(conv_id, {"role": "user", "content": req.message})

    # Get conversation history for context
    history = store.get_history(conv_id)
    # Remove the last message (we send it separately as `message`)
    history = history[:-1] if history else []

    # Forward to agent
    agent_url = AGENT_URLS.get(req.agent)
    if not agent_url:
        raise HTTPException(status_code=400, detail=f"Unknown agent: {req.agent}")

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{agent_url}/chat",
                json={"message": req.message, "history": history},
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Agent error: {str(e)}")

    # Parse reasoning steps
    steps = [
        ReasoningStep(
            type=s.get("type", "tool_call"),
            tool_name=s.get("tool_name", ""),
            summary=s.get("summary", ""),
            result=s.get("result", ""),
        )
        for s in data.get("reasoning_steps", [])
    ]

    assistant_content = data.get("content", "")

    # Store assistant message
    store.add_message(conv_id, {
        "role": "assistant",
        "content": assistant_content,
        "reasoning_steps": [s.model_dump() for s in steps],
    })

    return ChatMessageResponse(
        conversation_id=conv_id,
        message=AssistantMessage(
            content=assistant_content,
            reasoning_steps=steps,
        ),
    )


@app.get("/conversations")
def list_conversations():
    return store.list_all()


@app.get("/conversations/{conv_id}")
def get_conversation(conv_id: str):
    conv = store.get(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conv


@app.delete("/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    if not store.delete(conv_id):
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {"ok": True}


@app.get("/")
def health():
    return {"service": "api_gateway", "status": "online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
