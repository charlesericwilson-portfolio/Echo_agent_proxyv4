import asyncio
import subprocess
from datetime import datetime

class SessionManager:
    def __init__(self):
        self.active_sessions = {}  # session_id -> tmux_name

    async def create_session(self, session_id: str, command: str = "bash -i"):
        if session_id in self.active_sessions:
            return f"Session '{session_id}' already exists"

        tmux_name = f"echo_{session_id}"
        try:
            subprocess.run(["tmux", "new-session", "-d", "-s", tmux_name, command], check=True)
            self.active_sessions[session_id] = tmux_name
            return f"Session '{session_id}' created"
        except Exception as e:
            return f"Failed to create session: {str(e)}"

    async def send_command(self, session_id: str, command: str):
        if session_id not in self.active_sessions:
            return f"Session '{session_id}' not found"

        tmux_name = self.active_sessions[session_id]

        # Safety check
        if self.is_dangerous_command(command):
            return f"Blocked: {command}"

        try:
            # Send command
            subprocess.run(["tmux", "send-keys", "-t", tmux_name, command, "Enter"], check=True)
            await asyncio.sleep(1.5)  # give time for output

            # Capture recent output
            result = subprocess.run(
                ["tmux", "capture-pane", "-p", "-S", "-300", "-t", tmux_name],
                capture_output=True, text=True, check=True
            )

            raw = result.stdout
            cleaned = self.clean_output(raw, command)
            return cleaned

        except Exception as e:
            return f"Error: {str(e)}"

    def is_dangerous_command(self, command: str) -> bool:
        dangerous = [
            "rm -rf", "rm --recursive", "sudo rm", "rm -rf /",
            "dd if=/dev/zero", "> /dev/sda", "mkfs", "format", "shred",
            "chmod -R 777", "chown -R", "shutdown", "reboot",
        ]
        return any(d in command.lower() for d in dangerous)

    def clean_output(self, output: str, original_command: str) -> str:
        lines = output.splitlines()
        cleaned = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.startswith(("eric@", "root@", "msf >", "msf exploit")):
                continue
            if line == original_command:
                continue
            if "===ECHO_" in line:
                continue
            cleaned.append(line)
        return "\n".join(cleaned[-120:])  # last 120 meaningful lines

    async def close_session(self, session_id: str):
        if session_id in self.active_sessions:
            tmux_name = self.active_sessions[session_id]
            subprocess.run(["tmux", "kill-session", "-t", tmux_name], check=False)
            del self.active_sessions[session_id]
