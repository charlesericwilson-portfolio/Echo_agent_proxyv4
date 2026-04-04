#!/usr/bin/env python3
"""
Echo Agent Proxy - Orchestrator v1.1
Clean version with session routes + Heartbeat
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from src.heartbeat.monitor import HeartbeatMonitor
from src.pty_backend.session_manager import create_session as pty_create_session, send_to_session

heartbeat = HeartbeatMonitor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting Echo Agent Orchestrator v1.1...")
    task = asyncio.create_task(heartbeat.start())
    print("   Heartbeat Monitor started")
    yield
    print("Shutting down...")
    heartbeat.stop()
    task.cancel()

app = FastAPI(title="Echo Agent Orchestrator v1.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "✅ Echo Agent Orchestrator v1.1 is running", "status": "healthy"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/sessions")
async def create_new_session(request: Request):
    data = await request.json()
    session_id = data.get("session_id") or data.get("name")
    command = data.get("command", "bash -i")

    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    result = await pty_create_session(session_id, command)
    return {"status": "success", "session_id": session_id, "result": result}

@app.post("/sessions/{session_id}/input")
async def send_input(session_id: str, request: Request):
    data = await request.json()
    command = data.get("command")

    if not command:
        raise HTTPException(status_code=400, detail="command is required")

    result = await send_to_session(session_id, command)
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
