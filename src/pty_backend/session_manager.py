import asyncio
import subprocess
from datetime import datetime

class SessionManager:
    def __init__(self):
        self.active_sessions = {}
        self._sync_active_sessions()

    def _session_exists(self, tmux_name: str) -> bool:
        try:
            result = subprocess.run(
                ["tmux", "has-session", "-t", tmux_name],
                capture_output=True, check=False, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def _sync_active_sessions(self):
        try:
            result = subprocess.run(
                ["tmux", "list-sessions", "-F", "#{session_name}"],
                capture_output=True, text=True, timeout=5, check=False
            )
            if result.returncode == 0:
                for name in result.stdout.strip().splitlines():
                    if name.startswith("echo_"):
                        session_id = name[5:]
                        self.active_sessions[session_id] = name
        except:
            pass

    async def create_session(self, session_id: str, command: str = "bash -i"):
        tmux_name = f"echo_{session_id}"

        if session_id in self.active_sessions:
            if self._session_exists(tmux_name):
                return f"Session '{session_id}' already active"
            else:
                del self.active_sessions[session_id]

        if self._session_exists(tmux_name):
            self.active_sessions[session_id] = tmux_name
            return f"Session '{session_id}' re-entered"

        try:
            subprocess.run(["tmux", "new-session", "-d", "-s", tmux_name, command], check=True)
            self.active_sessions[session_id] = tmux_name
            return f"Session '{session_id}' created"
        except Exception as e:
            return f"Failed to create session: {str(e)}"

    async def send_command(self, session_id: str, command: str):
        if session_id not in self.active_sessions:
            await self.create_session(session_id, "bash -i")

        if session_id not in self.active_sessions:
            return f"Session '{session_id}' not found"

        tmux_name = self.active_sessions[session_id]

        if self.is_dangerous_command(command):
            return f"Blocked: {command}"

        try:
            ts = str(int(datetime.now().timestamp() * 1000))
            start = f"===ECHO_START_{ts}==="
            end = f"===ECHO_END_{ts}==="

            full_cmd = f"echo '{start}'; {command}; echo '{end}'"
            subprocess.run(["tmux", "send-keys", "-t", tmux_name, full_cmd, "Enter"], check=True)

            output = ""
            for _ in range(300):
                result = subprocess.run(
                    ["tmux", "capture-pane", "-p", "-S", "-500", "-t", tmux_name],
                    capture_output=True, text=True, check=True
                )
                output = result.stdout
                if end in output:
                    break
                await asyncio.sleep(0.5)

            if end not in output:
                return "Timed out"

            start_idx = output.rfind(start)
            end_idx = output.rfind(end)
            raw = output[start_idx + len(start):end_idx].strip() if start_idx != -1 and end_idx != -1 else ""

            if not raw:
                raw = "\n".join(output.splitlines()[-30:])

            return self.clean_output(raw, command)

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
        """Only remove the marker flags — pass everything else to the summarizer"""
        lines = output.splitlines()
        cleaned = [line for line in lines if "===ECHO_" not in line]
        return "\n".join(cleaned)

    async def close_session(self, session_id: str):
        if session_id in self.active_sessions:
            tmux_name = self.active_sessions[session_id]
            subprocess.run(["tmux", "kill-session", "-t", tmux_name], check=False)
            del self.active_sessions[session_id]
