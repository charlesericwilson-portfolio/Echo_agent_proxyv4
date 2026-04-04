"""
PTY Session Manager for Echo Agent Proxy
"""

import asyncio
import os
import pty
import subprocess
from typing import Dict

active_sessions: Dict[str, 'PTYSession'] = {}

class PTYSession:
    def __init__(self, session_id: str, command: str):
        self.session_id = session_id
        self.command = command
        self.proc = None
        self.master_fd = None

    async def start(self):
        master, slave = pty.openpty()
        self.master_fd = master

        self.proc = subprocess.Popen(
            self.command.split(),
            preexec_fn=os.setsid,
            stdin=slave,
            stdout=slave,
            stderr=slave,
            close_fds=True
        )
        os.close(slave)
        print(f"[PTY] Session '{self.session_id}' started with: {self.command}")

    async def send_command(self, command: str):
        if self.master_fd:
            os.write(self.master_fd, (command + "\n").encode('utf-8'))
            await asyncio.sleep(0.5)   # Small delay to allow output

    def get_output(self):
        if not self.master_fd:
            return ""
        try:
            data = os.read(self.master_fd, 8192)
            if data:
                return data.decode('utf-8', errors='ignore')
            return ""
        except:
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
    
    await active_sessions[session_id].send_command(command)
    output = active_sessions[session_id].get_output()
    return {"session_id": session_id, "output": output}
