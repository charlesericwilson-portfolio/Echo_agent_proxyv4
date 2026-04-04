#!/usr/bin/env python3
"""
Echo Agent Proxy - Orchestrator v0.4
Now integrated with PTY Session Manager
"""

import sqlite3
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import asyncio

from src.pty_backend.session_manager import create_session as pty_create_session, send_to_session

BASE_DIR = Path(__file__).parent.parent.parent
DB_PATH = BASE_DIR / "database" / "echo.db"

app = FastAPI(title="Echo Agent Orchestrator v0.4")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/")
async def root():
    return {
        "message": "✅ Echo Agent Orchestrator v0.4 is running",
        "status": "healthy",
        "port": 8000,
        "components": ["Echo (Reasoning)", "Heartbeat", "Checker", "PTY Backend"]
    }

@app.get("/health")
async def health_check():
    return {"status": "ok", "database": "connected"}

# Create a new session (Echo will call this)
@app.post("/sessions")
async def create_new_session(request: Request):
    try:
        data = await request.json()
        session_id = data.get("session_id") or data.get("name")
        command = data.get("command", "bash -i")

        if not session_id:
            raise HTTPException(status_code=400, detail="session_id is required")

        # Create PTY session
        result = await pty_create_session(session_id, command)

        # Also log it in the database
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO sessions (session_id, name, tool_type, command, status)
            VALUES (?, ?, ?, ?, 'active')
        """, (session_id, session_id, "general", command))
        conn.commit()
        conn.close()

        return {"status": "success", "session_id": session_id, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Send command to an existing session
@app.post("/sessions/{session_id}/input")
async def send_input(session_id: str, request: Request):
    try:
        data = await request.json()
        command = data.get("command")

        if not command:
            raise HTTPException(status_code=400, detail="command is required")

        result = await send_to_session(session_id, command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Echo Agent Orchestrator v0.4 on port 8000...")
    print(f"   Database: {DB_PATH}")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
