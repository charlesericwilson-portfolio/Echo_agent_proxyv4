from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
from src.heartbeat.monitor import get_summary
from src.pty_backend.session_manager import SessionManager

app = FastAPI(title="Echo Agent Orchestrator v4 - TMUX Edition")
session_manager = SessionManager()

class ToolCall(BaseModel):
    action: str
    session_id: str
    command: str = None

@app.post("/tool")
async def handle_tool_call(call: ToolCall):
    try:
        if call.action == "create_session":
            result = await session_manager.create_session(call.session_id, call.command or "bash -i")
            return {"status": "success", "session_id": call.session_id, "message": result}

        elif call.action == "send_command":
            if not call.command:
                raise HTTPException(status_code=400, detail="Command is required")

            # Get raw output from session
            raw_output = await session_manager.send_command(call.session_id, call.command)

            # Summarize + save to DB
            summary = await get_summary(call.session_id, raw_output)

            return {"session_id": call.session_id, "output": summary}

        else:
            raise HTTPException(status_code=400, detail="Invalid action")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "healthy", "components": ["Echo", "Session Manager (TMUX)", "Summarizer"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
