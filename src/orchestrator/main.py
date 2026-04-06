#!/usr/bin/env python3
"""
Echo Agent Orchestrator v1.4 - Improved Live Logging + Colors
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from colorama import init, Fore, Style

from src.heartbeat.monitor import HeartbeatMonitor
from src.pty_backend.session_manager import create_session as pty_create_session, send_to_session

init(autoreset=True)

heartbeat = HeartbeatMonitor()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"{Fore.CYAN}🚀 Starting Echo Agent Orchestrator v1.4 - Live Mode{Style.RESET_ALL}")
    task = asyncio.create_task(heartbeat.start())
    print(f"{Fore.GREEN}   ❤️ Heartbeat Monitor started{Style.RESET_ALL}")
    yield
    print(f"{Fore.YELLOW}Shutting down...{Style.RESET_ALL}")
    heartbeat.stop()
    task.cancel()

app = FastAPI(title="Echo Agent Orchestrator v1.4", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "✅ Echo Agent Orchestrator v1.4 is running", "status": "healthy"}

@app.post("/sessions")
async def create_new_session(request: Request):
    data = await request.json()
    session_id = data.get("session_id") or data.get("name")
    command = data.get("command", "bash -i")
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id is required")

    print(f"{Fore.BLUE}→ Creating session: {session_id} | Command: {command}{Style.RESET_ALL}")
    result = await pty_create_session(session_id, command)
    print(f"{Fore.GREEN}✓ Session '{session_id}' created{Style.RESET_ALL}")
    return result

@app.post("/sessions/{session_id}/input")
async def send_input(session_id: str, request: Request):
    data = await request.json()
    command = data.get("command")
    if not command:
        raise HTTPException(status_code=400, detail="command is required")

    print(f"{Fore.MAGENTA}→ Sending to session '{session_id}': {command}{Style.RESET_ALL}")
    result = await send_to_session(session_id, command)
    print(f"{Fore.GREEN}✓ Command executed on '{session_id}'{Style.RESET_ALL}")
    return result

@app.post("/tool")
async def tool_call(request: Request):
    data = await request.json()
    action = data.get("action")
    session_id = data.get("session_id")
    command = data.get("command")

    print(f"{Fore.BLUE}Tool call received → Action: {action} | Session: {session_id} | Command: {command}{Style.RESET_ALL}")

    if action == "create_session":
        result = await pty_create_session(session_id, command)
        print(f"{Fore.GREEN}✓ Created session '{session_id}'{Style.RESET_ALL}")
        return result
    elif action == "send_command":
        result = await send_to_session(session_id, command)
        print(f"{Fore.GREEN}✓ Sent command to '{session_id}'{Style.RESET_ALL}")
        return result
    else:
        raise HTTPException(status_code=400, detail=f"Unknown action: {action}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
