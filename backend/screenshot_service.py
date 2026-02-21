import base64
import os
import uuid

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from playwright.async_api import async_playwright, Browser

app = FastAPI(title="Screenshot Service")

SCREENSHOTS_DIR = "/app/screenshots"
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

# Mount static files for serving screenshots
app.mount("/screenshots", StaticFiles(directory=SCREENSHOTS_DIR), name="screenshots")

SCREEN_URLS = {
    "Alice": os.environ.get("SCREEN_ALICE_URL", "http://screen-alice:80"),
    "Bob": os.environ.get("SCREEN_BOB_URL", "http://screen-bob:80"),
    "Charlie": os.environ.get("SCREEN_CHARLIE_URL", "http://screen-charlie:80"),
}

# Default states matching existing screens
_screen_states = {
    "Alice": "focus_work",
    "Bob": "available",
    "Charlie": "communication",
}

_browser: Browser | None = None
_playwright = None


class ScreenshotRequest(BaseModel):
    user_name: str


@app.on_event("startup")
async def startup():
    global _browser, _playwright
    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch()


@app.on_event("shutdown")
async def shutdown():
    global _browser, _playwright
    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()


@app.post("/set-screen/{user_name}")
async def set_screen(user_name: str, body: dict):
    """Switch a user's screen to a different activity state."""
    state = body.get("state", "available")
    _screen_states[user_name] = state
    return {"ok": True, "user_name": user_name, "state": state}


@app.get("/screen-states")
async def get_screen_states():
    """Get current screen state for all users."""
    return _screen_states


@app.post("/screenshot")
async def take_screenshot(req: ScreenshotRequest):
    url = SCREEN_URLS.get(req.user_name)
    if not url:
        return {"error": f"Unknown user: {req.user_name}"}

    state = _screen_states.get(req.user_name, "available")
    target_url = f"{url}/{state}.html"

    page = await _browser.new_page(viewport={"width": 1280, "height": 720})
    try:
        await page.goto(target_url, wait_until="networkidle", timeout=10000)
        png_bytes = await page.screenshot(type="png")
    finally:
        await page.close()

    filename = f"{req.user_name.lower()}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(SCREENSHOTS_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(png_bytes)

    return {
        "screenshot_base64": base64.b64encode(png_bytes).decode("utf-8"),
        "screenshot_url": f"/screenshots/{filename}",
    }


@app.get("/")
def health():
    return {"service": "screenshot_service", "status": "online"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000)
