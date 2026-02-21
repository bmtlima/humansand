from pydantic import BaseModel
from typing import Optional


class ChatMessageRequest(BaseModel):
    conversation_id: Optional[str] = None
    message: str
    agent: str = "Alice"


class ReasoningStep(BaseModel):
    type: str = "tool_call"
    tool_name: str = ""
    summary: str = ""
    result: str = ""


class AssistantMessage(BaseModel):
    role: str = "assistant"
    content: str
    reasoning_steps: list[ReasoningStep] = []


class ChatMessageResponse(BaseModel):
    conversation_id: str
    message: AssistantMessage


class ConversationSummary(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    agent: str
