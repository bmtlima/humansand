import json
import os
import uuid
from datetime import datetime, timezone

import aiosqlite

DB_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(DB_DIR, "conversations.db")


class ConversationStore:
    def __init__(self):
        self._db: aiosqlite.Connection | None = None

    async def initialize(self):
        os.makedirs(DB_DIR, exist_ok=True)
        self._db = await aiosqlite.connect(DB_PATH)
        self._db.row_factory = aiosqlite.Row
        await self._db.execute("PRAGMA journal_mode=WAL")
        await self._db.execute(
            """
            CREATE TABLE IF NOT EXISTS conversations (
                id         TEXT PRIMARY KEY,
                title      TEXT NOT NULL DEFAULT 'New conversation',
                agent      TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                messages   TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        await self._db.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_conversations_updated_at
            ON conversations(updated_at DESC)
            """
        )
        await self._db.commit()

    async def close(self):
        if self._db:
            await self._db.close()

    async def create(self, agent: str) -> str:
        conv_id = str(uuid.uuid4())[:8]
        now = datetime.now(timezone.utc).isoformat()
        await self._db.execute(
            """
            INSERT INTO conversations (id, title, agent, created_at, updated_at, messages)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (conv_id, "New conversation", agent, now, now, "[]"),
        )
        await self._db.commit()
        return conv_id

    async def get(self, conv_id: str) -> dict | None:
        cursor = await self._db.execute(
            "SELECT * FROM conversations WHERE id = ?", (conv_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return None
        return self._row_to_dict(row)

    async def list_all(self) -> list[dict]:
        cursor = await self._db.execute(
            "SELECT id, title, agent, created_at, updated_at FROM conversations ORDER BY updated_at DESC"
        )
        rows = await cursor.fetchall()
        return [
            {
                "id": r["id"],
                "title": r["title"],
                "agent": r["agent"],
                "created_at": r["created_at"],
                "updated_at": r["updated_at"],
            }
            for r in rows
        ]

    async def add_message(self, conv_id: str, message: dict):
        cursor = await self._db.execute(
            "SELECT messages, title FROM conversations WHERE id = ?", (conv_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return

        messages = json.loads(row["messages"])
        messages.append(message)
        now = datetime.now(timezone.utc).isoformat()

        title = row["title"]

        await self._db.execute(
            "UPDATE conversations SET messages = ?, title = ?, updated_at = ? WHERE id = ?",
            (json.dumps(messages), title, now, conv_id),
        )
        await self._db.commit()

    async def rename(self, conv_id: str, title: str) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        cursor = await self._db.execute(
            "UPDATE conversations SET title = ?, updated_at = ? WHERE id = ?",
            (title, now, conv_id),
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def delete(self, conv_id: str) -> bool:
        cursor = await self._db.execute(
            "DELETE FROM conversations WHERE id = ?", (conv_id,)
        )
        await self._db.commit()
        return cursor.rowcount > 0

    async def get_history(self, conv_id: str, max_messages: int = 20) -> list[dict]:
        """Get recent message history formatted for the LLM (role + content only)."""
        cursor = await self._db.execute(
            "SELECT messages FROM conversations WHERE id = ?", (conv_id,)
        )
        row = await cursor.fetchone()
        if not row:
            return []
        messages = json.loads(row["messages"])[-max_messages:]
        return [{"role": m["role"], "content": m["content"]} for m in messages]

    @staticmethod
    def _row_to_dict(row) -> dict:
        return {
            "id": row["id"],
            "title": row["title"],
            "agent": row["agent"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "messages": json.loads(row["messages"]),
        }


store = ConversationStore()
