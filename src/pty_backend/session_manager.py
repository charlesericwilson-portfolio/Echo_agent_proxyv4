"""
PTY Session Manager - Fixed v1.5 (non-blocking FD)
"""

import asyncio
import os
import pty
import subprocess
from typing import Dict, Optional

active_sessions: Dict[str, 'PTYSession'] = {}

class PTYSession:
    def __init__(self, session_id: str, command: str):
        self.session_id = session_id
        self.command = command
        self.master_fd: Optional[int] = None
        self.proc = None

    async def start(self):
        master, slave = pty.openpty()
        self.master_fd = master
        os.set_blocking(self.master_fd, False)   # ← THIS FIXES THE HANG

        self.proc = subprocess.Popen(
            self.command.split(),
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True,
            start_new_session=True,
        )
        os.close(slave)
        print(f"[PTY] ✅ Session '{self.session_id}' started (PID {self.proc.pid})")

    async def send_command(self, command: str):
        if not self.master_fd:
            return {"error": "Session not started"}
        try:
            await asyncio.to_thread(
                os.write, self.master_fd, (command.rstrip() + "\n").encode('utf-8')
            )
            await asyncio.sleep(0.6)   # small delay to let output appear
            return {"status": "sent"}
        except Exception as e:
            print(f"[PTY] Write error: {e}")
            return {"error": str(e)}

    async def get_output(self) -> str:
        if not self.master_fd:
            return ""
        try:
            # Try multiple short reads to catch more output
            output = ""
            for _ in range(3):   # up to 3 quick reads
                try:
                    data = await asyncio.to_thread(os.read, self.master_fd, 8192)
                    if data:
                        output += data.decode('utf-8', errors='ignore')
                    else:
                        break
                except (BlockingIOError, OSError):
                    break
            return output
        except Exception as e:
            print(f"[PTY] Read error: {e}")
            return ""

async def create_session(session_id: str, command: str = "bash -i"):
    if session_id in active_sessions:
        return {"status": "exists", "session_id": session_id}
    session = PTYSession(session_id, command)
    await session.start()
    active_sessions[session_id] = session
    return {"status": "created", "session_id": session_id}

async def send_to_session(session_id: str, command: str):
    if session_id not in active_sessions:
        return {"error": f"Session {session_id} not found"}
    session = active_sessions[session_id]
    await session.send_command(command)
    output = await session.get_output()
    import re
    clean = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', output)
    return {"session_id": session_id, "output": clean.strip()}
