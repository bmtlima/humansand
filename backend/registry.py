from fastapi import FastAPI, Query
from typing import Optional

app = FastAPI(title="Agent Registry")

USERS = {
    "Alice": {
        "name": "Alice",
        "role": "Software Engineer",
        "skills": ["Rust", "Python"],
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


@app.get("/")
def health():
    return {"service": "registry", "status": "online", "users": list(USERS.keys())}
