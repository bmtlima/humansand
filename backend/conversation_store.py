import uuid
from datetime import datetime, timezone


class ConversationStore:
    def __init__(self):
        self._conversations: dict[str, dict] = {}

    def create(self, agent: str) -> str:
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        self._conversations[conv_id] = {
            "id": conv_id,
            "title": "New conversation",
            "agent": agent,
            "created_at": now,
            "updated_at": now,
            "messages": [],
        }
        return conv_id

    def get(self, conv_id: str) -> dict | None:
        return self._conversations.get(conv_id)

    def list_all(self) -> list[dict]:
        convos = sorted(
            self._conversations.values(),
            key=lambda c: c["updated_at"],
            reverse=True,
        )
        return [
            {
                "id": c["id"],
                "title": c["title"],
                "agent": c["agent"],
                "created_at": c["created_at"],
                "updated_at": c["updated_at"],
            }
            for c in convos
        ]

    def add_message(self, conv_id: str, message: dict):
        conv = self._conversations.get(conv_id)
        if not conv:
            return
        conv["messages"].append(message)
        conv["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Auto-title from first user message
        if conv["title"] == "New conversation" and message.get("role") == "user":
            text = message.get("content", "")
            conv["title"] = text[:50] + ("..." if len(text) > 50 else "")

    def delete(self, conv_id: str) -> bool:
        if conv_id in self._conversations:
            del self._conversations[conv_id]
            return True
        return False

    def get_history(self, conv_id: str, max_messages: int = 20) -> list[dict]:
        """Get recent message history formatted for the LLM (role + content only)."""
        conv = self._conversations.get(conv_id)
        if not conv:
            return []
        messages = conv["messages"][-max_messages:]
        return [{"role": m["role"], "content": m["content"]} for m in messages]


store = ConversationStore()
