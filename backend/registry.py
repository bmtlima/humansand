import os
import re

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="Agent Registry")

USERS = {
    "Alice": {
        "name": "Alice",
        "role": "Software Engineer",
        "skills": ["Rust", "Python", "Java"],
        "agent_url": "http://localhost:8001",
    },
    "Bob": {
        "name": "Bob",
        "role": "Software Engineer",
        "skills": ["Rust", "Go"],
        "agent_url": "http://localhost:8002",
    },
    "Charlie": {
        "name": "Charlie",
        "role": "Software Engineer",
        "skills": ["Python", "JavaScript"],
        "agent_url": "http://localhost:8003",
    },
}


@app.get("/search")
def search(
    role: Optional[str] = Query(None),
    skill: Optional[str] = Query(None),
    exclude: Optional[str] = Query(None),
):
    results = []
    for name, user in USERS.items():
        if exclude and name == exclude:
            continue
        if role and role.lower() not in user["role"].lower():
            continue
        if skill and not any(skill.lower() in s.lower() for s in user["skills"]):
            continue
        results.append(user)
    return results


@app.get("/users/{user_name}")
def get_user(user_name: str):
    if user_name not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    return USERS[user_name]


class ProfileUpdate(BaseModel):
    role: str | None = None
    skills: list[str] | None = None


@app.patch("/users/{user_name}")
def update_user(user_name: str, body: ProfileUpdate):
    if user_name not in USERS:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role is not None:
        USERS[user_name]["role"] = body.role
    if body.skills is not None:
        USERS[user_name]["skills"] = body.skills
    _persist_users()
    return USERS[user_name]


def _persist_users():
    """Rewrite the USERS dict in this file so edits survive restarts."""
    lines = ["USERS = {"]
    for name, user in USERS.items():
        lines.append(f'    "{name}": {{')
        lines.append(f'        "name": "{user["name"]}",')
        lines.append(f'        "role": "{user["role"]}",')
        skills = ", ".join(f'"{s}"' for s in user["skills"])
        lines.append(f'        "skills": [{skills}],')
        lines.append(f'        "agent_url": "{user["agent_url"]}",')
        lines.append("    },")
    lines.append("}")
    new_block = "\n".join(lines)

    file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry.py")
    with open(file_path, "r") as f:
        source = f.read()
    source = re.sub(r"USERS = \{.*?\n\}", new_block, source, flags=re.DOTALL)
    with open(file_path, "w") as f:
        f.write(source)


@app.get("/")
def health():
    return {"service": "registry", "status": "online", "users": list(USERS.keys())}
