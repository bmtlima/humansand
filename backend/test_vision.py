"""Quick test: screenshot Charlie's screen and send to Haiku for classification."""
import asyncio
import base64
import json
import os
import httpx
from dotenv import load_dotenv
import anthropic

load_dotenv()

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


async def main():
    # 1. Take screenshot via the running screenshot service
    print("Taking screenshot of Charlie's screen...")
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            "http://localhost:7777/screenshot",
            json={"user_name": "Charlie"},
            timeout=15,
        )
        data = resp.json()
        screenshot_base64 = data["screenshot_base64"]
        print(f"Screenshot taken: {data['screenshot_url']}")

    # 2. Send to Haiku
    print("\nSending to Claude Haiku 4.5 for classification...")
    client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=50,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": screenshot_base64},
                },
                {"type": "text", "text": VISION_PROMPT},
            ],
        }],
    )

    raw = response.content[0].text
    print(f"\nRaw Haiku response: {raw}")
    try:
        result = json.loads(raw)
        print(f"Parsed status: {result['status']}")
    except json.JSONDecodeError:
        print("Failed to parse as JSON")


asyncio.run(main())
